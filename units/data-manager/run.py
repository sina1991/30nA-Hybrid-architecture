"""Local WSGI runner for the Data Manager unit."""
import importlib.util
import os
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

UNIT = Path(__file__).resolve().parent
sys.path.insert(0, str(UNIT.parent))

spec = importlib.util.spec_from_file_location(
    "data_manager",
    UNIT / "__init__.py",
    submodule_search_locations=[str(UNIT)],
)
package = importlib.util.module_from_spec(spec)
sys.modules["data_manager"] = package
spec.loader.exec_module(package)

from data_manager.api.app import application  # noqa: E402

host = os.environ.get("DATA_MANAGER_HOST", "127.0.0.1")
port = int(os.environ.get("DATA_MANAGER_PORT", "8080"))

with make_server(host, port, application) as server:
    print(f"Data Manager listening on http://{host}:{port}")
    server.serve_forever()
