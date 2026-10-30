"""Manifest-based registry for built-in Dashboard UI modules.

Only explicitly supported UI types are accepted. Manifests describe modules;
they do not authorize arbitrary Python or JavaScript execution.
"""

import json
import re
from pathlib import Path

PACKAGES_DIR = Path(__file__).resolve().parent / "packages"
MODULE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SUPPORTED_TYPES = {
    "empty",
    "health",
    "theme-summary",
    "slot-note",
    "dice-roller",
    "clock",
    "counter",
    "calculator",
}


class ModuleManifestError(ValueError):
    """Raised when a module manifest is invalid."""


def load_modules() -> list[dict[str, str]]:
    """Discover and validate module manifests in deterministic order."""
    if not PACKAGES_DIR.is_dir():
        raise ModuleManifestError("Module packages directory is missing")

    modules = []
    seen_ids = set()

    for manifest_path in sorted(PACKAGES_DIR.glob("*/manifest.json")):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ModuleManifestError(
                f"Invalid manifest: {manifest_path}"
            ) from exc

        if not isinstance(data, dict):
            raise ModuleManifestError(
                f"Manifest must contain a JSON object: {manifest_path}"
            )

        required = (
            "id", "name", "description", "version", "api_version", "type"
        )
        if any(not isinstance(data.get(key), str) or not data[key].strip()
               for key in required):
            raise ModuleManifestError(
                f"Missing or invalid required fields: {manifest_path}"
            )

        module_id = data["id"]

        if not MODULE_ID_PATTERN.fullmatch(module_id):
            raise ModuleManifestError(
                f"Invalid module id: {module_id}"
            )

        if manifest_path.parent.name != module_id:
            raise ModuleManifestError(
                f"Module directory must match id: {module_id}"
            )

        if module_id in seen_ids:
            raise ModuleManifestError(
                f"Duplicate module id: {module_id}"
            )

        if data["type"] not in SUPPORTED_TYPES:
            raise ModuleManifestError(
                f"Unsupported module type for {module_id}: {data['type']}"
            )

        if data["api_version"] != "1":
            raise ModuleManifestError(
                f"Unsupported API version for {module_id}: "
                f"{data['api_version']}"
            )

        seen_ids.add(module_id)
        modules.append({
            "id": module_id,
            "name": data["name"],
            "description": data["description"],
            "version": data["version"],
            "api_version": data["api_version"],
            "type": data["type"],
        })

    if not modules:
        raise ModuleManifestError("No valid module manifests were found")

    return modules


def list_modules() -> list[dict[str, str]]:
    """Return the validated module catalog."""
    return [dict(module) for module in load_modules()]


def get_module(module_id: str) -> dict[str, str] | None:
    """Return one validated module, or None if it is not registered."""
    for module in load_modules():
        if module["id"] == module_id:
            return dict(module)
    return None
