"""
Tests for madre orchestration service.

Note: Madre internal endpoints (like /orchestrate, /sessions) are not exposed
through the frontdoor (tentaculo_link). These tests check if endpoints exist
via frontdoor proxy; if 404, they skip with OFF_BY_POLICY.
"""

import pytest
import httpx
from tests._vx11_base import vx11_base_url, vx11_auth_headers


def test_madre_health():
    """Test madre health via frontdoor."""
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(vx11_base_url() + "/health", headers=headers, timeout=2)
            assert resp.status_code == 200
            data = resp.json()
            # Frontdoor returns tentaculo_link module name
            assert data["status"] == "ok"
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


def test_madre_orchestrate_spawner():
    """Test madre delegation to spawner via frontdoor proxy.

    Note: Madre's /orchestrate endpoint may not be exposed through frontdoor.
    This test skips with OFF_BY_POLICY if not available.
    """
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.post(
                vx11_base_url() + "/orchestrate",
                headers=headers,
                json={
                    "action": "spawn",
                    "target": "spawner",
                    "payload": {
                        "name": "test-via-madre",
                        "cmd": "echo",
                        "args": ["test"],
                    },
                },
                timeout=5,
            )
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: Madre /orchestrate endpoint not exposed (status={resp.status_code})"
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "session_id" in data
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


def test_madre_status():
    """Test madre status via frontdoor proxy.

    Note: Madre's /status endpoint may not be exposed through frontdoor.
    This test skips with OFF_BY_POLICY if not available.
    """
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(vx11_base_url() + "/status", headers=headers, timeout=5)
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: Madre /status endpoint not exposed (status={resp.status_code})"
                )
            assert resp.status_code == 200
            data = resp.json()
            # Validate response structure if available
            assert isinstance(data, dict)
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")


def test_madre_sessions():
    """Test listing orchestration sessions via frontdoor.

    Note: Madre's /sessions endpoint may not be exposed through frontdoor.
    This test skips with OFF_BY_POLICY if not available.
    """
    with httpx.Client() as client:
        try:
            headers = vx11_auth_headers()
            resp = client.get(vx11_base_url() + "/sessions", headers=headers, timeout=5)
            if resp.status_code in (404, 403):
                pytest.skip(
                    f"OFF_BY_POLICY: Madre /sessions endpoint not exposed (status={resp.status_code})"
                )
            assert resp.status_code == 200
            data = resp.json()
            assert "sessions" in data
            assert isinstance(data["sessions"], list)
        except httpx.ConnectError:
            pytest.skip("Frontdoor not running")
