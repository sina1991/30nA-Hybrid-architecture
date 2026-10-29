import hashlib
import io
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
    secret_file = tmp_path / "host-secret.txt"
    secret_file.write_text("host-secret-must-not-be-visible", encoding="utf-8")
    source = ('''import os, socket\ndef run(data, config):\n    readonly = bool(os.statvfs("/").f_flag & os.ST_RDONLY)\n    interfaces = sorted(name for _, name in socket.if_nameindex())\n    def read(path):\n        try:\n            with open(path) as stream: return stream.read().strip()\n        except OSError: return None\n    try:\n        with open(%r, encoding="utf-8") as stream: secret_visible = stream.read() == "host-secret-must-not-be-visible"\n    except OSError:\n        secret_visible = False\n    try:\n        with open("/host-write-probe", "w", encoding="utf-8") as stream: stream.write("bad")\n        host_write = True\n    except OSError:\n        host_write = False\n    probe = socket.socket()\n    probe.settimeout(0.5)\n    try:\n        probe.connect(("1.1.1.1", 53))\n        network_blocked = False\n    except OSError:\n        network_blocked = True\n    finally:\n        probe.close()\n    return {"uid": os.geteuid(), "readonly": readonly, "interfaces": interfaces,\n            "host_secret_visible": secret_visible, "host_write": host_write,\n            "network_blocked": network_blocked,\n            "memory_limit": read("/sys/fs/cgroup/memory.max"),\n            "cpu_limit": read("/sys/fs/cgroup/cpu.max"),\n            "pids_limit": read("/sys/fs/cgroup/pids.max")}\n''' % str(secret_file)).encode("utf-8")
    archive = tmp_path / "artifact.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("worker.py", source)
    runner = Path(__file__).parents[1] / "worker_runtime" / "_runner.py"
    backend = DockerSandboxBackend(image, startup_timeout=10)
    proc = None
    try:
        proc = backend.launch(
            archive, runner, "worker:run", execution_id="integration-probe",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(
            json.dumps({"input": {}, "configuration": {}}).encode("utf-8"),
            timeout=20,
        )
        assert proc.returncode == 0, stderr.decode("utf-8", "replace")
        result = json.loads(stdout)
        assert result["ok"] is True, result
        assert result["result"]["uid"] != 0
        assert result["result"]["readonly"] is True
        assert result["result"]["interfaces"] == ["lo"]
        assert result["result"]["memory_limit"] not in (None, "max")
        assert result["result"]["cpu_limit"] not in (None, "max")
        assert result["result"]["pids_limit"] == "64"
        assert result["result"]["host_secret_visible"] is False
        assert result["result"]["host_write"] is False
        assert result["result"]["network_blocked"] is True
    finally:
        if proc is not None:
            if proc.poll() is None:
                backend.terminate(proc)
                proc.wait(timeout=5)
            backend.cleanup(proc)


def test_real_docker_runtime_loads_hash_verified_vendored_wheel(tmp_path):
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
    wheel_name = "sampledep-1.0.0-py3-none-any.whl"
    wheel_buffer = io.BytesIO()
    with zipfile.ZipFile(wheel_buffer, "w", zipfile.ZIP_DEFLATED) as wheel:
        wheel.writestr("sampledep/__init__.py", "VALUE = 'runtime-vendor'\n")
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
    digest = hashlib.sha256(wheel_bytes).hexdigest()
    archive_path = tmp_path / "vendored-runtime.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "worker.py",
            "import sampledep\ndef run(data, config): return {'value': sampledep.VALUE}\n",
        )
        archive.writestr("vendor/" + wheel_name, wheel_bytes)
        archive.writestr(
            "vendor/dependencies.json",
            json.dumps({"version": 1, "wheels": [{"filename": wheel_name, "sha256": digest}]}),
        )
    runner = Path(__file__).parents[1] / "worker_runtime" / "_runner.py"
    backend = DockerSandboxBackend(image, startup_timeout=10)
    proc = None
    try:
        proc = backend.launch(
            archive_path, runner, "worker:run", execution_id="vendored-wheel-probe",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(
            json.dumps({"input": {}, "configuration": {}}).encode("utf-8"),
            timeout=20,
        )
        assert proc.returncode == 0, stderr.decode("utf-8", "replace")
        result = json.loads(stdout)
        assert result["ok"] is True, result
        assert result["result"]["value"] == "runtime-vendor"
    finally:
        if proc is not None:
            if proc.poll() is None:
                backend.terminate(proc)
                proc.wait(timeout=5)
            backend.cleanup(proc)


def test_real_docker_cpu_quota_is_applied(tmp_path):
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
    source = b'''def run(data, config):\n    with open("/sys/fs/cgroup/cpu.max") as stream: return {"cpu_limit": stream.read().strip()}\n'''
    archive = tmp_path / "cpu-quota.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("worker.py", source)
    runner = Path(__file__).parents[1] / "worker_runtime" / "_runner.py"
    backend = DockerSandboxBackend(image, cpus="0.25", startup_timeout=10)
    proc = None
    try:
        proc = backend.launch(
            archive, runner, "worker:run", execution_id="cpu-quota-probe",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(
            json.dumps({"input": {}, "configuration": {}}).encode("utf-8"),
            timeout=20,
        )
        assert proc.returncode == 0, stderr.decode("utf-8", "replace")
        result = json.loads(stdout)
        assert result["ok"] is True, result
        quota, period = map(int, result["result"]["cpu_limit"].split())
        assert 0 < quota / period <= 0.30
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
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            proc.stdin.write(b'{"input":{},"configuration":{}}')
            proc.stdin.close()
        except BrokenPipeError:
            proc.wait(timeout=5)
            raise AssertionError("Docker failed to start: " + proc.stderr.read().decode("utf-8", "replace"))
        returncode = proc.wait(timeout=0.5)
        pytest.fail("sleeping worker unexpectedly exited with " + str(returncode) + ": " + proc.stderr.read().decode("utf-8", "replace"))
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


def test_real_docker_pids_limit_blocks_fork_storm(tmp_path):
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
    source = b'''import subprocess, sys\ndef run(data, config):\n    children = []\n    blocked = False\n    try:\n        for _ in range(128):\n            try:\n                children.append(subprocess.Popen([sys.executable, "-c", "import time; time.sleep(5)"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))\n            except OSError:\n                blocked = True\n                break\n    finally:\n        for child in children:\n            try: child.terminate()\n            except OSError: pass\n        for child in children:\n            try: child.wait(timeout=2)\n            except Exception: pass\n    return {"fork_blocked": blocked, "children": len(children)}\n'''
    archive = tmp_path / "fork-storm.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("worker.py", source)
    runner = Path(__file__).parents[1] / "worker_runtime" / "_runner.py"
    backend = DockerSandboxBackend(image, startup_timeout=10)
    proc = None
    try:
        proc = backend.launch(
            archive, runner, "worker:run", execution_id="fork-storm-probe",
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, stderr = proc.communicate(
            json.dumps({"input": {}, "configuration": {}}).encode("utf-8"),
            timeout=20,
        )
        assert proc.returncode == 0, stderr.decode("utf-8", "replace")
        result = json.loads(stdout)
        assert result["ok"] is True, result
        assert result["result"]["fork_blocked"] is True, result
        assert result["result"]["children"] < 64, result
    finally:
        if proc is not None:
            if proc.poll() is None:
                backend.terminate(proc)
                proc.wait(timeout=5)
            backend.cleanup(proc)


def test_real_docker_memory_cgroup_kills_over_limit_process():
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
    name = "sandbox-memory-probe-" + __import__("uuid").uuid4().hex
    command = [
        "docker", "run", "--pull=never", "--log-driver=none", "--name", name,
        "--network=none", "--read-only", "--user", "65532:65532",
        "--memory=64m", "--memory-swap=64m", "--cpus=1.0", "--pids-limit=16",
        "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=8m",
        image, "python", "-I", "-c",
        "x=bytearray(256*1024*1024); x[::4096]=b'X'*(len(x)//4096); import time; time.sleep(1)",
    ]
    try:
        run = subprocess.run(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=15, check=False,
        )
        assert run.returncode != 0, "memory allocation unexpectedly exceeded the configured cgroup limit"
        inspect = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.OOMKilled}} {{.HostConfig.Memory}} {{.State.ExitCode}}", name],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=5, check=False,
        )
        assert inspect.returncode == 0, "memory-test container disappeared before inspection"
        oom_killed, memory_limit, container_exit = inspect.stdout.decode("ascii", "replace").strip().split()
        assert memory_limit == str(64 * 1024 * 1024), "Docker did not configure the requested memory cgroup limit"
        assert run.returncode != 0, "over-limit memory allocation unexpectedly succeeded"
        assert oom_killed == "true" or (
            container_exit == "1" and "MemoryError" in run.stderr.decode("utf-8", "replace")
        ), "memory limit neither killed the process nor rejected its allocation"
    finally:
        subprocess.run(
            ["docker", "rm", "--force", name], stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False,
        )
