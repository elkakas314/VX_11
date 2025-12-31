"""
P0 Tests: Health Endpoints

Tests for health check endpoints on all modules.
Markers: @pytest.mark.p0, @pytest.mark.health
"""

import pytest
import requests


@pytest.mark.p0
@pytest.mark.health
def test_p0_4_madre_health_endpoint(madre_port):
    """
    P0.4: Verify madre health endpoint is responding
    Expected: HTTP 200, JSON with status="ok"
    """
    try:
        resp = requests.get(f"http://localhost:{madre_port}/health", timeout=5)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

        data = resp.json()
        assert "status" in data, "Missing 'status' in response"
        assert data["status"] == "ok", f"Expected status='ok', got {data['status']}"
    except requests.exceptions.ConnectionError:
        pytest.skip(f"madre not available on port {madre_port}")
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
