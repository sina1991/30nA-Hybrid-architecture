"""Owner-scoped lookup and integrity verification for registered sources."""

from __future__ import annotations

import hashlib
from typing import Any

from .blob_storage import BlobStorage
from .data_manager_client import DataManagerAPIError
from .errors import BlobIntegrityError, CodeManagerError
from .source_registration import SourceRegistrationService


class SourceNotFound(CodeManagerError):
    """The requested source version does not exist for this owner."""


class SourceIntegrityError(CodeManagerError):
    """Source metadata or stored source bytes failed integrity checks."""


class SourceRegistry:
    """Read source metadata through DATA MANAGER and bytes through BlobStorage."""

    def __init__(self, blob_storage: BlobStorage, data_manager_client: Any):
        if not isinstance(blob_storage, BlobStorage):
            raise TypeError("blob_storage must be a BlobStorage instance")
        self.blob_storage = blob_storage
        self.data_manager = data_manager_client

    def _owner_records(self, owner_id: str) -> tuple[str, list[dict]]:
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id must come from trusted identity context")

        resource_id = SourceRegistrationService._resource_id(owner_id)
        try:
            resource = self.data_manager.get_resource(resource_id)
        except DataManagerAPIError as exc:
            if exc.status == 404 or exc.code == "RESOURCE_NOT_FOUND":
                # Do not disclose whether another owner's source exists.
                raise SourceNotFound("Source was not found") from exc
            raise

        if (
            resource.get("resource_id") != resource_id
            or resource.get("model_id")
            != SourceRegistrationService._model_id(owner_id)
            or resource.get("model_version") != "1.0.0"
        ):
            raise SourceIntegrityError("Source metadata resource contract mismatch")

        response = self.data_manager.list_records(resource_id)
        if isinstance(response, dict):
            records = response.get("records")
        else:
            records = response

        if not isinstance(records, list) or any(
            not isinstance(record, dict) for record in records
        ):
            raise SourceIntegrityError("Invalid source metadata records response")

        return resource_id, records

    @staticmethod
    def _metadata(record: dict) -> dict:
        metadata = record.get("data")
        if not isinstance(metadata, dict):
            raise SourceIntegrityError("Source metadata record is malformed")

        required = (
            "source_id",
            "source_version",
            "source_hash",
            "blob_digest",
            "entrypoint",
            "input_schema",
            "output_schema",
            "contract_dependencies",
            "calculation_version",
        )
        if any(key not in metadata for key in required):
            raise SourceIntegrityError("Source metadata is incomplete")

        return metadata

    def list_sources(self, *, owner_id: str) -> list[dict]:
        """Return registered source versions, including an owner's empty registry."""
        try:
            resource_id, records = self._owner_records(owner_id)
        except SourceNotFound:
            return []
        result = []

        for record in records:
            metadata = self._metadata(record)
            result.append({
                "source_id": metadata["source_id"],
                "source_version": metadata["source_version"],
                "source_hash": metadata["source_hash"],
                "entrypoint": metadata["entrypoint"],
                "calculation_version": metadata["calculation_version"],
                "resource_id": resource_id,
                "record_id": record.get("record_id"),
            })

        return result

    def get_source(
        self,
        *,
        owner_id: str,
        source_id: str,
        source_version: str,
    ) -> dict:
        """Find an owner's exact source version and verify its stored ZIP bytes."""
        resource_id, records = self._owner_records(owner_id)

        for record in records:
            metadata = self._metadata(record)
            if (
                metadata.get("source_id") != source_id
                or metadata.get("source_version") != source_version
            ):
                continue

            source_hash = metadata.get("source_hash")
            blob_digest = metadata.get("blob_digest")

            if (
                not isinstance(source_hash, str)
                or not isinstance(blob_digest, str)
                or source_hash != blob_digest
            ):
                raise SourceIntegrityError(
                    "Source hash and blob digest do not match"
                )

            try:
                source_bytes = self.blob_storage.get_bytes(blob_digest)
            except (BlobIntegrityError, OSError, ValueError) as exc:
                raise SourceIntegrityError(
                    "Stored source blob failed integrity verification"
                ) from exc

            actual_hash = hashlib.sha256(source_bytes).hexdigest()
            if actual_hash != source_hash:
                raise SourceIntegrityError(
                    "Stored ZIP bytes do not match registered source hash"
                )

            return {
                **metadata,
                "resource_id": resource_id,
                "record_id": record.get("record_id"),
                "source_bytes": source_bytes,
            }

        raise SourceNotFound(
            f"Source version {source_id!r} {source_version!r} was not found"
        )
