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

**NOT A PRODUCTION SANDBOX.** Python subprocess isolation (`-I`) is not a
security boundary. Worker code may access the host filesystem, network, secrets,
processes and resources under the service identity. Deploy only trusted worker
artifacts in a development environment. Production requires a dedicated sandbox
(container/microVM with unprivileged UID, filesystem and network isolation,
CPU/memory/PID limits, no inherited credentials, and audited egress), plus
external scheduling and persistent state. ZIP path/symlink checks, hash checks,
size limits and subprocess timeouts are defense-in-depth, not a substitute.

Captured stdout is now drained by a reader thread and retained only up to
`max_output_bytes + 1`. Crossing the cap triggers process termination and
returns `OUTPUT_LIMIT_EXCEEDED`; this prevents unbounded stdout accumulation in
the parent process. The regression test uses a worker that prints indefinitely.
This is a memory-protection improvement, **not a sandbox**: a worker can still
consume CPU, memory outside stdout, filesystem or network resources. Run only
trusted artifacts until a real sandbox is implemented and independently tested.
