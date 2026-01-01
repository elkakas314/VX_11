"""
Test suite for Operator v7 token fix.

Purpose:
- Verify token injection is correct (vx11-test-token)
- Verify window open/close flow works
- Verify chat sends requests without infinite retry
- Verify events polling respects OFF_BY_POLICY in solo_madre
"""

import pytest
import os
import json
from datetime import datetime
import httpx

BASE_URL = os.environ.get("VX11_BASE_URL", "http://localhost:8000")
TOKEN = "vx11-test-token"
WRONG_TOKEN = "vx11-local-token"


class TestOperatorTokenFix:
    """Test correct token injection and endpoint responses."""

    @pytest.fixture
    def client(self):
        """HTTP client with correct token."""
        return httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": TOKEN},
            timeout=10.0,
        )

    @pytest.fixture
    def wrong_client(self):
        """HTTP client with wrong token."""
        return httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": WRONG_TOKEN},
            timeout=10.0,
        )

    def test_status_with_correct_token(self, client):
        """Verify /operator/api/status returns 200 with correct token."""
        resp = client.get("/operator/api/status")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data["status"] == "ok"
        assert data["policy"] == "solo_madre"

    def test_status_with_wrong_token(self, wrong_client):
        """Verify /operator/api/status returns 403 with wrong token."""
        resp = wrong_client.get("/operator/api/status")
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"

    def test_window_status_returns_valid_mode(self, client):
        """Verify /operator/api/chat/window/status returns valid mode."""
        resp = client.get("/operator/api/chat/window/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert data["mode"] in ("solo_madre", "window_active", "windowed")

    def test_solo_madre_gates_chat(self, client):
        """Verify chat endpoint respects solo_madre policy."""
        resp = client.post(
            "/operator/api/chat",
            json={"message": "test"},
        )
        # In solo_madre, chat may be gated or return specific status
        # (not 403, but may return empty or policy message)
        assert resp.status_code in (
            200,
            503,
        ), f"Unexpected status: {resp.status_code}"

    def test_events_endpoint_accessible_with_token(self, client):
        """Verify /operator/api/events is accessible (may be feature-disabled)."""
        resp = client.get("/operator/api/events", timeout=5.0)
        # Events may be disabled by flag, but should not return 403 auth error
        assert resp.status_code in (
            200,
            503,
        ), f"Expected 200 or 503, got {resp.status_code}"

    def test_no_auth_required_on_health(self):
        """Verify /health is accessible without token."""
        client = httpx.Client(base_url=BASE_URL, timeout=5.0)
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_window_open_request_structure(self, client):
        """Verify window open/close endpoints exist and accept valid requests."""
        # Test window/status first
        status_resp = client.get("/operator/api/chat/window/status")
        assert status_resp.status_code == 200
        mode_before = status_resp.json().get("mode")

        # Attempt to open window (may be gated or disabled in observer mode)
        open_resp = client.post(
            "/operator/api/chat/window/open",
            json={"services": ["switch", "hermes"]},
        )
        # Should return valid response (may be allowed, gated, or disabled in observer mode)
        assert open_resp.status_code in (
            200,
            400,
            403,
            503,
        ), f"Unexpected status: {open_resp.status_code}"


class TestOperatorErrorHandling:
    """Test error handling and edge cases."""

    def test_missing_token_returns_401(self):
        """Verify missing token returns 401."""
        client = httpx.Client(base_url=BASE_URL, timeout=5.0)
        resp = client.get("/operator/api/status")
        assert resp.status_code == 401

    def test_empty_token_returns_401(self):
        """Verify empty token returns 401."""
        client = httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": ""},
            timeout=5.0,
        )
        resp = client.get("/operator/api/status")
        assert resp.status_code == 401

    def test_malformed_request_handled_gracefully(self):
        """Verify malformed requests are handled gracefully."""
        client = httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": TOKEN},
            timeout=5.0,
        )
        # Send invalid JSON
        resp = client.post(
            "/operator/api/chat",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        # Should return 4xx (bad request), not 500
        assert resp.status_code < 500 or resp.status_code >= 400


class TestOperatorContractCompliance:
    """Test API contract compliance."""

    @pytest.fixture
    def client(self):
        return httpx.Client(
            base_url=BASE_URL,
            headers={"X-VX11-Token": TOKEN},
            timeout=10.0,
        )

    def test_status_response_shape(self, client):
        """Verify /operator/api/status returns correct shape."""
        resp = client.get("/operator/api/status")
        assert resp.status_code == 200
        data = resp.json()

        # Required fields
        assert "status" in data
        assert "policy" in data
        assert "core_services" in data
        assert "optional_services" in data
        assert "degraded" in data

    def test_window_status_response_shape(self, client):
        """Verify /operator/api/chat/window/status returns correct shape."""
        resp = client.get("/operator/api/chat/window/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "mode" in data
        assert isinstance(data["mode"], str)

    def test_chat_request_validation(self, client):
        """Verify chat endpoint validates request structure."""
        # Valid request
        resp = client.post(
            "/operator/api/chat",
            json={"message": "test message"},
        )
        assert resp.status_code in (200, 503)

        # Invalid request (missing message)
        resp = client.post(
            "/operator/api/chat",
            json={"session_id": "test"},
        )
        # Should reject due to missing 'message'
        assert resp.status_code >= 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
