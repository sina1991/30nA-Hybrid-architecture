"""Source registration orchestration for CODE MANAGER.

The authenticated API boundary must supply owner_id from trusted identity
context, never directly from an untrusted request body.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .blob_storage import BlobStorage
from .data_manager_client import DataManagerAPIError
from .errors import CodeManagerError, SourceValidationError
from .source_archive import ArchiveLimits, inspect_source_archive


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_METADATA_MODEL_ID = "code_source_metadata"
_METADATA_MODEL_VERSION = "1.0.0"


class SourceRegistrationError(CodeManagerError):
    """Raised when source metadata cannot be registered safely."""


class SourceVersionConflict(SourceRegistrationError):
    """Raised when an existing source version is submitted with new content."""


class SourceRegistrationService:
    """Store original source bytes and register their metadata via DATA MANAGER."""

    def __init__(
        self,
        blob_storage: BlobStorage,
        data_manager_client: Any,
        *,
        archive_limits: ArchiveLimits | None = None,
    ) -> None:
        if not isinstance(blob_storage, BlobStorage):
            raise TypeError("blob_storage must be a BlobStorage instance")
        if archive_limits is not None and not isinstance(archive_limits, ArchiveLimits):
            raise TypeError("archive_limits must be an ArchiveLimits instance")

        self.blob_storage = blob_storage
        self.data_manager = data_manager_client
        self.archive_limits = archive_limits

    @staticmethod
    def _validate_identifier(value: str, name: str) -> str:
        if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
            raise SourceValidationError(f"{name} is not a valid identifier")
        return value

    @staticmethod
    def _validate_schema(value: Any, name: str) -> dict:
        if not isinstance(value, dict):
            raise SourceValidationError(f"{name} must be a JSON Schema object")
        if value.get("type") not in (None, "object"):
            raise SourceValidationError(f"{name} must describe an object")
        return value

    @staticmethod
    def _model_id(owner_id: str) -> str:
        # DATA MANAGER model IDs are globally unique per version.
        suffix = hashlib.sha256(owner_id.encode("utf-8")).hexdigest()[:32]
        return f"code_source_meta_{suffix}"

    @staticmethod
    def _metadata_model(owner_id: str) -> dict:
        return {
            "model_id": SourceRegistrationService._model_id(owner_id),
            "owner_id": owner_id,
            "version": _METADATA_MODEL_VERSION,
            "fields": {
                "source_id": {"type": "string"},
                "source_version": {"type": "string"},
                "source_hash": {"type": "string"},
                "blob_digest": {"type": "string"},
                "entrypoint": {"type": "string"},
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
                "contract_dependencies": {"type": "array"},
                "calculation_version": {"type": "string"},
                "archive_size": {"type": "integer"},
                "entry_count": {"type": "integer"},
                "expanded_size": {"type": "integer"},
            },
            "required": [
                "source_id",
                "source_version",
                "source_hash",
                "blob_digest",
                "entrypoint",
                "input_schema",
                "output_schema",
                "contract_dependencies",
                "calculation_version",
                "archive_size",
                "entry_count",
                "expanded_size",
            ],
        }

    @staticmethod
    def _resource_id(owner_id: str) -> str:
        # Avoid embedding email addresses or other identity strings in IDs.
        suffix = hashlib.sha256(owner_id.encode("utf-8")).hexdigest()[:32]
        return f"code_sources_{suffix}"

    def _ensure_metadata_resource(self, owner_id: str) -> str:
        model = self._metadata_model(owner_id)
        self.data_manager.register_model(model)

        resource_id = self._resource_id(owner_id)
        model_id = self._model_id(owner_id)
        try:
            self.data_manager.create_resource({
                "resource_id": resource_id,
                "model_id": model_id,
                "model_version": _METADATA_MODEL_VERSION,
            })
        except DataManagerAPIError as exc:
            if exc.status != 409:
                raise

            # A conflict is acceptable only if the existing resource uses the
            # expected model contract. Never silently reuse another resource.
            existing = self.data_manager.get_resource(resource_id)
            if (
                existing.get("resource_id") != resource_id
                or existing.get("model_id") != model_id
                or existing.get("model_version") != _METADATA_MODEL_VERSION
            ):
                raise SourceRegistrationError(
                    "Existing metadata resource has an incompatible contract"
                ) from exc

        return resource_id

    @staticmethod
    def _records(response: Any) -> list[dict]:
        if isinstance(response, list):
            return response
        if isinstance(response, dict) and isinstance(response.get("records"), list):
            return response["records"]
        raise SourceRegistrationError(
            "DATA MANAGER returned an invalid records response"
        )

    def register_source(
        self,
        *,
        owner_id: str,
        source_id: str,
        source_version: str,
        source_bytes: bytes,
        entrypoint: str,
        input_schema: dict,
        output_schema: dict,
        contract_dependencies: list[str] | None = None,
        calculation_version: str = "1.0.0",
    ) -> dict:
        """Register a ZIP source version without extracting or executing it.

        The source hash is calculated from the exact submitted ZIP bytes.
        Published-artifact creation and execution are intentionally out of scope.
        """
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise SourceValidationError("owner_id must come from trusted identity")
        self._validate_identifier(source_id, "source_id")

        if (
            not isinstance(source_version, str)
            or not source_version.strip()
            or len(source_version) > 128
        ):
            raise SourceValidationError("source_version must be a non-empty string")

        if not isinstance(source_bytes, bytes):
            raise SourceValidationError("source_bytes must be bytes")

        input_schema = self._validate_schema(input_schema, "input_schema")
        output_schema = self._validate_schema(output_schema, "output_schema")

        if contract_dependencies is None:
            contract_dependencies = []
        if (
            not isinstance(contract_dependencies, list)
            or any(
                not isinstance(item, str) or not item.strip()
                for item in contract_dependencies
            )
        ):
            raise SourceValidationError(
                "contract_dependencies must be a list of non-empty strings"
            )

        if (
            not isinstance(calculation_version, str)
            or not calculation_version.strip()
            or len(calculation_version) > 128
        ):
            raise SourceValidationError("calculation_version must be non-empty")

        inspection = inspect_source_archive(
            source_bytes,
            entrypoint,
            limits=self.archive_limits,
        )

        # Store exact original bytes before metadata registration. If the
        # metadata API fails, the blob is harmless and can be reconciled later.
        blob_digest = self.blob_storage.put_bytes(
            source_bytes,
            expected_digest=inspection.source_hash,
        )

        resource_id = self._ensure_metadata_resource(owner_id)
        existing_records = self._records(
            self.data_manager.list_records(resource_id)
        )

        for record in existing_records:
            data = record.get("data", {})
            if (
                data.get("source_id") == source_id
                and data.get("source_version") == source_version
            ):
                if data.get("source_hash") != inspection.source_hash:
                    raise SourceVersionConflict(
                        "Source version already exists with different ZIP bytes"
                    )
                return {
                    "source_id": source_id,
                    "source_version": source_version,
                    "source_hash": inspection.source_hash,
                    "blob_digest": blob_digest,
                    "resource_id": resource_id,
                    "record_id": record.get("record_id"),
                    "idempotent": True,
                }

        metadata = {
            "source_id": source_id,
            "source_version": source_version,
            "source_hash": inspection.source_hash,
            "blob_digest": blob_digest,
            "entrypoint": inspection.entrypoint,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "contract_dependencies": contract_dependencies,
            "calculation_version": calculation_version,
            "archive_size": inspection.archive_size,
            "entry_count": inspection.entry_count,
            "expanded_size": inspection.expanded_size,
        }

        # Do not automatically retry this POST: DATA MANAGER does not yet
        # provide a record-creation idempotency key.
        created = self.data_manager.write_record(resource_id, metadata)

        record_id = (
            created.get("record_id") if isinstance(created, dict) else None
        )
        return {
            "source_id": source_id,
            "source_version": source_version,
            "source_hash": inspection.source_hash,
            "blob_digest": blob_digest,
            "resource_id": resource_id,
            "record_id": record_id,
            "idempotent": False,
        }
