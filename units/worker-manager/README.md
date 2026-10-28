# WORKER MANAGER

WORKER MANAGER owns worker definitions, manager-side configuration, manager lifecycle and scheduling policy. It does not load or execute worker code.

## Current scope

- Register a worker against an explicit artifact identity (\`artifact_id\` and \`artifact_hash\`).
- Keep configuration separate from the immutable worker definition.
- Support \`configured\`, \`enabled\` and \`disabled\` manager lifecycle states.
- Support manual-only scheduling by default, or a positive interval when explicitly configured.
- Reject duplicate worker identifiers and prevent rebinding an existing identifier.
- Submit execution requests through an injected \`RuntimeGateway\` adapter boundary.
- Optionally persist worker definitions, lifecycle, JSON configuration and schedule metadata in SQLite.

## Durable metadata storage

The default \`WorkerManager()\` remains in-memory. To persist worker metadata, create a store and inject it:

\`\`\`python
from worker_manager import SQLiteWorkerStore, WorkerManager

store = SQLiteWorkerStore("./var/workers.sqlite3")
manager = WorkerManager(store=store)
\`\`\`

The parent directory is created when needed. Successful registration, configuration changes, enable/disable operations and removal are written to SQLite before the in-memory snapshot changes. Recreating the manager with the same database restores the registered worker metadata. Configuration must be JSON-compatible; non-finite numbers and arbitrary Python objects are rejected.

This is a durable metadata store, not a distributed coordination service. Operate one manager process per database file; independent processes can have stale in-memory snapshots. Execution history/idempotency, scheduler leases, worker execution results and Runtime state are not persisted by this store. Back up the database and protect it with filesystem permissions appropriate for worker configuration.

## Runtime boundary

\`worker_manager.runtime_gateway\` defines:

- \`ExecutionRequest\`: the worker definition, configuration and input payload passed to the adapter.
- \`RuntimeGateway\`: a structural interface with \`submit(request)\`.

The manager only submits requests for registered, enabled workers. It does not execute artifact code. The adapter response is passed through unchanged because the authoritative \`contracts/worker/\` contract and WORKER RUNTIME implementation are not currently present in this repository.

The included Fake Runtime tests validate the manager-to-adapter boundary only. They do not prove compatibility with a real WORKER RUNTIME.

## Ownership boundaries

- Artifact publication, validation and immutability remain CODE MANAGER responsibilities.
- Runtime operation statuses (\`accepted\`, \`running\`, \`succeeded\`, \`failed\`, \`cancelled\`) are distinct from manager lifecycle states.
- Execution isolation, child-worker execution, input/output validation, and result aggregation remain WORKER RUNTIME responsibilities.
- No direct DATA MANAGER database access is implemented.
- A real scheduler, HTTP API, production Runtime adapter and production sandbox are not included.
- \`contracts/worker/\` and \`units/worker-runtime/\` remain owned by WORKER RUNTIME and are not modified here.

## Tests

From repository root:

\`\`\`bash
python3 -m unittest discover -s units/worker-manager/tests -v
\`\`\`

The SQLite persistence regression suite is \`units/worker-manager/tests/test_sqlite_store.py\`. The repository-wide CI also runs the unit and contract suites.
