"""Immutable, content-addressed local blob storage."""

import hashlib
import os
import tempfile
from pathlib import Path

from .errors import BlobIntegrityError


class BlobStorage:
    """Store exact bytes under their SHA-256 digest.

    This component stores binary blobs only. It does not store metadata,
    access SQLite directly, or execute stored content.
    """

    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def digest(data):
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        return hashlib.sha256(data).hexdigest()

    def _path_for_digest(self, digest):
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            raise ValueError("digest must be a lowercase SHA-256 hex string")
        return self.root / digest[:2] / digest

    def put_bytes(self, data, expected_digest=None):
        """Persist exact bytes and return their SHA-256 digest."""
        actual_digest = self.digest(data)

        if expected_digest is not None and actual_digest != expected_digest:
            raise BlobIntegrityError("Content does not match expected SHA-256")

        target = self._path_for_digest(actual_digest)
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            if self.digest(target.read_bytes()) != actual_digest:
                raise BlobIntegrityError("Existing blob failed integrity check")
            return actual_digest

        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target.parent,
                prefix=".blob-",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(data)
                temporary.flush()
                os.fsync(temporary.fileno())

            # A digest identifies the content, not a caller-controlled path.
            if target.exists():
                if self.digest(target.read_bytes()) != actual_digest:
                    raise BlobIntegrityError(
                        "Existing blob failed integrity check"
                    )
                return actual_digest

            os.replace(temporary_path, target)
            temporary_path = None
            return actual_digest
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def get_bytes(self, digest):
        """Return a blob only if its stored content matches its digest."""
        target = self._path_for_digest(digest)
        try:
            data = target.read_bytes()
        except FileNotFoundError:
            raise

        if self.digest(data) != digest:
            raise BlobIntegrityError("Stored blob failed integrity check")
        return data

    def exists(self, digest):
        """Return whether an integrity-valid blob exists."""
        target = self._path_for_digest(digest)
        if not target.is_file():
            return False
        try:
            self.get_bytes(digest)
        except (OSError, BlobIntegrityError):
            return False
        return True
