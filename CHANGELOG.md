# Changelog

## v0.1.2

- Add an English interactive CLI with refreshed status, numbered menus, navigation path and terminal colors.
- Add independent server monitoring modules and owner-scoped slot execution and saved results.
- Add module search to each Dashboard slot and share saved monitor results with the terminal.
- Limit host monitoring to configured owners and permitted resources; document permissions and terminal commands.
- External API, SSL, weather and BiQuote modules remain future work.

## Unreleased — v0.1.1 Dashboard layout

- Compact account access in the header; keep slots at the top before and after login.
- Show Worker management, execution and history below all slots only after account data loads.
- Keep Worker notices out of the header and add desktop/mobile layout regression using real theme/module fixtures.

## v0.1.0 — 2026-10-30

نسخه MVP مدیریت Worker و اجراها؛ [Release notes](docs/releases/v0.1.0.md). شاخه اصلی نصب و توسعه `main` است.

## Unreleased — Documentation and Runtime correctness

- Preserve active and terminal Runtime history when an invalid request reuses an execution ID; cover SQLite restart and idempotency replay.
- Add explicit private-CA configuration for owner-bound Manager-to-Runtime HTTPS with verification enabled.
- Align CODE/Worker contracts and active READMEs; add a generated standalone AI Agent guide, architecture diagram and real Dashboard screenshot.
- Refresh the Persian manual, source index and offline PDF; check generated Agent references in CI.

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

## Unreleased — Guided Ubuntu installation

- Add a fresh-host Ubuntu 24.04 installer with dedicated Rootless Docker, generated owner-bound credentials, systemd services and Nginx.
- Obtain and renew a public Let’s Encrypt certificate for the supplied Dashboard domain; keep private upstream TLS on loopback.
- Gate completion on Build/publication and real Dashboard BFF success/failure verification; preserve install credentials and SHA when resuming.

## Unreleased — ACME standalone and contact input

- Use Certbot standalone HTTP-01, stopping and restoring installer-owned Nginx even after issuance failure; configure standalone renewal pre/post hooks.
- Normalize outer terminal paste whitespace/direction wrappers while preserving strict address validation; test valid/invalid contacts and real PTY prompts.

## Unreleased — Worker management Dashboard

- Add owner-bound Worker CRUD, configuration/schedule editing, lifecycle confirmation and typed deletion to Dashboard BFF and UI.
- Filter the latest 100 executions by Worker/execution ID and status; keep history after Worker deletion.
- Exercise real HTTPS/Docker CRUD in Chromium, clear private editor fields on logout and reject stale refresh results.
- Add an opt-in Dashboard-only VPS updater with startup rollback, leaving backend units and data unchanged.
