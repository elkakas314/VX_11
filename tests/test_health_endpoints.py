import os

import pytest
import requests


pytestmark = pytest.mark.integration

if os.getenv("VX11_INTEGRATION", "0") != "1":
    pytest.skip("Integration tests disabled. Set VX11_INTEGRATION=1 to run.", allow_module_level=True)

BASES = {
    "mcp": "http://127.0.0.1:8006/health",
    "spawner": "http://127.0.0.1:8008/health",
}


def test_health_endpoints():
    for name, url in BASES.items():
        try:
            r = requests.get(url, timeout=5)
        except requests.RequestException:
            pytest.skip(f"{name} health endpoint not reachable")
        assert r.status_code == 200, f"{name} devolvió {r.status_code}"
        assert r.json().get("status") == "ok"
