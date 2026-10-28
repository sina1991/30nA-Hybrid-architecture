# WORKER RUNTIME — Stage 4

The synchronous `WorkerRuntime.submit` returns an `ExecutionResult`. `get` exposes
accepted/running/terminal state and `cancel` terminates the active process group
and propagates a cancellation request to descendant executions. Worker lifecycle
is maintained separately by WORKER MANAGER. Disabling/removing a worker affects
future submissions only; already accepted executions are not implicitly cancelled.

The idempotency map is in-memory, process-local and not durable across restarts.
A repeated key while an execution is in flight returns its current snapshot,
not a future/promise; poll by execution ID. A retry with a new idempotency key
is a new execution. Max concurrent subprocesses, archive size, output size,
child count and depth are configurable. Children inherit the parent's remaining
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
draft, and HTTP publication is intentionally blocked. The WORKER RUNTIME
`CodeManagerArtifactProvider` still needs a real-service integration test with
the expected authentication and URL configuration. Existing in-memory provider
fixtures do not prove that end-to-end path.

## Security limitations

**NOT A PRODUCTION SANDBOX.** Python subprocess isolation (`-I`) is not a
security boundary. Worker code may access the host filesystem, network, secrets,
processes and resources under the service identity. Deploy only trusted worker
artifacts in a development environment. Production requires a dedicated sandbox
(container/microVM with unprivileged UID, filesystem and network isolation,
CPU/memory/PID limits, no inherited credentials, and audited egress), plus
external scheduling and persistent state. ZIP path/symlink checks, hash checks,
size limits and subprocess timeouts are defense-in-depth, not a substitute.

Captured stdout is bounded only *after* the subprocess exits: a malicious worker
can still exhaust memory by printing indefinitely. Output limits must be enforced
while streaming, before the data is accumulated in memory. Run only trusted
artifacts until the sandbox and streaming output controls are independently
implemented and tested.
