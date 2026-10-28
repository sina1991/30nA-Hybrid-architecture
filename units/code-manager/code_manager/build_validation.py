"""Fail-closed static preflight for untrusted Python source ZIPs.

This module never extracts or executes source. It intentionally cannot produce a
publishable artifact: the isolated test/build stage is not available yet.
"""
from __future__ import annotations

import ast
import hashlib
import json
import zipfile
from io import BytesIO

from .source_archive import inspect_source_archive
from .errors import SourceValidationError


def validate_build_preflight(source: dict) -> dict:
    """Run non-executing checks and report unavailable mandatory stages explicitly."""
    stages = []

    def record(name, status, detail):
        stages.append({"stage": name, "status": status, "detail": detail})

    data = source.get("source_bytes")
    declared_hash = source.get("source_hash")
    entrypoint = source.get("entrypoint")

    try:
        inspection = inspect_source_archive(data, entrypoint)
        record("inspect_archive", "passed", "ZIP structure and resource limits validated without extraction")
    except (SourceValidationError, TypeError) as exc:
        record("inspect_archive", "failed", str(exc))
        return {"status": "failed", "publishable": False, "stages": stages}

    actual_hash = hashlib.sha256(data).hexdigest()
    if not isinstance(declared_hash, str) or actual_hash != declared_hash:
        record("verify_source_hash", "failed", "Original ZIP bytes do not match the registered SHA-256")
        return {"status": "failed", "publishable": False, "stages": stages}
    record("verify_source_hash", "passed", actual_hash)

    # Archive inspection already rejects traversal, duplicate names and symlinks.
    record("validate_archive_paths", "passed", "Path, duplicate, symlink, encryption and size checks passed")

    syntax_errors = []
    dependency_files = []
    try:
        with zipfile.ZipFile(BytesIO(data), "r") as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                if name.rsplit("/", 1)[-1] in {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "poetry.lock"}:
                    dependency_files.append(name)
                if name.endswith(".py"):
                    try:
                        raw = archive.read(info)
                        ast.parse(raw.decode("utf-8"), filename=name)
                    except (UnicodeDecodeError, SyntaxError, ValueError) as exc:
                        syntax_errors.append({"file": name, "reason": str(exc)})
    except (zipfile.BadZipFile, OSError, ValueError):
        record("syntax_check", "failed", "Source ZIP could not be read consistently")
        return {"status": "failed", "publishable": False, "stages": stages}

    if syntax_errors:
        record("syntax_check", "failed", json.dumps(syntax_errors, ensure_ascii=False))
        return {"status": "failed", "publishable": False, "stages": stages}
    record("syntax_check", "passed", "All Python files parse; source code was not imported or executed")

    # Until a pinned/allowlisted dependency resolver exists, dependency manifests
    # cannot be accepted as validated and no package may be published.
    if dependency_files:
        record("dependency_check", "blocked", "Dependency manifests require a pinned, allowlisted resolver: " + ", ".join(sorted(dependency_files)))
    else:
        record("dependency_check", "passed", "No dependency manifest found; third-party import resolution is not proven")

    for key in ("input_schema", "output_schema"):
        value = source.get(key)
        if not isinstance(value, dict) or value.get("type") not in (None, "object"):
            record("contract_check", "failed", key + " must be a JSON Schema object")
            return {"status": "failed", "publishable": False, "stages": stages}
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError):
            record("contract_check", "failed", key + " is not JSON serializable")
            return {"status": "failed", "publishable": False, "stages": stages}
    record("contract_check", "passed", "Input/output schema objects are present; full JSON Schema meta-validation remains pending")

    record("normalize_working_copy", "not_run", "Normalization requires the isolated build worker")
    record("test", "not_run", "Tests must execute in a resource-limited isolated build environment")
    record("package", "not_run", "Packaging is prohibited until every mandatory validation stage passes")
    record("hash", "not_run", "No final artifact exists to hash")

    return {
        "status": "blocked",
        "publishable": False,
        "source_hash": actual_hash,
        "archive_size": inspection.archive_size,
        "entry_count": inspection.entry_count,
        "expanded_size": inspection.expanded_size,
        "python_files": list(inspection.python_files),
        "stages": stages,
    }
