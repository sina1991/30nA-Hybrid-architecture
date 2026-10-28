import importlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

UNIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UNIT.parent))

spec = importlib.util.spec_from_file_location(
    "data_manager",
    UNIT / "__init__.py",
    submodule_search_locations=[str(UNIT)],
)
package = importlib.util.module_from_spec(spec)
sys.modules["data_manager"] = package
spec.loader.exec_module(package)

api = importlib.import_module("data_manager.api.app")


class DataManagerAPITests(unittest.TestCase):
    def request(self, method="GET", path="/api/v1/unknown",
                identity=None, body=b"", extra=None):
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
        if identity is not None:
            environ["REMOTE_USER"] = identity
        if extra:
            environ.update(extra)

        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        result = api.application(environ, start_response)
        payload = json.loads(b"".join(result).decode("utf-8"))
        return captured, payload

    def test_request_without_trusted_identity_is_forbidden(self):
        captured, payload = self.request()
        self.assertTrue(captured["status"].startswith("403 "))
        self.assertEqual(payload["error"]["code"], "FORBIDDEN")

    def test_health_check_does_not_require_identity(self):
        captured, payload = self.request(path="/health")
        self.assertTrue(captured["status"].startswith("200 "))
        self.assertEqual(payload, {"status": "ok"})

    def test_oversized_request_body_is_rejected(self):
        body = b" " * 1_000_001
        captured, payload = self.request(
            method="POST",
            path="/api/v1/models",
            identity="manager-a",
            body=body,
        )
        self.assertTrue(captured["status"].startswith("400 "))
        self.assertEqual(payload["error"]["code"], "INVALID_INPUT")

    def test_unexpected_exception_does_not_leak_details(self):
        with patch.object(
            api.service,
            "register_model",
            side_effect=RuntimeError("private database detail"),
        ):
            captured, payload = self.request(
                method="POST",
                path="/api/v1/models",
                identity="manager-a",
                body=b"{}",
            )

        self.assertTrue(captured["status"].startswith("500 "))
        self.assertEqual(payload["error"]["code"], "INTERNAL_ERROR")
        self.assertEqual(payload["error"]["message"], "Internal server error")
        self.assertNotIn("private database detail", json.dumps(payload))

    def test_invalid_content_length_is_rejected(self):
        captured, payload = self.request(
            method="POST",
            path="/api/v1/models",
            identity="manager-a",
            body=b"{}",
            extra={"CONTENT_LENGTH": "invalid"},
        )
        self.assertTrue(captured["status"].startswith("400 "))
        self.assertEqual(payload["error"]["code"], "INVALID_INPUT")


if __name__ == "__main__":
    unittest.main()
