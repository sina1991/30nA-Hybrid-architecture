"""Docker-backed execution boundary for untrusted Worker artifacts.

Use a dedicated, rootless Docker daemon where possible. This backend is defense-in-depth,
not a claim that containers eliminate kernel/runtime escape risk.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading


class SandboxUnavailable(RuntimeError):
    """Raised when the required sandbox cannot be configured or launched."""


class DockerSandboxBackend:
    """Launch a worker in a resource-limited, network-disabled Docker container.

    The image must be immutable (digest reference) and contain Python plus the
    runtime dependencies needed by worker artifacts. Never point this backend at
    a daemon socket exposed to untrusted users.
    """

    def __init__(self, image, *, docker_binary="docker", memory="256m",
                 cpus="1.0", pids_limit=64, tmpfs_size="64m",
                 user="65532:65532", stop_grace_seconds=1):
        if not isinstance(image, str) or not re.search(r"@sha256:[0-9a-f]{64}$", image):
            raise ValueError("sandbox image must be pinned by sha256 digest")
        if not isinstance(docker_binary, str) or not docker_binary:
            raise ValueError("docker_binary must be nonempty")
        if not isinstance(memory, str) or not re.fullmatch(r"[1-9][0-9]*(m|g)", memory):
            raise ValueError("memory must be a positive value such as 256m or 1g")
        if not isinstance(cpus, str) or not re.fullmatch(r"[1-9][0-9]*(\.[0-9]+)?", cpus):
            raise ValueError("cpus must be a positive decimal string")
        if type(pids_limit) is not int or pids_limit <= 0:
            raise ValueError("pids_limit must be a positive integer")
        if not isinstance(tmpfs_size, str) or not re.fullmatch(r"[1-9][0-9]*(m|g)", tmpfs_size):
            raise ValueError("tmpfs_size must be a positive value such as 64m")
        if not isinstance(user, str) or not re.fullmatch(r"[0-9]+:[0-9]+", user):
            raise ValueError("user must be an explicit numeric UID:GID")
        if type(stop_grace_seconds) is not int or stop_grace_seconds < 0:
            raise ValueError("stop_grace_seconds must be a nonnegative integer")
        self.image = image
        self.docker_binary = docker_binary
        self.memory = memory
        self.cpus = cpus
        self.pids_limit = pids_limit
        self.tmpfs_size = tmpfs_size
        self.user = user
        self.stop_grace_seconds = stop_grace_seconds
        self._cidfiles = {}
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls):
        image = os.environ.get("WORKER_RUNTIME_SANDBOX_IMAGE")
        if not image:
            raise SandboxUnavailable("WORKER_RUNTIME_SANDBOX_IMAGE is required")
        return cls(
            image,
            docker_binary=os.environ.get("WORKER_RUNTIME_DOCKER_BINARY", "docker"),
            memory=os.environ.get("WORKER_RUNTIME_SANDBOX_MEMORY", "256m"),
            cpus=os.environ.get("WORKER_RUNTIME_SANDBOX_CPUS", "1.0"),
            pids_limit=int(os.environ.get("WORKER_RUNTIME_SANDBOX_PIDS", "64")),
            tmpfs_size=os.environ.get("WORKER_RUNTIME_SANDBOX_TMPFS", "64m"),
        )

    def launch(self, archive, runner, entrypoint, *, execution_id, stdin, stdout, stderr):
        cidfile = Path(tempfile.gettempdir()) / (
            "worker-runtime-" + re.sub(r"[^A-Za-z0-9_-]", "_", execution_id) + ".cid"
        )
        try:
            cidfile.unlink(missing_ok=True)
            command = [
                self.docker_binary, "run", "--rm", "--cidfile", str(cidfile),
                "--network=none", "--read-only", "--user", self.user,
                "--memory", self.memory, "--cpus", self.cpus,
                "--pids-limit", str(self.pids_limit),
                "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--ipc=private", "--ulimit", "nofile=64:64", "--ulimit", "core=0",
                "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size={self.tmpfs_size}",
                "--mount", f"type=bind,src={Path(archive).resolve()},dst=/artifact.zip,readonly",
                "--mount", f"type=bind,src={Path(runner).resolve()},dst=/runner.py,readonly",
                self.image, "python", "-I", "/runner.py", "/artifact.zip", entrypoint,
            ]
            proc = subprocess.Popen(command, stdin=stdin, stdout=stdout, stderr=stderr,
                                   start_new_session=True, close_fds=True)
        except (OSError, ValueError) as exc:
            cidfile.unlink(missing_ok=True)
            raise SandboxUnavailable("Could not launch sandbox runtime") from exc
        with self._lock:
            self._cidfiles[proc.pid] = cidfile
        return proc

    def terminate(self, proc):
        with self._lock:
            cidfile = self._cidfiles.get(proc.pid)
        if cidfile is not None:
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
        try:
            if proc.poll() is None:
                if os.name == "posix":
                    os.killpg(proc.pid, 9)
                else:
                    proc.kill()
        except (ProcessLookupError, OSError):
            pass

    def cleanup(self, proc):
        with self._lock:
            cidfile = self._cidfiles.pop(proc.pid, None)
        if cidfile is not None:
            cidfile.unlink(missing_ok=True)
