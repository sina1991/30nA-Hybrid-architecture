"""Explicitly configured Dashboard BFF factory, with end-user bearer identity."""
import os

from public_api import PublicAPI
from .app import create_app as application


def create_app():
    destinations = {name: os.environ[key] for name,key in (
        ('worker-manager','DASHBOARD_WORKER_MANAGER_URL'),
        ('code-manager','DASHBOARD_CODE_MANAGER_URL')) if os.environ.get(key)}
    def upstreams(owner,token):
        # Use the authenticated user's credential, never a universal service token.
        return {name:PublicAPI(url,token=token) for name,url in destinations.items()}
    return application(credential_path=os.environ['DASHBOARD_CREDENTIAL_FILE'],upstream_factory=upstreams)
