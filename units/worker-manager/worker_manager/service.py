"""In-memory management service with an injectable Runtime adapter boundary."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Any, Mapping

from .models import Schedule, WorkerDefinition, WorkerLifecycle, WorkerRecord
from .runtime_gateway import ExecutionRequest, RuntimeGateway


class WorkerManagerError(Exception):
    """Base exception for WORKER MANAGER domain errors."""


class WorkerNotFound(WorkerManagerError):
    """Raised when a worker identifier is not registered."""


class WorkerConflict(WorkerManagerError):
    """Raised when a worker identifier is already registered differently."""


class WorkerNotEnabled(WorkerManagerError):
    """Raised when execution is requested for a non-enabled worker."""


class RuntimeGatewayUnavailable(WorkerManagerError):
    """Raised when execution is requested without a configured Runtime adapter."""


class WorkerManager:
    """Manage workers without loading or executing worker code."""

    def __init__(self, runtime_gateway: RuntimeGateway | None = None) -> None:
        self._records: dict[str, WorkerRecord] = {}
        self._lock = RLock()
        self._runtime_gateway = runtime_gateway

    def register(
        self,
        definition: WorkerDefinition,
        *,
        configuration: Mapping[str, Any] | None = None,
        schedule: Schedule | None = None,
    ) -> WorkerRecord:
        record = WorkerRecord(
            definition=definition,
            lifecycle=WorkerLifecycle.CONFIGURED,
            configuration={} if configuration is None else configuration,
            schedule=Schedule() if schedule is None else schedule,
        )
        with self._lock:
            existing = self._records.get(definition.worker_id)
            if existing is not None:
                if existing.definition == definition:
                    raise WorkerConflict(
                        f"worker already registered: {definition.worker_id}"
                    )
                raise WorkerConflict(
                    "worker identifier already belongs to another definition: "
                    f"{definition.worker_id}"
                )
            self._records[definition.worker_id] = record
            return record

    def get(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            return self._require(worker_id)

    def list(self) -> tuple[WorkerRecord, ...]:
        with self._lock:
            return tuple(self._records[key] for key in sorted(self._records))

    def configure(
        self,
        worker_id: str,
        *,
        configuration: Mapping[str, Any] | None = None,
        schedule: Schedule | None = None,
    ) -> WorkerRecord:
        with self._lock:
            current = self._require(worker_id)
            updated = replace(
                current,
                configuration=(
                    current.configuration
                    if configuration is None
                    else configuration
                ),
                schedule=current.schedule if schedule is None else schedule,
            )
            self._records[worker_id] = updated
            return updated

    def enable(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            current = self._require(worker_id)
            updated = replace(current, lifecycle=WorkerLifecycle.ENABLED)
            self._records[worker_id] = updated
            return updated

    def disable(self, worker_id: str) -> WorkerRecord:
        with self._lock:
            current = self._require(worker_id)
            updated = replace(current, lifecycle=WorkerLifecycle.DISABLED)
            self._records[worker_id] = updated
            return updated

    def request_execution(
        self,
        worker_id: str,
        *,
        input_payload: Mapping[str, Any] | None = None,
        timeout_seconds: float = 30.0,
        idempotency_key: str | None = None,
    ) -> Any:
        """Submit an enabled worker's request through the injected gateway.

        The Runtime execution result is returned unchanged. This method
        submits a request; it does not execute worker code itself.
        """
        if input_payload is not None and not isinstance(input_payload, Mapping):
            raise ValueError("input_payload must be a mapping")

        with self._lock:
            record = self._require(worker_id)
            if record.lifecycle != WorkerLifecycle.ENABLED:
                raise WorkerNotEnabled(
                    f"worker is not enabled: {worker_id}"
                )
            gateway = self._runtime_gateway
            if gateway is None:
                raise RuntimeGatewayUnavailable(
                    "no WORKER RUNTIME gateway has been configured"
                )
            request = ExecutionRequest(
                definition=record.definition,
                configuration=record.configuration,
                input_payload={} if input_payload is None else input_payload,
                timeout_seconds=timeout_seconds,
                idempotency_key=idempotency_key,
            )

        # Do not hold the manager lock while calling an external adapter.
        return gateway.submit(request)

    def remove(self, worker_id: str) -> None:
        with self._lock:
            self._require(worker_id)
            del self._records[worker_id]

    def _require(self, worker_id: str) -> WorkerRecord:
        try:
            return self._records[worker_id]
        except KeyError as exc:
            raise WorkerNotFound(f"worker not found: {worker_id}") from exc

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel by execution identity; does not change worker lifecycle."""
        if not isinstance(execution_id, str) or not execution_id:
            raise ValueError('execution_id must be a nonempty string')
        with self._lock:
            gateway = self._runtime_gateway
        if gateway is None or not callable(getattr(gateway, 'cancel', None)):
            raise RuntimeGatewayUnavailable('runtime gateway does not support cancellation')
        return gateway.cancel(execution_id)

    def get_execution(self, execution_id: str) -> Any:
        """Read execution state independently from lifecycle state."""
        with self._lock:
            gateway = self._runtime_gateway
        if gateway is None or not callable(getattr(gateway, 'get', None)):
            raise RuntimeGatewayUnavailable('runtime gateway does not support execution lookup')
        return gateway.get(execution_id)
