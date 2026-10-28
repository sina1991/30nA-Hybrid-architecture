import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from code_manager.data_manager_client import (
    DataManagerAPIError,
    DataManagerClient,
    DataManagerClientError,
    DataManagerTransportError,
)


class FakeTransport:
    def __init__(self, status=200, payload=None):
        self.status = status
        self.payload = payload if payload is not None else {"ok": True}
        self.calls = []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        return (
            self.status,
            {"Content-Type": "application/json"},
            json.dumps(self.payload).encode("utf-8"),
        )


class DataManagerClientTests(unittest.TestCase):
    def test_get_model_builds_url_and_query(self):
        transport = FakeTransport(payload={"model_id": "sample"})
        client = DataManagerClient(
            "http://127.0.0.1:8080",
            transport=transport,
        )

        result = client.get_model("sample", version="1.0")

        self.assertEqual(result, {"model_id": "sample"})
        method, url, headers, body, timeout = transport.calls[0]
        self.assertEqual(method, "GET")
        self.assertEqual(
            url,
            "http://127.0.0.1:8080/api/v1/models/sample?version=1.0",
        )
        self.assertEqual(headers["Accept"], "application/json")
        self.assertIsNone(body)
        self.assertEqual(timeout, 5.0)
        self.assertNotIn("X-Manager-ID", headers)

    def test_post_encodes_json_payload(self):
        transport = FakeTransport(status=201, payload={"resource_id": "r1"})
        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        result = client.create_resource(
            {
                "resource_id": "r1",
                "model_id": "m1",
                "model_version": "1.0",
            }
        )

        self.assertEqual(result["resource_id"], "r1")
        method, url, headers, body, _ = transport.calls[0]
        self.assertEqual(method, "POST")
        self.assertEqual(url, "http://localhost:8080/api/v1/resources")
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(json.loads(body.decode("utf-8"))["model_id"], "m1")

    def test_identity_provider_is_optional_and_replaceable(self):
        transport = FakeTransport()
        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
            identity_provider=lambda: {"Authorization": "Bearer test-token"},
        )

        client.request("GET", "/api/v1/resources/r1")

        headers = transport.calls[0][2]
        self.assertEqual(headers["Authorization"], "Bearer test-token")
        self.assertNotIn("X-Manager-ID", headers)

    def test_identity_provider_must_return_dictionary(self):
        client = DataManagerClient(
            "http://localhost:8080",
            transport=FakeTransport(),
            identity_provider=lambda: None,
        )
        with self.assertRaises(DataManagerClientError):
            client.request("GET", "/api/v1/resources/r1")

    def test_api_error_is_parsed(self):
        transport = FakeTransport(
            status=403,
            payload={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Authentication required",
                    "retryable": False,
                    "context": {"reason": "missing_identity"},
                    "contract_version": "1.0.0",
                }
            },
        )
        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        with self.assertRaises(DataManagerAPIError) as caught:
            client.get_resource("r1")

        error = caught.exception
        self.assertEqual(error.status, 403)
        self.assertEqual(error.code, "FORBIDDEN")
        self.assertEqual(error.message, "Authentication required")
        self.assertFalse(error.retryable)
        self.assertEqual(error.context, {"reason": "missing_identity"})

    def test_non_json_error_response_is_reported(self):
        def transport(*args):
            return 502, {}, b"upstream unavailable"

        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        with self.assertRaises(DataManagerAPIError) as caught:
            client.request("GET", "/api/v1/resources/r1")

        self.assertEqual(caught.exception.status, 502)
        self.assertEqual(caught.exception.code, "HTTP_ERROR")

    def test_invalid_success_json_is_rejected(self):
        def transport(*args):
            return 200, {}, b"not json"

        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        with self.assertRaises(DataManagerTransportError):
            client.request("GET", "/api/v1/resources/r1")

    def test_non_object_success_json_is_rejected(self):
        def transport(*args):
            return 200, {}, b'["unexpected"]'

        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        with self.assertRaises(DataManagerTransportError):
            client.request("GET", "/api/v1/resources/r1")

    def test_transport_exception_is_wrapped(self):
        def transport(*args):
            raise TimeoutError("private transport detail")

        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        with self.assertRaises(DataManagerTransportError) as caught:
            client.request("GET", "/api/v1/resources/r1")

        self.assertNotIn("private transport detail", str(caught.exception))

    def test_absolute_and_traversal_paths_are_rejected(self):
        client = DataManagerClient(
            "http://localhost:8080",
            transport=FakeTransport(),
        )

        for path in (
            "https://example.com/steal",
            "//example.com/steal",
            "../outside",
            "/api/../outside",
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    client.request("GET", path)

    def test_payload_must_be_json_object(self):
        client = DataManagerClient(
            "http://localhost:8080",
            transport=FakeTransport(),
        )
        with self.assertRaises(ValueError):
            client.request("POST", "/api/v1/models", payload=["not", "object"])

    def test_no_automatic_retry_for_mutating_operation(self):
        transport = FakeTransport(
            status=503,
            payload={
                "error": {
                    "code": "TEMPORARY_FAILURE",
                    "message": "Unavailable",
                    "retryable": True,
                }
            },
        )
        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        with self.assertRaises(DataManagerAPIError):
            client.write_record("r1", {"value": 42})

        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0][0], "POST")

    def test_invalid_base_url_and_timeout_are_rejected(self):
        for base_url in ("", "localhost:8080", "ftp://localhost"):
            with self.subTest(base_url=base_url):
                with self.assertRaises(ValueError):
                    DataManagerClient(base_url, transport=FakeTransport())

        for timeout in (0, -1, True, "5"):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    DataManagerClient(
                        "http://localhost:8080",
                        timeout=timeout,
                        transport=FakeTransport(),
                    )


    def test_identifier_contract_is_enforced_before_transport(self):
        transport = FakeTransport()
        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        invalid_calls = (
            lambda: client.get_model("../outside"),
            lambda: client.get_resource("r/1"),
            lambda: client.list_records("r?x=1"),
            lambda: client.read_record("r1", "../record"),
            lambda: client.delete_record("r1", "record/1"),
            lambda: client.create_resource({
                "resource_id": "r1",
                "model_id": "../model",
                "model_version": "1.0",
            }),
        )

        for operation in invalid_calls:
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    operation()

        self.assertEqual(transport.calls, [])

    def test_valid_identifier_boundaries_are_accepted(self):
        transport = FakeTransport()
        client = DataManagerClient(
            "http://localhost:8080",
            transport=transport,
        )

        client.get_resource("A.b-c_d:1")
        self.assertEqual(len(transport.calls), 1)

        identifier = "a" * 128
        client.get_resource(identifier)
        self.assertEqual(len(transport.calls), 2)

    def test_invalid_base_url_credentials_query_and_fragment_are_rejected(self):
        invalid_urls = (
            "http://user:password@localhost:8080",
            "http://localhost:8080?debug=1",
            "http://localhost:8080#fragment",
            "http://localhost:99999",
            "http:///missing-host",
        )

        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    DataManagerClient(url, transport=FakeTransport())


if __name__ == "__main__":
    unittest.main()
