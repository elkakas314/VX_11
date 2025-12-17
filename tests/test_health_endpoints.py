import requests
import pytest


pytestmark = pytest.mark.integration

BASES = {
    "mcp": "http://127.0.0.1:8006/health",
    "spawner": "http://127.0.0.1:8008/health",
}


def test_health_endpoints():
    for name, url in BASES.items():
        r = requests.get(url)
        assert r.status_code == 200, f"{name} devolvió {r.status_code}"
        assert r.json().get("status") == "ok"
