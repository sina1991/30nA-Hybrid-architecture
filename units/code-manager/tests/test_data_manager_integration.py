"""Optional integration test against a running DATA MANAGER.

Enable only for a local development DATA MANAGER configured with
DATA_MANAGER_ALLOW_INSECURE_HEADER=1. Never enable this mode in production.
"""

import io
import os
import tempfile
import unittest
import zipfile
from urllib.parse import urlsplit

from code_manager.blob_storage import BlobStorage
from code_manager.data_manager_client import DataManagerClient
from code_manager.source_registration import SourceRegistrationService
from code_manager.source_registry import SourceRegistry


class DataManagerIntegrationTests(unittest.TestCase):
    def test_register_and_retrieve_through_real_data_manager_api(self):
        enabled = os.environ.get("CODE_MANAGER_INTEGRATION") == "1"
        if not enabled:
            self.skipTest("Set CODE_MANAGER_INTEGRATION=1 to enable")

        base_url = os.environ.get(
            "CODE_MANAGER_DATA_MANAGER_URL", "http://127.0.0.1:8080"
        )
        parsed = urlsplit(base_url)
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            self.fail("Integration test permits only a loopback DATA MANAGER")

        if os.environ.get("DATA_MANAGER_ALLOW_INSECURE_HEADER", "").lower() not in {
            "1", "true", "yes"
        }:
            self.fail(
                "Local DATA MANAGER must explicitly enable its development header"
            )

        owner_id = os.environ.get(
            "CODE_MANAGER_INTEGRATION_OWNER", "code-manager-integration"
        )

        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("integration/__init__.py", "")
            archive.writestr(
                "integration/main.py",
                "def run(data):\n    return data\n",
            )
        source_bytes = output.getvalue()

        client = DataManagerClient(
            base_url,
            identity_provider=lambda: {"X-Manager-ID": owner_id},
        )

        with tempfile.TemporaryDirectory() as directory:
            storage = BlobStorage(directory)
            service = SourceRegistrationService(storage, client)
            registry = SourceRegistry(storage, client)

            import uuid
            source_id = "integration-" + uuid.uuid4().hex[:16]
            result = service.register_source(
                owner_id=owner_id,
                source_id=source_id,
                source_version="1.0.0",
                source_bytes=source_bytes,
                entrypoint="integration.main:run",
                input_schema={"type": "object"},
                output_schema={"type": "object"},
            )

            retrieved = registry.get_source(
                owner_id=owner_id,
                source_id=source_id,
                source_version="1.0.0",
            )

            self.assertEqual(result["source_hash"], retrieved["source_hash"])
            self.assertEqual(source_bytes, retrieved["source_bytes"])


if __name__ == "__main__":
    unittest.main()
