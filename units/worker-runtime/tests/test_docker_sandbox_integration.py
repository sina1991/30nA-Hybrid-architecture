import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

from worker_runtime.docker_sandbox import DockerSandboxBackend


def test_real_docker_container_enforces_identity_and_read_only_root(tmp_path):
    image = os.environ.get("WORKER_RUNTIME_SANDBOX_TEST_IMAGE")
    if not image or not shutil.which("docker"):
        pytest.skip("CI Docker sandbox image is not configured")
    probe = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=5, check=False,
    )
    if probe.returncode != 0:
        pytest.skip("Docker daemon is not available")
    source = b'''import os, socket\ndef run(data, config):\n    readonly = bool(os.statvfs("/").f_flag & os.ST_RDONLY)\n    interfaces = sorted(name for _, name in socket.if_nameindex())\n    def read(path):\n        try:\n            with open(path) as stream: return stream.read().strip()\n        except OSError: return None\n    return {"uid": os.geteuid(), "readonly": readonly, "interfaces": interfaces,\n            "memory_limit": read("/sys/fs/cgroup/memory.max"),\n            "cpu_limit": read("/sys/fs/cgroup/cpu.max"),\n            "pids_limit": read("/sys/fs/cgroup/pids.max")}\n'''
    archive = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("worker.py", source)
    runner = Path(__file__).parents[1] / "worker_runtime" / "_runner.py"
    backend = DockerSandboxBackend(image, startup_timeout=10)
    proc = None
    try:
        proc = backend.launch(
            archive, runner, "worker:run", execution_id="integration-probe",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        stdout, _ = proc.communicate(
            json.dumps({"input": {}, "configuration": {}}).encode("utf-8"),
            timeout=20,
        )
        assert proc.returncode == 0, stdout.decode("utf-8", "replace")
        result = json.loads(stdout)
        assert result["ok"] is True, result
        assert result["result"]["uid"] != 0
        assert result["result"]["readonly"] is True
        assert result["result"]["interfaces"] == ["lo"]
        assert result["result"]["memory_limit"] not in (None, "max")
        assert result["result"]["cpu_limit"] not in (None, "max")
        assert result["result"]["pids_limit"] == "64"
    finally:
        if proc is not None:
            if proc.poll() is None:
                backend.terminate(proc)
                proc.wait(timeout=5)
            backend.cleanup(proc)


def test_real_docker_cancellation_removes_container(tmp_path):
    image = os.environ.get("WORKER_RUNTIME_SANDBOX_TEST_IMAGE")
    if not image or not shutil.which("docker"):
        pytest.skip("CI Docker sandbox image is not configured")
    probe = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        timeout=5, check=False,
    )
    if probe.returncode != 0:
        pytest.skip("Docker daemon is not available")
    source = b'''import time\ndef run(data, config):\n    time.sleep(30)\n'''
    archive = tmp_path / "hang.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("worker.py", source)
    runner = Path(__file__).parents[1] / "worker_runtime" / "_runner.py"
    backend = DockerSandboxBackend(image, startup_timeout=10)
    proc = None
    try:
        proc = backend.launch(
            archive, runner, "worker:run", execution_id="cancel-probe",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        proc.stdin.write(b'{"input":{},"configuration":{}}')
        proc.stdin.close()
        proc.wait(timeout=0.5)
        pytest.fail("sleeping worker unexpectedly exited before cancellation")
    except subprocess.TimeoutExpired:
        assert proc is not None
        with backend._lock:
            paths = backend._cidfiles.get(proc.pid)
        assert paths is not None
        container_id = paths[0].read_text(encoding="ascii").strip()
        backend.terminate(proc)
        proc.wait(timeout=5)
        inspect = subprocess.run(
            ["docker", "inspect", container_id],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
        assert inspect.returncode != 0, "container remained after cancellation"
    finally:
        if proc is not None:
            if proc.poll() is None:
                backend.terminate(proc)
                proc.wait(timeout=5)
            backend.cleanup(proc)
