"""Read-only public API adapter for Dashboard Core (stdlib only)."""
from __future__ import annotations
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _RejectRedirectHandler(HTTPRedirectHandler):
    """Prevent authenticated API requests from following redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(
            req.full_url, code, "API redirects are not allowed", headers, fp
        )

_ID = re.compile(r"^[A-Za-z0-9_.:-]+$")

class ConsumerAPIError(Exception):
    def __init__(self, code: str, message: str, status: int | None = None):
        self.code, self.status = code, status
        super().__init__(message)

def _identifier(value: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("invalid identifier")
    return quote(value, safe="")

class PublicAPI:
    def __init__(self, base_url: str, *, token: str | None = None, timeout: float = 5.0,
                 identity_header: str | None = None, identity: str | None = None,
                 transport=None):
        parts = urlsplit(base_url)
        if parts.scheme not in ("http", "https") or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
            raise ValueError("base_url must be an HTTP(S) origin without credentials/query/fragment")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not 0 < timeout <= 120:
            raise ValueError("timeout must be between 0 and 120 seconds")
        if token is not None:
            if not isinstance(token, str) or not token.strip() or "\\r" in token or "\\n" in token:
                raise ValueError("token must be a non-empty single-line string")
            if parts.scheme != "https" and parts.hostname not in ("localhost", "127.0.0.1", "::1"):
                raise ValueError("bearer tokens require HTTPS except on loopback")
        if identity_header and identity_header not in ("X-Manager-ID", "X-Code-Manager-ID"):
            raise ValueError("unsupported development identity header")
        if bool(identity_header) != bool(identity):
            raise ValueError("identity and identity_header must be supplied together")
        if identity is not None and (not isinstance(identity, str) or "\\r" in identity or "\\n" in identity):
            raise ValueError("identity must be a single-line string")
        if identity_header and parts.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("development identity headers require loopback")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = token
        self.identity_header, self.identity = identity_header, identity
        self.transport = transport

    def get(self, path: str) -> dict:
        if not path.startswith("/api/v1/") or ".." in path or "?" in path or "#" in path:
            raise ValueError("unsupported API path")
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.identity_header:
            headers[self.identity_header] = self.identity
        request = Request(self.base_url + path, headers=headers, method="GET")
        try:
            if self.transport is None:
                opener = build_opener(_RejectRedirectHandler)
                response = opener.open(request, timeout=self.timeout)
            else:
                response = self.transport(request, timeout=self.timeout)
            with response:
                body = response.read(2_000_001)
                if len(body) > 2_000_000:
                    raise ConsumerAPIError("INVALID_RESPONSE", "response too large")
        except HTTPError as exc:
            code = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 408: "TIMEOUT"}.get(exc.code, "UPSTREAM_ERROR")
            raise ConsumerAPIError(code, f"upstream returned HTTP {exc.code}", exc.code) from None
        except (URLError, TimeoutError, OSError) as exc:
            raise ConsumerAPIError("SERVICE_UNAVAILABLE", "upstream unavailable or timed out") from None
        try:
            data = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            raise ConsumerAPIError("INVALID_RESPONSE", "upstream returned invalid JSON") from None
        if not isinstance(data, dict):
            raise ConsumerAPIError("INVALID_RESPONSE", "upstream response must be an object")
        version = data.get("contract_version")
        if not isinstance(version, str) or not version.startswith("1."):
            raise ConsumerAPIError("UNSUPPORTED_CONTRACT_VERSION", "unsupported or missing contract_version")
        if "error" in data:
            error = data["error"]
            if not isinstance(error, dict) or not isinstance(error.get("code"), str) or not isinstance(error.get("message"), str):
                raise ConsumerAPIError("INVALID_RESPONSE", "invalid error envelope")
            raise ConsumerAPIError(error["code"], error["message"])
        if not isinstance(data.get("payload"), dict):
            raise ConsumerAPIError("INVALID_RESPONSE", "missing payload object")
        return data["payload"]

    def list_sources(self) -> dict:
        return self.get("/api/v1/sources")

    def get_source(self, source_id: str, source_version: str) -> dict:
        return self.get(f"/api/v1/sources/{_identifier(source_id)}/versions/{_identifier(source_version)}")

    def get_model(self, model_id: str) -> dict:
        return self.get(f"/api/v1/models/{_identifier(model_id)}")

    def get_resource(self, resource_id: str) -> dict:
        return self.get(f"/api/v1/resources/{_identifier(resource_id)}")

    def list_records(self, resource_id: str) -> dict:
        return self.get(f"/api/v1/resources/{_identifier(resource_id)}/records")

    def get_record(self, resource_id: str, record_id: str) -> dict:
        return self.get(f"/api/v1/resources/{_identifier(resource_id)}/records/{_identifier(record_id)}")


def from_environment(prefix: str) -> PublicAPI:
    if prefix not in ("DATA_MANAGER", "CODE_MANAGER"):
        raise ValueError("unsupported service")
    base_url = os.environ.get(prefix + "_URL")
    if not base_url:
        raise ValueError(prefix + "_URL is required")
    return PublicAPI(base_url, token=os.environ.get(prefix + "_TOKEN"),
                     timeout=float(os.environ.get(prefix + "_TIMEOUT", "5")))
