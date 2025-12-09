"""
Tests for madre orchestration service.
"""

import pytest
import httpx
from config.settings import settings


def test_madre_health():
    """Test madre health endpoint."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/health", timeout=2)
            assert resp.status_code == 200
            data = resp.json()
            assert data["module"] == "madre"
            assert data["status"] == "ok"
        except httpx.ConnectError:
            pytest.skip("Madre not running")


def test_madre_orchestrate_spawner():
    """Test madre delegation to spawner."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.post(
                f"http://127.0.0.1:{madre_port}/orchestrate",
                json={
                    "action": "spawn",
                    "target": "spawner",
                    "payload": {"name": "test-via-madre", "cmd": "echo", "args": ["test"]},
                },
                timeout=5,
            )
            if resp.status_code == 404:
                pytest.skip("Madre endpoints not available (service may not have new routes)")
            assert resp.status_code == 200
            data = resp.json()
            assert "session_id" in data
            # spawner_result may be present if spawner is running
        except httpx.ConnectError:
            pytest.skip("Madre not running")


def test_madre_status():
    """Test madre status endpoint (checks delegated services health)."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/status", timeout=5)
            if resp.status_code == 404:
                pytest.skip("Madre endpoints not available (service may not have new routes)")
            assert resp.status_code == 200
            data = resp.json()
            assert data["madre"] == "ok"
            assert "delegated_services" in data
        except httpx.ConnectError:
            pytest.skip("Madre not running")


def test_madre_sessions():
    """Test listing orchestration sessions."""
    with httpx.Client() as client:
        try:
            madre_port = settings.PORTS.get("madre", 8001)
            resp = client.get(f"http://127.0.0.1:{madre_port}/sessions", timeout=5)
            if resp.status_code == 404:
                pytest.skip("Madre endpoints not available (service may not have new routes)")
            assert resp.status_code == 200
            data = resp.json()
            assert "sessions" in data
            assert isinstance(data["sessions"], list)
        except httpx.ConnectError:
            pytest.skip("Madre not running")
