# WORKER MANAGER

WORKER MANAGER owns worker definitions, manager-side configuration, manager lifecycle and scheduling policy. It does not load or execute worker code.

## Current scope

- Register a worker against an explicit artifact identity (`artifact_id` and `artifact_hash`).
- Keep configuration separate from the immutable worker definition.
- Support `configured`, `enabled` and `disabled` manager lifecycle states.
- Support manual-only scheduling by default, or a positive interval when explicitly configured.
- Reject duplicate worker identifiers and prevent rebinding an existing identifier.
- Submit execution requests through an injected `RuntimeGateway` adapter boundary.

## Runtime boundary

`worker_manager.runtime_gateway` defines:

- `ExecutionRequest`: the worker definition, configuration and input payload passed to the adapter.
- `RuntimeGateway`: a structural interface with `submit(request)`.

The manager only submits requests for registered, enabled workers. It does not execute artifact code. The adapter response is passed through unchanged because the authoritative `contracts/worker/` contract and WORKER RUNTIME implementation are not currently present in this repository.

The included Fake Runtime tests validate the manager-to-adapter boundary only. They do not prove compatibility with a real WORKER RUNTIME.

## Ownership boundaries

- Artifact publication, validation and immutability remain CODE MANAGER responsibilities.
- Runtime operation statuses (`accepted`, `running`, `succeeded`, `failed`, `cancelled`) are distinct from manager lifecycle states.
- Execution isolation, child-worker execution, input/output validation, and result aggregation remain WORKER RUNTIME responsibilities.
- No direct DATA MANAGER database access is implemented.
- The service is in-memory. No durable persistence, real scheduler, HTTP API, or production Runtime adapter is included.
- `contracts/worker/` and `units/worker-runtime/` remain owned by WORKER RUNTIME and are not modified here.

## Tests

From repository root:

```bash
python3 -m unittest discover -s units/worker-manager/tests -v
```
