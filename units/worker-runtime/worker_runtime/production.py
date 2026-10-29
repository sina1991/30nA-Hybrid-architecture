"""Owner-isolated HTTP Runtime factory; requires a preloaded immutable sandbox."""
from contextlib import asynccontextmanager
import hashlib
import json
import os
from pathlib import Path

from worker_manager.http_common import ProcessLock
from .api import create_app as application
from . import CodeManagerArtifactProvider, DockerSandboxBackend, SQLiteExecutionStore, WorkerRuntime


def create_app():
    os.umask(0o077)
    root = Path(os.environ['WORKER_RUNTIME_STATE_ROOT']).resolve()
    root.mkdir(parents=True,exist_ok=True)
    process_lock = ProcessLock(root/'.service.lock')
    credentials = Path(os.environ['WORKER_RUNTIME_CODE_CREDENTIALS'])
    backend = DockerSandboxBackend.from_env()
    def runtime(owner):
        binding=json.loads(credentials.read_text())[owner]
        provider=CodeManagerArtifactProvider(binding['url'],'Bearer '+binding['token'])
        name=hashlib.sha256(owner.encode()).hexdigest()+'.sqlite3'
        return WorkerRuntime(provider,sandbox_backend=backend,
                             execution_store=SQLiteExecutionStore(root/name))
    app=application(os.environ['WORKER_RUNTIME_CREDENTIAL_FILE'],runtime)
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            # Retained cidfiles remain available for operator reconciliation.
            backend.reconcile_unconfirmed_cleanup()
            process_lock.close()
    app.router.lifespan_context=lifespan
    return app
