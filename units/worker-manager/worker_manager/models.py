"""Domain models owned by WORKER MANAGER.

These models intentionally do not model Runtime execution status or duplicate
CORE message/error envelopes. Execution is delegated to WORKER RUNTIME.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class WorkerLifecycle(StrEnum):
    CONFIGURED = "configured"
    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class Schedule:
    """Optional scheduling policy. ``None`` at WorkerRecord means manual-only."""

    kind: str = "manual"
    interval_seconds: int | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"manual", "interval"}:
            raise ValueError("schedule kind must be 'manual' or 'interval'")
        if self.kind == "manual" and self.interval_seconds is not None:
            raise ValueError("manual schedule cannot define interval_seconds")
        if self.kind == "interval":
            if isinstance(self.interval_seconds, bool) or not isinstance(
                self.interval_seconds, int
            ) or self.interval_seconds <= 0:
                raise ValueError("interval schedule requires positive integer seconds")


@dataclass(frozen=True, slots=True)
class WorkerDefinition:
    """Stable manager-owned identity and immutable published artifact reference."""

    worker_id: str
    artifact_id: str
    artifact_hash: str
    entrypoint: str

    def __post_init__(self) -> None:
        for name in ("worker_id", "artifact_id", "artifact_hash", "entrypoint"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if ":" not in self.entrypoint:
            raise ValueError("entrypoint must use module:function syntax")
        module, function = self.entrypoint.split(":", 1)
        if not module.strip() or not function.strip():
            raise ValueError("entrypoint must use module:function syntax")


@dataclass(frozen=True, slots=True)
class WorkerRecord:
    definition: WorkerDefinition
    lifecycle: WorkerLifecycle = WorkerLifecycle.CONFIGURED
    configuration: Mapping[str, Any] = field(default_factory=dict)
    schedule: Schedule = field(default_factory=Schedule)

    def __post_init__(self) -> None:
        if not isinstance(self.lifecycle, WorkerLifecycle):
            raise ValueError("lifecycle must be a WorkerLifecycle value")
        if not isinstance(self.configuration, Mapping):
            raise ValueError("configuration must be a mapping")
        if not isinstance(self.schedule, Schedule):
            raise ValueError("schedule must be a Schedule value")
        # Prevent mutation of caller-owned configuration after registration.
        object.__setattr__(self, "configuration", dict(self.configuration))
