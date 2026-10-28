import hashlib
import tempfile
from concurrent.futures import ThreadPoolExecutor
import unittest
from pathlib import Path

from code_manager.blob_storage import BlobStorage
from code_manager.published_artifacts import (
    ArtifactConflict, ArtifactIntegrityError, ArtifactInvalid,
    ArtifactNotFound, PublishedArtifactRegistry,
)


class Registry:
    def __init__(self, data=b'PK\x03\x04fixture', entrypoint='sample.main:run'):
        self.data = data
        self.entrypoint = entrypoint

    def get_source(self, *, owner_id, source_id, source_version):
        if owner_id != 'alice' or (source_id, source_version) != ('demo', '1'):
            from code_manager.source_registry import SourceNotFound
            raise SourceNotFound('not found')
        return {'source_bytes': self.data,
                'source_hash': hashlib.sha256(self.data).hexdigest(),
                'entrypoint': self.entrypoint}


class PublishedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.blobs = BlobStorage(Path(self.tmp.name) / 'blobs')
        self.publications = PublishedArtifactRegistry(self.blobs)
        self.registry = Registry()

    def test_not_available_before_explicit_publish(self):
        with self.assertRaises(ArtifactNotFound):
            self.publications.get('alice', 'demo@1')

    def test_publish_preserves_exact_bytes_and_hash(self):
        metadata, created = self.publications.publish(self.registry, 'alice', 'demo@1')
        self.assertTrue(created)
        returned, data = self.publications.get('alice', 'demo@1')
        self.assertEqual(data, self.registry.data)
        self.assertEqual(returned, metadata)
        self.assertEqual(metadata['artifact_hash'], 'sha256:' + hashlib.sha256(data).hexdigest())
        self.assertEqual(metadata['artifact_type'], 'source_zip')
        self.assertNotIn('owner_id', metadata)

    def test_idempotent_across_registry_instances(self):
        self.publications.publish(self.registry, 'alice', 'demo@1')
        other = PublishedArtifactRegistry(self.blobs)
        _, created = other.publish(self.registry, 'alice', 'demo@1')
        self.assertFalse(created)

    def test_changed_source_conflicts(self):
        self.publications.publish(self.registry, 'alice', 'demo@1')
        with self.assertRaises(ArtifactConflict):
            self.publications.publish(Registry(data=b'changed'), 'alice', 'demo@1')

    def test_owner_isolation(self):
        self.publications.publish(self.registry, 'alice', 'demo@1')
        with self.assertRaises(ArtifactNotFound):
            self.publications.get('bob', 'demo@1')

    def test_invalid_ids(self):
        for value in ('../x@1', 'demo@../1', 'demo/1', 'demo@1/../../etc', ''):
            with self.subTest(value=value), self.assertRaises(ArtifactInvalid):
                self.publications.get('alice', value)

    def test_tampered_blob_is_rejected(self):
        metadata, _ = self.publications.publish(self.registry, 'alice', 'demo@1')
        blob_path = self.blobs._path_for_digest(metadata['blob_digest'])
        blob_path.write_bytes(b'corrupted')
        with self.assertRaises(ArtifactIntegrityError):
            self.publications.get('alice', 'demo@1')

    def test_corrupt_manifest_is_rejected(self):
        self.publications.publish(self.registry, 'alice', 'demo@1')
        manifest_path = self.publications._path('alice', 'demo@1')
        manifest_path.write_bytes(b'{}')
        with self.assertRaises(ArtifactIntegrityError):
            self.publications.get('alice', 'demo@1')

    def test_size_limit(self):
        limited = PublishedArtifactRegistry(self.blobs, max_bytes=3)
        with self.assertRaises(ArtifactInvalid):
            limited.publish(self.registry, 'alice', 'demo@1')


if __name__ == '__main__':
    unittest.main()
