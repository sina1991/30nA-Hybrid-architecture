"""Manager-owned interface for interacting with WORKER RUNTIME.

The gateway is an adapter boundary; worker execution and lifecycle management
remain outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol
from uuid import uuid4

from .models import WorkerDefinition


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """Immutable request metadata passed from the manager to a Runtime adapter."""

    definition: WorkerDefinition
    configuration: Mapping[str, Any] = field(default_factory=dict)
    input_payload: Mapping[str, Any] = field(default_factory=dict)
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    timeout_seconds: float = 30.0
    idempotency_key: str | None = None
    depth: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.definition, WorkerDefinition):
            raise ValueError("definition must be a WorkerDefinition")
        if not isinstance(self.configuration, Mapping):
            raise ValueError("configuration must be a mapping")
        if not isinstance(self.input_payload, Mapping):
            raise ValueError("input_payload must be a mapping")

        object.__setattr__(self, "configuration", dict(self.configuration))
        object.__setattr__(self, "input_payload", dict(self.input_payload))


class RuntimeGateway(Protocol):
    """Structural interface for the WORKER RUNTIME adapter."""

    def submit(self, request: ExecutionRequest) -> Any:
        """Submit a request and return its execution result."""
        ...

    def get(self, execution_id: str) -> Any:
        """Return the known execution result, or None if it is unknown."""
        ...

    def cancel(self, execution_id: str) -> bool:
        """Request best-effort cancellation of an execution."""
        ...
