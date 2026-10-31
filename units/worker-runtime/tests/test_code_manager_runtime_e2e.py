"""Real HTTPS CODE MANAGER -> Worker Runtime artifact execution integration test."""
import base64
import hashlib
import importlib
import importlib.util
import sys
import httpx
import io
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import tempfile
import threading
import unittest
import zipfile
from types import SimpleNamespace
from unittest.mock import patch
from wsgiref.simple_server import WSGIRequestHandler, make_server

from code_manager.api import APIError, create_application
from code_manager.build_pipeline import BuildPipeline
from code_manager.internal_data_manager import client_factory
from code_manager.blob_storage import BlobStorage
from code_manager.secure_gateway import authenticated_wsgi
from code_manager.published_artifacts import PublishedArtifactRegistry
from worker_runtime import (
    ArtifactAPIUnavailable,
    CodeManagerArtifactProvider,
    DockerSandboxBackend,
    WorkerRuntime,
    SQLiteExecutionStore,
)


class QuietWSGIRequestHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        # Do not emit request metadata into the test log.
        return


def make_worker_artifact():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "worker.py",
            "def run(data, config):\n"
            "    return {'value': data['value'] + config['increment']}\n",
        )
        archive.writestr('tests/__init__.py', '')
        archive.writestr('tests/test_worker.py',
            'import unittest\nfrom worker import run\nclass Smoke(unittest.TestCase):\n'
            ' def test_run(self): self.assertEqual(run({"value":40},{"increment":2}), {"value":42})\n')
    return output.getvalue()


class CodeManagerRuntimeE2ETests(unittest.TestCase):
    def test_authenticated_https_download_executes_exact_published_artifact(self):
        image = os.environ.get("WORKER_RUNTIME_SANDBOX_TEST_IMAGE")
        if not image:
            if os.environ.get("CI", "").lower() == "true":
                self.fail("CI must provide the immutable Docker test image ID")
            self.skipTest("CI/staging must provide the immutable Docker test image ID")
        if shutil.which("docker") is None:
            if os.environ.get("CI", "").lower() == "true":
                self.fail("CI must provide the Docker CLI")
            self.skipTest("Docker CLI is unavailable")
        probe = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        if probe.returncode != 0:
            if os.environ.get("CI", "").lower() == "true":
                self.fail("CI Docker daemon is unavailable")
            self.skipTest("Docker daemon is unavailable")

        with tempfile.TemporaryDirectory(prefix="code-runtime-e2e-") as directory:
            root = Path(directory)
            cert_path = root / "server-cert.pem"
            key_path = root / "server-key.pem"
            subprocess.run(
                [
                    "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                    "-keyout", str(key_path), "-out", str(cert_path), "-days", "1",
                    "-subj", "/CN=localhost",
                    "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
                    "-addext", "basicConstraints=critical,CA:TRUE",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
                check=True,
            )

            storage = BlobStorage(root / "blobs")
            registry = PublishedArtifactRegistry(storage)
            # The same real DATA MANAGER application and trusted transport used
            # by the production CODE entrypoint, isolated under a distinct package.
            unit = Path(__file__).resolve().parents[2] / 'data-manager'
            spec = importlib.util.spec_from_file_location('e2e_data_manager', unit / '__init__.py',
                submodule_search_locations=[str(unit)])
            package = importlib.util.module_from_spec(spec)
            sys.modules['e2e_data_manager'] = package
            spec.loader.exec_module(package)
            with patch.dict(os.environ, {'DATA_MANAGER_DB': str(root / 'data.sqlite3')}):
                data_app = importlib.import_module('e2e_data_manager.api.app').application
            app = create_application(
                blob_storage=storage,
                data_manager_client_factory=client_factory(data_app),
                build_pipeline=BuildPipeline(storage, image=image),
                published_artifact_registry=registry,
            )
            credential_path = root / 'credentials.json'
            import json
            credential_path.write_text(json.dumps({
                hashlib.sha256((owner + '-integration-token').encode()).hexdigest(): owner
                for owner in ('alice','bob')}))
            app = authenticated_wsgi(app, credential_path)
            server = make_server(
                "127.0.0.1", 0, app, handler_class=QuietWSGIRequestHandler
            )
            server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            server_context.load_cert_chain(str(cert_path), str(key_path))
            server.socket = server_context.wrap_socket(server.socket, server_side=True)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            try:
                base_url = f"https://localhost:{server.server_port}"
                # Trust only the ephemeral test certificate; normal TLS verification
                # remains enabled and production adapter defaults are unchanged.
                with patch.dict(os.environ, {"SSL_CERT_FILE": str(cert_path), "DASHBOARD_MODULE_STATE_DIR": str(root / "dashboard-state")}):
                    source = make_worker_artifact()
                    with httpx.Client(verify=ssl.create_default_context(cafile=str(cert_path)),
                                      trust_env=False, timeout=60) as client:
                        headers = {'Authorization': 'Bearer alice-integration-token'}
                        payload = {'source_id':'sample-worker','source_version':'1.0.0',
                            'source_content_base64':base64.b64encode(source).decode(),
                            'entrypoint':'worker:run','input_schema':{'type':'object'},
                            'output_schema':{'type':'object'}}
                        registered = client.post(base_url+'/api/v1/sources',json=payload,headers=headers)
                        self.assertEqual(registered.status_code,201,registered.text)
                        built = client.post(base_url+'/api/v1/builds',headers=headers,
                            json={'source_id':'sample-worker','source_version':'1.0.0'})
                        self.assertEqual(built.status_code,200,built.text)
                        report = built.json()['payload']['build']
                        self.assertEqual(report['status'],'succeeded',report['stages'])
                        published = client.post(base_url+'/api/v1/artifacts/sample-worker@1.0.0/publish',
                            headers=headers,json={'build_id':report['build_id']})
                        self.assertEqual(published.status_code,201,published.text)
                        self.assertEqual(published.json()['payload']['artifact']['artifact_type'],'built_artifact')
                        downloaded = client.get(base_url+'/api/v1/artifacts/sample-worker@1.0.0/content',headers=headers)
                        self.assertEqual(downloaded.status_code,200)
                        artifact = downloaded.content
                        artifact_hash = 'sha256:'+hashlib.sha256(artifact).hexdigest()
                        self.assertEqual(artifact_hash,report['artifact_hash'])
                        self.assertNotEqual(artifact,source)
                        with zipfile.ZipFile(io.BytesIO(artifact)) as packaged:
                            self.assertFalse(any(name.startswith('tests/') for name in packaged.namelist()))
                    provider = CodeManagerArtifactProvider(
                        base_url, "Bearer alice-integration-token", timeout=5
                    )
                    self.assertEqual(provider.fetch("sample-worker@1.0.0"), artifact)

                    runtime = WorkerRuntime(
                        provider,
                        sandbox_backend=DockerSandboxBackend(image),
                        execution_store=SQLiteExecutionStore(root / "history.sqlite3"),
                    )
                    request = SimpleNamespace(
                        execution_id="code-manager-runtime-e2e",
                        definition=SimpleNamespace(
                            worker_id="sample-worker",
                            artifact_id="sample-worker@1.0.0",
                            artifact_hash=artifact_hash,
                            entrypoint="worker:run",
                        ),
                        configuration={"increment": 2},
                        input_payload={"value": 40},
                        depth=0,
                        timeout_seconds=30,
                        idempotency_key=None,
                    )
                    result = runtime.submit(request)
                    self.assertEqual(result.status, "succeeded", result.error)
                    self.assertEqual(result.result, {"value": 42})

                    restarted = WorkerRuntime(provider, sandbox_backend=DockerSandboxBackend(image),
                        execution_store=SQLiteExecutionStore(root / 'history.sqlite3'))
                    self.assertEqual(restarted.get(request.execution_id).result, {'value':42})
                    invalid = CodeManagerArtifactProvider(base_url, 'Bearer invalid-test-token')
                    with self.assertRaises(ArtifactAPIUnavailable) as denied:
                        invalid.fetch('sample-worker@1.0.0')
                    self.assertEqual(denied.exception.__cause__.code, 401)
                    with self.assertRaises(ArtifactAPIUnavailable) as missing:
                        provider.fetch('does-not-exist@1.0.0')
                    self.assertEqual(missing.exception.__cause__.code, 404)
                    from dataclasses import replace
                    from worker_manager import ExecutionRequest, WorkerDefinition
                    tampered = ExecutionRequest(WorkerDefinition('worker','sample-worker@1.0.0',
                        'sha256:'+'0'*64,'worker:run'))
                    bad_hash = restarted.submit(tampered)
                    self.assertEqual(bad_hash.error.code, 'ARTIFACT_HASH_MISMATCH')

                    other_owner = CodeManagerArtifactProvider(
                        base_url, "Bearer bob-integration-token", timeout=5
                    )
                    with self.assertRaises(ArtifactAPIUnavailable) as forbidden:
                        other_owner.fetch("sample-worker@1.0.0")
                    self.assertEqual(forbidden.exception.__cause__.code, 404)  # hide cross-owner existence
                    # Persisted Runtime and production credential middleware also
                    # participate in the Manager HTTP and Dashboard integration.
                    spec = importlib.util.spec_from_file_location('control_plane_helper',
                        Path(__file__).with_name('control_plane_helper.py'))
                    helper = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(helper)
                    helper.exercise_control_plane(root, cert_path, key_path, credential_path,
                        base_url, image, artifact_hash)
            finally:
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
