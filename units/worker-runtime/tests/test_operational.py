import hashlib
import io
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[2] / 'worker-manager'), str(Path(__file__).resolve().parents[1])]
from worker_manager import WorkerManager, WorkerDefinition
from worker_runtime import WorkerRuntime, CodeManagerArtifactProvider, SQLiteExecutionStore, ExecutionResult


def artifact(code):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        z.writestr('task.py', code)
    return buffer.getvalue()


class Provider:
    def __init__(self, sources):
        self.sources = sources
    def fetch(self, name):
        return self.sources[name]


class OperationalTests(unittest.TestCase):
    def setUp(self):
        self.sources = {'slow': artifact('import time\ndef run(input, configuration):\n time.sleep(3)\n return 1\n'),
                        'fast': artifact('def run(input, configuration):\n return input\n'),
                        'parent': artifact('def run(input, configuration):\n return {"value":1,"children":[{"worker_id":"slow"}]}\n'),
                        'flood': artifact('def run(input, configuration):\n while True: print("x" * 4096, flush=True)\n')}
        self.definitions = {k: WorkerDefinition(k, k, 'sha256:' + hashlib.sha256(v).hexdigest(), 'task:run') for k, v in self.sources.items()}
        self.runtime = WorkerRuntime(Provider(self.sources), self.definitions, max_concurrent=1)
        self.manager = WorkerManager(self.runtime)
        for definition in self.definitions.values():
            self.manager.register(definition)
            self.manager.enable(definition.worker_id)

    def background(self, worker):
        results = []
        thread = threading.Thread(target=lambda: results.append(self.manager.request_execution(worker, timeout_seconds=8)))
        thread.start()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            with self.runtime._lock:
                active = [(k, p) for k, p in self.runtime._active.items()]
            if active:
                return thread, results, active[0][0]
            time.sleep(.01)
        self.fail('Execution never started')

    def test_cancellation(self):
        thread, results, eid = self.background('slow')
        self.assertTrue(self.manager.cancel_execution(eid))
        thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0].status, 'cancelled')
        self.assertFalse(self.manager.cancel_execution(eid))
        self.assertEqual(self.manager.get_execution(eid).status, 'cancelled')

    def test_capacity_and_lifecycle(self):
        thread, results, eid = self.background('slow')
        self.manager.disable('slow')
        blocked = self.manager.request_execution('fast')
        self.assertEqual(blocked.error.code, 'CAPACITY_EXCEEDED')
        self.assertTrue(self.manager.cancel_execution(eid))
        thread.join(4)
        self.assertEqual(results[0].status, 'cancelled')

    def test_idempotency_in_flight(self):
        results = []
        thread = threading.Thread(target=lambda: results.append(self.manager.request_execution('slow', idempotency_key='same', timeout_seconds=8)))
        thread.start()
        deadline = time.monotonic() + 3
        while not self.runtime._active and time.monotonic() < deadline:
            time.sleep(.01)
        current = self.manager.request_execution('slow', idempotency_key='same', timeout_seconds=8)
        self.assertIn(current.status, ('accepted', 'running'))
        self.assertEqual(current.error, None)
        self.manager.cancel_execution(current.execution_id)
        thread.join(4)

    def test_child_cancel_and_single_capacity(self):
        thread, results, eid = self.background('parent')
        # parent may finish its process before a child becomes active
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            with self.runtime._lock:
                children = [k for k, p in self.runtime._parents.items() if p == eid]
            if children:
                break
            time.sleep(.01)
        self.assertTrue(children)
        self.manager.cancel_execution(eid)
        thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(results[0].status, 'cancelled')

    def test_runtime_rejects_invalid_resource_limits(self):
        for kwargs in ({'max_concurrent': 0}, {'max_artifact_bytes': 0},
                       {'max_output_bytes': -1}, {'max_input_bytes': 0}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    WorkerRuntime(Provider(self.sources), self.definitions, **kwargs)

    def test_input_validation(self):
        r = self.manager.request_execution('fast', timeout_seconds=float('nan'))
        self.assertEqual(r.error.code, 'INVALID_INPUT')

    def test_stdout_limit_is_enforced_while_streaming(self):
        runtime = WorkerRuntime(Provider(self.sources), self.definitions,
                                max_concurrent=1, max_output_bytes=128)
        manager = WorkerManager(runtime)
        manager.register(self.definitions['flood'])
        manager.enable('flood')
        started = time.monotonic()
        result = manager.request_execution('flood', timeout_seconds=5)
        elapsed = time.monotonic() - started
        self.assertEqual(result.status, 'failed')
        self.assertEqual(result.error.code, 'OUTPUT_LIMIT_EXCEEDED')
        self.assertLess(elapsed, 4)
        self.assertLessEqual(len(result.error.message), 128)


    def test_serialized_input_limit_is_enforced_before_execution(self):
        runtime = WorkerRuntime(Provider(self.sources), self.definitions,
                                max_concurrent=1, max_input_bytes=128)
        manager = WorkerManager(runtime)
        manager.register(self.definitions['fast'])
        manager.enable('fast')
        result = manager.request_execution('fast', input_payload={'payload': 'x' * 1024})
        self.assertEqual(result.status, 'failed')
        self.assertFalse(result.accepted)
        self.assertEqual(result.error.code, 'INVALID_INPUT')

    def test_execution_history_and_idempotency_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "runtime.sqlite3"
            first_runtime = WorkerRuntime(
                Provider(self.sources), self.definitions,
                execution_store=SQLiteExecutionStore(database),
            )
            first_manager = WorkerManager(first_runtime)
            first_manager.register(self.definitions['fast'])
            first_manager.enable('fast')
            first = first_manager.request_execution(
                'fast', input_payload={'value': 7}, idempotency_key='durable-key',
                timeout_seconds=30,
            )
            self.assertEqual(first.status, 'succeeded')

            second_runtime = WorkerRuntime(
                Provider(self.sources), self.definitions,
                execution_store=SQLiteExecutionStore(database),
            )
            second_manager = WorkerManager(second_runtime)
            second_manager.register(self.definitions['fast'])
            second_manager.enable('fast')
            replay = second_manager.request_execution(
                'fast', input_payload={'value': 7}, idempotency_key='durable-key',
                timeout_seconds=30,
            )
            self.assertEqual(replay.execution_id, first.execution_id)
            self.assertEqual(replay.result, {'value': 7})
            self.assertEqual(second_manager.get_execution(first.execution_id).status, 'succeeded')

    def test_nonterminal_snapshot_is_marked_interrupted_on_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "runtime.sqlite3"
            store = SQLiteExecutionStore(database)
            store.accept(
                ExecutionResult("inflight-id", "fast", True, "accepted"),
                idempotency_key="inflight-key",
                fingerprint="request-fingerprint",
            )
            runtime = WorkerRuntime(
                Provider(self.sources), self.definitions,
                execution_store=SQLiteExecutionStore(database),
            )
            result = runtime.get("inflight-id")
            self.assertEqual(result.status, 'failed')
            self.assertEqual(result.error.code, 'RUNTIME_RESTARTED')
            self.assertTrue(result.error.retryable)

    def test_code_manager_requires_https(self):
        with self.assertRaises(ValueError):
            CodeManagerArtifactProvider('http://localhost:8080', 'Bearer token')


if __name__ == '__main__':
    unittest.main()
