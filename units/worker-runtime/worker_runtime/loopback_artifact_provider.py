"""Loopback-only API adapter for local MVP deployments; no direct blob access."""
from urllib.parse import urlsplit
from .code_manager_adapter import CodeManagerArtifactProvider

class LoopbackArtifactProvider(CodeManagerArtifactProvider):
    def __init__(self, base_url, authorization_header, **kwargs):
        parsed = urlsplit(base_url)
        if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1'):
            raise ValueError('Plain HTTP is allowed only on loopback')
        # Parent requires HTTPS; set fields with equivalent validation, no global bypass.
        if not authorization_header:
            raise ValueError('Authorization header is required')
        self.base_url = base_url.rstrip('/')
        self.authorization_header = authorization_header
        self.timeout = kwargs.get('timeout', 10)
        self.max_bytes = kwargs.get('max_bytes', 16 * 1024 * 1024)
