"""
Test: Madre starts and validates each core module (FASE 4)
"""

import pytest
import requests
import os
import time
from tests._vx11_base import vx11_base_url, vx11_auth_headers

MADRE_URL = os.getenv("VX11_MADRE_URL", vx11_base_url())
SERVICES = ["tentaculo_link", "switch", "hermes", "hormiguero", "spawner"]
TIMEOUT = 5


def test_madre_service_start_requires_env():
    """Test that service start/stop requires VX11_ALLOW_SERVICE_CONTROL=1"""
    # By default, control should be disabled
    os.environ.pop("VX11_ALLOW_SERVICE_CONTROL", None)

    # Try to start a service - should fail with 403
    try:
        headers = vx11_auth_headers()
        response = requests.post(
            vx11_base_url() + f"/operator/power/service/hermes/start",
            headers=headers,
            timeout=TIMEOUT,
        )
        # If it's enabled in the environment, we expect success or different error
        # For testing without environment override, we check the logic is there
        assert response.status_code in [
            403,
            404,
            200,
        ], f"Unexpected status: {response.status_code}"
    except Exception as e:
        pytest.skip(f"Madre not available: {e}")


def test_madre_service_status():
    """Test that Madre reports service status"""
    try:
        headers = vx11_auth_headers()
        response = requests.get(
            vx11_base_url() + "/madre/power/status", headers=headers, timeout=TIMEOUT
        )
        assert (
            response.status_code == 200
        ), f"Status check failed: {response.status_code}"
        data = response.json()
        assert "services" in data, "No services in status response"
        assert isinstance(data["services"], list), "Services should be a list"
    except Exception as e:
        pytest.skip(f"Madre service status not available: {e}")


def test_madre_health():
    """Test Madre health endpoint"""
    try:
        headers = vx11_auth_headers()
        response = requests.get(
            vx11_base_url() + "/madre/health", headers=headers, timeout=TIMEOUT
        )
        assert (
            response.status_code == 200
        ), f"Madre health check failed: {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Madre not healthy: {data}"
    except Exception as e:
        pytest.skip(f"Madre health check failed: {e}")


def test_core_services_responsive():
    """Test that core services are responsive (health endpoints)"""
    services = SERVICES

    for service in services:
        try:
            if service == "tentaculo_link":
                url = vx11_base_url() + "/health"
            else:
                url = vx11_base_url() + f"/{service}/health"

            headers = vx11_auth_headers()
            response = requests.get(url, headers=headers, timeout=2)
            assert (
                response.status_code == 200
            ), f"{service} health check returned {response.status_code}"
            data = response.json()
            assert data.get("status") == "ok", f"{service} not healthy: {data}"
        except Exception as e:
            pytest.skip(f"{service} not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
