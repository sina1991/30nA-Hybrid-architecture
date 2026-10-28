"""Owner-scoped, immutable publication of registered source ZIP artifacts.

Publication is explicit: registering a source never publishes an artifact.
Manifests are atomically linked into place and never overwritten by this module.
This component does not execute source code or change DATA MANAGER persistence.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from .errors import BlobIntegrityError

_ARTIFACT_ID = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]{0,63})@([A-Za-z0-9][A-Za-z0-9._-]{0,63})$"
)
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_ARTIFACT_BYTES = 16 * 1024 * 1024


class ArtifactNotFound(Exception):
    """No published artifact is visible to this owner."""


class ArtifactInvalid(ValueError):
    """An artifact reference or source is invalid."""


class ArtifactConflict(Exception):
    """An immutable artifact identity already has different metadata."""


class ArtifactIntegrityError(Exception):
    """A published manifest or its blob is missing, corrupt, or inconsistent."""


def _identity(owner_id: str, artifact_id: str) -> tuple[str, str]:
    if not isinstance(owner_id, str) or not owner_id or len(owner_id) > 512:
        raise ArtifactInvalid("Invalid authenticated owner")
    if not isinstance(artifact_id, str):
        raise ArtifactInvalid("Invalid artifact ID")
    match = _ARTIFACT_ID.fullmatch(artifact_id)
    if match is None:
        raise ArtifactInvalid("Expected source_id@source_version")
    return match.group(1), match.group(2)


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


class PublishedArtifactRegistry:
    """Local publication registry backed by immutable JSON manifests.

    The root must be a trusted, persistent directory writable only by the
    CODE MANAGER service account. A trusted identity provider must supply
    owner_id; never accept it from an HTTP request body.
    """

    def __init__(self, blob_storage, root=None, max_bytes=_MAX_ARTIFACT_BYTES):
        from .blob_storage import BlobStorage

        if not isinstance(blob_storage, BlobStorage):
            raise TypeError("blob_storage must be BlobStorage")
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
            raise ValueError("max_bytes must be a positive integer")
        self.blob_storage = blob_storage
        self.max_bytes = max_bytes
        self.root = (Path(root) if root is not None else
                     blob_storage.root / "published-artifacts").expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _path(self, owner_id: str, artifact_id: str) -> Path:
        _identity(owner_id, artifact_id)
        key = hashlib.sha256(_canonical({"owner_id": owner_id,
                                         "artifact_id": artifact_id})).hexdigest()
        return self.root / key[:2] / (key + ".json")

    def _read(self, owner_id: str, artifact_id: str) -> dict:
        path = self._path(owner_id, artifact_id)
        try:
            raw = path.read_bytes()
        except FileNotFoundError as exc:
            raise ArtifactNotFound("Artifact has not been published") from exc
        except OSError as exc:
            raise ArtifactIntegrityError("Manifest cannot be read") from exc
        if len(raw) > 65536:
            raise ArtifactIntegrityError("Manifest exceeds maximum size")
        try:
            metadata = json.loads(raw.decode("ascii"))
        except (ValueError, UnicodeError) as exc:
            raise ArtifactIntegrityError("Invalid manifest") from exc
        if not isinstance(metadata, dict) or _canonical(metadata) != raw:
            raise ArtifactIntegrityError("Manifest is not canonical")
        if (metadata.get("owner_id") != owner_id or
                metadata.get("artifact_id") != artifact_id or
                metadata.get("artifact_type") not in {"source_zip", "built_artifact"} or
                metadata.get("manifest_version") != 1 or
                not isinstance(metadata.get("entrypoint"), str) or
                not metadata["entrypoint"] or
                type(metadata.get("size_bytes")) is not int or
                not 0 < metadata["size_bytes"] <= self.max_bytes or
                not isinstance(metadata.get("blob_digest"), str) or
                _DIGEST.fullmatch(metadata["blob_digest"]) is None or
                metadata.get("artifact_hash") != "sha256:" + metadata["blob_digest"]):
            raise ArtifactIntegrityError("Manifest identity or metadata mismatch")
        if metadata["artifact_type"] == "built_artifact":
            if (not isinstance(metadata.get("source_hash"), str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", metadata["source_hash"]) is None
                    or not isinstance(metadata.get("build_id"), str)
                    or re.fullmatch(r"[0-9a-f]{32}", metadata["build_id"]) is None
                    or not isinstance(metadata.get("provenance"), dict)
                    or metadata["provenance"].get("artifact_hash") != metadata.get("artifact_hash")
                    or metadata["provenance"].get("source_hash") != metadata.get("source_hash")
                    or metadata.get("source_id") != _identity(owner_id, artifact_id)[0]
                    or metadata.get("source_version") != _identity(owner_id, artifact_id)[1]
                    or metadata.get("artifact_version") != metadata.get("blob_digest")
                    or not isinstance(metadata.get("build_version"), str)
                    or not metadata["build_version"]
                    or not isinstance(metadata.get("calculation_version"), str)
                    or not metadata["calculation_version"]
                    or metadata.get("validation_status") != "passed"
                    or metadata.get("dependency_lock") != "stdlib-only"
                    or not isinstance(metadata.get("input_schema"), dict)
                    or not isinstance(metadata.get("output_schema"), dict)
                    or len(_canonical(metadata["input_schema"])) > 16384
                    or len(_canonical(metadata["output_schema"])) > 16384):
                raise ArtifactIntegrityError("Built artifact provenance is missing or inconsistent")
        return metadata

    def get(self, owner_id: str, artifact_id: str) -> tuple[dict, bytes]:
        """Return verified metadata and byte-exact content, or fail closed."""
        metadata = self._read(owner_id, artifact_id)
        try:
            data = self.blob_storage.get_bytes(metadata["blob_digest"])
        except (FileNotFoundError, BlobIntegrityError, OSError, ValueError) as exc:
            raise ArtifactIntegrityError("Published blob failed verification") from exc
        if len(data) != metadata["size_bytes"] or len(data) > self.max_bytes:
            raise ArtifactIntegrityError("Published blob size mismatch")
        public = {key: value for key, value in metadata.items() if key != "owner_id"}
        return public, data

    def publish(self, registry, owner_id: str, artifact_id: str) -> tuple[dict, bool]:
        """Publish an existing registered source ZIP. Returns (metadata, created).

        Repeated publication of the same immutable source is idempotent.
        No source is executed or transformed. Concurrent publishers converge
        on a single manifest via an atomic hard link (no replacement).
        """
        source_id, source_version = _identity(owner_id, artifact_id)
        source = registry.get_source(owner_id=owner_id, source_id=source_id,
                                     source_version=source_version)
        data = source["source_bytes"]
        if not isinstance(data, bytes) or not 0 < len(data) <= self.max_bytes:
            raise ArtifactInvalid("Source ZIP exceeds artifact size limit")
        digest = hashlib.sha256(data).hexdigest()
        if digest != source.get("source_hash"):
            raise ArtifactIntegrityError("Registered source digest mismatch")
        entrypoint = source.get("entrypoint")
        if not isinstance(entrypoint, str) or not entrypoint:
            raise ArtifactInvalid("Source entrypoint is invalid")
        try:
            self.blob_storage.put_bytes(data, expected_digest=digest)
        except (BlobIntegrityError, OSError) as exc:
            raise ArtifactIntegrityError("Artifact blob could not be stored") from exc
        metadata = {
            "manifest_version": 1,
            "owner_id": owner_id,
            "artifact_id": artifact_id,
            "artifact_type": "source_zip",
            "artifact_hash": "sha256:" + digest,
            "blob_digest": digest,
            "entrypoint": entrypoint,
            "size_bytes": len(data),
        }
        encoded = _canonical(metadata)
        path = self._path(owner_id, artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary_path = None
        created = False
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                             prefix=".manifest-", delete=False) as temp:
                temporary_path = Path(temp.name)
                os.chmod(temporary_path, 0o600)
                temp.write(encoded)
                temp.flush()
                os.fsync(temp.fileno())
            try:
                os.link(temporary_path, path)
                created = True
                directory_fd = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except FileExistsError:
                pass
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        existing = self._read(owner_id, artifact_id)
        if existing != metadata:
            raise ArtifactConflict("Artifact identity already published differently")
        public, _ = self.get(owner_id, artifact_id)
        return public, created

    def get_built(self, owner_id: str, artifact_id: str) -> tuple[dict, bytes]:
        """Return only a built artifact; registered/source ZIPs are never downloadable here."""
        metadata, data = self.get(owner_id, artifact_id)
        if metadata.get("artifact_type") != "built_artifact":
            raise ArtifactNotFound("A validated built artifact has not been published")
        return metadata, data

    def publish_built(
        self, owner_id: str, artifact_id: str, data: bytes, *,
        entrypoint: str, source_hash: str, build_id: str, provenance: dict,
        artifact_version: str | None = None,
        build_version: str = "code-manager-build-v1",
        calculation_version: str = "1.0.0",
        dependency_lock: str = "stdlib-only",
        input_schema: dict | None = None,
        output_schema: dict | None = None,
        validation_status: str = "passed",
    ) -> tuple[dict, bool]:
        """Publish only a pipeline-produced artifact with a verified immutable digest."""
        source_id, source_version = _identity(owner_id, artifact_id)
        if not isinstance(data, bytes) or not 0 < len(data) <= self.max_bytes:
            raise ArtifactInvalid("Built artifact exceeds the configured size limit")
        if not isinstance(source_hash, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", source_hash) is None:
            raise ArtifactInvalid("Invalid source SHA-256")
        if not isinstance(build_id, str) or re.fullmatch(r"[0-9a-f]{32}", build_id) is None:
            raise ArtifactInvalid("Invalid build ID")
        if not isinstance(entrypoint, str) or not entrypoint:
            raise ArtifactInvalid("Invalid built artifact entrypoint")
        if not isinstance(provenance, dict):
            raise ArtifactInvalid("Build provenance must be an object")
        digest = hashlib.sha256(data).hexdigest()
        if artifact_version is None:
            artifact_version = digest
        if artifact_version != digest:
            raise ArtifactInvalid("Artifact version must match the content digest")
        if not isinstance(build_version, str) or not build_version:
            raise ArtifactInvalid("Build version is required")
        if not isinstance(calculation_version, str) or not calculation_version:
            raise ArtifactInvalid("Calculation version is required")
        if dependency_lock != "stdlib-only":
            raise ArtifactInvalid("Unsupported dependency lock policy")
        if validation_status != "passed":
            raise ArtifactInvalid("Only passed build artifacts may be published")
        input_schema = {} if input_schema is None else input_schema
        output_schema = {} if output_schema is None else output_schema
        if not isinstance(input_schema, dict) or not isinstance(output_schema, dict):
            raise ArtifactInvalid("Artifact schemas must be objects")
        if len(_canonical(input_schema)) > 16384 or len(_canonical(output_schema)) > 16384:
            raise ArtifactInvalid("Artifact schema exceeds manifest limits")
        artifact_hash = "sha256:" + digest
        safe_provenance = dict(provenance)
        if safe_provenance.get("source_hash") != source_hash or safe_provenance.get("artifact_hash") != artifact_hash:
            raise ArtifactInvalid("Build provenance does not match artifact hashes")
        try:
            self.blob_storage.put_bytes(data, expected_digest=digest)
        except (BlobIntegrityError, OSError) as exc:
            raise ArtifactIntegrityError("Built artifact blob could not be stored") from exc
        metadata = {
            "manifest_version": 1, "owner_id": owner_id, "artifact_id": artifact_id,
            "artifact_type": "built_artifact", "artifact_hash": artifact_hash,
            "blob_digest": digest, "entrypoint": entrypoint, "size_bytes": len(data),
            "source_id": source_id, "source_version": source_version,
            "artifact_version": artifact_version, "build_version": build_version,
            "calculation_version": calculation_version, "dependency_lock": dependency_lock,
            "input_schema": input_schema, "output_schema": output_schema,
            "validation_status": validation_status,
            "source_hash": source_hash, "build_id": build_id, "provenance": safe_provenance,
        }
        path = self._path(owner_id, artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if path.exists():
            existing = self._read(owner_id, artifact_id)
            if (existing.get("artifact_type") == "built_artifact"
                    and existing.get("artifact_hash") == artifact_hash
                    and existing.get("source_hash") == source_hash
                    and existing.get("entrypoint") == entrypoint
                    and existing.get("size_bytes") == len(data)
                    and existing.get("build_version") == build_version
                    and existing.get("calculation_version") == calculation_version
                    and existing.get("dependency_lock") == dependency_lock
                    and existing.get("input_schema") == input_schema
                    and existing.get("output_schema") == output_schema
                    and existing.get("provenance") == safe_provenance):
                public, _ = self.get_built(owner_id, artifact_id)
                return public, False
            raise ArtifactConflict("Artifact identity already has a different publication")
        encoded = _canonical(metadata)
        temporary_path = None
        created = False
        try:
            with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                             prefix=".manifest-", delete=False) as temp:
                temporary_path = Path(temp.name)
                os.chmod(temporary_path, 0o600)
                temp.write(encoded)
                temp.flush()
                os.fsync(temp.fileno())
            try:
                os.link(temporary_path, path)
                created = True
                directory_fd = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except FileExistsError:
                existing = self._read(owner_id, artifact_id)
                if (existing.get("artifact_type") != "built_artifact"
                        or existing.get("artifact_hash") != artifact_hash
                        or existing.get("source_hash") != source_hash
                        or existing.get("entrypoint") != entrypoint
                        or existing.get("size_bytes") != len(data)
                        or existing.get("build_version") != build_version
                        or existing.get("calculation_version") != calculation_version
                        or existing.get("dependency_lock") != dependency_lock
                        or existing.get("input_schema") != input_schema
                        or existing.get("output_schema") != output_schema
                        or existing.get("provenance") != safe_provenance):
                    raise ArtifactConflict("Artifact identity already has a different publication")
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        public, _ = self.get_built(owner_id, artifact_id)
        return public, created

