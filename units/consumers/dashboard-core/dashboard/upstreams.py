"""Authenticated Dashboard BFF for explicit owner-scoped Manager operations."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from worker_manager.api import RegisterBody, ConfigureBody
from worker_manager.http_common import ERROR_RESPONSES, envelope, identifier, owner_dependency
from public_api import ConsumerAPIError, _identifier


class RunRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    input_payload: dict = Field(default_factory=dict)
    timeout_seconds: float = Field(default=30, gt=0, le=300, allow_inf_nan=False)
    idempotency_key: str = Field(min_length=1, max_length=256)


def create_router(credential_path, upstream_factory):
    """Authenticate before forwarding the caller's credential to configured services.

    No credential substitution, redirects, arbitrary proxy paths or source upload.
    Worker metadata mutations use the Manager schemas and caller identity.
    """
    router = APIRouter(prefix='/api/upstreams', responses=ERROR_RESPONSES)
    owner = owner_dependency(credential_path)
    routes = {'workers': ('worker-manager', '/api/v1/workers'),
              'executions': ('worker-manager', '/api/v1/executions'),
              'sources': ('code-manager', '/api/v1/sources')}

    def forward(request, identity, name, method, path, payload=None, status=200):
        adapters = upstream_factory(identity, request.headers['authorization'][7:])
        adapter = adapters.get(name)
        if adapter is None:
            raise HTTPException(503, 'Upstream is not configured')
        try:
            if method == 'GET': result = adapter.get(path)
            elif method == 'DELETE': result = adapter.delete(path)
            else: result = getattr(adapter, method.lower())(path, payload)
            response = JSONResponse(envelope(result), status_code=status)
        except ValueError:
            raise HTTPException(422, 'Invalid upstream request') from None
        except ConsumerAPIError as exc:
            code = exc.status if exc.status in (401, 403, 404, 409, 413, 422) else 503
            response = JSONResponse({'contract_version': '1.0.0', 'error': {
                'code': exc.code, 'message': 'Upstream request failed'}}, status_code=code)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.get('/{operation}')
    def read(operation: str, request: Request, identity=Depends(owner)):
        if operation not in routes:
            raise HTTPException(404, 'Unsupported upstream operation')
        name, path = routes[operation]
        return forward(request, identity, name, 'GET', path)

    def worker_path(worker_id):
        try:
            identifier(worker_id)
            if '..' in worker_id: raise ValueError()
        except ValueError:
            raise HTTPException(422, 'Invalid worker identifier') from None
        return '/api/v1/workers/' + _identifier(worker_id)

    @router.post('/workers', status_code=201)
    def register(body: RegisterBody, request: Request, identity=Depends(owner)):
        worker_path(body.worker_id)
        return forward(request, identity, 'worker-manager', 'POST', '/api/v1/workers', body.model_dump(), status=201)

    @router.get('/workers/{worker_id}')
    def worker(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'GET', worker_path(worker_id))

    @router.patch('/workers/{worker_id}')
    def configure(worker_id: str, body: ConfigureBody, request: Request, identity=Depends(owner)):
        if body.configuration is None and body.schedule is None:
            raise HTTPException(422, 'Configuration or schedule is required')
        return forward(request, identity, 'worker-manager', 'PATCH', worker_path(worker_id), body.model_dump(exclude_none=True))

    @router.delete('/workers/{worker_id}')
    def remove(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'DELETE', worker_path(worker_id))

    @router.post('/workers/{worker_id}/enable')
    def enable(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'POST', worker_path(worker_id) + '/enable', {})

    @router.post('/workers/{worker_id}/disable')
    def disable(worker_id: str, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'POST', worker_path(worker_id) + '/disable', {})

    @router.post('/workers/{worker_id}/executions', status_code=202)
    def run(worker_id: str, body: RunRequest, request: Request, identity=Depends(owner)):
        try:
            identifier(worker_id)
            if '..' in worker_id:
                raise ValueError()
            path = '/api/v1/workers/' + _identifier(worker_id) + '/executions'
        except ValueError:
            raise HTTPException(422, 'Invalid worker identifier') from None
        return forward(request, identity, 'worker-manager', 'POST', path, body.model_dump(), status=202)

    @router.get('/executions/{execution_id}')
    def execution(execution_id: UUID, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'GET', '/api/v1/executions/' + str(execution_id))

    @router.post('/executions/{execution_id}/cancel')
    def cancel(execution_id: UUID, request: Request, identity=Depends(owner)):
        return forward(request, identity, 'worker-manager', 'POST', '/api/v1/executions/' + str(execution_id) + '/cancel', {})

    return router
