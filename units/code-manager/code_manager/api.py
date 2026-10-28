"""Framework-independent WSGI API for CODE MANAGER.

Production deployments must inject a trusted identity provider and a
DATA MANAGER client factory that preserves the authenticated owner identity.
This module never executes submitted source code.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
from urllib.parse import parse_qs, unquote

from .data_manager_client import (
    DataManagerAPIError,
    DataManagerClient,
    DataManagerClientError,
    DataManagerTransportError,
)
from .errors import CodeManagerError, SourceValidationError
from .source_archive import inspect_source_archive
from .build_pipeline import BuildPipeline
from .published_artifacts import (
    PublishedArtifactRegistry, ArtifactInvalid, ArtifactNotFound,
    ArtifactConflict, ArtifactIntegrityError,
)
from .source_registration import (
    SourceRegistrationError,
    SourceRegistrationService,
    SourceVersionConflict,
)
from .source_registry import (
    SourceIntegrityError,
    SourceNotFound,
    SourceRegistry,
)

CONTRACT_VERSION = "1.0.0"
MAX_REQUEST_BYTES = 30 * 1024 * 1024
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_CORRELATION_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class APIError(Exception):
    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        retryable: bool = False,
        context: dict | None = None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.retryable = retryable
        self.context = context or {}


class RemoteUserIdentity:
    """Resolve identity only from trusted WSGI context.

    X-Code-Manager-ID is deliberately a development-only opt-in.
    """

    def resolve(self, environ: dict) -> str:
        identity = environ.get("REMOTE_USER")

        if not identity and (
            os.environ.get("CODE_MANAGER_ALLOW_INSECURE_HEADER", "").lower()
            in {"1", "true", "yes"}
        ):
            identity = environ.get("HTTP_X_CODE_MANAGER_ID")

        if (
            not isinstance(identity, str)
            or not _ID_PATTERN.fullmatch(identity)
        ):
            raise APIError(
                401,
                "ACCESS_DENIED",
                "A valid authenticated identity is required",
            )

        return identity


def _json_response(
    start_response,
    status: int,
    payload: dict,
    correlation_id: str | None,
):
    body = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")

    phrases = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        401: "Unauthorized",
        404: "Not Found",
        409: "Conflict",
        413: "Payload Too Large",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
    }

    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
    ]
    if correlation_id:
        headers.append(("X-Correlation-ID", correlation_id))

    start_response(
        f"{status} {phrases.get(status, 'Error')}",
        headers,
    )
    return [body]


def create_application(
    *,
    blob_storage,
    data_manager_client_factory,
    identity_provider=None,
    max_request_bytes: int = MAX_REQUEST_BYTES,
    published_artifact_registry=None,
    build_pipeline=None,
):
    """Create a WSGI application with injected storage and identity adapters.

    data_manager_client_factory(owner_id) MUST return a client whose
    requests are authorized by DATA MANAGER as that owner. A production
    deployment must provide the appropriate trusted integration.
    """
    if not callable(data_manager_client_factory):
        raise TypeError("data_manager_client_factory must be callable")

    if isinstance(max_request_bytes, bool) or not isinstance(
        max_request_bytes, int
    ):
        raise ValueError("max_request_bytes must be an integer")
    if max_request_bytes < 1:
        raise ValueError("max_request_bytes must be positive")

    identity_provider = identity_provider or RemoteUserIdentity()
    if published_artifact_registry is None:
        published_artifact_registry = PublishedArtifactRegistry(blob_storage)
    if not isinstance(published_artifact_registry, PublishedArtifactRegistry):
        raise TypeError("published_artifact_registry must be a PublishedArtifactRegistry instance")
    if build_pipeline is None:
        build_pipeline = BuildPipeline(blob_storage)
    if not hasattr(build_pipeline, "run") or not hasattr(build_pipeline, "history"):
        raise TypeError("build_pipeline must provide run() and durable history")

    def application(environ, start_response):
        correlation_id = environ.get("HTTP_X_CORRELATION_ID")
        if (
            not isinstance(correlation_id, str)
            or not _CORRELATION_PATTERN.fullmatch(correlation_id)
        ):
            correlation_id = None

        def fail(status, code, message, retryable=False, context=None):
            error = {
                "code": code,
                "message": message,
                "retryable": bool(retryable),
            }
            if context:
                error["context"] = context

            return _json_response(
                start_response,
                status,
                {
                    "contract_version": CONTRACT_VERSION,
                    **(
                        {"correlation_id": correlation_id}
                        if correlation_id else {}
                    ),
                    "error": error,
                },
                correlation_id,
            )

        try:
            method = environ.get("REQUEST_METHOD", "GET").upper()
            path = environ.get("PATH_INFO", "")
            content_type = environ.get("CONTENT_TYPE", "").split(";", 1)[0].lower()

            try:
                owner_id = identity_provider.resolve(environ)
            except APIError:
                raise

            def client_and_services():
                client = data_manager_client_factory(owner_id)
                from .blob_storage import BlobStorage

                if not isinstance(blob_storage, BlobStorage):
                    raise TypeError("blob_storage must be a BlobStorage instance")

                registration = SourceRegistrationService(
                    blob_storage,
                    client,
                )
                registry = SourceRegistry(blob_storage, client)
                return registration, registry

            def read_json_body():
                raw_length = environ.get("CONTENT_LENGTH", "")
                try:
                    length = int(raw_length) if raw_length else 0
                except (TypeError, ValueError):
                    raise APIError(
                        400, "SOURCE_INVALID", "Invalid Content-Length"
                    )

                if length < 0:
                    raise APIError(
                        400, "SOURCE_INVALID", "Invalid Content-Length"
                    )
                if length > max_request_bytes:
                    raise APIError(
                        413, "SOURCE_INVALID", "Request body exceeds size limit"
                    )
                if content_type != "application/json":
                    raise APIError(
                        400,
                        "SOURCE_INVALID",
                        "Content-Type must be application/json",
                    )

                stream = environ.get("wsgi.input")
                if stream is None:
                    raise APIError(
                        400, "SOURCE_INVALID", "Request body is missing"
                    )

                raw = stream.read(length)
                if len(raw) != length:
                    raise APIError(
                        400, "SOURCE_INVALID", "Incomplete request body"
                    )

                try:
                    value = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise APIError(
                        400, "SOURCE_INVALID", "Request body must be valid JSON"
                    )

                if not isinstance(value, dict):
                    raise APIError(
                        400, "SOURCE_INVALID", "Request body must be a JSON object"
                    )
                return value

            prefix = "/api/v1"

            if not path.startswith(prefix + "/") and path != prefix:
                raise APIError(404, "SOURCE_NOT_FOUND", "Route not found")

            route = path[len(prefix):] or "/"

            if route == "/sources" and method == "POST":
                body = read_json_body()

                required = (
                    "source_id",
                    "source_version",
                    "source_content_base64",
                    "entrypoint",
                    "input_schema",
                    "output_schema",
                )
                missing = [key for key in required if key not in body]
                if missing:
                    raise APIError(
                        400,
                        "SOURCE_INVALID",
                        "Required source fields are missing",
                        context={"missing_fields": missing},
                    )

                if "owner_id" in body:
                    raise APIError(
                        400,
                        "SOURCE_INVALID",
                        "owner_id must not be supplied in request JSON",
                    )

                encoded = body["source_content_base64"]
                if not isinstance(encoded, str):
                    raise APIError(
                        400,
                        "SOURCE_INVALID",
                        "source_content_base64 must be a string",
                    )
                try:
                    source_bytes = base64.b64decode(
                        encoded.encode("ascii"),
                        validate=True,
                    )
                except (UnicodeEncodeError, binascii.Error, ValueError):
                    raise APIError(
                        400,
                        "SOURCE_INVALID",
                        "source_content_base64 is invalid",
                    )

                registration, _ = client_and_services()
                result = registration.register_source(
                    owner_id=owner_id,
                    source_id=body["source_id"],
                    source_version=body["source_version"],
                    source_bytes=source_bytes,
                    entrypoint=body["entrypoint"],
                    input_schema=body["input_schema"],
                    output_schema=body["output_schema"],
                    contract_dependencies=body.get("contract_dependencies", []),
                    calculation_version=body.get(
                        "calculation_version", "1.0.0"
                    ),
                )

                public_result = {
                    key: result[key]
                    for key in (
                        "source_id",
                        "source_version",
                        "source_hash",
                        "idempotent",
                    )
                    if key in result
                }
                return _json_response(
                    start_response,
                    201 if not result.get("idempotent") else 200,
                    {
                        "contract_version": CONTRACT_VERSION,
                        **(
                            {"correlation_id": correlation_id}
                            if correlation_id else {}
                        ),
                        "payload": public_result,
                    },
                    correlation_id,
                )

            if route == "/sources" and method == "GET":
                _, registry = client_and_services()
                result = registry.list_sources(owner_id=owner_id)
                return _json_response(
                    start_response,
                    200,
                    {
                        "contract_version": CONTRACT_VERSION,
                        **(
                            {"correlation_id": correlation_id}
                            if correlation_id else {}
                        ),
                        "payload": {"sources": result},
                    },
                    correlation_id,
                )

            # /sources/{source_id}/versions/{version}
            # /sources/{source_id}/versions/{version}/inspect
            parts = route.strip("/").split("/")
            if (
                len(parts) in (4, 5)
                and parts[0] == "sources"
                and parts[2] == "versions"
                and (len(parts) == 4 or parts[4] == "inspect")
            ):
                source_id = unquote(parts[1])
                source_version = unquote(parts[3])

                if (
                    not _ID_PATTERN.fullmatch(source_id)
                    or not source_version
                    or len(source_version) > 128
                    or "/" in source_version
                    or "\\" in source_version
                    or "@" in source_version
                ):
                    raise APIError(
                        400, "SOURCE_INVALID", "Invalid source identity"
                    )

                if len(parts) == 5:
                    if method != "POST":
                        raise APIError(
                            404, "SOURCE_NOT_FOUND", "Route not found"
                        )

                    if environ.get("CONTENT_LENGTH", "0") not in ("", "0"):
                        raise APIError(
                            400,
                            "SOURCE_INVALID",
                            "Inspection endpoint does not accept a body",
                        )

                    _, registry = client_and_services()
                    source = registry.get_source(
                        owner_id=owner_id,
                        source_id=source_id,
                        source_version=source_version,
                    )
                    inspection = inspect_source_archive(
                        source["source_bytes"],
                        source["entrypoint"],
                    )
                    findings = [
                        {
                            "code": "DEPENDENCY_ANALYSIS_PENDING",
                            "message": (
                                "Import and dependency analysis is not yet "
                                "implemented; archive validation alone is not "
                                "a complete source validation."
                            ),
                        }
                    ]
                    return _json_response(
                        start_response,
                        200,
                        {
                            "contract_version": CONTRACT_VERSION,
                            **(
                                {"correlation_id": correlation_id}
                                if correlation_id else {}
                            ),
                            "payload": {
                                "inspection_status": "archive_validated",
                                "source_id": source_id,
                                "source_version": source_version,
                                "source_hash": inspection.source_hash,
                                "archive_size": inspection.archive_size,
                                "entry_count": inspection.entry_count,
                                "expanded_size": inspection.expanded_size,
                                "python_files": list(inspection.python_files),
                                "findings": findings,
                            },
                        },
                        correlation_id,
                    )

                if method != "GET":
                    raise APIError(404, "SOURCE_NOT_FOUND", "Route not found")

                _, registry = client_and_services()
                source = registry.get_source(
                    owner_id=owner_id,
                    source_id=source_id,
                    source_version=source_version,
                )
                source.pop("source_bytes", None)
                return _json_response(
                    start_response,
                    200,
                    {
                        "contract_version": CONTRACT_VERSION,
                        **(
                            {"correlation_id": correlation_id}
                            if correlation_id else {}
                        ),
                        "payload": source,
                    },
                    correlation_id,
                )

            if route.startswith("/artifacts/"):
                parts = route.strip("/").split("/")
                if len(parts) not in (2, 3) or (
                    len(parts) == 3 and parts[2] not in ("content", "publish")
                ):
                    raise APIError(
                        404, "ARTIFACT_NOT_FOUND", "Artifact route not found"
                    )
                if len(parts) == 3 and parts[2] == "content" and method == "GET":
                    metadata, artifact_bytes = published_artifact_registry.get_built(
                        owner_id, parts[1]
                    )
                    headers = [
                        ("Content-Type", "application/octet-stream"),
                        ("Content-Length", str(len(artifact_bytes))),
                        ("Cache-Control", "private, no-store"),
                        ("X-Content-Type-Options", "nosniff"),
                        ("ETag", '"' + metadata["artifact_hash"] + '"'),
                        ("X-Artifact-Hash", metadata["artifact_hash"]),
                    ]
                    if correlation_id:
                        headers.append(("X-Correlation-ID", correlation_id))
                    start_response("200 OK", headers)
                    return [artifact_bytes]
                if len(parts) == 3 and parts[2] == "publish" and method == "POST":
                    body = read_json_body()
                    if "owner_id" in body:
                        raise APIError(400, "SOURCE_INVALID",
                                       "owner_id must not be supplied in request JSON")
                    build_id = body.get("build_id")
                    if not isinstance(build_id, str) or re.fullmatch(r"[0-9a-f]{32}", build_id) is None:
                        raise APIError(400, "BUILD_INVALID", "A valid build_id is required")
                    report = build_pipeline.history.get(owner_id, build_id)
                    if report is None:
                        raise APIError(404, "BUILD_NOT_FOUND", "Build was not found")
                    expected_artifact_id = report.get("source_id", "") + "@" + report.get("source_version", "")
                    if expected_artifact_id != parts[1]:
                        raise APIError(404, "BUILD_NOT_FOUND", "Build does not belong to this artifact identity")
                    stages = report.get("stages")
                    required_stages = {
                        "inspect_archive", "verify_source_hash", "validate_archive_paths",
                        "syntax_check", "dependency_check", "contract_check",
                        "normalize_working_copy", "test", "reproducibility", "package", "hash",
                    }
                    stage_names = {
                        stage.get("stage") for stage in stages
                        if isinstance(stage, dict)
                    } if isinstance(stages, list) else set()
                    if (report.get("status") != "succeeded"
                            or report.get("publishable") is not True
                            or not isinstance(stages, list)
                            or len(stage_names) != len(stages)
                            or not required_stages.issubset(stage_names)
                            or any(not isinstance(stage, dict) or stage.get("status") != "passed"
                                   for stage in stages)):
                        raise APIError(409, "BUILD_NOT_PUBLISHABLE",
                                       "Every mandatory build stage must pass before publication")
                    digest = report.get("artifact_digest")
                    artifact_hash = report.get("artifact_hash")
                    source_hash = report.get("source_hash")
                    if (not isinstance(digest, str)
                            or not re.fullmatch(r"[0-9a-f]{64}", digest)
                            or artifact_hash != "sha256:" + digest
                            or not isinstance(source_hash, str)
                            or not isinstance(report.get("provenance"), dict)):
                        raise APIError(409, "BUILD_NOT_PUBLISHABLE",
                                       "Build artifact hashes or provenance are incomplete")
                    try:
                        artifact_bytes = blob_storage.get_bytes(digest)
                    except (OSError, ValueError):
                        raise APIError(409, "BUILD_NOT_PUBLISHABLE",
                                       "Built artifact blob is unavailable")
                    if hashlib.sha256(artifact_bytes).hexdigest() != digest:
                        raise APIError(409, "BUILD_NOT_PUBLISHABLE",
                                       "Built artifact digest verification failed")
                    metadata, created = published_artifact_registry.publish_built(
                        owner_id, parts[1], artifact_bytes,
                        entrypoint=report.get("entrypoint"),
                        source_hash=source_hash,
                        build_id=build_id,
                        provenance=report["provenance"],
                        artifact_version=report.get("artifact_version"),
                        build_version=report.get("build_version", "code-manager-build-v1"),
                        calculation_version=report.get("calculation_version", "1.0.0"),
                        dependency_lock=report.get("dependency_lock", "stdlib-only"),
                        input_schema=report.get("input_schema", {}),
                        output_schema=report.get("output_schema", {}),
                        validation_status=report.get("validation_status", "passed"),
                    )
                    return _json_response(
                        start_response, 201 if created else 200,
                        {"contract_version": CONTRACT_VERSION,
                         **({"correlation_id": correlation_id} if correlation_id else {}),
                         "payload": {"artifact": metadata, "created": created}},
                        correlation_id,
                    )
                if method in {"GET", "POST"}:
                    raise APIError(
                        501,
                        "OPERATION_NOT_IMPLEMENTED",
                        "Artifact metadata operation is not implemented",
                    )
                raise APIError(
                    404, "ARTIFACT_NOT_FOUND", "Artifact route not found"
                )

            if route == "/builds" and method == "POST":
                body = read_json_body()
                if "owner_id" in body:
                    raise APIError(
                        400, "SOURCE_INVALID",
                        "owner_id must not be supplied in request JSON",
                    )
                source_id = body.get("source_id")
                source_version = body.get("source_version")
                if (
                    not isinstance(source_id, str)
                    or not _ID_PATTERN.fullmatch(source_id)
                    or not isinstance(source_version, str)
                    or not source_version
                    or len(source_version) > 128
                    or "/" in source_version
                    or "\\" in source_version
                ):
                    raise APIError(
                        400, "SOURCE_INVALID",
                        "source_id and source_version are required",
                    )
                _, registry = client_and_services()
                source = registry.get_source(
                    owner_id=owner_id,
                    source_id=source_id,
                    source_version=source_version,
                )
                report = build_pipeline.run(
                    owner_id=owner_id, source_id=source_id,
                    source_version=source_version, source=source,
                )
                return _json_response(
                    start_response, 200,
                    {
                        "contract_version": CONTRACT_VERSION,
                        **({"correlation_id": correlation_id} if correlation_id else {}),
                        "payload": {
                            "source_id": source_id,
                            "source_version": source_version,
                            "build": report,
                        },
                    },
                    correlation_id,
                )

            if route == "/builds" and method == "GET":
                query = parse_qs(environ.get("QUERY_STRING", ""))
                raw_limit = query.get("limit", ["50"])[0]
                try:
                    limit = int(raw_limit)
                except (TypeError, ValueError):
                    raise APIError(400, "BUILD_INVALID", "limit must be an integer")
                if not 1 <= limit <= 100:
                    raise APIError(400, "BUILD_INVALID", "limit must be between 1 and 100")
                builds = build_pipeline.history.list(owner_id, limit=limit)
                return _json_response(
                    start_response, 200,
                    {"contract_version": CONTRACT_VERSION,
                     **({"correlation_id": correlation_id} if correlation_id else {}),
                     "payload": {"builds": builds}},
                    correlation_id,
                )

            if route.startswith("/builds/") and method == "GET":
                build_id = route[len("/builds/"):]
                if re.fullmatch(r"[0-9a-f]{32}", build_id) is None:
                    raise APIError(404, "BUILD_NOT_FOUND", "Build was not found")
                report = build_pipeline.history.get(owner_id, build_id)
                if report is None:
                    raise APIError(404, "BUILD_NOT_FOUND", "Build was not found")
                return _json_response(
                    start_response, 200,
                    {"contract_version": CONTRACT_VERSION,
                     **({"correlation_id": correlation_id} if correlation_id else {}),
                     "payload": {"build": report}},
                    correlation_id,
                )

            raise APIError(404, "SOURCE_NOT_FOUND", "Route not found")

        except APIError as exc:
            return fail(
                exc.status, exc.code, exc.message, exc.retryable, exc.context
            )
        except ArtifactInvalid as exc:
            return fail(400, "ARTIFACT_INVALID", str(exc))
        except ArtifactNotFound:
            return fail(404, "ARTIFACT_NOT_FOUND", "Artifact not published")
        except ArtifactConflict:
            return fail(409, "ARTIFACT_CONFLICT", "Artifact already published differently")
        except ArtifactIntegrityError:
            return fail(500, "ARTIFACT_INTEGRITY_FAILED", "Published artifact verification failed")
        except SourceVersionConflict as exc:
            return fail(409, "SOURCE_VERSION_CONFLICT", str(exc))
        except SourceNotFound:
            return fail(404, "SOURCE_NOT_FOUND", "Source version was not found")
        except SourceValidationError as exc:
            return fail(400, "SOURCE_INVALID", str(exc))
        except SourceIntegrityError:
            return fail(
                500, "ARTIFACT_INTEGRITY_FAILED",
                "Stored source integrity verification failed",
            )
        except DataManagerAPIError as exc:
            status = exc.status if exc.status in (400, 401, 403, 404, 409, 413, 422) else 502
            code = exc.code if status != 502 else "DATA_MANAGER_UNAVAILABLE"
            return fail(
                status,
                code,
                "DATA MANAGER request failed",
                exc.retryable,
            )
        except DataManagerTransportError:
            return fail(
                502, "DATA_MANAGER_UNAVAILABLE",
                "DATA MANAGER could not be reached", True,
            )
        except DataManagerClientError:
            return fail(
                502, "DATA_MANAGER_UNAVAILABLE",
                "DATA MANAGER client operation failed",
            )
        except (SourceRegistrationError, CodeManagerError):
            return fail(
                422, "SOURCE_INVALID",
                "The source operation could not be completed",
            )
        except Exception:
            # Do not return stack traces, filesystem paths, or credentials.
            return fail(
                500, "INTERNAL_ERROR",
                "An internal error occurred",
            )

    return application


def make_development_data_manager_client_factory(base_url: str):
    """Explicitly opt-in local development adapter; never for production."""
    from urllib.parse import urlsplit

    parsed = urlsplit(base_url)
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError(
            "Development identity adapter is restricted to loopback hosts"
        )

    if (
        os.environ.get("CODE_MANAGER_ALLOW_INSECURE_HEADER", "").lower()
        not in {"1", "true", "yes"}
        or os.environ.get("DATA_MANAGER_ALLOW_INSECURE_HEADER", "").lower()
        not in {"1", "true", "yes"}
    ):
        raise RuntimeError(
            "Both explicit development identity flags are required"
        )

    def factory(owner_id):
        return DataManagerClient(
            base_url,
            identity_provider=lambda: {"X-Manager-ID": owner_id},
        )

    return factory
