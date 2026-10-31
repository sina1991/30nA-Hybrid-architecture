from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.modules.registry import (
    list_modules,
    get_module,
    ModuleManifestError,
)

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "dashboard-core",
    }


def test_themes_endpoint():
    response = client.get("/api/themes")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    assert {item["id"] for item in payload["themes"]} == {
        "daylight", "forest", "midnight"
    }


def test_each_theme_has_colors():
    for theme_id in ("daylight", "forest", "midnight"):
        response = client.get(f"/api/themes/{theme_id}")
        assert response.status_code == 200
        theme = response.json()
        assert theme["colors"]["bg"]
        assert theme["colors"]["text"]


def test_unknown_theme_is_not_found():
    assert client.get("/api/themes/not-found").status_code == 404


def test_module_catalog():
    modules = list_modules()
    assert len({item["id"] for item in modules}) == len(modules)
    assert {"clock", "slot-note", "system-monitor", "music-player"} <= {item["id"] for item in modules}
    assert not {"calculator", "counter", "dice-roller"} & {item["id"] for item in modules}
    assert get_module("slot-note")["type"] == "slot-note"
    assert get_module("dice-roller")["type"] == "dice-roller"
    assert get_module("missing-module") is None


def test_module_catalog_endpoint():
    response = client.get("/api/modules")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == len(payload["modules"])
    assert {item["id"] for item in payload["modules"]} >= {"dice-roller"}
    assert all("type" in item for item in payload["modules"])


def test_dashboard_contains_generic_branding():
    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard Core" in response.text
    assert "xauusd-dashboard" not in response.text.lower()
