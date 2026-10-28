"""Agent 08: WorkerManager -> real WorkerRuntime -> read-only output API.

DEMO mode uses a local immutable ZIP artifact provider, NOT Code Manager.
CODE_MANAGER mode uses the existing public Artifact API and fails closed if unavailable.
This process owns the interval schedule; Dashboard never executes code.
"""
from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from threading import Event, Lock, Thread
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'units' / 'worker-manager'))
sys.path.insert(0, str(ROOT / 'units' / 'worker-runtime'))
from worker_manager import WorkerManager, WorkerDefinition, Schedule
from worker_runtime import WorkerRuntime, CodeManagerArtifactProvider
from worker_runtime.loopback_artifact_provider import LoopbackArtifactProvider

HERE = Path(__file__).resolve().parent
WORKER_ID = 'agent08-modules-ok'
ARTIFACT_ID = 'agent08-modules-ok@1'


def artifact_bytes():
    source = (HERE / 'script' / 'modules_ok.py').read_bytes()
    stream = BytesIO()
    with ZipFile(stream, 'w', compression=ZIP_DEFLATED) as archive:
        info = ZipInfo('modules_ok.py', date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o100600 << 16
        archive.writestr(info, source)
    return stream.getvalue()


class DemoArtifactProvider:
    """Explicit DEMO provider; does not impersonate Code Manager."""
    def __init__(self, data):
        self.data = data

    def fetch(self, artifact_id):
        if artifact_id != ARTIFACT_ID:
            raise KeyError(artifact_id)
        return self.data


class Integration:
    def __init__(self, mode='demo', interval=1):
        if interval != 1:
            raise ValueError('This integration proof uses interval=1 second')
        data = artifact_bytes()
        if mode == 'demo':
            provider = DemoArtifactProvider(data)
        elif mode == 'code-manager':
            url = os.environ['AGENT08_CODE_MANAGER_URL']
            auth = os.environ.get('AGENT08_CODE_MANAGER_AUTHORIZATION')
            if not auth:
                credentials_directory = os.environ.get('CREDENTIALS_DIRECTORY')
                if not credentials_directory:
                    raise RuntimeError('Agent 08 Code Manager credential is unavailable')
                token_path = Path(credentials_directory) / 'code-manager-token'
                token = token_path.read_text(encoding='utf-8').strip()
                if not token or any(char.isspace() for char in token):
                    raise RuntimeError('Agent 08 Code Manager credential is invalid')
                auth = 'Bearer ' + token
            provider = (LoopbackArtifactProvider(url, auth) if url.startswith('http://')
                        else CodeManagerArtifactProvider(url, auth))
        else:
            raise ValueError('mode must be demo or code-manager')
        self.mode = mode
        self.runtime = WorkerRuntime(provider)
        self.manager = WorkerManager(runtime_gateway=self.runtime)
        definition = WorkerDefinition(WORKER_ID, ARTIFACT_ID,
                                      'sha256:' + sha256(data).hexdigest(), 'modules_ok:main')
        self.manager.register(definition, schedule=Schedule(kind='interval', interval_seconds=interval))
        self.manager.enable(WORKER_ID)
        self.lock = Lock()
        self.state = {'type': 'text', 'data': None, 'status': 'pending',
                      'source': 'worker-runtime', 'mode': mode, 'sequence': 0}
        self.stop_event = Event()

    def execute_once(self):
        result = self.manager.request_execution(WORKER_ID, timeout_seconds=5)
        with self.lock:
            sequence = self.state['sequence'] + 1
            self.state = {
                'type': 'text',
                'data': result.result if result.status == 'succeeded' else None,
                'status': result.status,
                'source': 'worker-runtime',
                'mode': self.mode,
                'sequence': sequence,
                'execution_id': result.execution_id,
                'worker_id': result.worker_id,
                'timestamp': time.time(),
                'error': asdict(result.error) if result.error else None,
            }
        return result

    def run_loop(self):
        next_tick = time.monotonic()
        while not self.stop_event.is_set():
            try:
                self.execute_once()
            except Exception as exc:
                with self.lock:
                    self.state = {**self.state, 'status': 'failed', 'error': {'code': 'INTEGRATION_ERROR', 'message': type(exc).__name__}}
            next_tick += 1.0
            delay = next_tick - time.monotonic()
            if delay < 0:
                next_tick = time.monotonic()
                delay = 0
            self.stop_event.wait(delay)

    def snapshot(self):
        with self.lock:
            return dict(self.state)


def serve(integration, host='127.0.0.1', port=8098):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if urlsplit(self.path).path != '/v1/modules/agent08-modules-ok/output':
                self.send_error(404)
                return
            body = json.dumps(integration.snapshot(), allow_nan=False).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            return

    Thread(target=integration.run_loop, daemon=True).start()
    server = ThreadingHTTPServer((host, port), Handler)
    try:
        server.serve_forever()
    finally:
        integration.stop_event.set()
        server.server_close()


if __name__ == '__main__':
    mode = os.getenv('AGENT08_ARTIFACT_MODE', 'demo')
    integration = Integration(mode=mode)
    serve(integration)
