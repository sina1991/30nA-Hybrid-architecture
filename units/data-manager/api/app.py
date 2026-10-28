import json
import os
from urllib.parse import parse_qs

from ..errors import DataManagerError, Forbidden, InvalidInput, NotFound
from ..services import DataService
from ..storage import SQLiteStorage
from ..validation import require_id


_DEFAULT_DB = os.environ.get(
    "DATA_MANAGER_DB", "/tmp/data-manager/data.sqlite3"
)
_ALLOW_INSECURE_HEADER = (
    os.environ.get("DATA_MANAGER_ALLOW_INSECURE_HEADER", "").lower()
    in {"1", "true", "yes"}
)
service = DataService(SQLiteStorage(_DEFAULT_DB))


def _json_response(start_response, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    phrase = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        500: "Internal Server Error",
    }.get(status, "Error")
    start_response(
        f"{status} {phrase}",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        ],
    )
    return [body]


def _request_body(environ):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except (TypeError, ValueError) as exc:
        raise InvalidInput("Invalid Content-Length") from exc

    if length < 0:
        raise InvalidInput("Invalid Content-Length")
    if length > 1_000_000:
        raise InvalidInput("Request body exceeds 1 MB")

    raw = environ["wsgi.input"].read(length) if length else b"{}"
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidInput("Request body must be valid JSON") from exc

    if not isinstance(body, dict):
        raise InvalidInput("Request body must be a JSON object")
    return body


def _requester(environ):
    # REMOTE_USER must be populated by a trusted authentication layer.
    identity = environ.get("REMOTE_USER")
    if not identity and _ALLOW_INSECURE_HEADER:
        identity = environ.get("HTTP_X_MANAGER_ID")
    if not identity:
        raise Forbidden(
            "Authenticated identity is required; configure trusted WSGI "
            "authentication before using the Data Manager API"
        )
    return require_id(identity, "authenticated identity")


def application(environ, start_response):
    try:
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        # Health checks reveal no user data and do not require an identity.
        if path == "/health" and method == "GET":
            return _json_response(start_response, 200, {"status": "ok"})

        requester = _requester(environ)
        parts = [p for p in path.strip("/").split("/") if p]
        query = parse_qs(environ.get("QUERY_STRING", ""))

        body = {}
        if method in {"POST", "PUT", "PATCH"}:
            body = _request_body(environ)

        if parts == ["api", "v1", "models"] and method == "POST":
            return _json_response(
                start_response, 201, service.register_model(requester, body)
            )

        if (
            len(parts) == 4
            and parts[:3] == ["api", "v1", "models"]
            and method == "GET"
        ):
            version = query.get("version", [None])[0]
            return _json_response(
                start_response, 200,
                service.get_model(requester, parts[3], version)
            )

        if parts == ["api", "v1", "resources"] and method == "POST":
            return _json_response(
                start_response, 201, service.create_resource(requester, body)
            )

        if (
            len(parts) == 4
            and parts[:3] == ["api", "v1", "resources"]
            and method == "GET"
        ):
            return _json_response(
                start_response, 200, service.get_resource(requester, parts[3])
            )

        if len(parts) >= 5 and parts[:3] == ["api", "v1", "resources"]:
            resource_id = parts[3]

            if len(parts) == 5 and parts[4] == "records":
                if method == "POST":
                    result = service.write_record(
                        requester, resource_id, body
                    )
                    return _json_response(start_response, 201, result)

                if method == "GET":
                    raw_limit = query.get("limit", ["100"])[0]
                    try:
                        limit = int(raw_limit)
                    except (TypeError, ValueError) as exc:
                        raise InvalidInput(
                            "limit must be an integer"
                        ) from exc
                    return _json_response(
                        start_response, 200,
                        {
                            "records": service.list_records(
                                requester, resource_id, limit
                            )
                        },
                    )

            if (
                len(parts) == 6
                and parts[4] == "records"
            ):
                record_id = parts[5]
                if method == "GET":
                    return _json_response(
                        start_response, 200,
                        service.read_record(
                            requester, resource_id, record_id
                        ),
                    )
                if method == "PUT":
                    return _json_response(
                        start_response, 200,
                        service.replace_record(
                            requester, resource_id, record_id, body
                        ),
                    )
                if method == "PATCH":
                    return _json_response(
                        start_response, 200,
                        service.patch_record(
                            requester, resource_id, record_id, body
                        ),
                    )
                if method == "DELETE":
                    return _json_response(
                        start_response, 200,
                        service.delete_record(
                            requester, resource_id, record_id
                        ),
                    )

        raise NotFound("Endpoint not found")

    except DataManagerError as exc:
        return _json_response(
            start_response,
            exc.status,
            {
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "retryable": exc.retryable,
                    "context": exc.context,
                    "contract_version": "1.0.0",
                }
            },
        )
    except Exception:
        # Keep database internals and tracebacks out of client responses.
        return _json_response(
            start_response,
            500,
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "retryable": False,
                    "contract_version": "1.0.0",
                }
            },
        )
