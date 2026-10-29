"""Shared HTTP boundary for owner-scoped development services."""
import hashlib
import hmac
import json
import re
from pathlib import Path

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


ERROR_RESPONSES = {status: {
    'description': description,
    'content': {'application/json': {'schema': {
        'type': 'object', 'required': ['contract_version', 'error'],
        'properties': {'contract_version': {'type': 'string'},
            'error': {'type': 'object', 'required': ['code', 'message'],
                'properties': {'code': {'type': 'string'}, 'message': {'type': 'string'}}}}}}}
    } for status, description in {401:'Unauthorized', 403:'Forbidden', 404:'Not found',
        409:'Conflict', 413:'Request too large', 422:'Invalid input', 503:'Service unavailable'}.items()}

def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value) or value == '__legacy__':
        raise ValueError('Invalid identifier')
    return value


def envelope(payload):
    return {'contract_version': '1.0.0', 'payload': payload}


def owner_dependency(credential_path):
    path = Path(credential_path)

    bearer_scheme = HTTPBearer(auto_error=False)

    def authenticate(request: Request, bearer=Depends(bearer_scheme)):
        auth = request.headers.get('authorization', '')
        owner = None
        try:
            credentials = json.loads(path.read_text())
            if not isinstance(credentials, dict):
                raise ValueError()
            if any(not re.fullmatch(r'[0-9a-f]{64}', k) or identifier(v) != v
                   for k, v in credentials.items()):
                raise ValueError()
        except (OSError, ValueError, TypeError):
            raise HTTPException(503, 'Identity configuration unavailable') from None
        if auth.startswith('Bearer ') and 7 < len(auth) <= 512:
            token = auth[7:]
            if token.isascii() and not any(c.isspace() for c in token):
                digest = hashlib.sha256(token.encode('ascii')).hexdigest()
                for stored, mapped in credentials.items():
                    if hmac.compare_digest(digest, stored):
                        owner = mapped
        if owner is None:
            raise HTTPException(401, 'Unauthorized', headers={'WWW-Authenticate': 'Bearer'})
        return owner
    return authenticate


class BodyLimitMiddleware:
    """Bound the received body even when Content-Length is omitted or false."""
    def __init__(self, app, max_bytes=1048576):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        size, chunks = 0, []
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            size += len(chunk)
            if size > self.max_bytes:
                await send({'type': 'http.response.start', 'status': 413,
                            'headers': [(b'content-type', b'application/json')]})
                await send({'type': 'http.response.body', 'body': b'{"contract_version":"1.0.0","error":{"code":"REQUEST_TOO_LARGE","message":"Request too large"}}'})
                return
            chunks.append(chunk)
            if not message.get('more_body', False):
                break
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': b''.join(chunks), 'more_body': False}
            return await receive()
        async def private_send(message):
            if message['type'] == 'http.response.start' and scope.get('path', '').startswith('/api/'):
                headers = [(k,v) for k,v in message.get('headers', []) if k.lower() not in (b'cache-control',b'vary')]
                message = dict(message,headers=headers+[(b'cache-control',b'no-store'),(b'vary',b'Authorization')])
            await send(message)
        await self.app(scope, replay, private_send)


def register_error_handlers(app):
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from fastapi.responses import JSONResponse

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        code = {401:'UNAUTHORIZED',403:'FORBIDDEN',404:'NOT_FOUND',409:'CONFLICT',413:'REQUEST_TOO_LARGE',422:'INVALID_INPUT',503:'SERVICE_UNAVAILABLE'}.get(exc.status_code,'HTTP_ERROR')
        return JSONResponse({'contract_version':'1.0.0','error':{'code':code,'message':str(exc.detail)}}, status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not echo submitted fields: they can contain worker configuration.
        return JSONResponse({'contract_version':'1.0.0','error':{
            'code':'INVALID_INPUT','message':'Request does not match the API contract'}},status_code=422)


class ProcessLock:
    """Enforce one service process per persistent state root on Linux."""
    def __init__(self,path):
        import fcntl
        path=Path(path)
        path.parent.mkdir(parents=True,exist_ok=True)
        self.file=path.open('a')
        try:
            fcntl.flock(self.file,fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError('Another process owns this service state') from None
    def close(self):
        self.file.close()
