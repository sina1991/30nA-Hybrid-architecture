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
    assert "--pull=never" in command
    assert "--log-driver=none" in command
    assert not any(arg == "--pid=host" for arg in command)
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


def test_docker_launch_fails_closed_when_cli_cannot_start(tmp_path):
    backend = DockerSandboxBackend(
        "registry.example/worker@sha256:" + "a" * 64
    )
    archive = tmp_path / "artifact.zip"
    runner = tmp_path / "runner.py"
    archive.write_bytes(b"zip")
    runner.write_text("# trusted runner", encoding="utf-8")

    with patch(
        "worker_runtime.docker_sandbox.subprocess.Popen",
        side_effect=FileNotFoundError("simulated Docker CLI unavailable"),
    ):
        with pytest.raises(SandboxUnavailable, match="Could not launch sandbox runtime"):
            backend.launch(
                archive,
                runner,
                "worker:run",
                execution_id="docker-unavailable-test",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )



def _backend_with_cidfile(tmp_path):
    backend = DockerSandboxBackend("registry.example/worker@sha256:" + "a" * 64)
    cid_dir = tmp_path / "cid-evidence"
    cid_dir.mkdir(mode=0o700)
    cidfile = cid_dir / "container.cid"
    cidfile.write_text("a" * 64, encoding="ascii")
    proc = Mock()
    proc.pid = 8123
    backend._cidfiles[proc.pid] = (cidfile, cid_dir)
    return backend, proc, cidfile, cid_dir


def test_terminate_confirms_successful_container_removal(tmp_path):
    backend, proc, cidfile, cid_dir = _backend_with_cidfile(tmp_path)
    with patch("worker_runtime.docker_sandbox.subprocess.run", return_value=Mock(returncode=0, stderr="")) as run:
        with patch.object(backend, "_kill_cli"):
            assert backend.terminate(proc) is True
    assert run.call_args.args[0][:3] == ["docker", "rm", "--force"]
    assert backend.cleanup_unconfirmed(proc) is False
    assert backend.cleanup(proc) is True
    assert not cid_dir.exists()


def test_terminate_accepts_explicit_no_such_container_response(tmp_path):
    backend, proc, cidfile, cid_dir = _backend_with_cidfile(tmp_path)
    result = Mock(returncode=1, stderr="Error response from daemon: No such container: " + "a" * 64)
    with patch("worker_runtime.docker_sandbox.subprocess.run", return_value=result):
        with patch.object(backend, "_kill_cli"):
            assert backend.terminate(proc) is True
    assert backend.cleanup(proc) is True
    assert not cid_dir.exists()


@pytest.mark.parametrize("failure", [
    subprocess.TimeoutExpired(["docker", "rm"], 5),
    FileNotFoundError("Docker CLI unavailable"),
    Mock(returncode=1, stderr="Cannot connect to the Docker daemon"),
])
def test_terminate_failure_is_unconfirmed_and_preserves_cid_evidence(tmp_path, failure):
    backend, proc, cidfile, cid_dir = _backend_with_cidfile(tmp_path)
    with patch("worker_runtime.docker_sandbox.subprocess.run", side_effect=failure) if isinstance(failure, BaseException) else patch("worker_runtime.docker_sandbox.subprocess.run", return_value=failure):
        with patch.object(backend, "_kill_cli"):
            assert backend.terminate(proc) is False
    assert backend.cleanup_unconfirmed(proc) is True
    assert backend.cleanup(proc) is False
    assert cidfile.is_file()
    assert cidfile.read_text(encoding="ascii") == "a" * 64
    assert cid_dir.is_dir()


def test_runtime_reports_cleanup_unconfirmed_instead_of_cancelled():
    from worker_runtime.runtime import ExecutionResult, WorkerRuntime

    backend = Mock()
    backend.terminate.return_value = False
    runtime = WorkerRuntime(artifact_provider=Mock(), sandbox_backend=backend)
    proc = Mock()
    proc.pid = 8124
    with runtime._lock:
        runtime._history["cleanup-test"] = ExecutionResult(
            "cleanup-test", "worker", True, "running"
        )
        runtime._active["cleanup-test"] = proc

    assert runtime.cancel("cleanup-test") is False
    result = runtime._finish("cleanup-test", "worker", "cancelled")
    assert result.status == "failed"
    assert result.error.code == "SANDBOX_CLEANUP_UNCONFIRMED"
