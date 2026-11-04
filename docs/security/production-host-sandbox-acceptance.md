# Production-host sandbox acceptance

Run this on the actual deployment host or an isolated staging host with the same kernel, Docker version, cgroup mode, security policy, and image as production. CI success alone is not production acceptance.

## Run

1. Install the repository's test dependencies in a trusted environment.
2. Preload the approved immutable sandbox image; do not let the acceptance run pull images.
3. Run `bash scripts/security/run_sandbox_acceptance.sh sha256:<image-id>`.
4. Archive the complete command output, Docker server version/security options, image ID, commit SHA, and test summary as release evidence.
5. Repeat after changes to the kernel, Docker/containerd, cgroup configuration, seccomp/AppArmor/SELinux policy, image, or sandbox launch flags.

The script runs the Worker Runtime and CODE MANAGER unit/contract/integration suites, including real-Docker tests for host-secret visibility, root filesystem writes, network egress, UID, cgroup limits, fork storm, cancellation, and vendored dependency execution. It does not alter Docker daemon state.

## Daemon-fault injection

Do **not** stop or restart a shared production Docker daemon as part of this script. Validate daemon outage/timeout behavior in an isolated disposable staging VM or dedicated test daemon: run the same suite with the Docker socket unavailable and during controlled daemon termination, verify all executions fail closed, verify no host-process fallback occurs, and verify cleanup/recovery after daemon restart. Capture evidence separately.

## Release gate

Production approval requires all tests to pass on the target host and a reviewed fault-injection record. Use a dedicated, preferably rootless daemon; never expose the Docker socket, host credentials, or writable host directories to submitted code. Native dependency wheels remain unsupported. Transitive pure-Python dependencies require exact unconditional version pins in wheel metadata and root requirements, plus matching allowlist and offline wheelhouse entries.
