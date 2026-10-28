import sys
import tempfile
import unittest
from pathlib import Path

UNIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UNIT.parent))
# Hyphenated unit directory is loaded as a package alias for these tests.
import importlib.util
spec = importlib.util.spec_from_file_location("data_manager", UNIT / "__init__.py",
    submodule_search_locations=[str(UNIT)])
pkg = importlib.util.module_from_spec(spec)
sys.modules["data_manager"] = pkg
spec.loader.exec_module(pkg)

from data_manager.storage import SQLiteStorage
from data_manager.services import DataService
from data_manager.errors import Forbidden, InvalidInput, NotFound


class DataManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.service = DataService(SQLiteStorage(str(Path(self.tmp.name) / "test.db")))
        self.model = {
            "model_id": "sample",
            "owner_id": "manager-a",
            "version": "1.0.0",
            "fields": {"name": {"type": "string"}, "count": {"type": "integer"}},
            "required": ["name"],
        }
        self.service.register_model("manager-a", self.model)
        self.service.create_resource("manager-a", {
            "resource_id": "resource-a", "model_id": "sample", "model_version": "1.0.0"
        })

    def test_register_and_read_record(self):
        written = self.service.write_record("manager-a", "resource-a", {"name": "alpha"})
        read = self.service.read_record("manager-a", "resource-a", written["record_id"])
        self.assertEqual(read["data"], {"name": "alpha"})

    def test_invalid_record_rejected(self):
        with self.assertRaises(InvalidInput):
            self.service.write_record("manager-a", "resource-a", {"name": 12})

    def test_unknown_record_fields_are_rejected(self):
        with self.assertRaises(InvalidInput):
            self.service.write_record(
                "manager-a", "resource-a",
                {"name": "alpha", "unexpected": "value"},
            )

    def test_missing_required_record_fields_are_rejected(self):
        with self.assertRaises(InvalidInput):
            self.service.write_record(
                "manager-a", "resource-a", {"count": 3}
            )

    def test_boolean_is_not_accepted_as_integer(self):
        with self.assertRaises(InvalidInput):
            self.service.write_record(
                "manager-a", "resource-a",
                {"name": "alpha", "count": True},
            )

    def test_non_string_required_field_name_is_rejected(self):
        from data_manager.validation import validate_model

        invalid = {**self.model, "required": [["name"]]}
        with self.assertRaises(InvalidInput):
            validate_model(invalid)

    def test_invalid_required_field_name_is_rejected(self):
        from data_manager.validation import validate_model

        invalid = {**self.model, "required": ["missing"]}
        with self.assertRaises(InvalidInput):
            validate_model(invalid)

    def test_unsupported_model_field_type_is_rejected(self):
        from data_manager.validation import validate_model

        invalid = {
            **self.model,
            "fields": {"name": {"type": "unsupported"}},
        }
        with self.assertRaises(InvalidInput):
            validate_model(invalid)

    def test_owner_boundary(self):
        with self.assertRaises(Forbidden):
            self.service.get_resource("manager-b", "resource-a")

    def test_missing_record(self):
        with self.assertRaises(NotFound):
            self.service.read_record("manager-a", "resource-a", "missing")

    def test_duplicate_model_version_conflict(self):
        changed = {**self.model, "fields": {"other": {"type": "string"}}, "required": []}
        from data_manager.errors import Conflict
        with self.assertRaises(Conflict):
            self.service.register_model("manager-a", changed)


    def test_patch_preserves_unspecified_fields(self):
        created = self.service.write_record(
            "manager-a", "resource-a", {"name": "alpha", "count": 7}
        )
        updated = self.service.patch_record(
            "manager-a", "resource-a", created["record_id"], {"name": "beta"}
        )
        self.assertEqual(updated["data"], {"name": "beta", "count": 7})

    def test_put_replaces_complete_record(self):
        created = self.service.write_record(
            "manager-a", "resource-a", {"name": "alpha", "count": 7}
        )
        updated = self.service.replace_record(
            "manager-a", "resource-a", created["record_id"], {"name": "beta"}
        )
        self.assertEqual(updated["data"], {"name": "beta"})

    def test_duplicate_record_id_conflicts_instead_of_overwriting(self):
        from data_manager.errors import Conflict

        self.service.write_record(
            "manager-a", "resource-a", {"name": "alpha"}, "fixed-record"
        )
        with self.assertRaises(Conflict):
            self.service.write_record(
                "manager-a", "resource-a", {"name": "beta"}, "fixed-record"
            )
        stored = self.service.read_record(
            "manager-a", "resource-a", "fixed-record"
        )
        self.assertEqual(stored["data"], {"name": "alpha"})

    def test_schema_migrations_reach_current_version(self):
        version = self.service.storage.one(
            "SELECT MAX(version) AS version FROM dm_schema_version"
        )["version"]
        self.assertEqual(version, 2)

    def test_foreign_keys_are_enforced(self):
        import sqlite3

        with self.assertRaises(sqlite3.IntegrityError):
            self.service.storage.execute(
                """INSERT INTO dm_records(resource_id, record_id, data)
                   VALUES(?,?,?)""",
                ("missing-resource", "record-x", '{"name":"x"}'),
            )


if __name__ == "__main__":
    unittest.main()
