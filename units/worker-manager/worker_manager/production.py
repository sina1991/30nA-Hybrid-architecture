"""Uvicorn factory: worker_manager.production:create_app --factory --workers 1."""
import json
import os
from pathlib import Path

from .api import create_app as application
from .control_service import ControlService
from .http_gateway import RuntimeHTTPGateway


def create_app():
    os.umask(0o077)
    # Separate owner-bound upstream credentials from incoming credential hashes.
    # File shape: {owner_id: {"url": "https://runtime.example", "token": "..."}}.
    upstream_path = Path(os.environ['WORKER_MANAGER_RUNTIME_CREDENTIALS'])
    def gateway(owner):
        bindings = json.loads(upstream_path.read_text())
        item = bindings[owner]
        return RuntimeHTTPGateway(item['url'], item['token'])
    service = ControlService(os.environ['WORKER_MANAGER_DB'],gateway)
    return application(service,os.environ['WORKER_MANAGER_CREDENTIAL_FILE'])
