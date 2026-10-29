"""Owner-scoped Worker Manager HTTP API with explicit single-process ownership."""
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from . import Schedule, WorkerDefinition
from .http_common import BodyLimitMiddleware, ERROR_RESPONSES, envelope, identifier, owner_dependency, register_error_handlers
from .service import WorkerConflict, WorkerNotEnabled, WorkerNotFound


class ScheduleBody(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: str = 'manual'
    interval_seconds: int | None = Field(default=None, gt=0)


class RegisterBody(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    worker_id: str = Field(min_length=1, max_length=128)
    artifact_id: str = Field(min_length=1, max_length=256)
    artifact_hash: str = Field(pattern=r'^sha256:[0-9a-f]{64}$')
    entrypoint: str = Field(min_length=3, max_length=256)
    configuration: dict = Field(default_factory=dict)
    schedule: ScheduleBody = Field(default_factory=ScheduleBody)


class ConfigureBody(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    configuration: dict | None = None
    schedule: ScheduleBody | None = None


class RunBody(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    input_payload: dict = Field(default_factory=dict)
    timeout_seconds: float = Field(default=30, gt=0, le=300, allow_inf_nan=False)
    idempotency_key: str = Field(min_length=1, max_length=256)


def create_app(service, credential_path):
    @asynccontextmanager
    async def lifespan(app):
        service.start()
        try:
            yield
        finally:
            service.close()
    app = FastAPI(title='Worker Manager', version='0.1.0', lifespan=lifespan,
                  docs_url=None, redoc_url=None, responses=ERROR_RESPONSES)
    app.add_middleware(BodyLimitMiddleware)
    register_error_handlers(app)
    owner = owner_dependency(credential_path)

    def error_handler(status, code):
        def handler(request, exc):
            return JSONResponse({'contract_version': '1.0.0', 'error': {'code': code,
                'message': {404: 'Resource not found', 409: 'Operation conflicts with current state',
                            422: 'Invalid request'}[status]}}, status_code=status)
        return handler
    for error in (WorkerNotFound, KeyError):
        app.add_exception_handler(error, error_handler(404, 'NOT_FOUND'))
    for error in (WorkerConflict, WorkerNotEnabled):
        app.add_exception_handler(error, error_handler(409, 'CONFLICT'))
    app.add_exception_handler(ValueError, error_handler(422, 'INVALID_INPUT'))

    @app.get('/health')
    def health():
        if getattr(service, 'last_error', None):
            raise HTTPException(503, 'Scheduler unavailable')
        return {'status': 'ok', 'service': 'worker-manager'}

    @app.get('/api/v1/workers')
    def list_workers(identity=Depends(owner)):
        return envelope({'workers': [asdict(row) for row in service.manager(identity).list()]})

    @app.post('/api/v1/workers', status_code=201)
    def register(body: RegisterBody, identity=Depends(owner)):
        identifier(body.worker_id)
        definition = WorkerDefinition(**body.model_dump(include={'worker_id','artifact_id','artifact_hash','entrypoint'}))
        return envelope(service.register(identity, definition, body.configuration, Schedule(**body.schedule.model_dump())))

    @app.get('/api/v1/workers/{worker_id}')
    def get(worker_id: str, identity=Depends(owner)):
        return envelope(asdict(service.manager(identity).get(worker_id)))

    @app.patch('/api/v1/workers/{worker_id}')
    def configure(worker_id: str, body: ConfigureBody, identity=Depends(owner)):
        return envelope(service.change(identity, worker_id, 'configure', configuration=body.configuration,
            schedule=None if body.schedule is None else Schedule(**body.schedule.model_dump())))

    @app.delete('/api/v1/workers/{worker_id}')
    def delete(worker_id: str, identity=Depends(owner)):
        service.change(identity, worker_id, 'delete')
        return envelope({'deleted': True})

    @app.post('/api/v1/workers/{worker_id}/enable')
    def enable(worker_id: str, identity=Depends(owner)):
        return envelope(service.change(identity, worker_id, 'enable'))

    @app.post('/api/v1/workers/{worker_id}/disable')
    def disable(worker_id: str, identity=Depends(owner)):
        return envelope(service.change(identity, worker_id, 'disable'))

    @app.post('/api/v1/workers/{worker_id}/executions', status_code=202)
    def run(worker_id: str, body: RunBody, identity=Depends(owner)):
        return envelope(service.submit(identity, worker_id, body.input_payload, body.timeout_seconds, body.idempotency_key))

    @app.get('/api/v1/executions')
    def history(identity=Depends(owner)):
        return envelope({'executions': service.history(identity)})

    @app.get('/api/v1/executions/{execution_id}')
    def execution(execution_id: str, identity=Depends(owner)):
        return envelope(service.get(identity, execution_id))

    @app.post('/api/v1/executions/{execution_id}/cancel')
    def cancel(execution_id: str, identity=Depends(owner)):
        try:
            confirmed = service.cancel(identity, execution_id)
        except KeyError:
            raise
        except Exception:
            raise HTTPException(503, 'Cancellation could not be confirmed') from None
        return envelope({'cancelled': confirmed})

    return app
