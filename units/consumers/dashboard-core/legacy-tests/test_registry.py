import json

import pytest

from dashboard.modules import registry
from dashboard.modules.registry import ModuleManifestError


def write_manifest(root, directory, data, filename="manifest.json"):
    package_dir = root / directory
    package_dir.mkdir(parents=True, exist_ok=True)
    path = package_dir / filename

    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(json.dumps(data), encoding="utf-8")

    return path


def valid_manifest(module_id="sample-module"):
    return {
        "id": module_id,
        "name": "Sample Module",
        "description": "A test module.",
        "version": "1.0.0",
        "api_version": "1",
        "type": "health",
    }


def use_packages_dir(monkeypatch, tmp_path):
    packages = tmp_path / "packages"
    packages.mkdir()
    monkeypatch.setattr(registry, "PACKAGES_DIR", packages)
    return packages


def test_rejects_invalid_json(monkeypatch, tmp_path):
    packages = use_packages_dir(monkeypatch, tmp_path)
    write_manifest(packages, "sample-module", "{invalid json")

    with pytest.raises(ModuleManifestError, match="Invalid manifest"):
        registry.load_modules()


@pytest.mark.parametrize("payload", ["[]", "null", '"text"', "42"])
def test_rejects_non_object_json(monkeypatch, tmp_path, payload):
    packages = use_packages_dir(monkeypatch, tmp_path)
    write_manifest(packages, "sample-module", payload)

    with pytest.raises(ModuleManifestError, match="JSON object"):
        registry.load_modules()


def test_rejects_missing_required_field(monkeypatch, tmp_path):
    packages = use_packages_dir(monkeypatch, tmp_path)
    data = valid_manifest()
    del data["description"]
    write_manifest(packages, "sample-module", data)

    with pytest.raises(ModuleManifestError, match="required fields"):
        registry.load_modules()


@pytest.mark.parametrize(
    "module_id",
    ["Uppercase", "../escape", "two--hyphens", "-leading"],
)
def test_rejects_invalid_module_id(monkeypatch, tmp_path, module_id):
    packages = use_packages_dir(monkeypatch, tmp_path)

    # Keep the manifest path safe; validate the ID stored inside it.
    write_manifest(
        packages,
        "invalid-module",
        valid_manifest(module_id),
    )

    with pytest.raises(ModuleManifestError, match="Invalid module id"):
        registry.load_modules()


def test_rejects_directory_and_id_mismatch(monkeypatch, tmp_path):
    packages = use_packages_dir(monkeypatch, tmp_path)
    write_manifest(packages, "directory-name", valid_manifest("different-name"))

    with pytest.raises(ModuleManifestError, match="directory must match id"):
        registry.load_modules()


def test_rejects_unsupported_module_type(monkeypatch, tmp_path):
    packages = use_packages_dir(monkeypatch, tmp_path)
    data = valid_manifest()
    data["type"] = "arbitrary-code"
    write_manifest(packages, "sample-module", data)

    with pytest.raises(ModuleManifestError, match="Unsupported module type"):
        registry.load_modules()


def test_rejects_unsupported_api_version(monkeypatch, tmp_path):
    packages = use_packages_dir(monkeypatch, tmp_path)
    data = valid_manifest()
    data["api_version"] = "999"
    write_manifest(packages, "sample-module", data)

    with pytest.raises(ModuleManifestError, match="Unsupported API version"):
        registry.load_modules()


def test_rejects_empty_package_directory(monkeypatch, tmp_path):
    use_packages_dir(monkeypatch, tmp_path)

    with pytest.raises(ModuleManifestError, match="No valid module manifests"):
        registry.load_modules()


def test_valid_manifest_is_loaded(monkeypatch, tmp_path):
    packages = use_packages_dir(monkeypatch, tmp_path)
    write_manifest(packages, "sample-module", valid_manifest())

    modules = registry.load_modules()
    assert len(modules) == 1
    assert modules[0]["id"] == "sample-module"
    assert modules[0]["type"] == "health"
