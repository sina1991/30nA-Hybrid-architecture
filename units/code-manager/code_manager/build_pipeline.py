"""Fail-closed, reproducible build pipeline for untrusted source ZIPs.

Tests run in a pinned Docker image with no network and bounded resources.
Optional third-party dependencies are limited to trusted, hash-pinned,
pure-Python wheels from an offline wheelhouse and are vendored into artifacts.
"""
from __future__ import annotations

import ast
from email.parser import Parser
import hashlib
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sqlite3
import stat
import sys
import subprocess
import tempfile
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone

from .build_validation import validate_build_preflight
from .source_archive import inspect_source_archive
from .errors import SourceValidationError


_BUILDER_VERSION = "code-manager-build-v1"
_IMAGE_DIGEST = re.compile(r"[^/@\s]+(?:/[^/@\s]+)*@sha256:[0-9a-f]{64}$")
_IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}$")
_DEPENDENCY_FILES = {
    "requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py",
    "setup.cfg", "pipfile", "pipfile.lock", "poetry.lock", "pdm.lock",
    "uv.lock", "conda.yml", "environment.yml",
}
_TEXT_SUFFIXES = {".py", ".txt", ".md", ".toml", ".ini", ".cfg", ".json", ".yaml", ".yml", ".sh"}
_TEST_NAME = re.compile(r"(^|/)test[^/]*\.py$", re.IGNORECASE)
_SENSITIVE_BASENAMES = {
    ".netrc", ".npmrc", ".pypirc", "credentials", "credentials.json",
    "secrets.json", "id_rsa", "id_ed25519", "id_ecdsa", "authorized_keys",
}


class BuildPipelineError(RuntimeError):
    """Build orchestration failed without creating a publishable artifact."""


def _safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name and not path.is_absolute() and "\\" not in name
                and "\x00" not in name
                and all(part not in ("", ".", "..") for part in path.parts))


def normalize_source_archive(
    source_bytes: bytes, *, include_tests: bool,
    extra_files: dict[str, bytes] | None = None,
) -> bytes:
    """Return a deterministic ZIP without extracting untrusted paths on the host."""
    if not isinstance(source_bytes, bytes):
        raise TypeError("source_bytes must be bytes")
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(source_bytes), "r") as source:
        entries = source.infolist()
        seen = set()
        files = []
        for info in entries:
            name = info.filename.rstrip("/")
            if not _safe_name(name):
                raise SourceValidationError("Unsafe path encountered during normalization")
            if name in seen:
                raise SourceValidationError("Duplicate path encountered during normalization")
            seen.add(name)
            if info.is_dir():
                continue
            parts = PurePosixPath(name).parts
            basename = PurePosixPath(name).name.lower()
            if (any(part.lower() == ".env" or part.lower().startswith(".env.") for part in parts)
                    or basename == ".env" or basename.startswith(".env.")
                    or basename.endswith(".env")
                    or basename.startswith(("secret.", "credentials."))
                    or basename in _SENSITIVE_BASENAMES
                    or basename.endswith((".pem", ".key", ".p12", ".pfx", ".token", ".secret"))
                    or any(part.lower() in {".ssh", ".aws"} for part in parts[:-1])
                    and basename in {"credentials", "config"}):
                raise SourceValidationError("Source archive contains a credential-like file: " + name)
            if any(part in {".git", "__pycache__"} for part in parts) or name.endswith((".pyc", ".pyo")):
                continue
            if not include_tests and (
                any(part.lower() in {"test", "tests"} for part in parts[:-1])
                or PurePosixPath(name).name.lower().startswith("test_")
            ):
                continue
            data = source.read(info)
            if PurePosixPath(name).suffix.lower() in _TEXT_SUFFIXES:
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise SourceValidationError(f"Text file is not UTF-8: {name}") from exc
                data = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            files.append((name, data))
        for extra_name, extra_data in (extra_files or {}).items():
            if not _safe_name(extra_name) or not isinstance(extra_data, bytes):
                raise SourceValidationError("Unsafe or invalid generated package file")
            if extra_name in seen:
                raise SourceValidationError("Generated package file conflicts with source: " + extra_name)
            seen.add(extra_name)
            files.append((extra_name, extra_data))
        if not files:
            raise SourceValidationError("Normalization produced an empty package")
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9, strict_timestamps=True) as normalized:
            for name, data in sorted(files, key=lambda item: item[0]):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.flag_bits = 0
                normalized.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                                    compresslevel=9)
    return output.getvalue()


_TEST_RUNNER = r'''import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import sys
import unittest
import zipfile

class CappedText(io.TextIOBase):
    def __init__(self, limit=32768):
        self.limit = limit
        self.parts = []
        self.size = 0
        self.truncated = False
    def write(self, value):
        value = str(value)
        room = self.limit - self.size
        if room > 0:
            kept = value[:room]
            self.parts.append(kept)
            self.size += len(kept)
        if len(value) > max(room, 0):
            self.truncated = True
        return len(value)
    def getvalue(self):
        return "".join(self.parts) + ("\n[output truncated]" if self.truncated else "")

def count_tests(suite):
    return sum(count_tests(item) if isinstance(item, unittest.TestSuite) else 1 for item in suite)

def main():
    archive_path = Path(sys.argv[1])
    entrypoint = sys.argv[2]
    root = Path("/tmp/build-source")
    root.mkdir(mode=0o700)
    dependency_lock = json.loads(Path("/dependency-lock.json").read_text(encoding="utf-8"))
    wheels = dependency_lock.get("wheels", [])
    if not isinstance(wheels, list) or len(wheels) > 64:
        raise ValueError("invalid dependency lock")
    for item in reversed(wheels):
        filename = item.get("filename") if isinstance(item, dict) else None
        digest = item.get("sha256") if isinstance(item, dict) else None
        if not isinstance(filename, str) or re.fullmatch(r"[A-Za-z0-9_.+-]+-py3-none-any\.whl", filename) is None:
            raise ValueError("invalid vendored wheel name")
        wheel_path = Path("/") / filename
        if not wheel_path.is_file() or hashlib.sha256(wheel_path.read_bytes()).hexdigest() != digest:
            raise ValueError("vendored wheel SHA-256 mismatch")
        sys.path.insert(0, str(wheel_path))
    with zipfile.ZipFile(archive_path) as archive:
        for info in archive.infolist():
            name = info.filename
            target = (root / name).resolve()
            if target != root and root not in target.parents:
                raise ValueError("unsafe path in normalized archive")
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    tests = sorted(p for p in root.rglob("test*.py") if p.is_file())
    if not tests:
        print(json.dumps({"status":"no_tests","tests":0,"failures":0,"summary":"No test*.py files found"}))
        return 10
    sys.path.insert(0, str(root))
    os.chdir(root)
    module_name, separator, function_name = entrypoint.partition(":")
    if not separator:
        raise ValueError("invalid entrypoint")
    module = importlib.import_module(module_name)
    function = getattr(module, function_name, None)
    if not callable(function):
        raise ValueError("entrypoint does not resolve to a callable")
    loader = unittest.TestLoader()
    suite = loader.discover(str(root), pattern="test*.py", top_level_dir=str(root))
    total = count_tests(suite)
    if total == 0:
        print(json.dumps({"status":"no_tests","tests":0,"failures":0,"summary":"No tests discovered"}))
        return 10
    output = CappedText()
    runner = unittest.TextTestRunner(stream=output, verbosity=2)
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        result = runner.run(suite)
    summary = output.getvalue()[-4000:]
    print(json.dumps({"status":"passed" if result.wasSuccessful() else "failed",
                      "tests":total,"failures":len(result.failures)+len(result.errors),
                      "summary":summary}, ensure_ascii=True, separators=(",",":")))
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        print(json.dumps({"status":"failed","tests":0,"failures":1,
                          "summary":type(exc).__name__+": "+str(exc)[:500]}))
        raise SystemExit(1)
'''


def analyze_imports(source_bytes: bytes) -> dict:
    """Conservatively allow only standard-library and archive-local imports."""
    with zipfile.ZipFile(io.BytesIO(source_bytes), "r") as archive:
        names = [info.filename for info in archive.infolist() if not info.is_dir()]
        local_roots = set()
        for name in names:
            if not name.endswith(".py"):
                continue
            path = PurePosixPath(name)
            if path.name == "__init__.py":
                if len(path.parts) > 1:
                    local_roots.add(path.parts[0])
            else:
                local_roots.add(path.parts[0].removesuffix(".py"))
        stdlib = set(getattr(sys, "stdlib_module_names", ())) | set(sys.builtin_module_names)
        shadowed = sorted(local_roots & stdlib)
        external = set()
        for name in names:
            if not name.endswith(".py"):
                continue
            try:
                tree = ast.parse(archive.read(name).decode("utf-8"), filename=name)
            except (UnicodeDecodeError, SyntaxError, ValueError) as exc:
                raise SourceValidationError("Unable to analyze imports in " + name) from exc
            for node in ast.walk(tree):
                module = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".", 1)[0]
                        if root not in stdlib and root not in local_roots:
                            external.add(root)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    root = node.module.split(".", 1)[0]
                    if root not in stdlib and root not in local_roots:
                        external.add(root)
                elif isinstance(node, ast.Call):
                    dynamic_name = None
                    if isinstance(node.func, ast.Name) and node.func.id in {"__import__", "exec", "eval", "compile"}:
                        dynamic_name = node.args[0] if node.args else ast.Constant(value="")
                    elif (isinstance(node.func, ast.Attribute)
                          and node.func.attr in {"import_module", "spec_from_file_location", "run_module", "run_path"}):
                        dynamic_name = node.args[0] if node.args else ast.Constant(value="")
                    if dynamic_name is not None:
                        external.add("<dynamic-import>")
                        if isinstance(dynamic_name, ast.Constant) and isinstance(dynamic_name.value, str):
                            root = dynamic_name.value.lstrip(".").split(".", 1)[0]
                            if root and root not in stdlib and root not in local_roots:
                                external.add(root)
        return {"external": sorted(external), "stdlib_shadowing": shadowed}


def _normalize_distribution(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _wheel_metadata(wheel_path: Path, package: str, version: str) -> list[tuple[str, str]]:
    """Validate a pure-Python wheel and return exact, unconditional dependency pins."""
    if not wheel_path.name.endswith("-py3-none-any.whl"):
        raise SourceValidationError("Only pure-Python py3-none-any wheels are supported")
    if wheel_path.stat().st_size > 8 * 1024 * 1024:
        raise SourceValidationError("Dependency wheel exceeds the 8 MiB limit")
    with zipfile.ZipFile(wheel_path, "r") as wheel:
        infos = wheel.infolist()
        if len(infos) > 1000:
            raise SourceValidationError("Dependency wheel contains too many files")
        expanded = 0
        seen_paths = set()
        metadata_files = []
        wheel_metadata_files = []
        top_level_modules = set()
        for info in infos:
            name = info.filename.rstrip("/")
            if not _safe_name(name):
                raise SourceValidationError("Unsafe path in dependency wheel")
            if name in seen_paths:
                raise SourceValidationError("Duplicate path in dependency wheel")
            seen_paths.add(name)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise SourceValidationError("Symlinks are forbidden in dependency wheels")
            lower = name.lower()
            if (lower.endswith((".so", ".pyd", ".dll", ".dylib", ".pth", ".pyc"))
                    or "__pycache__" in PurePosixPath(name).parts):
                raise SourceValidationError("Native extensions, .pth files and bytecode are forbidden")
            expanded += info.file_size
            if expanded > 16 * 1024 * 1024:
                raise SourceValidationError("Dependency wheel expands beyond 16 MiB")
            if lower.endswith(".dist-info/metadata"):
                metadata_files.append(name)
            if lower.endswith(".dist-info/wheel"):
                wheel_metadata_files.append(name)
            if lower.endswith(".py"):
                top_level_modules.add(PurePosixPath(name).parts[0].removesuffix(".py"))
        if len(metadata_files) != 1 or len(wheel_metadata_files) != 1:
            raise SourceValidationError("Dependency wheel must contain exactly one METADATA and WHEEL file")
        metadata = Parser().parsestr(wheel.read(metadata_files[0]).decode("utf-8"))
        if _normalize_distribution(metadata.get("Name", "")) != package or metadata.get("Version") != version:
            raise SourceValidationError("Wheel metadata does not match the allowlisted package/version")
        wheel_metadata = Parser().parsestr(wheel.read(wheel_metadata_files[0]).decode("utf-8"))
        if (wheel_metadata.get("Root-Is-Purelib", "").lower() != "true"
                or wheel_metadata.get_all("Tag") != ["py3-none-any"]):
            raise SourceValidationError("Wheel WHEEL metadata must declare pure py3-none-any")
        stdlib = set(getattr(sys, "stdlib_module_names", ())) | set(sys.builtin_module_names)
        if top_level_modules & stdlib:
            raise SourceValidationError("Dependency wheel shadows a standard-library module")
        requirements = []
        for raw_requirement in metadata.get_all("Requires-Dist", []):
            requirement = re.fullmatch(
                r"\\s*([A-Za-z0-9][A-Za-z0-9._-]*)\\s*\\(==([A-Za-z0-9][A-Za-z0-9.+!-]*)\\)\\s*",
                raw_requirement,
            )
            if requirement is None:
                raise SourceValidationError(
                    "Requires-Dist must use unconditional exact-version pins without extras or markers"
                )
            dependency_name = _normalize_distribution(requirement.group(1))
            dependency_version = requirement.group(2)
            if dependency_name == package:
                raise SourceValidationError("A wheel cannot depend on itself")
            requirements.append((dependency_name, dependency_version))
        if len({name for name, _ in requirements}) != len(requirements):
            raise SourceValidationError("Wheel contains duplicate Requires-Dist entries")
        return requirements


def resolve_dependency_policy(source_bytes: bytes, import_report: dict, allowlist_config, wheelhouse) -> dict:
    """Resolve only trusted, hash-pinned, pure-Python wheels from an offline wheelhouse."""
    try:
        with zipfile.ZipFile(io.BytesIO(source_bytes), "r") as archive:
            names = [info.filename for info in archive.infolist() if not info.is_dir()]
            manifests = [name for name in names if PurePosixPath(name).name.lower() in _DEPENDENCY_FILES]
            if not manifests:
                if import_report["external"] or import_report["stdlib_shadowing"]:
                    return {"status":"blocked","detail":"External imports require an allowlisted requirements.txt","wheels":[]}
                return {"status":"passed","detail":"Standard-library and archive-local imports only","wheels":[],"lock":{"version":1,"wheels":[]}}
            if manifests != ["requirements.txt"]:
                return {"status":"blocked","detail":"Only a root requirements.txt is supported; other dependency manifests are forbidden","wheels":[]}
            requirements_bytes = archive.read("requirements.txt")
            if len(requirements_bytes) > 65536:
                return {"status":"blocked","detail":"requirements.txt exceeds 64 KiB","wheels":[]}
    except (zipfile.BadZipFile, KeyError, OSError):
        return {"status":"blocked","detail":"Dependency manifest could not be read","wheels":[]}
    if not isinstance(allowlist_config, (str, dict)) or not wheelhouse:
        return {"status":"blocked","detail":"Trusted dependency allowlist and offline wheelhouse are required","wheels":[]}
    try:
        allowlist = json.loads(allowlist_config) if isinstance(allowlist_config, str) else allowlist_config
        if not isinstance(allowlist, dict):
            raise ValueError("allowlist must be an object")
        wheelhouse_path = Path(wheelhouse).expanduser().resolve(strict=True)
        if not wheelhouse_path.is_dir():
            raise ValueError("wheelhouse must be a directory")
        requirements_text = requirements_bytes.decode("utf-8")
    except (ValueError, TypeError, OSError, UnicodeDecodeError) as exc:
        return {"status":"blocked","detail":"Invalid dependency policy configuration: "+str(exc)[:300],"wheels":[]}
    policy_by_name = {_normalize_distribution(name): value for name, value in allowlist.items()}
    wheel_pattern = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9.+!-]*)\s+--hash=sha256:([0-9a-f]{64})$")
    selected = []
    selected_modules = set()
    seen_packages = set()
    total_bytes = 0
    for raw_line in requirements_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = wheel_pattern.fullmatch(line)
        if match is None:
            return {"status":"blocked","detail":"requirements.txt must contain only exact package==version --hash=sha256:<digest> pins","wheels":[]}
        package_name, version, declared_hash = match.groups()
        normalized_name = _normalize_distribution(package_name)
        if normalized_name in seen_packages:
            return {"status":"blocked","detail":"Duplicate package pin: "+package_name,"wheels":[]}
        seen_packages.add(normalized_name)
        policy = policy_by_name.get(normalized_name)
        if not isinstance(policy, dict):
            return {"status":"blocked","detail":"Package is not in the trusted allowlist: "+package_name,"wheels":[]}
        trusted_hash = str(policy.get("sha256", "")).removeprefix("sha256:")
        filename = policy.get("wheel")
        modules = policy.get("modules")
        if (policy.get("version") != version or trusted_hash != declared_hash
                or not isinstance(filename, str) or Path(filename).name != filename
                or not filename.endswith("-py3-none-any.whl")
                or not isinstance(modules, list) or not modules
                or any(not isinstance(module, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", module) for module in modules)):
            return {"status":"blocked","detail":"Dependency pin does not exactly match trusted allowlist: "+package_name,"wheels":[]}
        expected_filename = normalized_name.replace("-", "_") + "-" + version + "-py3-none-any.whl"
        if filename != expected_filename:
            return {"status":"blocked","detail":"Allowlisted wheel filename does not match package/version","wheels":[]}
        wheel_path = (wheelhouse_path / filename).resolve()
        if wheel_path.parent != wheelhouse_path or not wheel_path.is_file():
            return {"status":"blocked","detail":"Allowlisted wheel is missing from the offline wheelhouse: "+filename,"wheels":[]}
        if wheel_path.stat().st_size > 8 * 1024 * 1024:
            return {"status":"blocked","detail":"Dependency wheel exceeds the 8 MiB limit","wheels":[]}
        digest = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
        if digest != trusted_hash:
            return {"status":"blocked","detail":"Offline wheel SHA-256 mismatch: "+filename,"wheels":[]}
        try:
            required_wheels = _wheel_metadata(wheel_path, normalized_name, version)
        except (SourceValidationError, OSError, zipfile.BadZipFile, UnicodeDecodeError) as exc:
            return {"status":"blocked","detail":"Unsafe or invalid dependency wheel: "+str(exc)[:300],"wheels":[]}
        total_bytes += wheel_path.stat().st_size
        if total_bytes > 8 * 1024 * 1024:
            return {"status":"blocked","detail":"Total vendored dependency wheels exceed 8 MiB","wheels":[]}
        if len(selected) >= 64:
            return {"status":"blocked","detail":"More than 64 dependency wheels are not supported","wheels":[]}
        selected.append({"package": normalized_name, "version": version, "filename": filename,
                         "sha256": digest, "path": str(wheel_path),
                         "requires": required_wheels})
        selected_modules.update(modules)
    if not selected:
        return {"status":"blocked","detail":"requirements.txt contains no pinned dependencies","wheels":[]}
    selected_versions = {item["package"]: item["version"] for item in selected}
    missing_dependencies = sorted({
        package + "==" + version
        for item in selected for package, version in item.get("requires", [])
        if selected_versions.get(package) != version
    })
    missing_modules = sorted(set(import_report["external"]) - selected_modules)
    if missing_dependencies:
        return {"status":"blocked","detail":"Required transitive pins are missing or mismatched: "+", ".join(missing_dependencies),"wheels":[]}
    if import_report["stdlib_shadowing"] or missing_modules or "<dynamic-import>" in import_report["external"]:
        return {"status":"blocked","detail":"External/dynamic imports are not covered by the trusted allowlist: "+", ".join(missing_modules or import_report["stdlib_shadowing"] or ["dynamic import"]),"wheels":[]}
    lock = {"version": 1, "wheels": [
        {"package": item["package"], "version": item["version"],
         "filename": item["filename"], "sha256": item["sha256"]}
        for item in selected
    ]}
    return {"status":"passed","detail":"All dependencies match trusted versions/hashes and are pure-Python offline wheels",
            "wheels": selected,"lock":lock}


class BuildHistoryStore:
    """Durable owner-scoped build history stored separately from source metadata."""

    def __init__(self, database_path):
        self.path = Path(database_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path.touch(mode=0o600, exist_ok=True)
        os.chmod(self.path, 0o600)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS build_history (
                    owner_id TEXT NOT NULL,
                    build_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    PRIMARY KEY (owner_id, build_id)
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS build_history_owner_source
                ON build_history(owner_id, source_id, source_version, created_at)
            """)

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def save(self, owner_id: str, report: dict) -> None:
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id must be a trusted identity")
        payload = json.dumps(report, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False)
        with self._connect() as db:
            db.execute(
                """INSERT INTO build_history
                   (owner_id, build_id, source_id, source_version, created_at, status, report_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(owner_id, build_id) DO NOTHING""",
                (owner_id, report["build_id"], report["source_id"],
                 report["source_version"], report["created_at"], report["status"], payload),
            )
            row = db.execute(
                "SELECT report_json FROM build_history WHERE owner_id=? AND build_id=?",
                (owner_id, report["build_id"]),
            ).fetchone()
            if row is None or row["report_json"] != payload:
                raise BuildPipelineError("Build ID conflicts with an existing immutable report")

    def get(self, owner_id: str, build_id: str) -> dict:
        with self._connect() as db:
            row = db.execute(
                "SELECT report_json FROM build_history WHERE owner_id=? AND build_id=?",
                (owner_id, build_id),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["report_json"])

    def list(self, owner_id: str, *, limit: int = 50) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        with self._connect() as db:
            rows = db.execute(
                """SELECT report_json FROM build_history WHERE owner_id=?
                   ORDER BY created_at DESC, build_id DESC LIMIT ?""",
                (owner_id, limit),
            ).fetchall()
        return [json.loads(row["report_json"]) for row in rows]

    def latest_successful(self, owner_id: str, source_id: str, source_version: str) -> dict:
        with self._connect() as db:
            rows = db.execute(
                """SELECT report_json FROM build_history
                   WHERE owner_id=? AND source_id=? AND source_version=? AND status='succeeded'
                   ORDER BY created_at DESC, build_id DESC LIMIT 20""",
                (owner_id, source_id, source_version),
            ).fetchall()
        for row in rows:
            report = json.loads(row["report_json"])
            if report.get("publishable") and report.get("artifact_digest"):
                return report
        return None


class DockerBuildExecutor:
    """Run source tests in an immutable, network-disabled Docker image."""

    def __init__(self, image: str, *, docker_binary: str = "docker",
                 timeout_seconds: int = 120, memory: str = "256m",
                 cpus: str = "1.0", pids_limit: int = 64,
                 tmpfs_size: str = "128m", max_output_bytes: int = 65536):
        if not isinstance(image, str) or not (
            _IMAGE_DIGEST.fullmatch(image) or _IMAGE_ID.fullmatch(image)
        ):
            raise ValueError("Build sandbox image must be pinned by sha256 digest or immutable image ID")
        if not isinstance(docker_binary, str) or not docker_binary:
            raise ValueError("docker_binary must be nonempty")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3600:
            raise ValueError("timeout_seconds must be between 1 and 3600")
        if not isinstance(memory, str) or not re.fullmatch(r"[1-9][0-9]*(m|g)", memory):
            raise ValueError("memory must be a positive m/g value")
        if (not isinstance(cpus, str)
                or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", cpus)
                or float(cpus) <= 0):
            raise ValueError("cpus must be a positive decimal")
        if type(pids_limit) is not int or pids_limit <= 0:
            raise ValueError("pids_limit must be positive")
        if not isinstance(tmpfs_size, str) or not re.fullmatch(r"[1-9][0-9]*(m|g)", tmpfs_size):
            raise ValueError("tmpfs_size must be a positive m/g value")
        self.image = image
        self.docker_binary = docker_binary
        self.timeout_seconds = timeout_seconds
        self.memory = memory
        self.cpus = cpus
        self.pids_limit = pids_limit
        self.tmpfs_size = tmpfs_size
        self.max_output_bytes = max_output_bytes

    def run_tests(self, source_archive: bytes, entrypoint: str, wheel_files=None) -> dict:
        binary = shutil.which(self.docker_binary)
        if binary is None:
            return {"status": "blocked", "tests": 0, "failures": 0,
                    "summary": "Docker CLI is unavailable"}
        with tempfile.TemporaryDirectory(prefix="code-manager-build-") as directory:
            root = Path(directory)
            archive_path = root / "source.zip"
            runner_path = root / "build_test_runner.py"
            dependency_lock_path = root / "dependency-lock.json"
            cidfile = root / "container.cid"
            container_name = "cm-build-" + uuid.uuid4().hex
            wheel_files = [dict(item) for item in (wheel_files or [])]
            for wheel in wheel_files:
                wheel_bytes = Path(wheel["path"]).read_bytes()
                if hashlib.sha256(wheel_bytes).hexdigest() != wheel["sha256"]:
                    return {"status": "failed", "tests": 0, "failures": 1,
                            "summary": "Allowlisted wheel changed before sandbox launch"}
                wheel_copy = root / wheel["filename"]
                wheel_copy.write_bytes(wheel_bytes)
                wheel_copy.chmod(0o644)
                wheel["container_path"] = str(wheel_copy)
            dependency_lock = {"version": 1, "wheels": [
                {"filename": item["filename"], "sha256": item["sha256"]}
                for item in wheel_files
            ]}
            archive_path.write_bytes(source_archive)
            runner_path.write_text(_TEST_RUNNER, encoding="utf-8")
            dependency_lock_path.write_text(
                json.dumps(dependency_lock, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            # The container runs as UID 65532; mounted inputs must be readable.
            # The parent temp directory remains private to the host process.
            archive_path.chmod(0o644)
            runner_path.chmod(0o644)
            dependency_lock_path.chmod(0o644)
            command = [
                binary, "run", "--rm", "--pull=never", "--interactive",
                "--name", container_name, "--cidfile", str(cidfile),
                "--network=none", "--read-only", "--user", "65532:65532",
                "--memory", self.memory, "--memory-swap", self.memory,
                "--cpus", self.cpus, "--pids-limit", str(self.pids_limit),
                "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
                "--ipc=private", "--ulimit", "nofile=64:64",
                "--ulimit", "core=0",
                "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size={self.tmpfs_size}",
                "--log-driver=none",
                "--mount", f"type=bind,src={archive_path},dst=/source.zip,readonly",
                "--mount", f"type=bind,src={runner_path},dst=/runner.py,readonly",
                "--mount", f"type=bind,src={dependency_lock_path},dst=/dependency-lock.json,readonly",
            ]
            for wheel in wheel_files:
                command.extend([
                    "--mount",
                    f"type=bind,src={wheel['container_path']},dst=/{wheel['filename']},readonly",
                ])
            command.extend([
                self.image, "python", "-I", "/runner.py", "/source.zip", entrypoint,
            ])
            try:
                proc = subprocess.Popen(
                    command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, start_new_session=True, close_fds=True,
                )
            except OSError:
                return {"status": "blocked", "tests": 0, "failures": 0,
                        "summary": "Could not start Docker build sandbox"}
            captured = bytearray()
            overflow = threading.Event()

            def stop_container():
                # Kill the container through the Docker control plane before killing
                # the CLI; killing only the CLI can leave a hostile test running.
                try:
                    subprocess.run(
                        [binary, "rm", "--force", container_name],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, timeout=5, check=False,
                    )
                except (OSError, subprocess.SubprocessError):
                    pass
                try:
                    if proc.poll() is None:
                        if os.name == "posix":
                            os.killpg(proc.pid, 9)
                        else:
                            proc.kill()
                except (ProcessLookupError, OSError):
                    pass

            def drain():
                try:
                    while True:
                        chunk = proc.stdout.read(4096)
                        if not chunk:
                            return
                        room = self.max_output_bytes + 1 - len(captured)
                        if room > 0:
                            captured.extend(chunk[:room])
                        if len(chunk) > max(room, 0) or len(captured) > self.max_output_bytes:
                            overflow.set()
                            stop_container()
                except (OSError, ValueError):
                    pass

            reader = threading.Thread(target=drain, name="code-manager-build-output", daemon=True)
            reader.start()
            timed_out = False
            try:
                try:
                    proc.wait(timeout=self.timeout_seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    stop_container()
                    proc.wait(timeout=5)
                reader.join(timeout=2)
            finally:
                if proc.poll() is None:
                    stop_container()
                    proc.wait(timeout=5)
                reader.join(timeout=1)
            if timed_out:
                return {"status": "failed", "tests": 0, "failures": 1,
                        "summary": "Build tests exceeded the wall-clock timeout"}
            if overflow.is_set():
                return {"status": "failed", "tests": 0, "failures": 1,
                        "summary": "Build test output exceeded the configured limit"}
            try:
                result = json.loads(bytes(captured).decode("utf-8").strip().splitlines()[-1])
            except (UnicodeDecodeError, ValueError, IndexError):
                diagnostic = bytes(captured).decode("utf-8", "replace")[-1000:]
                return {"status": "failed", "tests": 0, "failures": 1,
                        "summary": "Build test runner returned an invalid result: " + diagnostic}
            if proc.returncode != 0 and result.get("status") == "passed":
                result["status"] = "failed"
                result["summary"] = "Build test runner exited unsuccessfully"
            result["summary"] = str(result.get("summary", ""))[:4000]
            return result


class BuildPipeline:
    """Orchestrate preflight, normalization, isolated tests, packaging and hashes."""

    def __init__(self, blob_storage, *, history_store=None, image=None,
                 docker_binary="docker", timeout_seconds=120,
                 dependency_allowlist=None, wheelhouse=None):
        self.blob_storage = blob_storage
        self.history = history_store or BuildHistoryStore(blob_storage.root / "build-history.sqlite3")
        self.image = image if image is not None else os.environ.get(
            "CODE_MANAGER_BUILD_SANDBOX_IMAGE",
            os.environ.get("WORKER_RUNTIME_SANDBOX_IMAGE"),
        )
        self.docker_binary = docker_binary
        self.timeout_seconds = timeout_seconds
        self.dependency_allowlist = (
            dependency_allowlist if dependency_allowlist is not None
            else os.environ.get("CODE_MANAGER_DEPENDENCY_ALLOWLIST")
        )
        self.wheelhouse = (
            wheelhouse if wheelhouse is not None
            else os.environ.get("CODE_MANAGER_DEPENDENCY_WHEELHOUSE")
        )

    def run(self, *, owner_id: str, source_id: str, source_version: str, source: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        report = {
            "build_id": uuid.uuid4().hex,
            "source_id": source_id,
            "source_version": source_version,
            "created_at": now,
            "status": "blocked",
            "publishable": False,
            "builder_version": _BUILDER_VERSION,
            "stages": [],
        }

        def record(stage, status, detail, **extra):
            item = {"stage": stage, "status": status, "detail": str(detail)[:1000]}
            item.update(extra)
            report["stages"].append(item)

        try:
            preflight = validate_build_preflight(source)
            raw_source_hash = preflight.get("source_hash")
            report["source_hash"] = (
                "sha256:" + raw_source_hash
                if isinstance(raw_source_hash, str) and re.fullmatch(r"[0-9a-f]{64}", raw_source_hash)
                else None
            )
            report["source_archive_size"] = preflight.get("archive_size")
            # Replace preflight placeholders with actual stage outcomes below.
            report["stages"].extend(
                stage for stage in preflight.get("stages", [])
                if stage.get("stage") not in {"normalize_working_copy", "test", "package", "hash"}
            )
            if preflight.get("status") == "failed":
                for name in ("normalize_working_copy", "test", "reproducibility", "package", "hash"):
                    record(name, "not_run", "A mandatory preflight stage failed")
                report["status"] = "failed"
                return self._save(owner_id, report)
            dependency_stage = next((s for s in report["stages"] if s["stage"] == "dependency_check"), None)
            import_report = analyze_imports(source.get("source_bytes"))
            dependency_result = resolve_dependency_policy(
                source.get("source_bytes"), import_report,
                self.dependency_allowlist, self.wheelhouse,
            )
            if dependency_stage:
                dependency_stage["status"] = dependency_result["status"]
                dependency_stage["detail"] = dependency_result["detail"][:1000]
            if dependency_result["status"] != "passed":
                record("normalize_working_copy", "not_run", "Dependency policy blocked the build")
                record("test", "not_run", "Dependency policy blocked the build")
                record("reproducibility", "not_run", "No package produced")
                record("package", "not_run", "No package produced")
                record("hash", "not_run", "No package produced")
                return self._save(owner_id, report)
            source_bytes = source.get("source_bytes")
            inspection = inspect_source_archive(source_bytes, source.get("entrypoint"))
            try:
                normalized = normalize_source_archive(source_bytes, include_tests=True)
            except SourceValidationError as exc:
                record("normalize_working_copy", "failed", str(exc))
                record("test", "not_run", "Normalization failed")
                record("reproducibility", "not_run", "Normalization failed")
                record("package", "not_run", "Normalization failed")
                record("hash", "not_run", "No final artifact exists")
                report["status"] = "failed"
                return self._save(owner_id, report)
            record("normalize_working_copy", "passed",
                   "Normalized line endings, file permissions, timestamps and ZIP ordering")
            try:
                with zipfile.ZipFile(io.BytesIO(normalized)) as archive:
                    test_files = [name for name in archive.namelist()
                                  if _TEST_NAME.search(name)]
            except zipfile.BadZipFile:
                record("test", "failed", "Normalized source archive is invalid")
                record("package", "not_run", "Tests did not pass")
                record("hash", "not_run", "No final artifact exists")
                report["status"] = "failed"
                return self._save(owner_id, report)
            if not test_files:
                record("test", "not_run", "No test*.py files were found; a successful build requires an executed test suite")
                record("reproducibility", "not_run", "Tests did not pass")
                record("package", "not_run", "Tests did not pass")
                record("hash", "not_run", "No final artifact exists")
                return self._save(owner_id, report)
            if not isinstance(self.image, str) or not self.image:
                record("test", "blocked", "CODE_MANAGER_BUILD_SANDBOX_IMAGE is not configured")
                record("reproducibility", "not_run", "Sandbox tests did not pass")
                record("package", "not_run", "Sandbox tests did not pass")
                record("hash", "not_run", "No final artifact exists")
                return self._save(owner_id, report)
            try:
                executor = DockerBuildExecutor(
                    self.image, docker_binary=self.docker_binary,
                    timeout_seconds=self.timeout_seconds,
                )
            except ValueError as exc:
                record("test", "blocked", str(exc))
                record("reproducibility", "not_run", "Sandbox configuration is invalid")
                record("package", "not_run", "Sandbox configuration is invalid")
                record("hash", "not_run", "No final artifact exists")
                return self._save(owner_id, report)
            test_result = executor.run_tests(
                normalized, source["entrypoint"], dependency_result.get("wheels", [])
            )
            test_status = test_result.get("status")
            record("test", "passed" if test_status == "passed" else
                   "blocked" if test_status == "blocked" else "failed",
                   test_result.get("summary", "No test result"),
                   test_count=int(test_result.get("tests", 0)),
                   failure_count=int(test_result.get("failures", 0)))
            if test_status != "passed":
                record("reproducibility", "not_run", "Tests did not pass")
                record("package", "not_run", "Tests did not pass")
                record("hash", "not_run", "No final artifact exists")
                report["status"] = "failed" if test_status == "failed" else "blocked"
                return self._save(owner_id, report)

            extra_files = {}
            lock_manifest = dependency_result.get("lock", {"version": 1, "wheels": []})
            if dependency_result.get("wheels"):
                for wheel in dependency_result["wheels"]:
                    wheel_bytes = Path(wheel["path"]).read_bytes()
                    if hashlib.sha256(wheel_bytes).hexdigest() != wheel["sha256"]:
                        record("reproducibility", "failed", "Allowlisted wheel changed during the build")
                        record("package", "not_run", "Dependency wheel integrity changed")
                        record("hash", "not_run", "No final artifact exists")
                        report["status"] = "failed"
                        return self._save(owner_id, report)
                    extra_files["vendor/" + wheel["filename"]] = wheel_bytes
                extra_files["vendor/dependencies.json"] = json.dumps(
                    lock_manifest, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            dependency_lock = (
                "stdlib-only" if not dependency_result.get("wheels")
                else "sha256:" + hashlib.sha256(
                    json.dumps(lock_manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
                ).hexdigest()
            )
            artifact_one = normalize_source_archive(
                source_bytes, include_tests=False, extra_files=extra_files
            )
            artifact_two = normalize_source_archive(
                source_bytes, include_tests=False, extra_files=extra_files
            )
            if artifact_one != artifact_two:
                record("reproducibility", "failed", "Repeated deterministic packaging produced different bytes")
                record("package", "not_run", "Reproducibility check failed")
                record("hash", "not_run", "No final artifact exists")
                report["status"] = "failed"
                return self._save(owner_id, report)
            record("reproducibility", "passed", "Two independent normalization passes produced byte-identical output")
            if len(artifact_one) > 16 * 1024 * 1024:
                record("package", "failed", "Built artifact exceeds 16 MiB")
                record("hash", "not_run", "No final artifact exists")
                report["status"] = "failed"
                return self._save(owner_id, report)
            record("package", "passed", "Deterministic built ZIP excludes test files and caches",
                   artifact_size=len(artifact_one))
            digest = self.blob_storage.put_bytes(artifact_one)
            if hashlib.sha256(self.blob_storage.get_bytes(digest)).hexdigest() != digest:
                record("hash", "failed", "Stored build artifact failed SHA-256 verification")
                report["status"] = "failed"
                return self._save(owner_id, report)
            record("hash", "passed", "Final content-addressed artifact digest verified")
            report.update({
                "status": "succeeded",
                "publishable": True,
                "source_hash": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
                "artifact_hash": "sha256:" + digest,
                "artifact_digest": digest,
                "artifact_size": len(artifact_one),
                "artifact_version": digest,
                "build_version": _BUILDER_VERSION,
                "calculation_version": source.get("calculation_version", "1.0.0"),
                "dependency_lock": dependency_lock,
                "input_schema": source["input_schema"],
                "output_schema": source["output_schema"],
                "validation_status": "passed",
                "entrypoint": source["entrypoint"],
                "provenance": {
                    "builder_version": _BUILDER_VERSION,
                    "source_hash": "sha256:" + hashlib.sha256(source_bytes).hexdigest(),
                    "artifact_hash": "sha256:" + digest,
                    "sandbox_image": self.image,
                    "test_count": int(test_result.get("tests", 0)),
                    "dependency_policy": (
                        "stdlib-only" if not dependency_result.get("wheels")
                        else "allowlisted SHA-256-pinned pure-Python wheels from an offline wheelhouse"
                    ),
                    "dependency_lock": dependency_lock,
                    "dependency_lock_hash": (
                        "sha256:" + hashlib.sha256(b"stdlib-only").hexdigest()
                        if dependency_lock == "stdlib-only" else dependency_lock
                    ),
                    "normalized_archive_hash": "sha256:" + hashlib.sha256(normalized).hexdigest(),
                    "archive_entry_count": inspection.entry_count,
                },
            })
            return self._save(owner_id, report)
        except (SourceValidationError, ValueError, TypeError, OSError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
            record("pipeline", "failed", type(exc).__name__ + ": " + str(exc)[:500])
            report["status"] = "failed"
            report["publishable"] = False
            return self._save(owner_id, report)

    def _save(self, owner_id, report):
        if report["status"] != "succeeded":
            report["publishable"] = False
            report.pop("artifact_digest", None)
            report.pop("artifact_hash", None)
            report.pop("artifact_size", None)
            report.pop("artifact_version", None)
            report.pop("build_version", None)
            report.pop("calculation_version", None)
            report.pop("dependency_lock", None)
            report.pop("input_schema", None)
            report.pop("output_schema", None)
            report.pop("validation_status", None)
            report.pop("provenance", None)
        self.history.save(owner_id, report)
        return report
