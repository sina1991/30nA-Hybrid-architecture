import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from code_manager.blob_storage import BlobStorage
from code_manager.build_pipeline import (
    BuildHistoryStore, BuildPipeline, normalize_source_archive,
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


if __name__ == "__main__":
    unittest.main()
