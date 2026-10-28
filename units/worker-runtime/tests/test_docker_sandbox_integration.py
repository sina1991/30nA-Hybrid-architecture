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
    source = b'''import os\ndef run(data, config):\n    readonly = bool(os.statvfs("/").f_flag & os.ST_RDONLY)\n    return {"uid": os.geteuid(), "readonly": readonly}\n'''
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
    finally:
        if proc is not None:
            if proc.poll() is None:
                backend.terminate(proc)
                proc.wait(timeout=5)
            backend.cleanup(proc)
