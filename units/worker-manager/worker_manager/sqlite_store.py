"""SQLite-backed durable storage for WORKER MANAGER records.

This store persists manager metadata only; it never stores execution results or
executes worker code. A single manager process should own a database file.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Schedule, WorkerDefinition, WorkerLifecycle, WorkerRecord


class SQLiteWorkerStore:
    """Small SQLite repository for worker definitions and manager configuration."""

    def __init__(self, database_path: str | Path, *, timeout_seconds: float = 5.0):
        if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.database_path = str(database_path)
        if not self.database_path.strip() or self.database_path == ":memory:":
            raise ValueError("database_path must identify a durable SQLite file")
        Path(self.database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = float(timeout_seconds)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=self.timeout_seconds)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    artifact_id TEXT NOT NULL,
                    artifact_hash TEXT NOT NULL,
                    entrypoint TEXT NOT NULL,
                    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('configured', 'enabled', 'disabled')),
                    configuration_json TEXT NOT NULL,
                    schedule_kind TEXT NOT NULL CHECK (schedule_kind IN ('manual', 'interval')),
                    interval_seconds INTEGER NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    @staticmethod
    def _encode(record: WorkerRecord) -> tuple:
        try:
            configuration = json.dumps(
                dict(record.configuration), sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("configuration must contain JSON-compatible values") from exc
        return (
            record.definition.worker_id,
            record.definition.artifact_id,
            record.definition.artifact_hash,
            record.definition.entrypoint,
            record.lifecycle.value,
            configuration,
            record.schedule.kind,
            record.schedule.interval_seconds,
        )

    @staticmethod
    def _decode(row: sqlite3.Row) -> WorkerRecord:
        try:
            configuration = json.loads(row["configuration_json"])
            if not isinstance(configuration, dict):
                raise ValueError("stored configuration is not an object")
            return WorkerRecord(
                definition=WorkerDefinition(
                    worker_id=row["worker_id"],
                    artifact_id=row["artifact_id"],
                    artifact_hash=row["artifact_hash"],
                    entrypoint=row["entrypoint"],
                ),
                lifecycle=WorkerLifecycle(row["lifecycle"]),
                configuration=configuration,
                schedule=Schedule(
                    kind=row["schedule_kind"],
                    interval_seconds=row["interval_seconds"],
                ),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("invalid worker record stored in SQLite") from exc

    def list(self) -> tuple[WorkerRecord, ...]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM workers ORDER BY worker_id").fetchall()
        return tuple(self._decode(row) for row in rows)

    def get(self, worker_id: str) -> WorkerRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM workers WHERE worker_id = ?", (worker_id,)
            ).fetchone()
        return None if row is None else self._decode(row)

    def save_new(self, record: WorkerRecord) -> None:
        values = self._encode(record)
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO workers
                (worker_id, artifact_id, artifact_hash, entrypoint, lifecycle,
                 configuration_json, schedule_kind, interval_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                values,
            )

    def save(self, record: WorkerRecord) -> None:
        values = self._encode(record)
        with self._connect() as connection:
            cursor = connection.execute(
                """UPDATE workers SET artifact_id=?, artifact_hash=?, entrypoint=?,
                   lifecycle=?, configuration_json=?, schedule_kind=?, interval_seconds=?,
                   updated_at=CURRENT_TIMESTAMP WHERE worker_id=?""",
                values[1:] + (values[0],),
            )
            if cursor.rowcount != 1:
                raise KeyError(record.definition.worker_id)

    def delete(self, worker_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM workers WHERE worker_id = ?", (worker_id,))
            if cursor.rowcount != 1:
                raise KeyError(worker_id)
