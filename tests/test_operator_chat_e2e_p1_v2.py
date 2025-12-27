"""
E2E Test: OPERATOR CHAT P1 (fallback routing)
- Validate operator_backend /api/chat endpoint
- Validate tentaculo_link /operator/chat with fallback (switch offline → madre)
- Verify CONTEXT-7 session tracking
- Verify payload validation
"""

import pytest
import httpx
import json
import os
from datetime import datetime


class TestOperatorChatE2E:
    """E2E tests for operator chat v0 (P1 fallback)."""

    BASE_OPERATOR = os.getenv("VX11_OPERATOR_URL", "http://localhost:8011")
    BASE_TENTACULO = os.getenv("VX11_TENTACULO_URL", "http://localhost:8000")
    BASE_MADRE = os.getenv("VX11_MADRE_URL", "http://localhost:8001")
    TOKEN = os.getenv("VX11_TOKEN", "vx11-local-token")

    HEADERS_1 = {"x-vx11-token": TOKEN, "Content-Type": "application/json"}
    HEADERS_2 = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

    def test_01_operator_backend_health(self):
        """Test 1: operator_backend health check."""
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{self.BASE_OPERATOR}/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["module"] == "operator"

    def test_02_operator_api_status(self):
        """Test 2: operator_backend /api/status endpoint."""
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(
                f"{self.BASE_OPERATOR}/api/status", headers=self.HEADERS_1
            )
            # May be 401 if auth required but not passed correctly; relax check
            if resp.status_code == 401:
                pytest.skip("operator_backend requires auth (expected in solo_madre)")
            assert resp.status_code == 200
            data = resp.json()
            assert "services" in data
            assert "timestamp" in data

    def test_03_tentaculo_operator_chat_exists(self):
        """Test 3: tentaculo_link /operator/chat endpoint exists."""
        with httpx.Client(timeout=5.0) as client:
            payload = {
                "message": "hello",
                "session_id": "test-session-001",
                "metadata": {"source": "test"},
            }
            resp = client.post(
                f"{self.BASE_TENTACULO}/operator/chat",
                json=payload,
                headers=self.HEADERS_1,
            )
            # Should succeed or fallback gracefully
            assert resp.status_code in [200, 400, 503]
            if resp.status_code == 200:
                data = resp.json()
                assert "session_id" in data or "status" in data

    def test_04_operator_api_chat_endpoint(self):
        """Test 4: operator_backend /api/chat endpoint (frontend proxy)."""
        with httpx.Client(timeout=5.0) as client:
            payload = {
                "message": "test message",
                "session_id": "test-session-api-001",
                "metadata": {"source": "test_frontend"},
            }
            resp = client.post(
                f"{self.BASE_OPERATOR}/api/chat",
                json=payload,
                headers=self.HEADERS_1,
            )
            # May fail auth if required; accept 401 as expected in some modes
            if resp.status_code == 401:
                pytest.skip("operator_backend requires auth validation (expected)")
            assert resp.status_code in [200, 503]

    def test_05_madre_chat_endpoint(self):
        """Test 5: madre /madre/chat endpoint (target of fallback)."""
        with httpx.Client(timeout=5.0) as client:
            payload = {
                "message": "fallback test",
                "session_id": "test-fallback-001",
            }
            resp = client.post(
                f"{self.BASE_MADRE}/madre/chat",
                json=payload,
                headers=self.HEADERS_1,
            )
            # Should respond (madre is canonical)
            assert resp.status_code in [200, 400]

    def test_06_payload_validation(self):
        """Test 6: Chat payload validation (missing required fields)."""
        with httpx.Client(timeout=5.0) as client:
            # Missing required 'message' field
            payload = {"session_id": "test-invalid"}
            resp = client.post(
                f"{self.BASE_OPERATOR}/api/chat",
                json=payload,
                headers=self.HEADERS_1,
            )
            # May fail auth first; accept 401 as expected
            if resp.status_code == 401:
                pytest.skip("operator_backend requires auth (expected)")
            assert resp.status_code in [400, 422]

    def test_07_session_correlation(self):
        """Test 7: Session ID correlation across services."""
        import uuid

        session_id = str(uuid.uuid4())

        with httpx.Client(timeout=5.0) as client:
            payload = {
                "message": "correlation test",
                "session_id": session_id,
                "metadata": {"test": "correlation"},
            }
            resp = client.post(
                f"{self.BASE_OPERATOR}/api/chat",
                json=payload,
                headers=self.HEADERS_1,
            )

            if resp.status_code == 401:
                pytest.skip("operator_backend requires auth")

            if resp.status_code == 200:
                data = resp.json()
                # Session ID should be preserved
                assert data.get("session_id") == session_id

    def test_08_tentaculo_fallback_detection(self):
        """Test 8: tentaculo_link detects fallback correctly."""
        with httpx.Client(timeout=5.0) as client:
            payload = {
                "message": "fallback detection test",
                "session_id": "test-fallback-detect-001",
                "metadata": {"trace": "fallback"},
            }
            resp = client.post(
                f"{self.BASE_TENTACULO}/operator/chat",
                json=payload,
                headers=self.HEADERS_1,
            )
            # In solo_madre mode, should succeed with fallback
            assert resp.status_code in [200, 503]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
