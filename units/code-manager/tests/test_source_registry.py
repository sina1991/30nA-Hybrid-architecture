import tempfile
import unittest
from pathlib import Path

from code_manager.blob_storage import BlobStorage
from code_manager.source_registration import SourceRegistrationService
from code_manager.source_registry import (
    SourceIntegrityError,
    SourceNotFound,
    SourceRegistry,
)
from tests_support.code_manager import FakeDataManager, make_zip


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.blobs = BlobStorage(Path(self.temp_dir.name) / "blobs")
        self.data_manager = FakeDataManager()
        self.registration = SourceRegistrationService(
            self.blobs, self.data_manager
        )
        self.registry = SourceRegistry(self.blobs, self.data_manager)
        self.zip_bytes = make_zip()
        self.owner_id = "owner-1"
        self.registration.register_source(
            owner_id=self.owner_id,
            source_id="pricing",
            source_version="1.0.0",
            source_bytes=self.zip_bytes,
            entrypoint="main:run",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )

    def test_get_source_returns_exact_verified_zip_bytes(self):
        result = self.registry.get_source(
            owner_id=self.owner_id,
            source_id="pricing",
            source_version="1.0.0",
        )
        self.assertEqual(result["source_bytes"], self.zip_bytes)
        self.assertEqual(result["source_hash"], result["blob_digest"])

    def test_list_sources_returns_registered_versions(self):
        result = self.registry.list_sources(owner_id=self.owner_id)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_id"], "pricing")
        self.assertEqual(result[0]["source_version"], "1.0.0")
        self.assertNotIn("source_bytes", result[0])

    def test_unknown_source_version_is_not_found(self):
        with self.assertRaises(SourceNotFound):
            self.registry.get_source(
                owner_id=self.owner_id,
                source_id="pricing",
                source_version="9.9.9",
            )

    def test_other_owner_cannot_find_source(self):
        with self.assertRaises((SourceNotFound, KeyError)):
            self.registry.get_source(
                owner_id="another-owner",
                source_id="pricing",
                source_version="1.0.0",
            )

    def test_hash_metadata_mismatch_is_rejected(self):
        resource_id = SourceRegistrationService._resource_id(self.owner_id)
        record = self.data_manager.records[resource_id][0]
        record["data"]["source_hash"] = "0" * 64

        with self.assertRaises(SourceIntegrityError):
            self.registry.get_source(
                owner_id=self.owner_id,
                source_id="pricing",
                source_version="1.0.0",
            )

    def test_empty_owner_is_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.list_sources(owner_id="")


if __name__ == "__main__":
    unittest.main()


def test_new_owner_source_list_is_empty_without_hiding_detail_not_found(tmp_path):
    from unittest.mock import Mock
    import pytest
    from code_manager.data_manager_client import DataManagerAPIError
    from code_manager.source_registry import SourceRegistry, SourceNotFound
    from code_manager.blob_storage import BlobStorage
    client=Mock()
    client.get_resource.side_effect=DataManagerAPIError(404,'RESOURCE_NOT_FOUND','Not found')
    registry=SourceRegistry(BlobStorage(tmp_path),client)
    assert registry.list_sources(owner_id='new-owner') == []
    with pytest.raises(SourceNotFound):
        registry.get_source(owner_id='new-owner',source_id='missing',source_version='1.0.0')
