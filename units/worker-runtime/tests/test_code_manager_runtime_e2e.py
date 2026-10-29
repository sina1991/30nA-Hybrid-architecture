"""Real HTTPS CODE MANAGER -> Worker Runtime artifact execution integration test."""
import hashlib
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
from http.server import BaseHTTPRequestHandler
from types import SimpleNamespace
from unittest.mock import patch
from wsgiref.simple_server import WSGIRequestHandler, make_server

from code_manager.api import APIError, create_application
from code_manager.blob_storage import BlobStorage
from code_manager.published_artifacts import PublishedArtifactRegistry
from worker_runtime import (
    ArtifactAPIUnavailable,
    CodeManagerArtifactProvider,
    DockerSandboxBackend,
    WorkerRuntime,
)


class BearerIdentity:
    """Test-only identity gateway mapping bearer credentials to owners."""

    def resolve(self, environ):
        identities = {
            "Bearer alice-integration-token": "alice",
            "Bearer bob-integration-token": "bob",
        }
        owner = identities.get(environ.get("HTTP_AUTHORIZATION", ""))
        if owner is None:
            raise APIError(401, "ACCESS_DENIED", "Invalid integration credential")
        return owner


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
    return output.getvalue()


class CodeManagerRuntimeE2ETests(unittest.TestCase):
    def test_authenticated_https_download_executes_exact_published_artifact(self):
        image = os.environ.get("WORKER_RUNTIME_SANDBOX_TEST_IMAGE")
        if not image:
            self.skipTest("CI/staging must provide the immutable Docker test image ID")
        if shutil.which("docker") is None:
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
            artifact = make_worker_artifact()
            digest = hashlib.sha256(artifact).hexdigest()
            source_hash = "sha256:" + hashlib.sha256(b"registered source bytes").hexdigest()
            artifact_hash = "sha256:" + digest
            dependency_lock = "stdlib-only"
            dependency_lock_hash = "sha256:" + hashlib.sha256(b"stdlib-only").hexdigest()
            provenance = {
                "source_hash": source_hash,
                "artifact_hash": artifact_hash,
                "dependency_lock": dependency_lock,
                "dependency_lock_hash": dependency_lock_hash,
                "builder_version": "integration-test",
            }
            registry.publish_built(
                "alice",
                "sample-worker@1.0.0",
                artifact,
                entrypoint="worker:run",
                source_hash=source_hash,
                build_id="b" * 32,
                provenance=provenance,
                artifact_version=digest,
                dependency_lock=dependency_lock,
                validation_status="passed",
            )

            app = create_application(
                blob_storage=storage,
                data_manager_client_factory=lambda owner_id: object(),
                identity_provider=BearerIdentity(),
                published_artifact_registry=registry,
            )
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
                with patch.dict(os.environ, {"SSL_CERT_FILE": str(cert_path)}):
                    provider = CodeManagerArtifactProvider(
                        base_url, "Bearer alice-integration-token", timeout=5
                    )
                    self.assertEqual(provider.fetch("sample-worker@1.0.0"), artifact)

                    runtime = WorkerRuntime(
                        provider,
                        sandbox_backend=DockerSandboxBackend(image),
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

                    other_owner = CodeManagerArtifactProvider(
                        base_url, "Bearer bob-integration-token", timeout=5
                    )
                    with self.assertRaises(ArtifactAPIUnavailable):
                        other_owner.fetch("sample-worker@1.0.0")
            finally:
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
