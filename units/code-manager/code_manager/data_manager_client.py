"""HTTP client for the public DATA MANAGER API.

Authentication is supplied through an optional, replaceable identity provider.
No development identity header is enabled implicitly.
"""

import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _require_id(value, name):
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
        raise ValueError(
            f"{name} must match the DATA MANAGER identifier contract"
        )
    return value


class DataManagerClientError(Exception):
    """Base exception for DATA MANAGER client failures."""


class DataManagerTransportError(DataManagerClientError):
    """The HTTP transport failed before a usable response was received."""


class DataManagerAPIError(DataManagerClientError):
    """DATA MANAGER returned an unsuccessful HTTP response."""

    def __init__(
        self,
        status,
        code,
        message,
        retryable=False,
        context=None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.retryable = bool(retryable)
        self.context = context if isinstance(context, dict) else {}


def _urllib_transport(method, url, headers, body, timeout):
    """Return (status, headers, body_bytes), including HTTP error responses."""
    request = Request(
        url=url,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return (
                response.status,
                dict(response.headers.items()),
                response.read(),
            )
    except HTTPError as response:
        try:
            content = response.read()
        finally:
            response.close()
        return response.code, dict(response.headers.items()), content
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        raise DataManagerTransportError(
            "DATA MANAGER transport request failed"
        ) from exc


class DataManagerClient:
    """Small JSON client for DATA MANAGER's public API."""

    def __init__(
        self,
        base_url,
        timeout=5.0,
        transport=None,
        identity_provider=None,
    ):
        if not isinstance(base_url, str) or not base_url.strip():
            raise ValueError("base_url must be a non-empty URL")

        base_url = base_url.strip().rstrip("/")
        try:
            parsed_url = urlsplit(base_url)
            valid_port = parsed_url.port is None or (
                1 <= parsed_url.port <= 65535
            )
        except ValueError as exc:
            raise ValueError("base_url is invalid") from exc

        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.hostname
            or parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.query
            or parsed_url.fragment
            or not valid_port
        ):
            raise ValueError(
                "base_url must be an HTTP(S) URL without credentials, "
                "query, or fragment"
            )

        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError("timeout must be a positive number")
        if timeout <= 0:
            raise ValueError("timeout must be a positive number")

        self.base_url = base_url
        self.timeout = float(timeout)
        self._transport = transport or _urllib_transport
        self._identity_provider = identity_provider

    def request(self, method, path, payload=None, query=None):
        """Send one request and return its JSON object.

        This method deliberately performs no automatic retries.
        """
        if not isinstance(method, str) or not method.strip():
            raise ValueError("method must be a non-empty string")
        method = method.upper()

        if (
            not isinstance(path, str)
            or not path
            or path.startswith("//")
            or "://" in path
            or "?" in path
            or "#" in path
        ):
            raise ValueError("path must be a relative API path")

        path = path.lstrip("/")
        if any(part in {".", ".."} for part in path.split("/")):
            raise ValueError("path must not contain dot segments")

        url = f"{self.base_url}/{path}"
        if query is not None:
            if not isinstance(query, dict):
                raise ValueError("query must be a dictionary")
            encoded_query = urlencode(query, doseq=True)
            if encoded_query:
                url = f"{url}?{encoded_query}"

        headers = {
            "Accept": "application/json",
        }
        body = None

        if payload is not None:
            if not isinstance(payload, dict):
                raise ValueError("payload must be a JSON object")
            try:
                body = json.dumps(
                    payload,
                    ensure_ascii=False,
                    allow_nan=False,
                ).encode("utf-8")
            except (TypeError, ValueError) as exc:
                raise ValueError("payload must be valid JSON data") from exc
            headers["Content-Type"] = "application/json; charset=utf-8"

        if self._identity_provider is not None:
            try:
                identity_headers = self._identity_provider()
            except Exception as exc:
                raise DataManagerClientError(
                    "Identity provider failed"
                ) from exc

            if not isinstance(identity_headers, dict):
                raise DataManagerClientError(
                    "Identity provider must return a header dictionary"
                )

            for key, value in identity_headers.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise DataManagerClientError(
                        "Identity headers must contain string keys and values"
                    )
                if key.lower() in {"host", "content-length", "accept", "content-type", "transfer-encoding", "connection"}:
                    raise DataManagerClientError(
                        f"Identity provider may not override {key}"
                    )
                headers[key] = value

        try:
            status, response_headers, response_body = self._transport(
                method,
                url,
                headers,
                body,
                self.timeout,
            )
        except DataManagerClientError:
            raise
        except Exception as exc:
            raise DataManagerTransportError(
                "DATA MANAGER transport request failed"
            ) from exc

        if not isinstance(status, int):
            raise DataManagerTransportError(
                "Transport returned an invalid HTTP status"
            )
        if not isinstance(response_body, bytes):
            raise DataManagerTransportError(
                "Transport returned a non-bytes response body"
            )

        try:
            decoded = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if not 200 <= status < 300:
                raise DataManagerAPIError(
                    status,
                    "HTTP_ERROR",
                    "DATA MANAGER returned a non-JSON error response",
                )
            raise DataManagerTransportError(
                "DATA MANAGER returned an invalid JSON response"
            )

        if not 200 <= status < 300:
            error = decoded.get("error", {}) if isinstance(decoded, dict) else {}
            if not isinstance(error, dict):
                error = {}

            code = error.get("code", "HTTP_ERROR")
            message = error.get("message", "DATA MANAGER request failed")

            if not isinstance(code, str):
                code = "HTTP_ERROR"
            if not isinstance(message, str):
                message = "DATA MANAGER request failed"

            raise DataManagerAPIError(
                status=status,
                code=code,
                message=message,
                retryable=error.get("retryable", False),
                context=error.get("context", {}),
            )

        if not isinstance(decoded, dict):
            raise DataManagerTransportError(
                "DATA MANAGER response must be a JSON object"
            )

        return decoded

    def register_model(self, model):
        return self.request("POST", "/api/v1/models", payload=model)

    def get_model(self, model_id, version=None):
        model_id = _require_id(model_id, "model_id")
        query = {"version": version} if version is not None else None
        return self.request(
            "GET",
            f"/api/v1/models/{model_id}",
            query=query,
        )

    def create_resource(self, resource):
        if not isinstance(resource, dict):
            raise ValueError("resource must be a JSON object")
        _require_id(resource.get("resource_id"), "resource_id")
        _require_id(resource.get("model_id"), "model_id")
        return self.request("POST", "/api/v1/resources", payload=resource)

    def get_resource(self, resource_id):
        resource_id = _require_id(resource_id, "resource_id")
        return self.request("GET", f"/api/v1/resources/{resource_id}")

    def write_record(self, resource_id, record):
        resource_id = _require_id(resource_id, "resource_id")
        return self.request(
            "POST",
            f"/api/v1/resources/{resource_id}/records",
            payload=record,
        )

    def list_records(self, resource_id, limit=100):
        resource_id = _require_id(resource_id, "resource_id")
        return self.request(
            "GET",
            f"/api/v1/resources/{resource_id}/records",
            query={"limit": limit},
        )

    def read_record(self, resource_id, record_id):
        resource_id = _require_id(resource_id, "resource_id")
        record_id = _require_id(record_id, "record_id")
        return self.request(
            "GET",
            f"/api/v1/resources/{resource_id}/records/{record_id}",
        )

    def replace_record(self, resource_id, record_id, record):
        resource_id = _require_id(resource_id, "resource_id")
        record_id = _require_id(record_id, "record_id")
        return self.request(
            "PUT",
            f"/api/v1/resources/{resource_id}/records/{record_id}",
            payload=record,
        )

    def update_record(self, resource_id, record_id, patch):
        resource_id = _require_id(resource_id, "resource_id")
        record_id = _require_id(record_id, "record_id")
        return self.request(
            "PATCH",
            f"/api/v1/resources/{resource_id}/records/{record_id}",
            payload=patch,
        )

    def delete_record(self, resource_id, record_id):
        resource_id = _require_id(resource_id, "resource_id")
        record_id = _require_id(record_id, "record_id")
        return self.request(
            "DELETE",
            f"/api/v1/resources/{resource_id}/records/{record_id}",
        )
