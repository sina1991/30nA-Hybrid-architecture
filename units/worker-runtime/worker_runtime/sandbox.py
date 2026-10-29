"""Docker-backed execution boundary for untrusted Worker artifacts.

This backend fails closed when Docker or the configured image is unavailable.
The Docker daemon itself must be dedicated/trusted; prefer rootless Docker.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time


class SandboxUnavailable(RuntimeError):
    """Raised when a required sandbox cannot be started safely."""


class DockerSandboxRunner:
    """Run the Worker runner in a constrained, networkless Docker container.

    The image must contain the compatible Python interpreter at /usr/local/bin/python
    and must be pre-pulled. Image references must be pinned by digest in production.
    The host Docker endpoint is a privileged control plane and must not be exposed to
    Worker code. This class never falls back to host subprocess execution.
    """

    def __init__(
        self,
        image: str,
        *,
        docker_binary: str = "docker",
        memory_limit: str = "128m",
        cpu_limit: str = "1.0",
        pids_limit: int = 64,
        tmpfs_size: str = "16m",
        user: str = "65534:65534",
        runner_python: str = "/usr/local/bin/python",
    ):
        if not isinstance(image, str) or not image.strip():
            raise ValueError("A pinned sandbox image is required")
        if not isinstance(pids_limit, int) or isinstance(pids_limit, bool) or pids_limit <= 0:
            raise ValueError("pids_limit must be a positive integer")
        if not all(isinstance(v, str) and v.strip() for v in
                   (docker_binary, memory_limit, cpu_limit, tmpfs_size, user, runner_python)):
            raise ValueError("Sandbox configuration values must be nonempty strings")
        self.image = image
        self.docker_binary = docker_binary
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.pids_limit = pids_limit
        self.tmpfs_size = tmpfs_size
        self.user = user
        self.runner_python = runner_python

    @staticmethod
    def _kill(proc):
        try:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except ProcessLookupError:
            pass

    def run(self, *, source: bytes, runner_path: Path, entrypoint: str,
            payload: bytes, timeout_seconds: float, max_output_bytes: int):
        """Return (returncode, stdout, output_exceeded, timed_out).

        Stdout is drained incrementally and bounded. The Docker CLI process group is
        killed on timeout/output overflow; --rm removes the execution container.
        """
        binary = shutil.which(self.docker_binary)
        if binary is None:
            raise SandboxUnavailable("Docker CLI is unavailable; refusing host execution")
        if timeout_seconds <= 0:
            return -1, b"", False, True

        with tempfile.TemporaryDirectory(prefix="worker-sandbox-") as tmp:
            root = Path(tmp)
            archive = root / "artifact.zip"
            archive.write_bytes(source)
            payload_file = root / "payload.json"
            payload_file.write_bytes(payload)
            # Bind mounts are read-only; stdin is still passed via a pipe for protocol
            # compatibility. payload file exists only to ensure bounded input is staged
            # in the private temp directory and is not mounted into the container.
            del payload_file
            command = [
                binary, "run", "--rm", "--pull=never",
                "--network=none", "--read-only",
                "--memory", self.memory_limit, "--cpus", self.cpu_limit,
                "--pids-limit", str(self.pids_limit),
                "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
                "--user", self.user,
                "--ipc=private", "--pid=private",
                "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size={self.tmpfs_size}",
                "--log-driver=none",
                "--mount", f"type=bind,src={archive},dst=/worker/artifact.zip,readonly",
                "--mount", f"type=bind,src={Path(runner_path).resolve()},dst=/worker/runner.py,readonly",
                self.image, self.runner_python, "-I", "/worker/runner.py",
                "/worker/artifact.zip", entrypoint,
            ]
            try:
                proc = subprocess.Popen(
                    command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, start_new_session=True,
                    close_fds=True,
                )
            except OSError as exc:
                raise SandboxUnavailable("Cannot start Docker sandbox") from exc

            captured = bytearray()
            overflow = threading.Event()

            def drain():
                try:
                    while True:
                        chunk = proc.stdout.read(8192)
                        if not chunk:
                            return
                        room = max_output_bytes + 1 - len(captured)
                        if room > 0:
                            captured.extend(chunk[:room])
                        if len(chunk) > room or len(captured) > max_output_bytes:
                            overflow.set()
                            self._kill(proc)
                except (OSError, ValueError):
                    pass

            reader = threading.Thread(target=drain, name="docker-sandbox-stdout", daemon=True)
            reader.start()
            try:
                try:
                    proc.stdin.write(payload)
                    proc.stdin.close()
                except (BrokenPipeError, OSError, ValueError):
                    pass
                try:
                    proc.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    self._kill(proc)
                    proc.wait()
                    reader.join()
                    return proc.returncode, bytes(captured), overflow.is_set(), True
                reader.join()
                return proc.returncode, bytes(captured), overflow.is_set(), False
            finally:
                if proc.poll() is None:
                    self._kill(proc)
                    proc.wait()
                reader.join(timeout=1)
