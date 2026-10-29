"""Read-only authenticated Dashboard BFF; tokens never enter page HTML or URLs."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from worker_manager.http_common import envelope, owner_dependency
from public_api import ConsumerAPIError, PublicAPI


def create_router(credential_path, upstream_factory):
    """upstream_factory(owner, bearer_token) returns named, owner-bound adapters.

    Only explicitly registered read operations are exposed. The caller's bearer
    credential is validated locally before any upstream request. No service-wide
    credential is substituted for an end user's identity.
    """
    router = APIRouter(prefix='/api/upstreams')
    owner = owner_dependency(credential_path)
    routes = {'workers': ('worker-manager', '/api/v1/workers'),
              'executions': ('worker-manager', '/api/v1/executions'),
              'sources': ('code-manager', '/api/v1/sources')}

    @router.get('/{operation}')
    def read(operation: str, request: Request, identity=Depends(owner)):
        if operation not in routes:
            raise HTTPException(404, 'Unsupported upstream operation')
        name, path = routes[operation]
        adapters = upstream_factory(identity, request.headers['authorization'][7:])
        adapter = adapters.get(name)
        if adapter is None:
            raise HTTPException(503, 'Upstream is not configured')
        try:
            response = JSONResponse(envelope(adapter.get(path)))
            response.headers['Cache-Control'] = 'no-store'
            response.headers['Vary'] = 'Authorization'
            return response
        except ConsumerAPIError as exc:
            status = exc.status if exc.status in (401, 403, 404) else 503
            return JSONResponse({'contract_version': '1.0.0', 'error': {
                'code': exc.code, 'message': 'Upstream request failed'}}, status_code=status)

    return router
