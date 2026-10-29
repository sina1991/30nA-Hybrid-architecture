#!/usr/bin/env python3
"""Opt-in live Docker control-plane fault injection for a disposable staging VM.

This script briefly SIGSTOPs only the current non-root user's rootless dockerd
process. It must never be run on a shared host or against a rootful daemon.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile


ACK_VALUE = "freeze-rootless-dockerd-on-disposable-vm"
DOCKER_BINARY = os.environ.get("WORKER_RUNTIME_DOCKER_BINARY", "docker")


def _run(command, *, timeout=5):
    return subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def _preflight(image):
    if os.geteuid() == 0:
        raise RuntimeError("Refusing to run as root; use the non-root rootless-Docker account.")
    if os.environ.get("SANDBOX_FAULT_INJECTION_ACK") != ACK_VALUE:
        raise RuntimeError(
            "Explicit opt-in required: set SANDBOX_FAULT_INJECTION_ACK="
            + ACK_VALUE
        )
    expected_host = f"unix:///run/user/{os.getuid()}/docker.sock"
    if os.environ.get("DOCKER_HOST") != expected_host:
        raise RuntimeError(f"DOCKER_HOST must be exactly {expected_host}")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise RuntimeError("Pass the exact local immutable image ID: sha256:<64 lowercase hex>")
    info = _run([DOCKER_BINARY, "info", "--format", "{{json .SecurityOptions}}"])
    if info.returncode != 0 or "rootless" not in info.stdout.lower():
        raise RuntimeError("Docker endpoint did not positively identify itself as rootless")
    image_check = _run([DOCKER_BINARY, "image", "inspect", image])
    if image_check.returncode != 0:
        raise RuntimeError("The exact sandbox image ID is not available locally")
    pids = _run(["pgrep", "-u", str(os.getuid()), "-x", "dockerd"])
    if pids.returncode != 0:
        raise RuntimeError("Could not find the current user's dockerd process")
    matches = [int(line) for line in pids.stdout.splitlines() if line.strip().isdigit()]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one dockerd owned by UID {os.getuid()}, found {len(matches)}"
        )
    return matches[0], info.stdout.strip()


def _wait_for_docker():
    last_error = "not yet available"
    for _ in range(30):
        try:
            result = _run([DOCKER_BINARY, "info", "--format", "{{.ServerVersion}}"], timeout=2)
        except subprocess.TimeoutExpired:
            result = None
        if result is not None and result.returncode == 0:
            return result.stdout.strip()
        if result is not None:
            last_error = (result.stderr or result.stdout or "Docker info failed").strip()
        time.sleep(0.25)
    raise RuntimeError(f"Rootless Docker did not recover after SIGCONT: {last_error}")


def _container_running(container_id):
    result = _run(
        [DOCKER_BINARY, "inspect", "--format", "{{.State.Running}}", container_id],
        timeout=3,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def run_fault_injection(image):
    daemon_pid, security_options = _preflight(image)
    repository_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repository_root / "units" / "worker-runtime"))
    from worker_runtime.docker_sandbox import DockerSandboxBackend

    backend = DockerSandboxBackend(image, docker_binary=DOCKER_BINARY)
    proc = None
    cidfile = None
    cid_dir = None
    container_id = None
    frozen = False
    docker_version = None
    try:
        with tempfile.TemporaryDirectory(prefix="sandbox-daemon-fault-") as temp:
            archive_path = Path(temp) / "sleeping-worker.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(
                    "worker.py",
                    "import time\n"
                    "def run(data, config):\n"
                    "    time.sleep(60)\n"
                    "    return {'status': 'finished'}\n",
                )
            runner = repository_root / "units" / "worker-runtime" / "worker_runtime" / "_runner.py"
            proc = backend.launch(
                archive_path,
                runner,
                "worker:run",
                execution_id="fault-" + uuid.uuid4().hex,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            if proc.stdin is None:
                raise RuntimeError("Docker CLI stdin pipe was not created")
            proc.stdin.write(b'{"input":{},"configuration":{}}\n')
            proc.stdin.close()
            cidfile, cid_dir = backend._cidfiles[proc.pid]
            container_id = cidfile.read_text(encoding="ascii").strip()
            if not re.fullmatch(r"[0-9a-f]{12,64}", container_id):
                raise RuntimeError("Docker did not provide a valid container ID")
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not _container_running(container_id):
                time.sleep(0.1)
            if not _container_running(container_id):
                raise RuntimeError("Fault-injection container did not reach running state")

            # Freeze only the rootless daemon process. The container workload
            # should keep running while the control plane cannot confirm removal.
            os.kill(daemon_pid, signal.SIGSTOP)
            frozen = True
            confirmed = backend.terminate(proc)
            if confirmed:
                raise RuntimeError("Cleanup unexpectedly reported success while dockerd was frozen")
            if not backend.cleanup_unconfirmed(proc):
                raise RuntimeError("Backend did not retain the unconfirmed-cleanup state")
            if not cidfile.is_file():
                raise RuntimeError("CID evidence was lost while cleanup was unconfirmed")

            os.kill(daemon_pid, signal.SIGCONT)
            frozen = False
            docker_version = _wait_for_docker()
            if not _container_running(container_id):
                raise RuntimeError(
                    "Container did not remain running across the frozen control plane; "
                    "review this staging host's Docker live-restore behavior"
                )

            reconciliation = backend.reconcile_unconfirmed_cleanup()
            if proc.pid not in reconciliation["confirmed_pids"]:
                raise RuntimeError("Recovery did not confirm cleanup of the retained container")
            if reconciliation["pending_pids"]:
                raise RuntimeError("Recovery left pending cleanup PIDs")
            if backend.cleanup_unconfirmed(proc):
                raise RuntimeError("Unconfirmed-cleanup state was not cleared after recovery")
            if cid_dir.exists():
                raise RuntimeError("CID evidence directory was not removed after confirmed cleanup")
            if _run([DOCKER_BINARY, "inspect", container_id], timeout=3).returncode == 0:
                raise RuntimeError("Container still exists after recovery reconciliation")
            backend._kill_cli(proc)
            proc.wait(timeout=5)

            print(json.dumps({
                "status": "passed",
                "docker_version": docker_version,
                "docker_security_options": security_options,
                "daemon_pid": daemon_pid,
                "container_id": container_id,
                "cleanup_unconfirmed_before_recovery": True,
                "reconciliation_confirmed": True,
                "pending_pids": [],
            }, sort_keys=True))
    finally:
        if frozen:
            try:
                os.kill(daemon_pid, signal.SIGCONT)
                _wait_for_docker()
            except (OSError, RuntimeError):
                print(
                    f"MANUAL RECOVERY REQUIRED: send SIGCONT to rootless dockerd PID {daemon_pid}",
                    file=sys.stderr,
                )
        # Best-effort cleanup if the test failed before reconciliation completed.
        if proc is not None and proc.pid in backend._cidfiles:
            try:
                if not backend.terminate(proc):
                    _wait_for_docker()
                    backend.reconcile_unconfirmed_cleanup()
                backend.cleanup(proc)
            except Exception as exc:
                print(
                    f"MANUAL RECOVERY REQUIRED: inspect retained CID evidence for PID "
                    f"{proc.pid}: {exc}",
                    file=sys.stderr,
                )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="exact local immutable sandbox image ID (sha256:<64 hex>)")
    args = parser.parse_args()
    try:
        run_fault_injection(args.image)
    except Exception as exc:
        print(f"FAULT-INJECTION FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
