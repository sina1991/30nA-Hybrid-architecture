"""Local production entrypoint; configuration supplied by service manager."""
import importlib.util
import os
import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server

from .api import create_application
from .blob_storage import BlobStorage
from .internal_data_manager import client_factory
from .secure_gateway import authenticated_wsgi, load_credentials


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        # Avoid logging URL query strings, credentials or request metadata.
        pass


def main():
    unit = Path(__file__).resolve().parents[2] / 'data-manager'
    sys.path.insert(0, str(unit.parent))
    spec = importlib.util.spec_from_file_location(
        'data_manager', unit / '__init__.py',
        submodule_search_locations=[str(unit)])
    package = importlib.util.module_from_spec(spec)
    sys.modules['data_manager'] = package
    spec.loader.exec_module(package)
    from data_manager.api.app import application as data_app

    credential_path = os.environ['CODE_MANAGER_CREDENTIAL_FILE']
    load_credentials(credential_path)
    storage = BlobStorage(os.environ['CODE_MANAGER_BLOB_ROOT'])
    app = create_application(blob_storage=storage,
                             data_manager_client_factory=client_factory(data_app))
    gateway = authenticated_wsgi(app, credential_path)
    with make_server('127.0.0.1', 8099, gateway, handler_class=QuietHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
