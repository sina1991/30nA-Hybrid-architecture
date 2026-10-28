"""Synchronous, cancellable Worker execution. Subprocess isolation is NOT a sandbox."""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile


@dataclass(frozen=True)
class ExecutionError:
    code: str
    message: str
    retryable: bool = False


@dataclass(frozen=True)
class ExecutionResult:
    execution_id: str
    worker_id: str
    accepted: bool
    status: str
    result: object = None
    error: ExecutionError | None = None
    children: tuple = ()


class WorkerRuntime:
    def __init__(self, artifact_provider, definitions=None, max_depth=3, max_children=8,
                 max_concurrent=16, max_artifact_bytes=16 * 1024 * 1024,
                 max_output_bytes=1024 * 1024):
        if any(type(n) is not int or n < 0 for n in (max_depth, max_children, max_concurrent)):
            raise ValueError('Limits must be nonnegative integers')
        self.provider = artifact_provider
        self.definitions = {} if definitions is None else dict(definitions)
        self.max_depth, self.max_children = max_depth, max_children
        self.max_artifact_bytes, self.max_output_bytes = max_artifact_bytes, max_output_bytes
        self._capacity = threading.BoundedSemaphore(max_concurrent)
        self._lock = threading.RLock()
        self._history = {}
        self._keys = {}  # key -> (canonical request fingerprint, execution id)
        self._active = {}  # execution id -> Popen
        self._cancelled = set()
        self._parents = {}  # execution id -> parent execution id

    def get(self, execution_id):
        with self._lock:
            return self._history.get(execution_id)

    @staticmethod
    def _terminate(proc):
        try:
            if os.name == 'posix':
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except ProcessLookupError:
            pass

    def cancel(self, execution_id):
        """Request cancellation of a known nonterminal execution and its descendants."""
        with self._lock:
            pending = [execution_id]
            seen = set()
            processes = []
            affected = False
            while pending:
                current = pending.pop()
                if current in seen:
                    continue
                seen.add(current)
                state = self._history.get(current)
                if state is None or state.status in {'succeeded', 'failed', 'cancelled'}:
                    continue
                affected = True
                self._cancelled.add(current)
                if current in self._active:
                    processes.append(self._active[current])
                pending.extend(k for k, p in self._parents.items() if p == current)
        for proc in processes:
            self._terminate(proc)
        return affected

    def _finish(self, eid, wid, status, *, result=None, error=None, accepted=True, children=()):
        with self._lock:
            if eid in self._cancelled:
                status, result, error = 'cancelled', None, ExecutionError('CANCELLED', 'Execution cancelled')
            response = ExecutionResult(eid, wid, accepted, status, result, error, tuple(children))
            self._history[eid] = response
            return response

    def submit(self, request):
        eid = getattr(request, 'execution_id', None)
        wid = getattr(getattr(request, 'definition', None), 'worker_id', '')
        if not isinstance(eid, str) or not eid.strip():
            raise ValueError('execution_id must be a nonempty string')
        finish = lambda status, **kw: self._finish(eid, wid, status, **kw)
        try:
            definition = request.definition
            if not all(isinstance(getattr(definition, k), str) and getattr(definition, k) for k in
                       ('worker_id', 'artifact_id', 'artifact_hash', 'entrypoint')):
                raise ValueError('Invalid worker definition')
            if not isinstance(request.configuration, dict) or not isinstance(request.input_payload, dict):
                raise ValueError('Input and configuration must be JSON objects')
            if type(request.depth) is not int or request.depth < 0 or request.depth > self.max_depth:
                return finish('failed', accepted=False, error=ExecutionError('DEPTH_LIMIT', 'Child depth exceeded'))
            timeout = request.timeout_seconds
            if isinstance(timeout, bool) or not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or timeout <= 0:
                raise ValueError('timeout_seconds must be finite and positive')
            key = request.idempotency_key
            if key is not None and (not isinstance(key, str) or not key.strip()):
                raise ValueError('idempotency_key must be a nonempty string')
            fingerprint = json.dumps([definition.worker_id, definition.artifact_id,
                definition.artifact_hash, definition.entrypoint, request.configuration,
                request.input_payload, timeout, request.depth], sort_keys=True, allow_nan=False)
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', definition.artifact_hash):
                # Keep the existing bad-hash behavior for syntactically invalid hashes.
                return finish('failed', error=ExecutionError('ARTIFACT_HASH_MISMATCH', 'Invalid artifact hash'))
            module, sep, function = definition.entrypoint.partition(':')
            if not sep or not all(part.isidentifier() for part in module.split('.')) or not function.isidentifier():
                raise ValueError('Invalid entrypoint')
        except (AttributeError, TypeError, ValueError, OverflowError) as exc:
            return finish('failed', accepted=False, error=ExecutionError('INVALID_INPUT', str(exc)[:256]))

        with self._lock:
            if key is not None and key in self._keys:
                prior_fingerprint, prior_id = self._keys[key]
                if prior_fingerprint != fingerprint:
                    return ExecutionResult(eid, wid, False, 'failed', error=ExecutionError('IDEMPOTENCY_CONFLICT', 'Key reused with different request'))
                return self._history[prior_id]
            if eid in self._history:
                return ExecutionResult(eid, wid, False, 'failed', error=ExecutionError('EXECUTION_CONFLICT', 'Execution ID already used'))
            self._history[eid] = ExecutionResult(eid, wid, True, 'accepted')
            if key is not None:
                self._keys[key] = (fingerprint, eid)
        return self._execute(request, finish)

    def _execute(self, request, finish):
        eid = request.execution_id
        wid = request.definition.worker_id
        deadline = time.monotonic() + request.timeout_seconds
        with self._lock:
            if eid in self._cancelled:
                return finish('cancelled')
        try:
            source = self.provider.fetch(request.definition.artifact_id)
            if not isinstance(source, bytes) or len(source) > self.max_artifact_bytes:
                raise ValueError('Artifact must be bytes within size limit')
        except Exception:
            return finish('failed', error=ExecutionError('ARTIFACT_UNAVAILABLE', 'Artifact could not be fetched', True))
        if 'sha256:' + hashlib.sha256(source).hexdigest() != request.definition.artifact_hash:
            return finish('failed', error=ExecutionError('ARTIFACT_HASH_MISMATCH', 'Artifact hash mismatch'))
        try:
            with zipfile.ZipFile(BytesIO(source)) as z:
                names = z.namelist()
                if len(names) > 1024 or any(n.startswith('/') or '\\' in n or
                    any(part in {'.', '..'} for part in PurePosixPath(n).parts) or
                    (z.getinfo(n).external_attr >> 16) & 0o170000 == 0o120000
                    for n in names):
                    raise ValueError('Unsafe archive')
                module = request.definition.entrypoint.split(':')[0].replace('.', '/')
                if module + '.py' not in names and module + '/__init__.py' not in names:
                    raise ValueError('Entrypoint missing')
                if sum(info.file_size for info in z.infolist()) > self.max_artifact_bytes * 4:
                    raise ValueError('Archive expanded size exceeds limit')
        except (ValueError, zipfile.BadZipFile, OSError):
            return finish('failed', error=ExecutionError('ARTIFACT_INVALID', 'Invalid artifact archive'))
        if not self._capacity.acquire(blocking=False):
            return finish('failed', accepted=False, error=ExecutionError('CAPACITY_EXCEEDED', 'Runtime capacity exceeded', True))
        return self._run_subprocess(request, finish, source, deadline)

    def _run_subprocess(self, request, finish, source, deadline):
        eid = request.execution_id
        wid = request.definition.worker_id
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'artifact.zip'
            archive.write_bytes(source)
            runner = Path(__file__).with_name('_runner.py')
            try:
                proc = subprocess.Popen([sys.executable, '-I', str(runner), str(archive),
                    request.definition.entrypoint], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, text=True, start_new_session=True)
            except OSError:
                self._capacity.release()
                return finish('failed', error=ExecutionError('EXECUTION_ERROR', 'Cannot start worker'))
            with self._lock:
                self._active[eid] = proc
                self._history[eid] = ExecutionResult(eid, wid, True, 'running')
                cancelled = eid in self._cancelled
            if cancelled:
                self._terminate(proc)
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(proc.args, request.timeout_seconds)
                stdout, _ = proc.communicate(json.dumps({'input': request.input_payload,
                    'configuration': request.configuration}), timeout=remaining)
            except subprocess.TimeoutExpired:
                self._terminate(proc)
                proc.communicate()
                return finish('failed', error=ExecutionError('TIMEOUT', 'Execution timed out', True))
            except (BrokenPipeError, OSError):
                self._terminate(proc)
                proc.communicate()
                return finish('failed', error=ExecutionError('EXECUTION_ERROR', 'Worker process interrupted'))
            finally:
                with self._lock:
                    self._active.pop(eid, None)
                self._capacity.release()
            with self._lock:
                if eid in self._cancelled:
                    return finish('cancelled')
            if proc.returncode != 0 or len(stdout.encode('utf-8')) > self.max_output_bytes:
                return finish('failed', error=ExecutionError('EXECUTION_ERROR', 'Worker failed or output exceeded limit'))
            try:
                output = json.loads(stdout)
                if not isinstance(output, dict) or type(output.get('ok')) is not bool:
                    raise ValueError('Invalid worker response')
                if not output['ok']:
                    return finish('failed', error=ExecutionError('EXECUTION_ERROR', 'Worker raised an error'))
                result = output['result']
            except (ValueError, KeyError, TypeError):
                return finish('failed', error=ExecutionError('EXECUTION_ERROR', 'Invalid worker response'))
            children = []
            if isinstance(result, dict) and 'children' in result:
                specs = result['children']
                if not isinstance(specs, list) or len(specs) > self.max_children:
                    return finish('failed', error=ExecutionError('CHILD_LIMIT', 'Invalid child list'))
                for spec in specs:
                    with self._lock:
                        if eid in self._cancelled:
                            return finish('cancelled', children=children)
                    if not isinstance(spec, dict) or not isinstance(spec.get('worker_id'), str) or not isinstance(spec.get('input', {}), dict):
                        return finish('failed', error=ExecutionError('INVALID_INPUT', 'Invalid child specification'), children=children)
                    definition = self.definitions.get(spec['worker_id'])
                    if definition is None:
                        return finish('failed', error=ExecutionError('CHILD_NOT_FOUND', 'Child worker missing'), children=children)
                    if time.monotonic() >= deadline:
                        return finish('failed', error=ExecutionError('TIMEOUT', 'Execution timed out', True), children=children)
                    from types import SimpleNamespace
                    child_id = str(uuid.uuid4())
                    with self._lock:
                        self._parents[child_id] = eid
                    child = self.submit(SimpleNamespace(definition=definition, input_payload=spec.get('input', {}),
                        configuration={}, execution_id=child_id, timeout_seconds=max(.001, deadline - time.monotonic()),
                        idempotency_key=None, depth=request.depth + 1))
                    children.append(child)
                    if child.status != 'succeeded':
                        with self._lock:
                            was_cancelled = eid in self._cancelled
                        return finish('cancelled' if was_cancelled else 'failed',
                            error=ExecutionError('CHILD_FAILED', 'Child execution failed'), children=children)
                result = result.get('value')
            return finish('succeeded', result=result, children=children)
