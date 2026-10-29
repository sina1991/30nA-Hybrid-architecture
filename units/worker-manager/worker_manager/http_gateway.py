"""Owner-bound HTTPS Runtime transport; never follows authenticated redirects."""
from dataclasses import asdict
from urllib.parse import urlsplit, quote
import json

import httpx


class RuntimeHTTPGateway:
    def __init__(self, base_url, token, *, client=None):
        parsed = urlsplit(base_url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise ValueError('Runtime must use an HTTPS origin')
        if not isinstance(token, str) or not token or not token.isascii() or any(c.isspace() for c in token):
            raise ValueError('Invalid Runtime credential')
        self.base_url, self.token = base_url.rstrip('/'), token
        self.client = client

    def _request(self, method, path, payload=None, timeout=15):
        # An injected client is for trusted tests/embedding. Production retains
        # certificate verification and does not inherit HTTP proxy credentials.
        client = self.client or httpx.Client(trust_env=False, follow_redirects=False)
        try:
            with client.stream(method, self.base_url + path, json=payload,
                               headers={'Authorization': 'Bearer ' + self.token}, timeout=timeout) as response:
                response.raise_for_status()
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > 2_000_000:
                        raise ValueError('Runtime response too large')
                data = json.loads(body)
                if not str(data.get('contract_version', '')).startswith('1.') or not isinstance(data.get('payload'), dict):
                    raise ValueError('Invalid Runtime envelope')
                return data['payload']
        finally:
            if self.client is None:
                client.close()

    def submit(self, request):
        return self._request('POST', '/api/v1/executions', asdict(request),
                             timeout=request.timeout_seconds + 30)

    def get(self, execution_id):
        return self._request('GET', '/api/v1/executions/' + quote(execution_id, safe=''))

    def cancel(self, execution_id):
        return self._request('POST', '/api/v1/executions/' + quote(execution_id, safe='') + '/cancel')['cancelled']
