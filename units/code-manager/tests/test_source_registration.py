import hashlib
import tempfile
import unittest
from pathlib import Path

from code_manager.blob_storage import BlobStorage
from code_manager.errors import SourceValidationError
from tests_support.code_manager import FakeDataManager, make_zip

from code_manager.source_registration import (
    SourceRegistrationService,
    SourceVersionConflict,
)


class SourceRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.blobs = BlobStorage(Path(self.temp_dir.name) / "blobs")
        self.data_manager = FakeDataManager()
        self.service = SourceRegistrationService(self.blobs, self.data_manager)
        self.source_bytes = make_zip()
        self.arguments = {
            "owner_id": "user-123",
            "source_id": "pricing-model",
            "source_version": "1.0.0",
            "source_bytes": self.source_bytes,
            "entrypoint": "main:run",
            "input_schema": {"type": "object", "properties": {"value": {"type": "number"}}},
            "output_schema": {"type": "object"},
        }

    def test_registers_source_and_preserves_exact_zip_bytes(self):
        result = self.service.register_source(**self.arguments)
        expected_hash = hashlib.sha256(self.source_bytes).hexdigest()

        self.assertEqual(result["source_hash"], expected_hash)
        self.assertEqual(result["blob_digest"], expected_hash)
        self.assertEqual(self.blobs.get_bytes(expected_hash), self.source_bytes)
        self.assertFalse(result["idempotent"])
        self.assertEqual(len(self.data_manager.records[result["resource_id"]]), 1)

    def test_same_version_and_same_bytes_is_idempotent(self):
        first = self.service.register_source(**self.arguments)
        second = self.service.register_source(**self.arguments)

        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(first["record_id"], second["record_id"])
        self.assertEqual(len(self.data_manager.records[first["resource_id"]]), 1)

    def test_same_version_with_different_bytes_is_rejected(self):
        self.service.register_source(**self.arguments)
        changed = dict(self.arguments)
        changed["source_bytes"] = make_zip() + b"changed"

        with self.assertRaises(SourceVersionConflict):
            self.service.register_source(**changed)

    def test_two_owners_get_distinct_metadata_models_and_resources(self):
        first = self.service.register_source(**self.arguments)

        second_args = dict(self.arguments)
        second_args["owner_id"] = "user-456"
        second_args["source_id"] = "pricing-model"
        second = self.service.register_source(**second_args)

        first_model = self.data_manager.resources[first["resource_id"]]["model_id"]
        second_model = self.data_manager.resources[second["resource_id"]]["model_id"]

        self.assertNotEqual(first["resource_id"], second["resource_id"])
        self.assertNotEqual(first_model, second_model)
        self.assertEqual(len(self.data_manager.records[first["resource_id"]]), 1)
        self.assertEqual(len(self.data_manager.records[second["resource_id"]]), 1)

    def test_invalid_source_identifier_is_rejected(self):
        changed = dict(self.arguments)
        changed["source_id"] = "../bad"

        with self.assertRaises(SourceValidationError):
            self.service.register_source(**changed)

    def test_missing_owner_identity_is_rejected(self):
        changed = dict(self.arguments)
        changed["owner_id"] = ""

        with self.assertRaises(SourceValidationError):
            self.service.register_source(**changed)


if __name__ == "__main__":
    unittest.main()
