import base64
import io
import json
import os
import tempfile
import unittest
import zipfile

from code_manager.api import create_application
from code_manager.blob_storage import BlobStorage
from code_manager.published_artifacts import PublishedArtifactRegistry
from code_manager.source_registry import SourceRegistry
from code_manager.data_manager_client import DataManagerAPIError


class FakeDataManager:
    def __init__(self, owner_id, state):
        self.owner_id = owner_id
        self.state = state

    def register_model(self, model):
        key = (model["model_id"], model["version"])
        existing = self.state["models"].get(key)
        if existing is not None and existing != model:
            raise DataManagerAPIError(
                409, "CONFLICT", "Model contract conflict"
            )
        if model["owner_id"] != self.owner_id:
            raise DataManagerAPIError(403, "ACCESS_DENIED", "Wrong owner")
        self.state["models"][key] = model
        return model

    def create_resource(self, resource):
        resource_id = resource["resource_id"]
        key = (resource["model_id"], resource["model_version"])
        model = self.state["models"].get(key)
        if not model or model["owner_id"] != self.owner_id:
            raise DataManagerAPIError(403, "ACCESS_DENIED", "Wrong owner")
        if resource_id in self.state["resources"]:
            raise DataManagerAPIError(409, "CONFLICT", "Resource exists")
        self.state["resources"][resource_id] = {
            **resource,
            "owner_id": self.owner_id,
        }
        self.state["records"][resource_id] = []
        return resource

    def get_resource(self, resource_id):
        resource = self.state["resources"].get(resource_id)
        if not resource or resource["owner_id"] != self.owner_id:
            raise DataManagerAPIError(404, "RESOURCE_NOT_FOUND", "Not found")
        return resource

    def list_records(self, resource_id, limit=100):
        self.get_resource(resource_id)
        return {"records": self.state["records"][resource_id][:limit]}

    def write_record(self, resource_id, record):
        self.get_resource(resource_id)
        records = self.state["records"][resource_id]
        record_id = f"record-{len(records) + 1}"
        records.append({"record_id": record_id, "data": record})
        return {"record_id": record_id}


def make_zip():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sample/__init__.py", "")
        archive.writestr("sample/main.py", "def run(data):\n    return data\n")
    return output.getvalue()


class TestIdentity:
    def resolve(self, environ):
        identity = environ.get("REMOTE_USER")
        if not identity:
            raise __import__(
                "code_manager.api", fromlist=["APIError"]
            ).APIError(401, "ACCESS_DENIED", "No identity")
        return identity


class CodeManagerAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.storage = BlobStorage(self.temp.name)
        self.artifacts = PublishedArtifactRegistry(self.storage)
        self.state = {
            "models": {},
            "resources": {},
            "records": {},
        }

        def client_factory(owner_id):
            return FakeDataManager(owner_id, self.state)

        self.app = create_application(
            blob_storage=self.storage,
            data_manager_client_factory=client_factory,
            identity_provider=TestIdentity(),
            published_artifact_registry=self.artifacts,
        )

    def tearDown(self):
        self.temp.cleanup()

    def request(self, method, path, payload=None, owner="alice", content_type="application/json"):
        raw = b"" if payload is None else json.dumps(payload).encode()
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_TYPE": content_type,
            "CONTENT_LENGTH": str(len(raw)),
            "REMOTE_USER": owner,
            "wsgi.input": io.BytesIO(raw),
            "HTTP_X_CORRELATION_ID": "test-correlation-1",
        }
        captured = {}

        def start_response(status, headers):
            captured["status"] = int(status.split()[0])
            captured["headers"] = dict(headers)

        body = b"".join(self.app(environ, start_response))
        parsed = body if captured["headers"].get("Content-Type") == "application/octet-stream" else json.loads(body)
        return captured["status"], captured["headers"], parsed

    def source_payload(self, **overrides):
        payload = {
            "source_id": "pricing-model",
            "source_version": "1.0.0",
            "source_content_base64": base64.b64encode(make_zip()).decode(),
            "entrypoint": "sample.main:run",
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
        }
        payload.update(overrides)
        return payload

    def test_register_source_and_inspect_without_execution(self):
        status, headers, response = self.request(
            "POST", "/api/v1/sources", self.source_payload()
        )
        self.assertEqual(status, 201)
        self.assertEqual(response["contract_version"], "1.0.0")
        self.assertEqual(
            headers["X-Correlation-ID"], "test-correlation-1"
        )
        self.assertEqual(
            response["payload"]["source_id"], "pricing-model"
        )

        path = (
            "/api/v1/sources/pricing-model/versions/1.0.0/inspect"
        )
        status, _, inspection = self.request("POST", path)
        self.assertEqual(status, 200)
        self.assertEqual(
            inspection["payload"]["inspection_status"],
            "archive_validated",
        )
        self.assertTrue(inspection["payload"]["findings"])

    def test_owner_id_in_request_body_is_rejected(self):
        payload = self.source_payload(owner_id="victim")
        status, _, response = self.request(
            "POST", "/api/v1/sources", payload
        )
        self.assertEqual(status, 400)
        self.assertEqual(response["error"]["code"], "SOURCE_INVALID")

    def test_invalid_base64_is_rejected(self):
        payload = self.source_payload(source_content_base64="%%%")
        status, _, response = self.request(
            "POST", "/api/v1/sources", payload
        )
        self.assertEqual(status, 400)
        self.assertEqual(response["error"]["code"], "SOURCE_INVALID")

    def test_source_is_not_visible_to_another_owner(self):
        self.request("POST", "/api/v1/sources", self.source_payload())
        status, _, response = self.request(
            "GET",
            "/api/v1/sources/pricing-model/versions/1.0.0",
            owner="bob",
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "SOURCE_NOT_FOUND")

    def _publish_built(self, owner="alice"):
        payload = self.source_payload()
        data = base64.b64decode(payload["source_content_base64"])
        self.request("POST", "/api/v1/sources", payload, owner=owner)
        import hashlib
        source_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        artifact_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        return self.artifacts.publish_built(
            owner, "pricing-model@1.0.0", data,
            entrypoint="sample.main:run", source_hash=source_hash,
            build_id="a" * 32,
            provenance={"builder_version": "test", "source_hash": source_hash,
                        "artifact_hash": artifact_hash},
        )

    def test_published_artifact_content_returns_exact_bytes_and_digest(self):
        metadata, _ = self._publish_built()
        status, headers, content = self.request(
            "GET", "/api/v1/artifacts/pricing-model@1.0.0/content"
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/octet-stream")
        self.assertEqual(content, make_zip())
        self.assertEqual(headers["X-Artifact-Hash"], metadata["artifact_hash"])
        self.assertEqual(headers["ETag"], '"' + metadata["artifact_hash"] + '"')
        self.assertEqual(headers["Cache-Control"], "private, no-store")

    def test_unpublished_artifact_download_returns_404(self):
        status, _, response = self.request(
            "GET", "/api/v1/artifacts/pricing-model@1.0.0/content"
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "ARTIFACT_NOT_FOUND")

    def test_artifact_download_is_owner_scoped(self):
        self._publish_built(owner="alice")
        status, _, response = self.request(
            "GET", "/api/v1/artifacts/pricing-model@1.0.0/content", owner="bob"
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "ARTIFACT_NOT_FOUND")

    def test_build_preflight_reports_not_run_stages_and_never_publishes(self):
        self.request("POST", "/api/v1/sources", self.source_payload())
        status, _, response = self.request(
            "POST", "/api/v1/builds",
            {"source_id": "pricing-model", "source_version": "1.0.0"},
        )
        self.assertEqual(status, 200)
        report = response["payload"]["build"]
        self.assertEqual(report["status"], "blocked")
        self.assertFalse(report["publishable"])
        stages = {stage["stage"]: stage["status"] for stage in report["stages"]}
        self.assertEqual(stages["inspect_archive"], "passed")
        self.assertEqual(stages["verify_source_hash"], "passed")
        self.assertEqual(stages["syntax_check"], "passed")
        self.assertEqual(stages["test"], "not_run")
        self.assertEqual(stages["package"], "not_run")
        self.assertEqual(stages["hash"], "not_run")
        with self.assertRaises(Exception):
            self.artifacts.get("alice", "pricing-model@1.0.0")

    def test_build_preflight_does_not_disclose_another_owners_source(self):
        self.request("POST", "/api/v1/sources", self.source_payload())
        status, _, response = self.request(
            "POST", "/api/v1/builds",
            {"source_id": "pricing-model", "source_version": "1.0.0"},
            owner="bob",
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "SOURCE_NOT_FOUND")

    def test_build_preflight_rejects_owner_in_request(self):
        status, _, response = self.request(
            "POST", "/api/v1/builds",
            {"source_id": "pricing-model", "source_version": "1.0.0", "owner_id": "victim"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(response["error"]["code"], "SOURCE_INVALID")

    def test_unknown_route_is_not_found(self):
        status, _, response = self.request(
            "GET", "/api/v1/not-a-route"
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "SOURCE_NOT_FOUND")


    def test_source_zip_is_never_downloadable_from_artifact_endpoint(self):
        self.request("POST", "/api/v1/sources", self.source_payload())
        client = FakeDataManager("alice", self.state)
        source_registry = SourceRegistry(self.storage, client)
        self.artifacts.publish(source_registry, "alice", "pricing-model@1.0.0")
        status, _, response = self.request(
            "GET", "/api/v1/artifacts/pricing-model@1.0.0/content"
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "ARTIFACT_NOT_FOUND")

    def test_build_history_is_durable_and_owner_scoped(self):
        self.request("POST", "/api/v1/sources", self.source_payload())
        status, _, created = self.request(
            "POST", "/api/v1/builds",
            {"source_id": "pricing-model", "source_version": "1.0.0"},
        )
        self.assertEqual(status, 200)
        build = created["payload"]["build"]
        self.assertTrue(build["build_id"])
        status, _, history = self.request("GET", "/api/v1/builds")
        self.assertEqual(status, 200)
        self.assertEqual(history["payload"]["builds"][0]["build_id"], build["build_id"])
        status, _, detail = self.request("GET", "/api/v1/builds/" + build["build_id"])
        self.assertEqual(status, 200)
        self.assertEqual(detail["payload"]["build"]["build_id"], build["build_id"])
        status, _, hidden = self.request(
            "GET", "/api/v1/builds/" + build["build_id"], owner="bob"
        )
        self.assertEqual(status, 404)
        self.assertEqual(hidden["error"]["code"], "BUILD_NOT_FOUND")

    def test_publish_endpoint_rejects_missing_build(self):
        status, _, response = self.request(
            "POST", "/api/v1/artifacts/pricing-model@1.0.0/publish",
            {"build_id": "a" * 32},
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "BUILD_NOT_FOUND")

    def test_publish_endpoint_rejects_source_zip_even_if_registered(self):
        self.request("POST", "/api/v1/sources", self.source_payload())
        status, _, response = self.request(
            "POST", "/api/v1/artifacts/pricing-model@1.0.0/publish",
            {"build_id": "a" * 32},
        )
        self.assertEqual(status, 404)
        self.assertEqual(response["error"]["code"], "BUILD_NOT_FOUND")


    def test_publish_endpoint_requires_successful_build_and_downloads_built_artifact(self):
        import hashlib
        from code_manager.build_pipeline import BuildHistoryStore

        payload = self.source_payload()
        source_bytes = base64.b64decode(payload["source_content_base64"])
        self.request("POST", "/api/v1/sources", payload)
        artifact_bytes = make_zip()
        artifact_digest = self.storage.put_bytes(artifact_bytes)
        build_id = "b" * 32
        source_hash = "sha256:" + hashlib.sha256(source_bytes).hexdigest()
        artifact_hash = "sha256:" + artifact_digest
        stages = [
            {"stage": name, "status": "passed", "detail": "test fixture"}
            for name in ("inspect_archive", "verify_source_hash", "validate_archive_paths",
                         "syntax_check", "dependency_check", "contract_check",
                         "normalize_working_copy", "test", "reproducibility", "package", "hash")
        ]
        report = {
            "build_id": build_id, "source_id": "pricing-model", "source_version": "1.0.0",
            "created_at": "2026-10-29T00:00:00Z", "status": "succeeded", "publishable": True,
            "stages": stages, "source_hash": source_hash, "artifact_hash": artifact_hash,
            "artifact_digest": artifact_digest, "artifact_size": len(artifact_bytes),
            "entrypoint": "sample.main:run",
            "provenance": {"builder_version": "test", "source_hash": source_hash,
                           "artifact_hash": artifact_hash},
        }
        BuildHistoryStore(self.storage.root / "build-history.sqlite3").save("alice", report)
        status, _, response = self.request(
            "POST", "/api/v1/artifacts/pricing-model@1.0.0/publish", {"build_id": build_id}
        )
        self.assertEqual(status, 201)
        self.assertEqual(response["payload"]["artifact"]["artifact_type"], "built_artifact")
        status, _, downloaded = self.request(
            "GET", "/api/v1/artifacts/pricing-model@1.0.0/content"
        )
        self.assertEqual(status, 200)
        self.assertEqual(downloaded, artifact_bytes)


if __name__ == "__main__":
    unittest.main()
