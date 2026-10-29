import io
import json
import sys
import unittest
from pathlib import Path
from email.message import Message
from urllib.error import HTTPError, URLError
from urllib.request import Request
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_api import PublicAPI, ConsumerAPIError, _RejectRedirectHandler

class Response:
    def __init__(self, value): self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, n): return self.value

class APITests(unittest.TestCase):
    def test_sources_mapping(self):
        seen = []
        def transport(req, timeout):
            seen.append((req.full_url, timeout))
            return Response(json.dumps({"contract_version":"1.0.0","payload":{"sources":[]}}).encode())
        api = PublicAPI("http://localhost:8080", transport=transport)
        self.assertEqual(api.list_sources(), {"sources": []})
        self.assertEqual(seen, [("http://localhost:8080/api/v1/sources", 5.0)])

    def test_invalid_response(self):
        api = PublicAPI("http://localhost", transport=lambda *a, **k: Response(b"[]"))
        with self.assertRaisesRegex(ConsumerAPIError, "object"):
            api.list_sources()

    def test_version_rejection(self):
        api = PublicAPI("http://localhost", transport=lambda *a, **k: Response(b'{"contract_version":"2.0.0","payload":{}}'))
        with self.assertRaises(ConsumerAPIError) as cm: api.list_sources()
        self.assertEqual(cm.exception.code, "UNSUPPORTED_CONTRACT_VERSION")

    def test_auth_failure(self):
        def transport(req, timeout): raise HTTPError(req.full_url, 403, "Forbidden", {}, None)
        with self.assertRaises(ConsumerAPIError) as cm: PublicAPI("http://localhost", transport=transport).list_sources()
        self.assertEqual(cm.exception.code, "FORBIDDEN")

    def test_unavailable(self):
        def transport(req, timeout): raise URLError("offline")
        with self.assertRaises(ConsumerAPIError) as cm: PublicAPI("http://localhost", transport=transport).list_sources()
        self.assertEqual(cm.exception.code, "SERVICE_UNAVAILABLE")

    def test_bearer_tokens_require_tls_outside_loopback(self):
        with self.assertRaisesRegex(ValueError, "bearer tokens require HTTPS"):
            PublicAPI("http://api.example", token="secret")
        with self.assertRaisesRegex(ValueError, "single-line"):
            PublicAPI("https://api.example", token="secret\r\nX-Injected: yes")
        # Loopback HTTP remains available for local development only.
        PublicAPI("http://localhost:8080", token="local-test-token")

    def test_redirect_handler_rejects_redirect_target(self):
        handler = _RejectRedirectHandler()
        request = Request(
            "https://api.example/api/v1/sources",
            headers={"Authorization": "Bearer secret"},
        )
        with self.assertRaises(HTTPError) as raised:
            handler.redirect_request(
                request, None, 302, "Found", Message(),
                "https://attacker.example/collect",
            )
        self.assertEqual(raised.exception.code, 302)
        self.assertIn("redirects are not allowed", str(raised.exception).lower())

    def test_default_transport_uses_redirect_blocker_and_keeps_auth_header(self):
        payload = json.dumps(
            {"contract_version": "1.0.0", "payload": {"sources": []}}
        ).encode()
        opener = Mock()
        opener.open.return_value = Response(payload)
        with patch("public_api.build_opener", return_value=opener) as build:
            api = PublicAPI("https://api.example", token="secret")
            self.assertEqual(api.list_sources(), {"sources": []})

        build.assert_called_once_with(_RejectRedirectHandler)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 5.0)

    def test_invalid_identifiers_and_config(self):
        api = PublicAPI("http://localhost", transport=lambda *a, **k: Response(b"{}"))
        with self.assertRaises(ValueError): api.get_resource("../secrets")
        with self.assertRaises(ValueError): PublicAPI("http://user:password@localhost")
        with self.assertRaises(ValueError): PublicAPI("http://example.com", identity_header="X-Manager-ID", identity="alice")

if __name__ == "__main__": unittest.main()
