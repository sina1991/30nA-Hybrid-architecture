# Rootless Docker host checkpoint — acceptance record

**Status: ACCEPTED for this checkpoint only**  
**Review date:** 2026-10-29  
**Scope:** Installation and basic smoke test of the dedicated rootless Docker daemon on the target Ubuntu host.

## Verified evidence

The operator-provided host output recorded during this session supports the following:

- Ubuntu 24.04.4 LTS, kernel 6.8.0-117-generic.
- The rootless Docker user service for account `ubuntu` was active.
- The rootless daemon socket was `/run/user/1000/docker.sock`.
- `docker run --rm hello-world` completed successfully against the rootless daemon.
- Docker reported the security options `name=rootless`, `name=seccomp,profile=builtin`, and `name=cgroupns`.
- The rootless setup reported that `io.max` I/O cgroup limits were unsupported on this host. This is a documented limitation, not a passing I/O isolation test.
- The rootful Docker daemon remained installed and active. This checkpoint did not disable or remove it.

## Decision

The **rootless Docker installation and smoke-test checkpoint is accepted** based on the evidence above. This records the completion of that narrow setup stage; it is not a blanket approval of the host, the worker sandbox, or the application deployment.

## Explicitly not verified / not approved by this record

- The full sandbox acceptance suite on this target host, including host-secret/filesystem isolation, network egress denial, PID and memory exhaustion, CPU enforcement, cancellation cleanup, and daemon fault injection.
- Immutable/digest-pinned sandbox image availability and end-to-end Worker Runtime configuration.
- CODE MANAGER production deployment, service account, source deployment permissions, credentials, database initialization safety, and port-8099 checks.
- End-to-end CODE MANAGER → Worker Runtime → Agent08 integration, owner isolation, artifact publication/download integrity, and dashboard health.
- Production readiness of the minimal single-threaded `wsgiref` server.
- Any claim that rootful Docker has been disabled or that the whole server is security-certified.

## Required follow-up before production approval

1. Run and review `scripts/security/run_sandbox_acceptance.sh sha256:<image-id>` on the target host or an equivalent isolated staging host, using the exact immutable image ID.
2. Capture evidence for daemon fault injection and the resource/isolation controls listed in the security acceptance runbook.
3. Complete the CODE MANAGER Stage B provisioning checklist in [README-stage-b.md](../../units/code-manager/deployment/README-stage-b.md) before starting the service.
4. Verify the actual service configuration uses the intended rootless daemon safely; do not assume another service account can access the `ubuntu` user's Docker socket.
5. Keep the overall production security gate **OPEN** until those results have been reviewed.

## Audit wording

Use this wording in status reports:

> Rootless Docker setup checkpoint: **ACCEPTED** (rootless daemon active; hello-world smoke test passed; rootless/seccomp/cgroup namespace options reported). Overall production sandbox and application deployment: **NOT YET APPROVED**; target-host acceptance and integration evidence remain outstanding.

This document records the available evidence and its limits. It does not claim tests were run when no output was captured.
