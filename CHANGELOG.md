# Changelog

## Unreleased — Initial customer demo

- Dashboard executes enabled pre-registered trusted Workers with JSON input, result polling, history and cancellation.
- Uncertain submission retries reuse the original idempotency key; credentials remain in memory and logout clears visible account data.
- Add a deterministic trusted summary Worker, a repeatable Build/publication/setup command and a read-only Terminal review helper.
- Add Chromium regression and real HTTPS/Docker UI integration tests, plus an initial customer handoff guide.

## Release candidate preparation

- Integrate the existing Sandbox, Build/Publication, cleanup and HTTPS E2E PR stack while preserving main's Dashboard updates.
- Add owner-scoped Worker Manager HTTP CRUD/run/history/cancel APIs, SQLite migration, durable queue, interval scheduler, transactional claims and a single-process guard.
- Add authenticated, owner-isolated Runtime HTTP API with owner-bound HTTPS CODE credentials and durable per-owner execution history.
- Connect Dashboard read-only worker/history/source adapters with explicit bearer identity, no redirects, no token persistence and degraded/error responses.
- Exercise real HTTPS authentication, DATA application, source registration, Docker Build, gated publication, exact-byte download, Manager execution, Runtime result and Dashboard reads.
- Fix private-umask Sandbox input readability without changing caller files; preserve startup cleanup evidence; reject numeric root identities and strip inherited Docker proxy defaults.
- Pin dependency hashes, action SHAs and the Sandbox fixture base digest; add dependency/secret scans, Python 3.11/3.12 CI and an owned disposable test-service runner.
- Add Ubuntu/systemd deployment templates, OpenAPI contracts, recovery guidance and an explicit release checklist.

Production release remains gated on reviewed rootless target-host acceptance, live daemon fault-injection, deployed identity/TLS configuration and green CI on the exact release SHA. No final release tag is created by this preparation.
