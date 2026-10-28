import re
from .errors import InvalidInput


_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def require_id(value, name):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise InvalidInput(f"{name} must be a non-empty opaque identifier")
    return value


def validate_model(model):
    if not isinstance(model, dict):
        raise InvalidInput("Model must be an object")
    require_id(model.get("model_id"), "model_id")
    require_id(model.get("owner_id"), "owner_id")
    version = model.get("version", "1.0.0")
    if not isinstance(version, str) or not version:
        raise InvalidInput("version must be a non-empty string")
    fields = model.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise InvalidInput("fields must be a non-empty object")
    allowed = {"string", "integer", "number", "boolean", "object", "array"}
    for name, spec in fields.items():
        if not isinstance(name, str) or not name or not isinstance(spec, dict):
            raise InvalidInput("Each field needs a name and an object definition")
        if spec.get("type") not in allowed:
            raise InvalidInput(f"Unsupported type for field: {name}")
    required = model.get("required", [])
    if not isinstance(required, list) or any(
        not isinstance(name, str) or name not in fields
        for name in required
    ):
        raise InvalidInput("required must list existing field names")
    return {**model, "version": version, "required": required}


def validate_record(model, record):
    if not isinstance(record, dict):
        raise InvalidInput("Record must be a JSON object")
    fields = model["fields"]
    unknown = set(record) - set(fields)
    if unknown:
        raise InvalidInput("Unknown fields are not allowed", {"fields": sorted(unknown)})
    missing = set(model.get("required", [])) - set(record)
    if missing:
        raise InvalidInput("Required fields are missing", {"fields": sorted(missing)})

    for name, value in record.items():
        kind = fields[name]["type"]
        valid = {
            "string": lambda x: isinstance(x, str),
            "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
            "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            "boolean": lambda x: isinstance(x, bool),
            "object": lambda x: isinstance(x, dict),
            "array": lambda x: isinstance(x, list),
        }[kind](value)
        if not valid:
            raise InvalidInput(f"Field '{name}' must have type {kind}")
    return record
