"""Authenticated Runtime HTTP API. Each owner gets a separate persistent runtime."""
from dataclasses import asdict
import threading
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from worker_manager import ExecutionRequest, WorkerDefinition
from worker_manager.http_common import BodyLimitMiddleware, ERROR_RESPONSES, envelope, identifier, owner_dependency, register_error_handlers


class DefinitionBody(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    worker_id: str = Field(min_length=1, max_length=128)
    artifact_id: str = Field(min_length=1, max_length=256)
    artifact_hash: str = Field(pattern=r'^sha256:[0-9a-f]{64}$')
    entrypoint: str = Field(min_length=3, max_length=256)


class ExecutionBody(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    definition: DefinitionBody
    configuration: dict = Field(default_factory=dict)
    input_payload: dict = Field(default_factory=dict)
    execution_id: str
    timeout_seconds: float = Field(default=30, gt=0, le=300, allow_inf_nan=False)
    idempotency_key: str = Field(min_length=1, max_length=256)
    depth: int = Field(default=0, ge=0, le=0)


def create_app(credential_path, runtime_factory):
    """runtime_factory(owner) must use an owner-bound provider and distinct DB.

    Do not share a WorkerRuntime across owners. The factory runs once per owner;
    credentials are reloaded for every request, including lookup/cancellation.
    """
    app = FastAPI(title='Worker Runtime', version='0.1.0', docs_url=None, redoc_url=None, responses=ERROR_RESPONSES)
    app.add_middleware(BodyLimitMiddleware)
    register_error_handlers(app)
    owner = owner_dependency(credential_path)
    runtimes, lock = {}, threading.RLock()

    def runtime(identity):
        with lock:
            if identity not in runtimes:
                try:
                    instance = runtime_factory(identity)
                except (OSError, ValueError, KeyError):
                    raise HTTPException(503, 'Runtime owner configuration unavailable') from None
                if not instance.require_sandbox or instance.sandbox_backend is None:
                    raise HTTPException(503, 'Sandbox is required for HTTP execution')
                if any(instance is other for other in runtimes.values()):
                    raise HTTPException(503, 'Runtime owner isolation is not configured')
                runtimes[identity] = instance
            return runtimes[identity]

    @app.get('/health')
    def health():
        return {'status': 'ok', 'service': 'worker-runtime'}

    @app.post('/api/v1/executions')
    def submit(body: ExecutionBody, identity=Depends(owner)):
        try:
            UUID(body.execution_id)
            identifier(body.definition.worker_id)
            request = ExecutionRequest(WorkerDefinition(**body.definition.model_dump()),
                configuration=body.configuration, input_payload=body.input_payload,
                execution_id=body.execution_id, timeout_seconds=body.timeout_seconds,
                idempotency_key=body.idempotency_key)
        except ValueError:
            raise HTTPException(422, 'Invalid execution request') from None
        return envelope(asdict(runtime(identity).submit(request)))

    @app.get('/api/v1/executions/{execution_id}')
    def get(execution_id: str, identity=Depends(owner)):
        result = runtime(identity).get(execution_id)
        if result is None:
            raise HTTPException(404, 'Execution not found')
        return envelope(asdict(result))

    @app.post('/api/v1/executions/{execution_id}/cancel')
    def cancel(execution_id: str, identity=Depends(owner)):
        instance = runtime(identity)
        if instance.get(execution_id) is None:
            raise HTTPException(404, 'Execution not found')
        return envelope({'cancelled': instance.cancel(execution_id)})

    return app
