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

`CodeManagerArtifactProvider` expects an authenticated public
`GET /artifacts/{artifact_id}/content` returning raw ZIP bytes with content type
`application/octet-stream`. The current CODE MANAGER API returns HTTP 501 for
artifact routes. Production end-to-end artifact retrieval is therefore **blocked**
until CODE MANAGER implements and publishes a compatible endpoint. This module
never reaches into CODE MANAGER private storage or registries. The provider used
in local integration tests is an explicit in-memory fixture, not CODE MANAGER.

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
can still exhaust memory by printing indefinitely. Run only trusted artifacts.
