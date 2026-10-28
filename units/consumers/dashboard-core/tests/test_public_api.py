import io
import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from public_api import PublicAPI, ConsumerAPIError

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

    def test_invalid_identifiers_and_config(self):
        api = PublicAPI("http://localhost", transport=lambda *a, **k: Response(b"{}"))
        with self.assertRaises(ValueError): api.get_resource("../secrets")
        with self.assertRaises(ValueError): PublicAPI("http://user:password@localhost")
        with self.assertRaises(ValueError): PublicAPI("http://example.com", identity_header="X-Manager-ID", identity="alice")

if __name__ == "__main__": unittest.main()
