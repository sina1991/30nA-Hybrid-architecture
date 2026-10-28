import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worker_manager import (
    Schedule,
    WorkerDefinition,
    WorkerLifecycle,
    WorkerManager,
    WorkerManagerError,
)
from worker_manager.service import WorkerConflict, WorkerNotFound


class WorkerManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = WorkerManager()
        self.definition = WorkerDefinition(
            worker_id="example-worker",
            artifact_id="artifact-001",
            artifact_hash="sha256:example",
            entrypoint="worker.main:run",
        )

    def test_register_defaults_to_configured_and_manual_schedule(self):
        record = self.manager.register(self.definition)
        self.assertEqual(record.lifecycle, WorkerLifecycle.CONFIGURED)
        self.assertEqual(record.schedule, Schedule(kind="manual"))
        self.assertEqual(record.configuration, {})

    def test_duplicate_registration_is_rejected(self):
        self.manager.register(self.definition)
        with self.assertRaises(WorkerConflict):
            self.manager.register(self.definition)

    def test_same_worker_id_cannot_be_rebound_to_other_artifact(self):
        self.manager.register(self.definition)
        changed = WorkerDefinition(
            worker_id="example-worker",
            artifact_id="artifact-002",
            artifact_hash="sha256:other",
            entrypoint="worker.main:run",
        )
        with self.assertRaises(WorkerConflict):
            self.manager.register(changed)

    def test_configure_enable_disable(self):
        self.manager.register(self.definition)
        configured = self.manager.configure(
            self.definition.worker_id,
            configuration={"batch_size": 100},
            schedule=Schedule(kind="interval", interval_seconds=30),
        )
        self.assertEqual(configured.configuration["batch_size"], 100)
        self.assertEqual(configured.schedule.interval_seconds, 30)
        self.assertEqual(
            self.manager.enable(self.definition.worker_id).lifecycle,
            WorkerLifecycle.ENABLED,
        )
        self.assertEqual(
            self.manager.disable(self.definition.worker_id).lifecycle,
            WorkerLifecycle.DISABLED,
        )

    def test_list_is_sorted_by_worker_id(self):
        self.manager.register(self.definition)
        self.manager.register(
            WorkerDefinition("alpha", "artifact-a", "hash-a", "pkg:run")
        )
        self.assertEqual([r.definition.worker_id for r in self.manager.list()], [
            "alpha", "example-worker"
        ])

    def test_missing_worker_raises_domain_error(self):
        with self.assertRaises(WorkerNotFound):
            self.manager.get("missing")
        with self.assertRaises(WorkerManagerError):
            self.manager.remove("missing")

    def test_schedule_validation(self):
        with self.assertRaises(ValueError):
            Schedule(kind="interval", interval_seconds=0)
        with self.assertRaises(ValueError):
            Schedule(kind="cron")
        with self.assertRaises(ValueError):
            Schedule(kind="manual", interval_seconds=5)

    def test_definition_requires_explicit_artifact_and_entrypoint(self):
        with self.assertRaises(ValueError):
            WorkerDefinition("w", "", "hash", "pkg:run")
        with self.assertRaises(ValueError):
            WorkerDefinition("w", "a", "hash", "invalid-entrypoint")


if __name__ == "__main__":
    unittest.main()
