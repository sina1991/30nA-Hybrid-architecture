import sys
import unittest
from email.message import Message
from urllib.error import HTTPError
from urllib.request import Request
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from worker_runtime.code_manager_adapter import (
    ArtifactAPIUnavailable,
    CodeManagerArtifactProvider,
    _RejectRedirectHandler,
)


class FakeResponse:
    def __init__(self, body, *, status=200, content_type="application/octet-stream"):
        self.body = body
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body[:size] if size >= 0 else self.body


class CodeManagerArtifactProviderTests(unittest.TestCase):
    def test_uses_versioned_public_endpoint_and_returns_exact_bytes(self):
        body = b"\x00artifact\xff"
        provider = CodeManagerArtifactProvider(
            "https://code.example/", "Bearer test-token", timeout=2, max_bytes=100
        )
        opener = Mock()
        opener.open.return_value = FakeResponse(body)
        with patch(
            "worker_runtime.code_manager_adapter.build_opener",
            return_value=opener,
        ) as build:
            self.assertEqual(provider.fetch("artifact-1"), body)

        build.assert_called_once_with(_RejectRedirectHandler)
        request = opener.open.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://code.example/api/v1/artifacts/artifact-1/content",
        )
        self.assertEqual(request.headers["Authorization"], "Bearer test-token")
        self.assertEqual(request.headers["Accept"], "application/octet-stream")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 2.0)

    def test_rejects_oversized_artifact(self):
        provider = CodeManagerArtifactProvider(
            "https://code.example", "Bearer token", max_bytes=4
        )
        opener = Mock()
        opener.open.return_value = FakeResponse(b"12345")
        with patch("worker_runtime.code_manager_adapter.build_opener", return_value=opener):
            with self.assertRaises(ArtifactAPIUnavailable):
                provider.fetch("artifact-1")

    def test_rejects_unexpected_content_type(self):
        provider = CodeManagerArtifactProvider("https://code.example", "Bearer token")
        opener = Mock()
        opener.open.return_value = FakeResponse(b"{}", content_type="application/json")
        with patch("worker_runtime.code_manager_adapter.build_opener", return_value=opener):
            with self.assertRaises(ArtifactAPIUnavailable):
                provider.fetch("artifact-1")

    def test_rejects_invalid_limits_and_identity(self):
        for kwargs in ({"timeout": 0}, {"timeout": float("nan")}, {"max_bytes": 0}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    CodeManagerArtifactProvider(
                        "https://code.example", "Bearer token", **kwargs
                    )
        with self.assertRaises(ValueError):
            CodeManagerArtifactProvider("http://localhost", "Bearer token")
        with self.assertRaises(ValueError):
            CodeManagerArtifactProvider("https://code.example", "")

    def test_redirect_handler_rejects_cross_origin_redirects(self):
        handler = _RejectRedirectHandler()
        request = Request("https://code.example/api/v1/artifacts/id/content")
        with self.assertRaises(HTTPError) as raised:
            handler.redirect_request(
                request, None, 302, "Found", Message(),
                "https://attacker.example/collect",
            )
        self.assertEqual(raised.exception.code, 302)
        self.assertIn("redirects are not allowed", str(raised.exception).lower())

    def test_provider_does_not_follow_redirect_responses(self):
        provider = CodeManagerArtifactProvider("https://code.example", "Bearer token")
        opener = Mock()
        opener.open.side_effect = HTTPError(
            "https://code.example/api/v1/artifacts/id/content",
            302, "Redirect", Message(), None,
        )
        with patch("worker_runtime.code_manager_adapter.build_opener", return_value=opener):
            with self.assertRaises(ArtifactAPIUnavailable):
                provider.fetch("id")
        opener.open.assert_called_once()

    def test_rejects_invalid_artifact_id_before_network_access(self):
        provider = CodeManagerArtifactProvider("https://code.example", "Bearer token")
        for artifact_id in ("", "../escape", "folder/item"):
            with self.subTest(artifact_id=artifact_id):
                with patch("worker_runtime.code_manager_adapter.build_opener") as build:
                    with self.assertRaises(ValueError):
                        provider.fetch(artifact_id)
                    build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
