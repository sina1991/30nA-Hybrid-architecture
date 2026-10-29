import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile

from code_manager.blob_storage import BlobStorage
from code_manager.build_pipeline import (
    BuildHistoryStore, BuildPipeline, DockerBuildExecutor, analyze_imports,
    normalize_source_archive, resolve_dependency_policy,
)


def make_source(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, body in files.items():
            archive.writestr(name, body)
    return output.getvalue()


def source_record(data, *, entrypoint="sample.main:run"):
    return {
        "source_bytes": data,
        "source_hash": hashlib.sha256(data).hexdigest(),
        "entrypoint": entrypoint,
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
    }


class BuildPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.blobs = BlobStorage(self.root / "blobs")
        self.history = BuildHistoryStore(self.root / "history.sqlite3")

    def test_normalization_is_deterministic_and_excludes_tests_from_package(self):
        data = make_source({
            "sample/__init__.py": "",
            "sample/main.py": "def run(data):\r\n    return data\r\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": "import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
            "sample/__pycache__/stale.pyc": "ignored",
        })
        first = normalize_source_archive(data, include_tests=False)
        second = normalize_source_archive(data, include_tests=False)
        self.assertEqual(first, second)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            names = archive.namelist()
            self.assertIn("sample/main.py", names)
            self.assertFalse(any("test_" in name or "__pycache__" in name for name in names))
            self.assertEqual(archive.read("sample/main.py"), b"def run(data):\n    return data\n")

    def test_dependency_manifest_blocks_without_installing_from_network(self):
        data = make_source({
            "sample/main.py": "def run(data): return data\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": "import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
            "requirements.txt": "requests==2.32.0\n",
        })
        pipeline = BuildPipeline(self.blobs, history_store=self.history, image="")
        report = pipeline.run(
            owner_id="alice", source_id="demo", source_version="1",
            source=source_record(data),
        )
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["publishable"])
        stages = {item["stage"]: item["status"] for item in report["stages"]}
        self.assertEqual(stages["dependency_check"], "blocked")
        self.assertEqual(stages["test"], "not_run")
        self.assertEqual(stages["package"], "not_run")
        self.assertNotIn("artifact_digest", report)

    def test_missing_test_suite_never_creates_artifact(self):
        data = make_source({
            "sample/__init__.py": "",
            "sample/main.py": "def run(data): return data\n",
        })
        pipeline = BuildPipeline(self.blobs, history_store=self.history, image="")
        report = pipeline.run(
            owner_id="alice", source_id="demo", source_version="1",
            source=source_record(data),
        )
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["publishable"])
        stages = {item["stage"]: item["status"] for item in report["stages"]}
        self.assertEqual(stages["test"], "not_run")
        self.assertEqual(stages["package"], "not_run")
        self.assertEqual(stages["hash"], "not_run")
        self.assertNotIn("artifact_digest", report)

    def test_history_is_owner_scoped_and_survives_store_reopen(self):
        data = make_source({"sample/main.py": "def run(data): return data\n"})
        pipeline = BuildPipeline(self.blobs, history_store=self.history, image="")
        report = pipeline.run(
            owner_id="alice", source_id="demo", source_version="1",
            source=source_record(data),
        )
        reopened = BuildHistoryStore(self.root / "history.sqlite3")
        self.assertEqual(reopened.get("alice", report["build_id"]), report)
        self.assertIsNone(reopened.get("bob", report["build_id"]))
        self.assertEqual(reopened.list("alice")[0]["build_id"], report["build_id"])

    def test_docker_build_executes_tests_and_emits_reproducible_artifact(self):
        image = os.environ.get("CODE_MANAGER_BUILD_SANDBOX_IMAGE")
        if not image or not shutil.which("docker"):
            self.skipTest("CI Docker build image is not configured")
        probe = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
        if probe.returncode != 0:
            self.skipTest("Docker daemon is not available")
        data = make_source({
            "sample/__init__.py": "",
            "sample/main.py": "def run(data): return {'ok': True}\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": (
                "import unittest\nfrom sample.main import run\n"
                "class Smoke(unittest.TestCase):\n"
                " def test_entrypoint(self): self.assertEqual(run({}), {'ok': True})\n"
            ),
        })
        pipeline = BuildPipeline(
            self.blobs, history_store=self.history, image=image, timeout_seconds=30,
        )
        report = pipeline.run(
            owner_id="alice", source_id="smoke", source_version="1",
            source=source_record(data),
        )
        self.assertEqual(report["status"], "succeeded", report["stages"])
        self.assertTrue(report["publishable"])
        stages = {item["stage"]: item["status"] for item in report["stages"]}
        self.assertTrue(all(value == "passed" for value in stages.values()), stages)
        digest = report["artifact_digest"]
        artifact = self.blobs.get_bytes(digest)
        self.assertEqual(hashlib.sha256(artifact).hexdigest(), digest)
        with zipfile.ZipFile(io.BytesIO(artifact)) as archive:
            self.assertIn("sample/main.py", archive.namelist())
            self.assertFalse(any(name.startswith("tests/") for name in archive.namelist()))


    def test_unresolved_external_import_blocks_build(self):
        data = make_source({
            "sample/main.py": "import requests\ndef run(data): return data\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": "import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
        })
        pipeline = BuildPipeline(self.blobs, history_store=self.history, image="")
        report = pipeline.run(
            owner_id="alice", source_id="external", source_version="1",
            source=source_record(data),
        )
        self.assertEqual(report["status"], "blocked")
        stages = {item["stage"]: item["status"] for item in report["stages"]}
        self.assertEqual(stages["dependency_check"], "blocked")
        self.assertEqual(stages["test"], "not_run")
        self.assertNotIn("artifact_digest", report)

    def test_standard_library_shadowing_blocks_build(self):
        data = make_source({
            "os.py": "VALUE = 1\n",
            "sample/main.py": "import os\ndef run(data): return data\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": "import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
        })
        pipeline = BuildPipeline(self.blobs, history_store=self.history, image="")
        report = pipeline.run(
            owner_id="alice", source_id="shadow", source_version="1",
            source=source_record(data),
        )
        self.assertEqual(report["status"], "blocked")
        stages = {item["stage"]: item["status"] for item in report["stages"]}
        self.assertEqual(stages["dependency_check"], "blocked")


    def test_credential_like_files_block_build_before_tests(self):
        data = make_source({
            "sample/main.py": "def run(data): return data\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": "import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
            ".env": "TOKEN=do-not-package\n",
        })
        pipeline = BuildPipeline(self.blobs, history_store=self.history, image="")
        report = pipeline.run(
            owner_id="alice", source_id="secret", source_version="1",
            source=source_record(data),
        )
        self.assertEqual(report["status"], "failed")
        stages = {item["stage"]: item["status"] for item in report["stages"]}
        self.assertEqual(stages["normalize_working_copy"], "failed")
        self.assertEqual(stages["test"], "not_run")
        self.assertNotIn("artifact_digest", report)


    def test_hash_pinned_allowlisted_wheel_is_tested_and_vendored(self):
        image = os.environ.get("CODE_MANAGER_BUILD_SANDBOX_IMAGE")
        if not image or not shutil.which("docker"):
            self.skipTest("CI Docker build image is not configured")
        probe = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
        if probe.returncode != 0:
            self.skipTest("Docker daemon is not available")
        wheelhouse = self.root / "wheelhouse"
        wheelhouse.mkdir()
        wheel_name = "sampledep-1.0.0-py3-none-any.whl"
        wheel_buffer = io.BytesIO()
        with zipfile.ZipFile(wheel_buffer, "w", zipfile.ZIP_DEFLATED) as wheel:
            wheel.writestr("sampledep/__init__.py", "VALUE = 'vendored-wheel'\n")
            wheel.writestr(
                "sampledep-1.0.0.dist-info/METADATA",
                "Metadata-Version: 2.1\nName: sampledep\nVersion: 1.0.0\n\n",
            )
            wheel.writestr(
                "sampledep-1.0.0.dist-info/WHEEL",
                "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            )
            wheel.writestr("sampledep-1.0.0.dist-info/RECORD", "")
        wheel_bytes = wheel_buffer.getvalue()
        (wheelhouse / wheel_name).write_bytes(wheel_bytes)
        wheel_hash = hashlib.sha256(wheel_bytes).hexdigest()
        allowlist = {
            "sampledep": {
                "version": "1.0.0", "sha256": wheel_hash,
                "wheel": wheel_name, "modules": ["sampledep"],
            }
        }
        data = make_source({
            "sample/__init__.py": "",
            "sample/main.py": "import sampledep\ndef run(data): return {'value': sampledep.VALUE}\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": (
                "import unittest\nfrom sample.main import run\n"
                "class Smoke(unittest.TestCase):\n"
                " def test_vendor(self): self.assertEqual(run({}), {'value': 'vendored-wheel'})\n"
            ),
            "requirements.txt": f"sampledep==1.0.0 --hash=sha256:{wheel_hash}\n",
        })
        with patch.dict(os.environ, {
            "CODE_MANAGER_DEPENDENCY_ALLOWLIST": json.dumps(allowlist),
            "CODE_MANAGER_DEPENDENCY_WHEELHOUSE": str(wheelhouse),
        }):
            pipeline = BuildPipeline(
                self.blobs, history_store=self.history, image=image, timeout_seconds=30,
            )
            report = pipeline.run(
                owner_id="alice", source_id="wheel-smoke", source_version="1",
                source=source_record(data),
            )
        self.assertEqual(report["status"], "succeeded", report["stages"])
        self.assertTrue(report["dependency_lock"].startswith("sha256:"))
        artifact = self.blobs.get_bytes(report["artifact_digest"])
        with zipfile.ZipFile(io.BytesIO(artifact)) as packaged:
            names = packaged.namelist()
            self.assertIn("vendor/" + wheel_name, names)
            self.assertIn("vendor/dependencies.json", names)
            lock = json.loads(packaged.read("vendor/dependencies.json"))
            self.assertEqual(lock["wheels"][0]["sha256"], wheel_hash)


    def test_dynamic_import_is_blocked_even_for_standard_library(self):
        data = make_source({
            "sample/main.py": "import importlib\ndef run(data): return importlib.import_module('json').dumps(data)\n",
            "tests/__init__.py": "",
            "tests/test_smoke.py": "import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n",
        })
        pipeline = BuildPipeline(self.blobs, history_store=self.history, image="")
        report = pipeline.run(
            owner_id="alice", source_id="dynamic", source_version="1",
            source=source_record(data),
        )
        self.assertEqual(report["status"], "blocked")
        stages = {item["stage"]: item["status"] for item in report["stages"]}
        self.assertEqual(stages["dependency_check"], "blocked")
        self.assertEqual(stages["test"], "not_run")


    def _make_wheel(self, package, version, module, *, requires=()):
        output = io.BytesIO()
        dist = package.replace("-", "_") + "-" + version + ".dist-info"
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as wheel:
            wheel.writestr(module + "/__init__.py", "VALUE = 1\n")
            metadata = (
                "Metadata-Version: 2.1\n"
                f"Name: {package}\nVersion: {version}\n"
                + "".join(f"Requires-Dist: {name} (=={pin})\n" for name, pin in requires)
                + "\n"
            )
            wheel.writestr(dist + "/METADATA", metadata)
            wheel.writestr(
                dist + "/WHEEL",
                "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
            )
            wheel.writestr(dist + "/RECORD", "")
        return output.getvalue()

    def test_transitive_pure_python_wheels_require_exact_allowlisted_pins(self):
        wheelhouse = self.root / "wheelhouse-transitive"
        wheelhouse.mkdir()
        leaf = self._make_wheel("leafdep", "1.0.0", "leafdep")
        parent = self._make_wheel(
            "parentdep", "2.0.0", "parentdep", requires=(("leafdep", "1.0.0"),)
        )
        (wheelhouse / "leafdep-1.0.0-py3-none-any.whl").write_bytes(leaf)
        (wheelhouse / "parentdep-2.0.0-py3-none-any.whl").write_bytes(parent)
        leaf_hash = hashlib.sha256(leaf).hexdigest()
        parent_hash = hashlib.sha256(parent).hexdigest()
        allowlist = {
            "leafdep": {
                "version": "1.0.0", "sha256": leaf_hash,
                "wheel": "leafdep-1.0.0-py3-none-any.whl", "modules": ["leafdep"],
            },
            "parentdep": {
                "version": "2.0.0", "sha256": parent_hash,
                "wheel": "parentdep-2.0.0-py3-none-any.whl", "modules": ["parentdep"],
            },
        }
        source = make_source({
            "sample/main.py": "import parentdep\ndef run(data): return parentdep.VALUE\n",
            "requirements.txt": (
                f"parentdep==2.0.0 --hash=sha256:{parent_hash}\n"
                f"leafdep==1.0.0 --hash=sha256:{leaf_hash}\n"
            ),
        })
        result = resolve_dependency_policy(
            source, analyze_imports(source), allowlist, str(wheelhouse)
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(
            {(item["package"], item["version"]) for item in result["wheels"]},
            {("parentdep", "2.0.0"), ("leafdep", "1.0.0")},
        )
        self.assertEqual(result["wheels"][1]["requires"], []) if result["wheels"][1]["package"] == "leafdep" else None

    def test_transitive_dependency_missing_from_requirements_fails_closed(self):
        wheelhouse = self.root / "wheelhouse-missing-transitive"
        wheelhouse.mkdir()
        parent = self._make_wheel(
            "parentdep", "2.0.0", "parentdep", requires=(("leafdep", "1.0.0"),)
        )
        (wheelhouse / "parentdep-2.0.0-py3-none-any.whl").write_bytes(parent)
        digest = hashlib.sha256(parent).hexdigest()
        allowlist = {
            "parentdep": {
                "version": "2.0.0", "sha256": digest,
                "wheel": "parentdep-2.0.0-py3-none-any.whl", "modules": ["parentdep"],
            },
        }
        source = make_source({
            "sample/main.py": "import parentdep\ndef run(data): return parentdep.VALUE\n",
            "requirements.txt": f"parentdep==2.0.0 --hash=sha256:{digest}\n",
        })
        result = resolve_dependency_policy(
            source, analyze_imports(source), allowlist, str(wheelhouse)
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("leafdep==1.0.0", result["detail"])


    def test_docker_daemon_failure_fails_build_and_retains_recovery_reference(self):
        class FakeProcess:
            pid = 54321
            stdout = io.BytesIO(b"")
            returncode = None

            def poll(self):
                return self.returncode

            def wait(self, timeout=None):
                if self.returncode is None:
                    self.returncode = 137
                    if timeout != 5:
                        raise subprocess.TimeoutExpired(["docker", "run"], timeout)
                return self.returncode

        old_tempdir = tempfile.tempdir
        tempfile.tempdir = str(self.root)
        self.addCleanup(setattr, tempfile, "tempdir", old_tempdir)
        process = FakeProcess()
        executor = DockerBuildExecutor(
            "registry.example/build@sha256:" + "a" * 64,
            timeout_seconds=1,
        )
        with patch("code_manager.build_pipeline.shutil.which", return_value="docker"), \
             patch("code_manager.build_pipeline.subprocess.Popen", return_value=process), \
             patch("code_manager.build_pipeline.subprocess.run",
                   return_value=Mock(returncode=1, stderr="Cannot connect to the Docker daemon")), \
             patch("code_manager.build_pipeline.os.killpg"):
            result = executor.run_tests(b"archive", "sample.main:run")

        self.assertEqual(result["status"], "failed")
        self.assertIn("could not confirm", result["summary"].lower())
        evidence_dirs = list(self.root.glob("code-manager-cleanup-evidence-*"))
        self.assertEqual(len(evidence_dirs), 1)
        reference = (evidence_dirs[0] / "container.ref").read_text(encoding="ascii")
        self.assertTrue(reference.startswith("name:cm-build-"))


if __name__ == "__main__":
    unittest.main()
