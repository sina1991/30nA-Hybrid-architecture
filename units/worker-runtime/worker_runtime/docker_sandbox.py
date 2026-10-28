"""Docker-backed execution boundary for untrusted Worker artifacts.

Use a dedicated rootless Docker daemon where possible. Containers are defense in
depth, not a claim that kernel/runtime escape risk is eliminated.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
import time


class SandboxUnavailable(RuntimeError):
    """Raised when the required sandbox cannot be configured or launched."""


_IMAGE_DIGEST = re.compile(r"[^/@\s]+(?:/[^/@\s]+)*@sha256:[0-9a-f]{64}$")
_IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}$")


class DockerSandboxBackend:
    """Launch a worker in a network-disabled, resource-limited Docker container.

    Production configuration should use a registry reference pinned by digest.
    A local sha256 image ID is accepted for hermetic CI integration tests.
    The daemon must be dedicated to trusted callers and preferably rootless.
    """

    def __init__(self, image, *, docker_binary="docker", memory="256m",
                 cpus="1.0", pids_limit=64, tmpfs_size="64m",
                 user="65532:65532", startup_timeout=5):
        if not isinstance(image, str) or not (
            _IMAGE_DIGEST.fullmatch(image) or _IMAGE_ID.fullmatch(image)
        ):
            raise ValueError("sandbox image must be pinned by sha256 digest or immutable image ID")
        if not isinstance(docker_binary, str) or not docker_binary:
            raise ValueError("docker_binary must be nonempty")
        if not isinstance(memory, str) or not re.fullmatch(r"[1-9][0-9]*(m|g)", memory):
            raise ValueError("memory must be a positive value such as 256m or 1g")
        if (not isinstance(cpus, str)
                or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", cpus)
                or float(cpus) <= 0):
            raise ValueError("cpus must be a positive decimal string")
        if type(pids_limit) is not int or pids_limit <= 0:
            raise ValueError("pids_limit must be a positive integer")
        if not isinstance(tmpfs_size, str) or not re.fullmatch(r"[1-9][0-9]*(m|g)", tmpfs_size):
            raise ValueError("tmpfs_size must be a positive value such as 64m")
        if not isinstance(user, str) or not re.fullmatch(r"[0-9]+:[0-9]+", user):
            raise ValueError("user must be an explicit numeric UID:GID")
        if isinstance(startup_timeout, bool) or not isinstance(startup_timeout, (int, float)) or startup_timeout <= 0:
            raise ValueError("startup_timeout must be positive")
        self.image = image
        self.docker_binary = docker_binary
        self.memory = memory
        self.cpus = cpus
        self.pids_limit = pids_limit
        self.tmpfs_size = tmpfs_size
        self.user = user
        self.startup_timeout = float(startup_timeout)
        self._cidfiles = {}
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls):
        image = os.environ.get("WORKER_RUNTIME_SANDBOX_IMAGE")
        if not image:
            raise SandboxUnavailable("WORKER_RUNTIME_SANDBOX_IMAGE is required")
        try:
            pids_limit = int(os.environ.get("WORKER_RUNTIME_SANDBOX_PIDS", "64"))
        except ValueError as exc:
            raise SandboxUnavailable("WORKER_RUNTIME_SANDBOX_PIDS must be an integer") from exc
        try:
            return cls(
                image,
                docker_binary=os.environ.get("WORKER_RUNTIME_DOCKER_BINARY", "docker"),
                memory=os.environ.get("WORKER_RUNTIME_SANDBOX_MEMORY", "256m"),
                cpus=os.environ.get("WORKER_RUNTIME_SANDBOX_CPUS", "1.0"),
                pids_limit=pids_limit,
                tmpfs_size=os.environ.get("WORKER_RUNTIME_SANDBOX_TMPFS", "64m"),
            )
        except ValueError as exc:
            raise SandboxUnavailable("Invalid Docker sandbox configuration") from exc

    def launch(self, archive, runner, entrypoint, *, execution_id, stdin, stdout, stderr):
        # A private directory prevents other local users from pre-creating the cidfile.
        cid_dir = Path(tempfile.mkdtemp(prefix="worker-runtime-cid-"))
        try:
            cid_dir.chmod(0o700)
            cidfile = cid_dir / "container.cid"
            command = [
                self.docker_binary, "run", "--rm", "--interactive", "--init",
                "--cidfile", str(cidfile),
                "--network=none", "--read-only", "--user", self.user,
                "--memory", self.memory, "--memory-swap", self.memory,
                "--cpus", self.cpus, "--pids-limit", str(self.pids_limit),
                "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
                "--ipc=private", "--ulimit", "nofile=64:64", "--ulimit", "core=0",
                "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size={self.tmpfs_size}",
                "--mount", f"type=bind,src={Path(archive).resolve()},dst=/artifact.zip,readonly",
                "--mount", f"type=bind,src={Path(runner).resolve()},dst=/runner.py,readonly",
                self.image, "python", "-I", "/runner.py", "/artifact.zip", entrypoint,
            ]
            proc = subprocess.Popen(
                command, stdin=stdin, stdout=stdout, stderr=stderr,
                start_new_session=True, close_fds=True,
            )
            # Do not return a live process until cancellation can find its container ID.
            # If Docker exits early, return the exited CLI so Runtime can report failure.
            deadline = time.monotonic() + self.startup_timeout
            while not cidfile.is_file() and proc.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            if proc.poll() is None and not cidfile.is_file():
                self._kill_cli(proc)
                proc.wait(timeout=2)
                raise SandboxUnavailable("Docker did not create the container ID file")
            with self._lock:
                self._cidfiles[proc.pid] = (cidfile, cid_dir)
            return proc
        except SandboxUnavailable:
            shutil.rmtree(cid_dir, ignore_errors=True)
            raise
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            shutil.rmtree(cid_dir, ignore_errors=True)
            raise SandboxUnavailable("Could not launch sandbox runtime") from exc

    @staticmethod
    def _kill_cli(proc):
        try:
            if proc.poll() is None:
                if os.name == "posix":
                    os.killpg(proc.pid, 9)
                else:
                    proc.kill()
        except (ProcessLookupError, OSError):
            pass

    def terminate(self, proc):
        with self._lock:
            paths = self._cidfiles.get(proc.pid)
        if paths is not None:
            cidfile, _ = paths
            try:
                container_id = cidfile.read_text(encoding="ascii").strip()
                if re.fullmatch(r"[0-9a-f]{12,64}", container_id):
                    subprocess.run(
                        [self.docker_binary, "rm", "--force", container_id],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, timeout=5, check=False,
                    )
            except (OSError, subprocess.SubprocessError):
                pass
        self._kill_cli(proc)

    def cleanup(self, proc):
        with self._lock:
            paths = self._cidfiles.pop(proc.pid, None)
        if paths is not None:
            _, cid_dir = paths
            shutil.rmtree(cid_dir, ignore_errors=True)
