#!/usr/bin/env bash
set -euo pipefail

# Run from a checked-out repository on the actual deployment/staging host.
# This intentionally does not stop/restart Docker or mutate daemon settings.
IMAGE="${1:-}"
if [[ ! "$IMAGE" =~ ^sha256:[0-9a-f]{64}$ ]]; then
  echo "Usage: $0 sha256:<64-hex immutable image ID>" >&2
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
  echo "WARNING: daemon does not advertise rootless mode; verify this is a dedicated, appropriately hardened daemon." >&2
fi

export WORKER_RUNTIME_SANDBOX_TEST_IMAGE="$IMAGE"
export CODE_MANAGER_BUILD_SANDBOX_IMAGE="$IMAGE"
python -m pytest -ra units/worker-runtime/tests units/code-manager/tests
