import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worker_manager import (
    ExecutionRequest,
    RuntimeGatewayUnavailable,
    WorkerDefinition,
    WorkerLifecycle,
    WorkerManager,
    WorkerNotEnabled,
    WorkerNotFound,
)


class FakeRuntimeGateway:
    def __init__(self):
        self.requests = []
        self.response = {"test_result": "accepted"}
        self.error = None

    def submit(self, request):
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.response


class RuntimeGatewayIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.gateway = FakeRuntimeGateway()
        self.manager = WorkerManager(runtime_gateway=self.gateway)
        self.definition = WorkerDefinition(
            worker_id="worker-1",
            artifact_id="artifact-1",
            artifact_hash="sha256:abc123",
            entrypoint="sample.worker:run",
        )

    def register_enabled(self, **kwargs):
        self.manager.register(self.definition, **kwargs)
        return self.manager.enable(self.definition.worker_id)

    def test_enabled_worker_request_reaches_gateway_with_exact_identity(self):
        self.register_enabled(configuration={"batch_size": 20})

        response = self.manager.request_execution(
            "worker-1",
            input_payload={"items": [1, 2, 3]},
        )

        self.assertEqual(response, {"test_result": "accepted"})
        self.assertEqual(len(self.gateway.requests), 1)
        request = self.gateway.requests[0]
        self.assertIsInstance(request, ExecutionRequest)
        self.assertEqual(request.definition.artifact_id, "artifact-1")
        self.assertEqual(request.definition.artifact_hash, "sha256:abc123")
        self.assertEqual(request.definition.entrypoint, "sample.worker:run")
        self.assertEqual(request.configuration, {"batch_size": 20})
        self.assertEqual(request.input_payload, {"items": [1, 2, 3]})

    def test_configured_worker_is_not_submitted(self):
        self.manager.register(self.definition)

        with self.assertRaises(WorkerNotEnabled):
            self.manager.request_execution("worker-1")

        self.assertEqual(self.gateway.requests, [])

    def test_disabled_worker_is_not_submitted(self):
        self.register_enabled()
        self.manager.disable("worker-1")

        with self.assertRaises(WorkerNotEnabled):
            self.manager.request_execution("worker-1")

        self.assertEqual(self.gateway.requests, [])

    def test_unknown_worker_is_not_submitted(self):
        with self.assertRaises(WorkerNotFound):
            self.manager.request_execution("missing")

        self.assertEqual(self.gateway.requests, [])

    def test_missing_gateway_rejects_execution(self):
        manager = WorkerManager()
        manager.register(self.definition)
        manager.enable("worker-1")

        with self.assertRaises(RuntimeGatewayUnavailable):
            manager.request_execution("worker-1")

    def test_gateway_error_is_propagated(self):
        self.register_enabled()
        self.gateway.error = RuntimeError("adapter failure")

        with self.assertRaisesRegex(RuntimeError, "adapter failure"):
            self.manager.request_execution("worker-1")

        self.assertEqual(len(self.gateway.requests), 1)

    def test_non_mapping_input_is_rejected(self):
        self.register_enabled()

        with self.assertRaises(ValueError):
            self.manager.request_execution(
                "worker-1",
                input_payload=["not", "a", "mapping"],
            )

        self.assertEqual(self.gateway.requests, [])

    def test_default_input_is_empty_mapping(self):
        self.register_enabled()
        self.manager.request_execution("worker-1")

        self.assertEqual(self.gateway.requests[0].input_payload, {})
        self.assertEqual(
            self.manager.get("worker-1").lifecycle,
            WorkerLifecycle.ENABLED,
        )


if __name__ == "__main__":
    unittest.main()
