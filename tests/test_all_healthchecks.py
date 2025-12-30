import os
import requests
import pytest


pytestmark = pytest.mark.integration

if not os.getenv("VX11_E2E"):
    pytest.skip("VX11_E2E not set; skipping integration health checks", allow_module_level=True)

MODULES = {
    "tentaculo_link": 8000,
    "madre": 8001,
    "switch": 8002,
    "hermes": 8003,
    "hormiguero": 8004,
    "mcp": 8006,
    "spawner": 8008,
    "operator_backend": 8011,
}


def test_health_all():
    for name, port in MODULES.items():
        try:
            r = requests.get(f"http://127.0.0.1:{port}/health", timeout=2)
        except Exception as e:
            raise AssertionError(f"{name} no respondió: {e}")

        assert r.status_code == 200, f"{name} devolvió {r.status_code}"
        assert r.json().get("status") == "ok", f"{name} respondió {r.text}"
