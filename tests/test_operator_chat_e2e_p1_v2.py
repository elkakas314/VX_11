"""
E2E Test: OPERATOR CHAT P1 v2
"""

import pytest
import httpx
import os


if not os.getenv("VX11_E2E"):
    pytest.skip("VX11_E2E not set; skipping live integration tests", allow_module_level=True)


class TestOperatorChatE2E:
    BASE_OPERATOR = os.getenv("VX11_OPERATOR_URL", "http://localhost:8011")
    BASE_TENTACULO = os.getenv("VX11_TENTACULO_URL", "http://localhost:8000")
    TOKEN = os.getenv("VX11_TOKEN", "vx11-local-token")

    HEADERS = {"X-VX11-Token": TOKEN, "Content-Type": "application/json"}

    def test_01_operator_backend_health(self):
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{self.BASE_OPERATOR}/operator/api/health", headers=self.HEADERS)
            if resp.status_code == 401:
                pytest.skip("operator_backend requires auth")
            assert resp.status_code == 200

    def test_02_operator_api_status(self):
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{self.BASE_OPERATOR}/operator/api/status", headers=self.HEADERS)
            if resp.status_code == 401:
                pytest.skip("operator_backend requires auth")
            assert resp.status_code in [200, 403]

    def test_03_tentaculo_operator_chat_exists(self):
        with httpx.Client(timeout=5.0) as client:
            payload = {"message": "hello", "session_id": "test-session-001"}
            resp = client.post(
                f"{self.BASE_TENTACULO}/operator/chat", json=payload, headers=self.HEADERS
            )
            assert resp.status_code in [200, 400, 503]

    def test_04_operator_api_chat_endpoint(self):
        with httpx.Client(timeout=5.0) as client:
            payload = {"message": "test", "session_id": "test-session-api-001"}
            resp = client.post(
                f"{self.BASE_OPERATOR}/operator/api/chat", json=payload, headers=self.HEADERS
            )
            if resp.status_code == 401:
                pytest.skip("operator_backend requires auth validation")
            assert resp.status_code in [200, 403, 503]
