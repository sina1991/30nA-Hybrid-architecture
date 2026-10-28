import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worker_manager import Schedule, WorkerDefinition, WorkerLifecycle, WorkerManager
from worker_manager.service import WorkerConflict, WorkerNotFound
from worker_manager.sqlite_store import SQLiteWorkerStore


class SQLiteWorkerStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "workers.sqlite3"
        self.definition = WorkerDefinition(
            "example-worker", "artifact-001", "sha256:abc", "worker.main:run"
        )
        self.store = SQLiteWorkerStore(self.database)

    def test_worker_metadata_survives_manager_restart(self):
        manager = WorkerManager(store=self.store)
        manager.register(
            self.definition,
            configuration={"batch_size": 25, "enabled_feature": True},
            schedule=Schedule(kind="interval", interval_seconds=60),
        )
        manager.enable("example-worker")

        restarted = WorkerManager(store=SQLiteWorkerStore(self.database))
        record = restarted.get("example-worker")
        self.assertEqual(record.lifecycle, WorkerLifecycle.ENABLED)
        self.assertEqual(record.configuration, {"batch_size": 25, "enabled_feature": True})
        self.assertEqual(record.schedule, Schedule(kind="interval", interval_seconds=60))
        self.assertEqual(record.definition, self.definition)

    def test_configuration_and_lifecycle_mutations_are_persisted(self):
        manager = WorkerManager(store=self.store)
        manager.register(self.definition)
        manager.configure("example-worker", configuration={"mode": "safe"})
        manager.enable("example-worker")
        manager.disable("example-worker")

        record = WorkerManager(store=SQLiteWorkerStore(self.database)).get("example-worker")
        self.assertEqual(record.configuration, {"mode": "safe"})
        self.assertEqual(record.lifecycle, WorkerLifecycle.DISABLED)

    def test_duplicate_registration_across_manager_instances_is_rejected(self):
        first = WorkerManager(store=self.store)
        second = WorkerManager(store=SQLiteWorkerStore(self.database))
        first.register(self.definition)
        with self.assertRaises(WorkerConflict):
            second.register(self.definition)

    def test_remove_persists(self):
        manager = WorkerManager(store=self.store)
        manager.register(self.definition)
        manager.remove("example-worker")
        self.assertEqual(WorkerManager(store=SQLiteWorkerStore(self.database)).list(), ())

    def test_non_json_configuration_is_rejected_without_memory_mutation(self):
        manager = WorkerManager(store=self.store)
        manager.register(self.definition)
        with self.assertRaises(ValueError):
            manager.configure("example-worker", configuration={"not_json": object()})
        self.assertEqual(manager.get("example-worker").configuration, {})

    def test_missing_worker_is_consistent(self):
        with self.assertRaises(WorkerNotFound):
            WorkerManager(store=self.store).get("missing")


if __name__ == "__main__":
    unittest.main()
