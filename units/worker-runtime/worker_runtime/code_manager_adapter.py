"""CODE MANAGER public-API adapter; fail closed until artifact download exists."""
import base64
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class ArtifactAPIUnavailable(RuntimeError):
    pass


class CodeManagerArtifactProvider:
    """Requires an authenticated, public GET /artifacts/{id}/content API.

    The current CODE MANAGER responds 501 for /artifacts/*, so this adapter
    deliberately never reads CODE MANAGER's registry, database or blob store.
    """
    def __init__(self, base_url, authorization_header, timeout=10, max_bytes=16 * 1024 * 1024):
        if not base_url.startswith('https://'):
            raise ValueError('CODE MANAGER URL must use HTTPS')
        if not authorization_header:
            raise ValueError('Authorization header is required')
        self.base_url = base_url.rstrip('/')
        self.authorization_header = authorization_header
        self.timeout = timeout
        self.max_bytes = max_bytes

    def fetch(self, artifact_id):
        if not isinstance(artifact_id, str) or not artifact_id or '/' in artifact_id:
            raise ValueError('Invalid artifact ID')
        request = Request(self.base_url + '/artifacts/' + quote(artifact_id, safe='') + '/content',
            headers={'Authorization': self.authorization_header, 'Accept': 'application/octet-stream'})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                if response.status != 200 or response.headers.get_content_type() != 'application/octet-stream':
                    raise ArtifactAPIUnavailable('Artifact endpoint returned unexpected response')
                content = response.read(self.max_bytes + 1)
                if len(content) > self.max_bytes:
                    raise ArtifactAPIUnavailable('Artifact exceeds size limit')
                return content
        except HTTPError as exc:
            if exc.code == 501:
                raise ArtifactAPIUnavailable('CODE MANAGER artifact download is not implemented') from exc
            raise ArtifactAPIUnavailable('CODE MANAGER artifact API request failed') from exc
        except (URLError, TimeoutError) as exc:
            raise ArtifactAPIUnavailable('CODE MANAGER artifact API unavailable') from exc
