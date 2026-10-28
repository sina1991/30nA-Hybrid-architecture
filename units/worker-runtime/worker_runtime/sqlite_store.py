"""Optional SQLite persistence for WORKER RUNTIME execution snapshots.

Only JSON-compatible execution results and idempotency metadata are stored.
This does not persist live processes or make execution recoverable after a crash.
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any

from .runtime import ExecutionError, ExecutionResult


class SQLiteExecutionStore:
    """Persist execution snapshots and idempotency keys in a local SQLite file."""

    def __init__(self, database_path: str | Path, *, timeout_seconds: float = 5.0):
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be finite and positive")
        if not str(database_path).strip() or str(database_path) == ":memory:":
            raise ValueError("database_path must identify a durable SQLite file")
        path = Path(database_path).expanduser()
        path.parent.resolve().mkdir(parents=True, exist_ok=True)
        self.database_path = str(path)
        self.timeout_seconds = float(timeout_seconds)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=self.timeout_seconds)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS idempotency_keys (
                    idempotency_key TEXT PRIMARY KEY,
                    fingerprint TEXT NOT NULL,
                    execution_id TEXT NOT NULL
                )"""
            )

    @classmethod
    def _encode_result(cls, result: ExecutionResult) -> str:
        def encode(item: ExecutionResult) -> dict[str, Any]:
            error = None if item.error is None else {
                "code": item.error.code,
                "message": item.error.message,
                "retryable": item.error.retryable,
            }
            return {
                "execution_id": item.execution_id,
                "worker_id": item.worker_id,
                "accepted": item.accepted,
                "status": item.status,
                "result": item.result,
                "error": error,
                "children": [encode(child) for child in item.children],
            }

        try:
            return json.dumps(encode(result), sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("execution result must be JSON-compatible") from exc

    @staticmethod
    def _decode_result(payload: str) -> ExecutionResult:
        def decode(item: dict[str, Any]) -> ExecutionResult:
            error_data = item.get("error")
            error = None if error_data is None else ExecutionError(
                code=error_data["code"],
                message=error_data["message"],
                retryable=error_data.get("retryable", False),
            )
            return ExecutionResult(
                execution_id=item["execution_id"],
                worker_id=item["worker_id"],
                accepted=item["accepted"],
                status=item["status"],
                result=item.get("result"),
                error=error,
                children=tuple(decode(child) for child in item.get("children", [])),
            )

        try:
            value = json.loads(payload)
            if not isinstance(value, dict):
                raise ValueError("execution payload must be an object")
            return decode(value)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("invalid execution snapshot stored in SQLite") from exc

    def load(self) -> tuple[dict[str, ExecutionResult], dict[str, tuple[str, str]]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload_json FROM executions").fetchall()
            keys = connection.execute(
                "SELECT idempotency_key, fingerprint, execution_id FROM idempotency_keys"
            ).fetchall()
        history = {}
        for row in rows:
            result = self._decode_result(row["payload_json"])
            history[result.execution_id] = result
        key_map = {
            row["idempotency_key"]: (row["fingerprint"], row["execution_id"])
            for row in keys
        }
        if any(execution_id not in history for _, execution_id in key_map.values()):
            raise RuntimeError("idempotency key references a missing execution snapshot")
        return history, key_map

    def accept(
        self,
        result: ExecutionResult,
        *,
        idempotency_key: str | None,
        fingerprint: str,
    ) -> None:
        payload = self._encode_result(result)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO executions (execution_id, payload_json) VALUES (?, ?)",
                (result.execution_id, payload),
            )
            if idempotency_key is not None:
                connection.execute(
                    """INSERT INTO idempotency_keys
                    (idempotency_key, fingerprint, execution_id) VALUES (?, ?, ?)""",
                    (idempotency_key, fingerprint, result.execution_id),
                )

    def save_result(self, result: ExecutionResult) -> None:
        payload = self._encode_result(result)
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO executions (execution_id, payload_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(execution_id) DO UPDATE SET
                payload_json=excluded.payload_json, updated_at=CURRENT_TIMESTAMP""",
                (result.execution_id, payload),
            )
