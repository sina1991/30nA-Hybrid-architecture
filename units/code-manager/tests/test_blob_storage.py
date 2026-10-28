import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_manager.blob_storage import BlobStorage
from code_manager.errors import BlobIntegrityError


class BlobStorageTests(unittest.TestCase):
    def test_round_trip_preserves_exact_bytes(self):
        content = b"\x00ZIP\xff\r\noriginal bytes"
        with tempfile.TemporaryDirectory() as directory:
            storage = BlobStorage(directory)
            digest = storage.put_bytes(content)

            self.assertEqual(digest, hashlib.sha256(content).hexdigest())
            self.assertEqual(storage.get_bytes(digest), content)
            self.assertTrue(storage.exists(digest))

    def test_same_content_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = BlobStorage(directory)
            first = storage.put_bytes(b"same")
            second = storage.put_bytes(b"same")
            self.assertEqual(first, second)

    def test_expected_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = BlobStorage(directory)
            with self.assertRaises(BlobIntegrityError):
                storage.put_bytes(b"content", expected_digest="0" * 64)

    def test_invalid_digest_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = BlobStorage(directory)
            with self.assertRaises(ValueError):
                storage.get_bytes("../outside")


if __name__ == "__main__":
    unittest.main()
