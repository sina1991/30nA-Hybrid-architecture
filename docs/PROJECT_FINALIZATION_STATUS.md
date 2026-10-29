# Project finalization status

Last updated: 2026-10-29

Repository: [sina1991/30nA-Hybrid-architecture](https://github.com/sina1991/30nA-Hybrid-architecture)

Related pull requests:
- [PR #29 — Worker Runtime Docker sandbox](https://github.com/sina1991/30nA-Hybrid-architecture/pull/29)
- [PR #30 — Build Pipeline / Publication Gate](https://github.com/sina1991/30nA-Hybrid-architecture/pull/30)

## Acceptance status

**Local host test suite: PASS. Production sandbox acceptance: NOT YET COMPLETE.**

On an Ubuntu 24.04.5 LTS host, using Python 3.12.3 and pytest 9.2.0, the CI-equivalent suite was run from an isolated worktree at commit `29187ba2c2f5c0a1f917cfa05c70e87caf7c0d87` (PR #30 branch). Data Manager was started locally on `127.0.0.1:8080` with a disposable SQLite database under `/tmp`. The runner exited with code 0 and shut down; the port was no longer listening afterwards.

Final result:

- **207 passed**
- **9 skipped**
- **65 subtests passed**
- **1 warning**
- **4.43 seconds**
- **Exit code: 0**

The skipped tests include real-Docker checks for container identity and read-only root filesystem, vendored wheel execution, CPU quota, cancellation/cleanup, PID limits, and memory-cgroup enforcement. Docker was not installed/available on this host, so these results establish a successful non-Docker test run only; they do **not** establish production-host sandbox acceptance. The warning should be reviewed before release.

An earlier focused Build Pipeline test run on this branch reported **10 passed, 2 skipped**; the skipped cases required a configured CI Docker build image.

## Completed

- [x] PR #29 Worker Runtime sandbox implementation is available for review.
- [x] PR #30 Build Pipeline / Publication Gate implementation is available for review.
- [x] Focused Build Pipeline tests run: 10 passed, 2 skipped (Docker build image not configured).
- [x] Full CI-equivalent local suite run in an isolated worktree: 207 passed, 9 skipped, 65 subtests passed, 1 warning; exit code 0.
- [x] Local test runner and Data Manager exited; port 8080 was confirmed free after the run.
- [x] Original working tree was kept separate from the acceptance worktree to avoid overwriting unrelated uncommitted changes.

## Remaining before final approval

- [ ] Review and resolve or explicitly accept the pytest warning.
- [ ] Run `scripts/security/run_sandbox_acceptance.sh sha256:<approved-image-id>` on the actual deployment host or an isolated staging host matching production, with Docker available and the approved immutable image preloaded.
- [ ] Capture and review the Docker server version, security options, cgroup mode, image ID, commit SHA, complete output, and test summary.
- [ ] Obtain passing evidence for the real-Docker security tests currently skipped, including identity, read-only root filesystem, dependency execution, CPU/memory/PID limits, cancellation/cleanup, and network/secret isolation where covered by the acceptance script.
- [ ] Perform daemon-outage/timeout fault injection only in a disposable staging VM or dedicated test daemon. Verify fail-closed behavior, no host-process fallback, and cleanup/recovery after restart; do not disrupt a shared production Docker daemon.
- [ ] Confirm the final CI checks are green on the exact commits intended for release.
- [ ] Review PR #29 and PR #30 together, including their dependency/stacking relationship and any new acceptance evidence.
- [ ] Only after the above gates pass, approve and merge the PRs in the intended dependency order, then perform post-deploy smoke/security checks and record the deployed commit/image identifiers.

## Release decision

**Do not treat the project as production-ready yet and do not merge PR #29 or PR #30 solely on the strength of this local run.** The remaining blocker is real-Docker acceptance and controlled daemon fault-injection evidence on a production-equivalent host, plus review of the warning and final CI status.
