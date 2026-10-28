import json
import sqlite3
from pathlib import Path


SCHEMA_VERSION = 2

MIGRATIONS = {
    1: (
        """CREATE TABLE dm_models (
            model_id TEXT NOT NULL,
            version TEXT NOT NULL,
            owner_id TEXT NOT NULL,
            definition TEXT NOT NULL,
            PRIMARY KEY(model_id, version)
        )""",
        """CREATE TABLE dm_resources (
            resource_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            model_version TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(model_id, model_version)
                REFERENCES dm_models(model_id, version)
        )""",
        """CREATE TABLE dm_records (
            resource_id TEXT NOT NULL,
            record_id TEXT NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(resource_id, record_id),
            FOREIGN KEY(resource_id)
                REFERENCES dm_resources(resource_id) ON DELETE CASCADE
        )""",
    ),
    2: (
        "CREATE INDEX idx_dm_resources_owner ON dm_resources(owner_id)",
        "CREATE INDEX idx_dm_models_owner ON dm_models(owner_id)",
        "CREATE INDEX idx_dm_records_updated ON dm_records(resource_id, updated_at)",
    ),
}


class SQLiteStorage:
    def __init__(self, path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA busy_timeout = 10000")
        return db

    def initialize(self):
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS dm_schema_version (
                    version INTEGER NOT NULL
                )
            """)
            if db.execute(
                "SELECT 1 FROM dm_schema_version LIMIT 1"
            ).fetchone() is None:
                db.execute(
                    "INSERT INTO dm_schema_version(version) VALUES(0)"
                )

            version = db.execute(
                "SELECT MAX(version) FROM dm_schema_version"
            ).fetchone()[0]

            if version is None or version < 0:
                raise RuntimeError("Invalid database schema version")
            if version > SCHEMA_VERSION:
                raise RuntimeError(
                    f"Database schema version {version} is newer than "
                    f"supported version {SCHEMA_VERSION}"
                )

            # Commit schema-version table initialization before starting
            # each explicit migration transaction.
            db.commit()

            while version < SCHEMA_VERSION:
                target = version + 1
                statements = MIGRATIONS.get(target)
                if statements is None:
                    raise RuntimeError(f"Missing migration {target}")

                # Each migration and its version update commit atomically.
                db.execute("BEGIN")
                try:
                    for statement in statements:
                        db.execute(statement)
                    db.execute(
                        "UPDATE dm_schema_version SET version=?", (target,)
                    )
                    db.commit()
                except Exception:
                    db.rollback()
                    raise
                version = target

    def execute(self, sql, params=()):
        with self.connect() as db:
            cursor = db.execute(sql, params)
            return cursor.lastrowid

    def one(self, sql, params=()):
        with self.connect() as db:
            row = db.execute(sql, params).fetchone()
            return dict(row) if row else None

    def many(self, sql, params=()):
        with self.connect() as db:
            return [dict(row) for row in db.execute(sql, params).fetchall()]

    @staticmethod
    def decode_model(row):
        if row:
            row["definition"] = json.loads(row["definition"])
        return row

    @staticmethod
    def decode_record(row):
        if row:
            row["data"] = json.loads(row["data"])
        return row
