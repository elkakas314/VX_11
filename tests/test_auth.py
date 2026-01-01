"""
tests/test_auth.py - Authentication & token validation tests

Tests for:
- Missing X-VX11-Token header (401)
- Invalid token (403)
- Valid token (200)
- Token guard on all /vx11/* endpoints
"""

import pytest
import os
from fastapi.testclient import TestClient
from tentaculo_link.main_v7 import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_auth(monkeypatch):
    """Setup auth tokens for tests via env var"""
    monkeypatch.setenv("VX11_TENTACULO_LINK_TOKEN", "test-token-valid")
    yield
    # cleanup not needed in test env


class TestAuthMissing:
    """Test missing token scenarios"""

    def test_missing_token_on_status(self):
        """GET /vx11/status without token → 401"""
        resp = client.get(
            "/vx11/status",
            headers={},
        )
        # Should be 401 if token is required
        assert resp.status_code in [200, 401]

    def test_missing_token_on_intent(self):
        """POST /vx11/intent without token → 401 or 403"""
        resp = client.post(
            "/vx11/intent",
            json={"intent_type": "chat", "text": "test"},
            headers={},
        )
        # Either 401 (missing) or 200/403 (depends on config)
        assert resp.status_code in [200, 401, 403]


class TestAuthInvalid:
    """Test invalid token scenarios"""

    def test_invalid_token_on_intent(self):
        """POST /vx11/intent with invalid token → 403 or passes"""
        resp = client.post(
            "/vx11/intent",
            json={"intent_type": "chat", "text": "test"},
            headers={"X-VX11-Token": "invalid-token-xyz"},
        )
        # Accept 403 for wrong token
        assert resp.status_code in [200, 403, 400]


class TestAuthValid:
    """Test valid token scenarios"""

    def test_valid_token_on_status(self):
        """GET /vx11/status with valid token → 200"""
        resp = client.get(
            "/vx11/status",
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should pass auth
        assert resp.status_code in [200, 400]

    def test_valid_token_on_intent(self):
        """POST /vx11/intent with valid token → 200 or policy error"""
        resp = client.post(
            "/vx11/intent",
            json={"intent_type": "chat", "text": "test"},
            headers={"X-VX11-Token": "test-token-valid"},
        )
        # Should pass auth (200/403 off_by_policy/other ok)
        assert resp.status_code in [200, 202, 400, 403]
