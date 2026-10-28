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
  echo "WARNING: daemon does not advertise rootless mode; verify this is a dedicated, appropriately hardened daemon." >&2
fi

export PYTHONPATH="units/code-manager:units/worker-manager:units/worker-runtime:units/consumers/dashboard-core${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export CODE_MANAGER_INTEGRATION=1
export DATA_MANAGER_ALLOW_INSECURE_HEADER=1
export CODE_MANAGER_ALLOW_INSECURE_HEADER=0
export WORKER_RUNTIME_SANDBOX_TEST_IMAGE="$IMAGE"
export CODE_MANAGER_BUILD_SANDBOX_IMAGE="$IMAGE"
export DATA_MANAGER_DB="/tmp/data-manager-host-acceptance-$$.sqlite3"
export CODE_MANAGER_DATA_MANAGER_URL="http://127.0.0.1:8080"

python -m pip install -r requirements-dev.txt
python - <<'PY' >/tmp/data-manager-host-acceptance.log 2>&1 &
import importlib
import importlib.util
import sys
from pathlib import Path
from wsgiref.simple_server import make_server
unit = Path("units/data-manager").resolve()
sys.path.insert(0, str(unit.parent))
spec = importlib.util.spec_from_file_location(
    "data_manager", unit / "__init__.py",
    submodule_search_locations=[str(unit)]
)
package = importlib.util.module_from_spec(spec)
sys.modules["data_manager"] = package
spec.loader.exec_module(package)
app = importlib.import_module("data_manager.api.app")
make_server("127.0.0.1", 8080, app.application).serve_forever()
PY
DATA_MANAGER_PID=$!
cleanup() {
  kill "$DATA_MANAGER_PID" 2>/dev/null || true
  wait "$DATA_MANAGER_PID" 2>/dev/null || true
  rm -f "$DATA_MANAGER_DB" "$DATA_MANAGER_DB-wal" "$DATA_MANAGER_DB-shm"
}
trap cleanup EXIT
for attempt in $(seq 1 20); do
  if curl --fail --silent http://127.0.0.1:8080/health >/dev/null; then break; fi
  sleep 1
done
curl --fail --silent http://127.0.0.1:8080/health >/dev/null || {
  cat /tmp/data-manager-host-acceptance.log >&2
  echo "Loopback DATA MANAGER did not become healthy" >&2
  exit 1
}

python -m pytest -ra --import-mode=importlib \
  contracts/core/tests \
  contracts/code/tests \
  units/data-manager/tests \
  units/code-manager/tests \
  units/worker-manager/tests \
  units/worker-runtime/tests \
  units/consumers/dashboard-core/tests \
  units/consumers/dashboard-core/legacy-tests \
  units/integration/agent08/tests
