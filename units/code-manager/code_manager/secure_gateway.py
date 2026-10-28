"""Bearer-authenticated WSGI boundary. Never trust inbound identity fields."""
import hashlib
import hmac
import json
import re
from pathlib import Path

OWNER = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$')


def load_credentials(path):
    """Credential file: {sha256(token): owner_id}; read afresh for revocation."""
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(raw, dict) or not raw or any(
        not isinstance(k, str) or not re.fullmatch('[0-9a-f]{64}', k)
        or not isinstance(v, str) or not OWNER.fullmatch(v)
        for k, v in raw.items()
    ):
        raise ValueError('Invalid credential map')
    return raw


def authenticated_wsgi(app, credential_path):
    def gateway(environ, start_response):
        auth = environ.get('HTTP_AUTHORIZATION', '')
        owner = None
        if isinstance(auth, str) and auth.startswith('Bearer ') and len(auth) <= 512:
            token = auth[7:]
            if token and token.isascii() and not any(c.isspace() for c in token):
                digest = hashlib.sha256(token.encode('ascii')).hexdigest()
                # Compare all keys with constant-time primitive.
                for stored_hash, mapped_owner in load_credentials(credential_path).items():
                    if hmac.compare_digest(digest, stored_hash):
                        owner = mapped_owner
        if owner is None:
            body = b'{"error":{"code":"ACCESS_DENIED","message":"Unauthorized"}}'
            start_response('401 Unauthorized', [('Content-Type', 'application/json'),
                                                ('Content-Length', str(len(body))),
                                                ('Cache-Control', 'no-store'),
                                                ('WWW-Authenticate', 'Bearer')])
            return [body]
        trusted = {k: v for k, v in environ.items()
                   if k != 'REMOTE_USER' and not k.startswith('HTTP_X_')}
        trusted.pop('HTTP_AUTHORIZATION', None)
        trusted['REMOTE_USER'] = owner
        return app(trusted, start_response)
    return gateway
