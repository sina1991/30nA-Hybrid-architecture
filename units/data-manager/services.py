import json
import sqlite3
import uuid

from .errors import Conflict, Forbidden, NotFound, UnsupportedVersion
from .storage import SQLiteStorage
from .validation import require_id, validate_model, validate_record


class DataService:
    def __init__(self, storage):
        self.storage = storage

    def register_model(self, requester, definition):
        model = validate_model(definition)
        if requester != model["owner_id"]:
            raise Forbidden("Only the declared model owner may register it")

        existing = self.storage.one(
            "SELECT * FROM dm_models WHERE model_id=? AND version=?",
            (model["model_id"], model["version"]),
        )
        if existing:
            if json.loads(existing["definition"]) == model:
                return self.storage.decode_model(existing)
            raise Conflict(
                "Model version already exists with a different definition"
            )

        self.storage.execute(
            """INSERT INTO dm_models(model_id, version, owner_id, definition)
               VALUES(?,?,?,?)""",
            (
                model["model_id"],
                model["version"],
                model["owner_id"],
                json.dumps(model, separators=(",", ":"), sort_keys=True),
            ),
        )
        return {
            "model_id": model["model_id"],
            "version": model["version"],
            "owner_id": model["owner_id"],
            "definition": model,
        }

    def get_model(self, requester, model_id, version=None):
        require_id(model_id, "model_id")
        if version:
            row = self.storage.one(
                "SELECT * FROM dm_models WHERE model_id=? AND version=?",
                (model_id, version),
            )
        else:
            row = self.storage.one(
                "SELECT * FROM dm_models WHERE model_id=? "
                "ORDER BY rowid DESC LIMIT 1",
                (model_id,),
            )
        if not row:
            raise NotFound("Model not found")
        if requester != row["owner_id"]:
            raise Forbidden("Model access denied")
        return self.storage.decode_model(row)

    def create_resource(self, requester, body):
        resource_id = require_id(body.get("resource_id"), "resource_id")
        model_id = require_id(body.get("model_id"), "model_id")
        version = body.get("model_version")
        if not isinstance(version, str) or not version:
            raise UnsupportedVersion("model_version is required")

        model_row = self.storage.one(
            "SELECT * FROM dm_models WHERE model_id=? AND version=?",
            (model_id, version),
        )
        if not model_row:
            raise NotFound("Model version not found")
        if requester != model_row["owner_id"]:
            raise Forbidden("Only the model owner may create a resource for it")

        existing = self.storage.one(
            "SELECT * FROM dm_resources WHERE resource_id=?", (resource_id,)
        )
        if existing:
            raise Conflict("resource_id already exists")

        try:
            self.storage.execute(
                """INSERT INTO dm_resources(
                       resource_id, owner_id, model_id, model_version
                   ) VALUES(?,?,?,?)""",
                (resource_id, requester, model_id, version),
            )
        except sqlite3.IntegrityError as exc:
            raise Conflict("Resource conflicts with existing data") from exc
        return self.get_resource(requester, resource_id)

    def get_resource(self, requester, resource_id):
        require_id(resource_id, "resource_id")
        row = self.storage.one(
            "SELECT * FROM dm_resources WHERE resource_id=?", (resource_id,)
        )
        if not row:
            raise NotFound("Resource not found")
        if requester != row["owner_id"]:
            raise Forbidden("Resource access denied")
        return row

    def _model_for_resource(self, requester, resource):
        row = self.storage.one(
            "SELECT * FROM dm_models WHERE model_id=? AND version=?",
            (resource["model_id"], resource["model_version"]),
        )
        if not row:
            raise NotFound("Resource model version not found")
        if requester != row["owner_id"]:
            raise Forbidden("Model access denied")
        return self.storage.decode_model(row)["definition"]

    def _validated_record(self, requester, resource_id, body):
        resource = self.get_resource(requester, resource_id)
        model = self._model_for_resource(requester, resource)
        return validate_record(model, body)

    def write_record(self, requester, resource_id, body, record_id=None):
        """Create a new record; never silently overwrite an existing record."""
        data = self._validated_record(requester, resource_id, body)
        record_id = require_id(record_id or str(uuid.uuid4()), "record_id")

        try:
            self.storage.execute(
                """INSERT INTO dm_records(resource_id, record_id, data)
                   VALUES(?,?,?)""",
                (
                    resource_id,
                    record_id,
                    json.dumps(data, separators=(",", ":"), sort_keys=True),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise Conflict("Record already exists or resource is invalid") from exc
        return self.read_record(requester, resource_id, record_id)

    def read_record(self, requester, resource_id, record_id):
        self.get_resource(requester, resource_id)
        row = self.storage.one(
            "SELECT * FROM dm_records WHERE resource_id=? AND record_id=?",
            (resource_id, require_id(record_id, "record_id")),
        )
        if not row:
            raise NotFound("Record not found")
        return self.storage.decode_record(row)

    def replace_record(self, requester, resource_id, record_id, body):
        """Replace the complete record; required fields must be present."""
        current = self.read_record(requester, resource_id, record_id)
        data = self._validated_record(requester, resource_id, body)
        self.storage.execute(
            """UPDATE dm_records
               SET data=?, updated_at=CURRENT_TIMESTAMP
               WHERE resource_id=? AND record_id=?""",
            (
                json.dumps(data, separators=(",", ":"), sort_keys=True),
                resource_id,
                current["record_id"],
            ),
        )
        return self.read_record(requester, resource_id, record_id)

    def patch_record(self, requester, resource_id, record_id, changes):
        """Merge partial changes with the current record, then validate."""
        if not isinstance(changes, dict):
            from .errors import InvalidInput
            raise InvalidInput("PATCH body must be a JSON object")
        current = self.read_record(requester, resource_id, record_id)
        if not changes:
            from .errors import InvalidInput
            raise InvalidInput("PATCH body must not be empty")

        merged = dict(current["data"])
        merged.update(changes)
        data = self._validated_record(requester, resource_id, merged)
        self.storage.execute(
            """UPDATE dm_records
               SET data=?, updated_at=CURRENT_TIMESTAMP
               WHERE resource_id=? AND record_id=?""",
            (
                json.dumps(data, separators=(",", ":"), sort_keys=True),
                resource_id,
                current["record_id"],
            ),
        )
        return self.read_record(requester, resource_id, record_id)

    def list_records(self, requester, resource_id, limit=100):
        self.get_resource(requester, resource_id)
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 1 <= limit <= 1000
        ):
            from .errors import InvalidInput
            raise InvalidInput("limit must be between 1 and 1000")

        rows = self.storage.many(
            """SELECT * FROM dm_records
               WHERE resource_id=? ORDER BY record_id LIMIT ?""",
            (resource_id, limit),
        )
        return [self.storage.decode_record(row) for row in rows]

    def delete_record(self, requester, resource_id, record_id):
        self.get_resource(requester, resource_id)
        record_id = require_id(record_id, "record_id")
        row = self.storage.one(
            "SELECT record_id FROM dm_records WHERE resource_id=? AND record_id=?",
            (resource_id, record_id),
        )
        if not row:
            raise NotFound("Record not found")

        self.storage.execute(
            "DELETE FROM dm_records WHERE resource_id=? AND record_id=?",
            (resource_id, record_id),
        )
        return {"deleted": True, "record_id": record_id}
