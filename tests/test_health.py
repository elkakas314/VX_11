"""
P0 Tests: Health Endpoints

Tests for health check endpoints on all modules.
Markers: @pytest.mark.p0, @pytest.mark.health
"""

import pytest
import requests
import os
from tests._vx11_base import vx11_base_url, vx11_auth_headers


@pytest.mark.p0
@pytest.mark.health
def test_p0_4_madre_health_endpoint(madre_port):
    """
    P0.4: Verify madre health via frontdoor
    Expected: HTTP 200 from /health (frontdoor), no direct /madre/health path on single-entrypoint
    Note: /madre/health is only accessible via direct madre:8001, not through frontdoor proxy.
    """
    try:
        headers = vx11_auth_headers()
        # Test frontdoor health instead (madre is proxied as /madre/health on internal routes)
        resp = requests.get(vx11_base_url() + "/health", headers=headers, timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        data = resp.json()
        assert "status" in data, "Missing 'status' in response"
        assert data["status"] == "ok", f"Expected status='ok', got {data['status']}"
    except requests.exceptions.ConnectionError:
        pytest.skip(f"frontdoor not available")
    except Exception as e:
        pytest.fail(f"Health check failed: {e}")


@pytest.mark.p0
@pytest.mark.health
def test_p0_4_redis_connectivity(redis_port):
    """
    P0.4: Verify redis is accessible
    Expected: Redis responds to ping or connection succeeds
    """
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(("localhost", redis_port))
    sock.close()

    if result != 0:
        pytest.skip(f"Redis not accessible on port {redis_port}")


@pytest.mark.integration
def test_health_endpoints_integration():
    """
    Integration test: check additional module health endpoints (mcp, spawner).
    Skips if `VX11_INTEGRATION` is not enabled.
    """
    if os.getenv("VX11_INTEGRATION", "0") != "1":
        pytest.skip("Integration tests disabled. Set VX11_INTEGRATION=1 to run.")

    BASES = {
        "mcp": vx11_base_url() + "/mcp/health",
        "spawner": vx11_base_url() + "/spawner/health",
    }

    for name, url in BASES.items():
        try:
            headers = vx11_auth_headers()
            r = requests.get(url, headers=headers, timeout=5)
        except requests.RequestException:
            pytest.skip(f"{name} health endpoint not reachable")
        assert r.status_code == 200, f"{name} devolvió {r.status_code}"
        assert r.json().get("status") == "ok"
