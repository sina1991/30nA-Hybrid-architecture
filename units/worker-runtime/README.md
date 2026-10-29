# WORKER RUNTIME — Stage 4

The synchronous `WorkerRuntime.submit` returns an `ExecutionResult`. `get` exposes
accepted/running/terminal state and `cancel` terminates the active process group
and propagates a cancellation request to descendant executions. Worker lifecycle
is maintained separately by WORKER MANAGER. Disabling/removing a worker affects
future submissions only; already accepted executions are not implicitly cancelled.

By default, execution history and idempotency are in-memory and are not durable across restarts. An optional `SQLiteExecutionStore` persists JSON-compatible execution snapshots and idempotency mappings:

```python
from worker_runtime import SQLiteExecutionStore, WorkerRuntime

store = SQLiteExecutionStore("./var/runtime.sqlite3")
runtime = WorkerRuntime(artifact_provider, execution_store=store)
```

On startup, persisted `accepted`/`running` records are marked failed with `RUNTIME_RESTARTED` and `retryable=true`; live processes are not resumed. This is durable history, not exactly-once execution or a distributed scheduler. Use one Runtime process per database file. A repeated key while an execution is in flight returns its current snapshot, not a future/promise; poll by execution ID. A retry with a new idempotency key is a new execution. Max concurrent subprocesses, archive size, serialized input size, output size,
child count and depth are configurable. The default serialized input/configuration
limit is 1 MiB; oversized or non-JSON payloads fail as `INVALID_INPUT` before
subprocess launch. Artifact, input and output byte limits, and the concurrency
limit must be positive integers; invalid resource-limit configuration is rejected
at Runtime initialization. Children inherit the parent's remaining
time budget and cancellation. No automatic retry is performed.

## Docker sandbox backend

Worker execution now fails closed by default: `WorkerRuntime(...)` requires an explicitly configured sandbox backend. The Docker backend requires an immutable image reference pinned by SHA-256 digest and launches workers with no network, a read-only root filesystem, numeric unprivileged UID/GID, dropped Linux capabilities, `no-new-privileges`, private IPC, CPU/memory/PID limits, bounded tmpfs, file-descriptor limits, and read-only mounts for the archive and runner. It uses Docker's default seccomp profile, disables persistent container log storage, refuses to pull images at launch, and uses private IPC/PID namespaces; do not set seccomp to unconfined. Images must already be present on the daemon. The host acceptance script requires a rootless Docker daemon by default; a rootful exception requires the explicit `WORKER_RUNTIME_ACCEPT_ROOTFUL_DOCKER=1` override and documented compensating controls. Never expose a Docker socket to untrusted callers.

Build and publish a trusted worker-runtime image with Python installed and compatible with the artifact ABI, then configure:

```python
from worker_runtime import DockerSandboxBackend, WorkerRuntime

sandbox = DockerSandboxBackend.from_env()
runtime = WorkerRuntime(artifact_provider, sandbox_backend=sandbox)
```

Required: `WORKER_RUNTIME_SANDBOX_IMAGE=registry.example/worker-runtime@sha256:<64 lowercase hex characters>`. Optional settings: `WORKER_RUNTIME_DOCKER_BINARY`, `WORKER_RUNTIME_SANDBOX_MEMORY` (default `256m`), `WORKER_RUNTIME_SANDBOX_CPUS` (default `1.0`), `WORKER_RUNTIME_SANDBOX_PIDS` (default `64`), and `WORKER_RUNTIME_SANDBOX_TMPFS` (default `64m`). The backend validates resource settings and fails instead of falling back to host execution. Missing Docker daemon, invalid image or launch errors return a terminal execution error.

This container boundary is a first implementation, not proof of production-grade isolation. Validate cgroup enforcement (especially memory/CPU/PID limits), Docker daemon trust, filesystem permissions, egress isolation, cancellation cleanup, and host-kernel/runtime patching on the actual deployment host. For hostile multi-tenant workloads, evaluate a microVM or hardened runtime such as gVisor/Kata. Never mount credentials or host paths into worker containers.

For tests that intentionally exercise the legacy direct-subprocess path with trusted fixtures only, explicitly pass `require_sandbox=False`. That compatibility mode is unsafe for untrusted artifacts and must not be used in production.

## CODE MANAGER dependency

The current CODE MANAGER API implements
`GET /api/v1/artifacts/{artifact_id}/content`, returning byte-exact content for
an already-published, owner-scoped artifact. It verifies the immutable manifest
and blob and returns a SHA-256 digest. This closes the earlier missing-download
endpoint gap.

**Important distinction:** the current publication registry identifies these
objects as `source_zip`; the download endpoint does not prove that a build
pipeline has validated, tested or packaged the source. The build contract remains
draft, and HTTP publication is intentionally blocked. The WORKER RUNTIME `CodeManagerArtifactProvider` now targets the versioned
`/api/v1/artifacts/{id}/content` route. Unit tests cover URL construction,
authorization header, byte-exact content, content type and size caps. A real-service
integration test with production identity/ownership configuration is still required;
adapter unit tests do not prove that end-to-end path.

## Security limitations

**The default direct-subprocess path is disabled.** Python subprocess isolation (`-I`) is not a security boundary. A Docker sandbox backend is now available and the Runtime fails closed unless a backend is explicitly configured. The backend adds OS/runtime-enforced network, filesystem, identity and resource restrictions, but it is not yet independently security-tested on the target deployment host. ZIP path/symlink checks, hash checks, size limits and subprocess timeouts are defense-in-depth, not a substitute for deployment validation.

Captured stdout is now drained by a reader thread and retained only up to
`max_output_bytes + 1`. Crossing the cap triggers process termination and
returns `OUTPUT_LIMIT_EXCEEDED`; this prevents unbounded stdout accumulation in
the parent process. The regression test uses a worker that prints indefinitely.
This is a memory-protection improvement, **not a sandbox**: a worker can still
consume CPU, memory outside stdout, filesystem or network resources. Run only trusted artifacts until the Docker backend has passed the real-runtime security and integration acceptance tests in the threat-model document.
