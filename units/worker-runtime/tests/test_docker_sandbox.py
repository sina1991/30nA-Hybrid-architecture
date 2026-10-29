import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from worker_runtime.docker_sandbox import DockerSandboxBackend, SandboxUnavailable


def test_requires_digest_pinned_image():
    with pytest.raises(ValueError, match="pinned by sha256 digest"):
        DockerSandboxBackend("python:3.11")


@pytest.mark.parametrize("kwargs", [
    {"memory": "0m"},
    {"cpus": "0"},
    {"pids_limit": 0},
    {"tmpfs_size": "64"},
    {"user": "root"},
])
def test_rejects_unsafe_or_invalid_limits(kwargs):
    with pytest.raises(ValueError):
        DockerSandboxBackend("registry.example/worker@sha256:" + "a" * 64, **kwargs)


def test_launch_uses_restrictive_container_options(tmp_path):
    backend = DockerSandboxBackend("registry.example/worker@sha256:" + "a" * 64)
    archive = tmp_path / "artifact.zip"
    runner = tmp_path / "runner.py"
    archive.write_bytes(b"zip")
    runner.write_text("# trusted runner", encoding="utf-8")
    fake_proc = Mock()
    fake_proc.pid = 12345

    with patch("worker_runtime.docker_sandbox.subprocess.Popen", return_value=fake_proc) as popen:
        proc = backend.launch(
            archive, runner, "worker:run", execution_id="execution-1",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )

    assert proc is fake_proc
    command = popen.call_args.args[0]
    assert "--network=none" in command
    assert "--read-only" in command
    assert "--cap-drop=ALL" in command
    assert "--security-opt=no-new-privileges:true" in command
    assert not any("seccomp=unconfined" in arg for arg in command)
    assert "--memory" in command and "256m" in command
    assert "--cpus" in command and "1.0" in command
    assert "--pids-limit" in command and "64" in command
    assert "--user" in command and "65532:65532" in command
    assert not any("docker.sock" in str(arg) for arg in command)
    backend.cleanup(fake_proc)


def test_from_env_fails_closed_without_image(monkeypatch):
    monkeypatch.delenv("WORKER_RUNTIME_SANDBOX_IMAGE", raising=False)
    with pytest.raises(SandboxUnavailable, match="is required"):
        DockerSandboxBackend.from_env()


def test_runtime_fails_closed_without_backend():
    import hashlib
    from types import SimpleNamespace
    from worker_runtime.runtime import WorkerRuntime

    stream = __import__("io").BytesIO()
    with __import__("zipfile").ZipFile(stream, "w") as zf:
        zf.writestr("worker.py", "def run(data, config): return {'ok': True}")
    artifact = stream.getvalue()

    class Provider:
        def fetch(self, artifact_id):
            return artifact

    request = SimpleNamespace(
        execution_id="fail-closed-test",
        definition=SimpleNamespace(
            worker_id="trusted-test-worker",
            artifact_id="test-artifact",
            artifact_hash="sha256:" + hashlib.sha256(artifact).hexdigest(),
            entrypoint="worker:run",
        ),
        configuration={},
        input_payload={},
        depth=0,
        timeout_seconds=2,
        idempotency_key=None,
    )
    result = WorkerRuntime(Provider()).submit(request)
    assert result.status == "failed"
    assert result.error.code == "SANDBOX_UNAVAILABLE"
