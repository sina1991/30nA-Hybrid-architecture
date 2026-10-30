"""Authenticated Dashboard BFF for explicit owner-scoped Manager operations."""
from uuid import UUID
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from worker_manager.api import RegisterBody, ConfigureBody
from worker_manager.http_common import ERROR_RESPONSES, envelope, identifier, owner_dependency
from public_api import ConsumerAPIError, _identifier
from modules.execution import run_module
from modules import slots
from modules import slot_workers
from market_data.data import chart as gold_chart


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

    @router.get('/market/candles')
    def market_candles(limit: int = Query(default=200, ge=1, le=1000),
                       period: int = Query(default=20, ge=1, le=500),
                       include_open: bool = True, identity=Depends(owner)):
        try:
            result = gold_chart(limit=limit, period=period, include_open=include_open)
        except (ValueError, OSError, sqlite3.Error):
            raise HTTPException(503, 'Market data is unavailable') from None
        response = JSONResponse(envelope(result))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.get('/market/indicators/sma')
    def market_sma(limit: int = Query(default=200, ge=1, le=1000),
                   period: int = Query(default=20, ge=1, le=500),
                   include_open: bool = True, identity=Depends(owner)):
        try:
            result = gold_chart(limit=max(limit, period), period=period, include_open=include_open)
        except (ValueError, OSError, sqlite3.Error):
            raise HTTPException(503, 'Market data is unavailable') from None
        response = JSONResponse(envelope({'symbol':result['symbol'], 'interval':result['interval'],
            'indicator':result['moving_average'], 'last_success':result['last_success'],
            'collector_error':result['collector_error']}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/modules/{module_id}/state')
    def module_state(module_id: str, body: dict, request: Request, identity=Depends(owner)):
        if module_id not in ('counter', 'slot-note'):
            raise HTTPException(404, 'Unsupported stateful module')
        if any(str(key).startswith('_') or key == 'owner' for key in body):
            raise HTTPException(422, 'Invalid module input')
        slot = body.get('slot')
        try:
            result = run_module(module_id, {**body, '_state_owner': identity, '_state_slot': slot})
        except (ValueError, TypeError, KeyError, OverflowError):
            raise HTTPException(422, 'Invalid module input') from None
        response = JSONResponse(envelope(result))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/modules/{module_id}/run')
    def run_independent_module(module_id: str, body: dict, identity=Depends(owner)):
        if set(body) != {'input'} or not isinstance(body['input'], dict) or any(
                str(key).startswith('_') or key in ('owner', 'slot') for key in body['input']):
            raise HTTPException(422, 'Invalid module input')
        try:
            slots._authorize_host_monitor(identity, module_id)
            result = run_module(module_id, body['input'])
        except LookupError:
            raise HTTPException(404, 'Unknown module') from None
        except (ValueError, TypeError, OverflowError, KeyError, ZeroDivisionError):
            raise HTTPException(422, 'Invalid module input or unavailable resource') from None
        response = JSONResponse(envelope({'result': result}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.get('/slots/active')
    def list_active_slots(identity=Depends(owner)):
        response = JSONResponse(envelope({'slots': slots.list_active(identity), 'owner': identity}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots')
    def create_slot(body: dict, identity=Depends(owner)):
        if body: raise HTTPException(422, 'Invalid slot request')
        try:
            value = slots.create(identity)
        except ValueError:
            raise HTTPException(422, 'Cannot create slot') from None
        response = JSONResponse(envelope({'slot': value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/overview')
    def update_slot_overview(slot_id: str, body: dict, identity=Depends(owner)):
        if set(body) != {'visible'} or type(body['visible']) is not bool:
            raise HTTPException(422, 'Invalid slot request')
        try:
            slots.set_overview(identity, slot_id, body['visible'])
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        response = JSONResponse(envelope({'slot': slot_id, 'visible': body['visible']}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.delete('/slots/{slot_id}')
    def delete_slot(slot_id: str, identity=Depends(owner)):
        try:
            slots.delete(identity, slot_id)
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        response = JSONResponse(envelope({'deleted': slot_id}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/appearance')
    def update_slot_appearance(slot_id: str, body: dict, identity=Depends(owner)):
        try:
            value = slots.update_appearance(identity, slot_id, body)
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        except (ValueError, TypeError):
            raise HTTPException(422, 'Invalid slot appearance') from None
        response = JSONResponse(envelope({'appearance': value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/worker')
    def configure_slot_worker(slot_id: str, body: dict, identity=Depends(owner)):
        try:
            value = slot_workers.configure(identity, slot_id, body)
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        except (ValueError, TypeError):
            raise HTTPException(422, 'Invalid slot worker configuration') from None
        response = JSONResponse(envelope({'worker': value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/binding')
    def bind_slot(slot_id: str, body: dict, identity=Depends(owner)):
        if set(body) - {'module_id', 'context', 'only_if_missing'} or type(body.get('only_if_missing', False)) is not bool:
            raise HTTPException(422, 'Invalid slot binding')
        try:
            value = slots.bind_active(identity, slot_id, body.get('module_id'), body.get('context', {}), body.get('only_if_missing', False))
        except LookupError:
            raise HTTPException(404, 'Slot not found') from None
        except (ValueError, TypeError):
            raise HTTPException(422, 'Invalid slot binding') from None
        response = JSONResponse(envelope({'binding':value}))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/read')
    def read_slot(slot_id: str, body: dict, identity=Depends(owner)):
        if set(body) != {'module_id'} or not isinstance(body['module_id'], str):
            raise HTTPException(422, 'Invalid slot request')
        try:
            value = slots.read(identity, slot_id)
            if value['module_id'] != body['module_id']:
                raise ValueError('slot binding changed')
        except LookupError:
            raise HTTPException(404, 'Slot not configured') from None
        except (ValueError, TypeError, OverflowError, KeyError):
            raise HTTPException(422, 'Invalid slot request') from None
        response = JSONResponse(envelope(value))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

    @router.post('/slots/{slot_id}/execute')
    def execute_slot(slot_id: str, body: dict, identity=Depends(owner)):
        if set(body) != {'module_id', 'input'} or not isinstance(body['input'], dict):
            raise HTTPException(422, 'Invalid module input')
        try:
            value = slots.execute(identity, slot_id, body['input'], expected_module=body['module_id'])
        except LookupError:
            raise HTTPException(404, 'Slot not configured') from None
        except (ValueError, TypeError, OverflowError, KeyError):
            raise HTTPException(422, 'Invalid module input') from None
        response = JSONResponse(envelope(value))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Vary'] = 'Authorization'
        return response

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
