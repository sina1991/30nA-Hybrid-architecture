#!/usr/bin/env bash
set -euo pipefail

# Run from a checked-out repository on the actual deployment/staging host.
# This intentionally does not stop/restart Docker or mutate daemon settings.
IMAGE="${1:-}"
if [[ ! "$IMAGE" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "Usage: bash $0 sha256:<64-hex immutable image ID>" >&2
  exit 2
fi
command -v docker >/dev/null || { echo "Docker CLI is required" >&2; exit 2; }
command -v python >/dev/null || { echo "Python is required" >&2; exit 2; }
docker info >/dev/null || { echo "Docker daemon unavailable: acceptance must fail closed" >&2; exit 2; }
docker image inspect "$IMAGE" >/dev/null || {
  echo "Pinned sandbox image is not preloaded: $IMAGE" >&2
  exit 2
}

echo "Docker server:"
docker info --format 'version={{.ServerVersion}} security={{json .SecurityOptions}} root={{.DockerRootDir}}'
echo "Pinned image:"
docker image inspect --format 'id={{.Id}} os={{.Os}} arch={{.Architecture}}' "$IMAGE"
if ! docker info --format '{{json .SecurityOptions}}' | grep -qi rootless; then
  if [[ "${WORKER_RUNTIME_ACCEPT_ROOTFUL_DOCKER:-0}" == "1" ]]; then
    echo "WARNING: explicit WORKER_RUNTIME_ACCEPT_ROOTFUL_DOCKER=1 override; rootful daemon risk accepted by operator." >&2
  else
    echo "ERROR: sandbox acceptance requires a rootless Docker daemon. For a reviewed exception only, set WORKER_RUNTIME_ACCEPT_ROOTFUL_DOCKER=1 and document compensating controls." >&2
    exit 2
  fi
fi

# Share the exact suite/startup lifecycle with CI; never probe an unrelated server.
python scripts/testing/run_ci.py --image "$IMAGE" --evidence-dir "${SANDBOX_EVIDENCE_DIR:-tmp/host-acceptance}"
