"""Authenticated adapter for CODE MANAGER's public artifact-content API."""
import math
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener


class _RejectRedirectHandler(HTTPRedirectHandler):
    """Never forward artifact authorization to a redirect target."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(
            req.full_url, code, "CODE MANAGER redirects are not allowed", headers, fp
        )


class ArtifactAPIUnavailable(RuntimeError):
    pass


class CodeManagerArtifactProvider:
    """Fetch byte-exact content through GET /api/v1/artifacts/{id}/content.

    The adapter deliberately never reads CODE MANAGER's registry, database or
    blob store directly. Its authorization header must be issued for an identity
    that is allowed to read the requested artifact.
    """

    def __init__(self, base_url, authorization_header, timeout=10, max_bytes=16 * 1024 * 1024):
        if not isinstance(base_url, str) or not base_url.startswith("https://"):
            raise ValueError("CODE MANAGER URL must use HTTPS")
        if not isinstance(authorization_header, str) or not authorization_header.strip():
            raise ValueError("Authorization header is required")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ValueError("timeout must be finite and positive")
        if type(max_bytes) is not int or max_bytes <= 0:
            raise ValueError("max_bytes must be a positive integer")
        self.base_url = base_url.rstrip("/")
        self.authorization_header = authorization_header
        self.timeout = float(timeout)
        self.max_bytes = max_bytes

    def fetch(self, artifact_id):
        if not isinstance(artifact_id, str) or not artifact_id or "/" in artifact_id:
            raise ValueError("Invalid artifact ID")
        url = (
            self.base_url
            + "/api/v1/artifacts/"
            + quote(artifact_id, safe="")
            + "/content"
        )
        request = Request(
            url,
            headers={
                "Authorization": self.authorization_header,
                "Accept": "application/octet-stream",
            },
        )
        try:
            # Build a private opener for each fetch so the redirect policy cannot
            # be bypassed by a process-global urllib opener or another caller.
            opener = build_opener(_RejectRedirectHandler)
            with opener.open(request, timeout=self.timeout) as response:
                if response.status != 200 or response.headers.get_content_type() != "application/octet-stream":
                    raise ArtifactAPIUnavailable("Artifact endpoint returned unexpected response")
                content = response.read(self.max_bytes + 1)
                if len(content) > self.max_bytes:
                    raise ArtifactAPIUnavailable("Artifact exceeds size limit")
                return content
        except HTTPError as exc:
            if exc.code == 501:
                raise ArtifactAPIUnavailable("CODE MANAGER artifact download is not implemented") from exc
            raise ArtifactAPIUnavailable("CODE MANAGER artifact API request failed") from exc
        except (URLError, TimeoutError) as exc:
            raise ArtifactAPIUnavailable("CODE MANAGER artifact API unavailable") from exc
