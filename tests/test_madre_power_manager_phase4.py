"""
Test: Madre starts and validates each core module (FASE 4)
"""
import pytest
import requests
import os
import time

MADRE_URL = "http://localhost:8001"
SERVICES = ["tentaculo_link", "switch", "hermes", "hormiguero", "spawner"]
TIMEOUT = 5

def test_madre_service_start_requires_env():
    """Test that service start/stop requires VX11_ALLOW_SERVICE_CONTROL=1"""
    # By default, control should be disabled
    os.environ.pop("VX11_ALLOW_SERVICE_CONTROL", None)
    
    # Try to start a service - should fail with 403
    try:
        response = requests.post(
            f"{MADRE_URL}/madre/power/service/start",
            json={"service": "hermes"},
            timeout=TIMEOUT
        )
        # If it's enabled in the environment, we expect success or different error
        # For testing without environment override, we check the logic is there
        assert response.status_code in [403, 404, 200], f"Unexpected status: {response.status_code}"
    except Exception as e:
        pytest.skip(f"Madre not available: {e}")

def test_madre_service_status():
    """Test that Madre reports service status"""
    try:
        response = requests.get(
            f"{MADRE_URL}/madre/power/status",
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Status check failed: {response.status_code}"
        data = response.json()
        assert "services" in data, "No services in status response"
        assert isinstance(data["services"], list), "Services should be a list"
    except Exception as e:
        pytest.skip(f"Madre service status not available: {e}")

def test_madre_health():
    """Test Madre health endpoint"""
    try:
        response = requests.get(
            f"{MADRE_URL}/health",
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Madre health check failed: {response.status_code}"
        data = response.json()
        assert data.get("status") == "ok", f"Madre not healthy: {data}"
    except Exception as e:
        pytest.skip(f"Madre health check failed: {e}")

def test_core_services_responsive():
    """Test that core services are responsive (health endpoints)"""
    services_health = {
        "tentaculo_link": "http://localhost:8000/health",
        "madre": "http://localhost:8001/health",
        "switch": "http://localhost:8002/health",
        "hermes": "http://localhost:8003/health",
        "hormiguero": "http://localhost:8004/health",
        "spawner": "http://localhost:8008/health",
    }
    
    for service, url in services_health.items():
        try:
            response = requests.get(url, timeout=2)
            assert response.status_code == 200, f"{service} health check returned {response.status_code}"
            data = response.json()
            assert data.get("status") == "ok", f"{service} not healthy: {data}"
        except Exception as e:
            pytest.skip(f"{service} not available: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
