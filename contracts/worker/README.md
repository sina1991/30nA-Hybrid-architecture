# Worker execution contract v1.0.0

Request: `ExecutionRequest(definition, configuration, input_payload, execution_id, timeout_seconds, idempotency_key, parent_execution_id, depth)`. Definition contains `worker_id`, `artifact_id`, `artifact_hash` (`sha256:<hex>`), `entrypoint` (`module:function`). Inputs and configuration must be JSON objects.

Gateway `submit(request)` returns `ExecutionResult(execution_id, worker_id, accepted, status, result, error, children)`. `status` uses CORE operation statuses `accepted/running/succeeded/failed/cancelled`; rejection is `accepted=False, status=failed`. Errors contain CORE `code/message/retryable`. Timeout maps to failed/TIMEOUT, explicit cancellation to cancelled/CANCELLED. Lifecycle belongs only to Manager.

Idempotency keys are scoped per runtime instance; duplicate same-key same-request returns cached result, changed request returns IDEMPOTENCY_CONFLICT. Retry without a key is a new execution. Child execution is declarative: a worker returns `{ "children": [{"worker_id": "...", "input": {...}}], "value": ... }`; Runtime executes children sequentially via a registered definition resolver and returns `children` plus the parent `value`. Child failure fails the parent. Maximum depth and child count are bounded. Cancellation/timeout apply to each subprocess; no distributed propagation guarantee.

Artifact provider must implement `fetch(artifact_id) -> bytes` using a public CODE MANAGER API. Until a public authenticated download API is exposed, production integration is blocked. An injected provider is supported for local execution/tests; do not access CODE MANAGER internal storage.

Security: subprocess isolation is NOT a sandbox. Untrusted Python can access the host with the subprocess permissions. Do not deploy with untrusted artifacts. No durable state, cross-process idempotency, scheduler, authenticated network gateway, or hard memory/CPU sandbox is provided.

Stage 4 clarifies cancellation, execution-ID uniqueness, process-local
idempotency, child limits, shared timeout budgets and CODE MANAGER's missing
public artifact download endpoint. See `units/worker-runtime/README.md` for
security constraints and production blockers.
