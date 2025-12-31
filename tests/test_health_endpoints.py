import os

import pytest
import requests
from tests._vx11_base import vx11_base_url, vx11_auth_headers


pytestmark = pytest.mark.integration

if os.getenv("VX11_INTEGRATION", "0") != "1":
    pytest.skip(
        "Integration tests disabled. Set VX11_INTEGRATION=1 to run.",
        allow_module_level=True,
    )

BASES = {
    "mcp": vx11_base_url() + "/mcp/health",
    "spawner": vx11_base_url() + "/spawner/health",
}


def test_health_endpoints():
    for name, url in BASES.items():
        try:
            headers = vx11_auth_headers()
            r = requests.get(url, headers=headers, timeout=5)
        except requests.RequestException:
            pytest.skip(f"{name} health endpoint not reachable")
        assert r.status_code == 200, f"{name} devolvió {r.status_code}"
        assert r.json().get("status") == "ok"
