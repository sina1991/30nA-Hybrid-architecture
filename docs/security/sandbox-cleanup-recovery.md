# Sandbox cleanup failure and recovery

## Meaning of `SANDBOX_CLEANUP_UNCONFIRMED`

A Docker CLI process exiting or being killed does **not** prove its container stopped. Worker Runtime now marks the execution failed with `SANDBOX_CLEANUP_UNCONFIRMED` if `docker rm --force` times out, the daemon is unavailable, or the removal result is otherwise ambiguous. The Worker Runtime cidfile directory is deliberately retained as recovery evidence. Code Manager's build-test executor likewise fails the build and retains a private reference if removal cannot be confirmed.

Do not report such an execution as successfully cancelled. Do not delete the evidence directory merely because the attached CLI exited.

## Retry from the live Worker Runtime

After the configured Docker daemon is reachable again, call `DockerSandboxBackend.reconcile_unconfirmed_cleanup()`. It retries removal for retained cidfiles and only deletes evidence after Docker confirms removal or explicitly reports that the container does not exist. Its return value separates `confirmed_pids` from `pending_pids`; pending entries require operator attention.

This in-memory registry is lost if the Worker Runtime process restarts, so retained files must still be handled during restart/recovery.

## Manual recovery after daemon restoration

Run as the same account that owns the rootless Docker daemon (on the acceptance host, `ubuntu`). First inspect retained references:

```bash
clear
sudo -iu ubuntu bash <<'EOF'
set -u
export DOCKER_HOST=unix:///run/user/1000/docker.sock

for f in /tmp/worker-runtime-cid-*/container.cid /tmp/code-manager-cleanup-evidence-*/container.ref; do
  [ -f "$f" ] || continue
  printf '\nEvidence: %s\nReference: '
  cat "$f"
done
EOF
```

For each reference, restore daemon connectivity and remove the referenced container by its full ID or name. Code Manager's `container.ref` may contain `name:cm-build-...`; remove the `name:` prefix before passing it to Docker. Example, after manually verifying the selected reference:

```bash
clear
sudo -iu ubuntu bash <<'EOF'
set -euo pipefail
export DOCKER_HOST=unix:///run/user/1000/docker.sock
REF='REPLACE_WITH_VERIFIED_CONTAINER_ID_OR_NAME'
docker rm --force "$REF"
EOF
```

Only remove the corresponding evidence file/directory after a successful `docker rm --force` or after independently verifying through a healthy daemon that the container is absent. If the daemon is unavailable or the command result is ambiguous, retain the evidence and escalate; do not infer success from killing the CLI.

## Host acceptance boundary

These recovery paths do not prove all production security properties. Run daemon-failure fault injection only in isolated CI/staging. Verify secret isolation, network isolation, cancellation/orphan cleanup, and deployed service wiring separately. Rootless Docker may not support every cgroup controller on every host; the target host's reported lack of `cpuset`, `io.weight`, and `io.max` must be documented and resolved or explicitly accepted by the deployment's security owner before production acceptance.
