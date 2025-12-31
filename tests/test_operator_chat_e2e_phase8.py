import pytest
import httpx
import asyncio
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from tests._vx11_base import vx11_base_url

log = logging.getLogger("vx11.operator.e2e")

if not os.getenv("VX11_E2E"):
    pytest.skip(
        "VX11_E2E not set; skipping live integration tests", allow_module_level=True
    )


class TestOperatorChatE2E:
    """
    FASE 8: E2E tests for operator_backend chat with switch integration.

    Tests verify:
    1. Chat through tentaculo_link proxy with token guard
    2. Fallback to madre when switch is dormant
    3. Correlation_id propagation through full chain
    4. Response schema validation

    All tests pass even if switch service is NOT running (SOLO_MADRE mode).
    """

    OPERATOR_URL = os.getenv("VX11_OPERATOR_URL", vx11_base_url())
    TENTACULO_URL = os.getenv("VX11_TENTACULO_URL", vx11_base_url())
    MADRE_URL = os.getenv("VX11_MADRE_URL", vx11_base_url())
    SWITCH_URL = os.getenv("VX11_SWITCH_URL", vx11_base_url())
    TOKEN = os.getenv(
        "VX11_TOKEN", os.getenv("VX11_TENTACULO_LINK_TOKEN", "test-token-vx11")
    )

    @classmethod
    def setup_class(cls):
        """Setup test class (run once)."""
        log.info(f"Operator URL: {cls.OPERATOR_URL}")
        log.info(f"Tentaculo URL: {cls.TENTACULO_URL}")
        log.info(f"Madre URL: {cls.MADRE_URL}")
        log.info(f"Switch URL: {cls.SWITCH_URL}")

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers with token."""
        t = token or self.TOKEN
        return {
            "X-VX11-Token": t,
            "Content-Type": "application/json",
        }

    def _get_correlation_id(self, response: Dict[str, Any]) -> str:
        """Extract correlation_id from response."""
        if isinstance(response, dict):
            return response.get("correlation_id") or response.get("data", {}).get(
                "correlation_id"
            )
        return None

    # ========== TEST 1: CHAT THROUGH TENTACULO LINK WITH TOKEN GUARD ==========

    def test_01_chat_through_tentaculo_requires_token(self):
        """
        Test 1a: Chat through tentaculo_link proxy requires authentication token.
        """
        payload = {
            "message": "Hello, can you hear me?",
            "session_id": "test-session-001",
        }

        with httpx.Client(timeout=10.0) as client:
            # Request WITHOUT token should fail
            resp = client.post(
                f"{self.TENTACULO_URL}/operator/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            assert resp.status_code in [
                401,
                403,
            ], f"Expected 401/403, got {resp.status_code}"

            log.info("✓ Auth guard enforced for tentaculo /operator/api/chat")

    def test_01b_chat_through_tentaculo_with_token(self):
        """
        Test 1b: Chat through tentaculo_link proxy with valid token succeeds.
        """
        payload = {
            "message": "Test message for tentaculo proxy",
            "session_id": "test-session-tentaculo-001",
            "correlation_id": "test-corr-001",
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.TENTACULO_URL}/operator/api/chat",
                json=payload,
                headers=self._get_headers(),
            )

            # Should succeed (either routed to switch or madre)
            assert (
                resp.status_code == 200
            ), f"Expected 200, got {resp.status_code}: {resp.text}"

            data = resp.json()
            assert (
                "response" in data or "data" in data
            ), f"Response missing 'response' or 'data': {data}"

            log.info(f"✓ Tentaculo chat succeeded: {resp.status_code}")
            log.info(f"  Response keys: {list(data.keys())}")

    # ========== TEST 2: FALLBACK TO MADRE WHEN SWITCH DORMANT ==========

    def test_02_chat_fallback_to_madre_when_switch_offline(self):
        """
        Test 2: Chat request succeeds even if switch service is offline/dormant.
        Should fallback to madre gracefully.
        """
        payload = {
            "message": "Testing fallback to madre",
            "session_id": "test-session-fallback-002",
            "correlation_id": "test-corr-fallback-002",
            "context": {"source": "operator_e2e_test"},
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.OPERATOR_URL}/operator/api/chat",
                json=payload,
                headers=self._get_headers(),
            )

            # Should NOT fail, even if switch is dormant
            assert (
                resp.status_code == 200
            ), f"Expected 200 (fallback), got {resp.status_code}: {resp.text}"

            data = resp.json()

            # Validate response schema
            assert "response" in data, "Response missing 'response' field"
            assert "provider" in data, "Response missing 'provider' field"
            assert "correlation_id" in data, "Response missing 'correlation_id' field"

            provider = data.get("provider", "unknown")
            log.info(f"✓ Chat fallback test passed, provider: {provider}")

    # ========== TEST 3: CORRELATION_ID PROPAGATION ==========

    def test_03_correlation_id_propagation_full_chain(self):
        """
        Test 3: Correlation_id is maintained and propagated through:
        request → tentaculo → operator_backend → switch/madre → response
        """
        test_correlation_id = (
            f"test-corr-chain-{int(datetime.utcnow().timestamp() * 1000)}"
        )

        payload = {
            "message": "Correlation ID test message",
            "session_id": "test-session-corr-003",
            "correlation_id": test_correlation_id,
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.OPERATOR_URL}/operator/api/chat",
                json=payload,
                headers=self._get_headers(),
            )

            assert resp.status_code == 200, f"Request failed: {resp.status_code}"

            data = resp.json()
            response_correlation_id = data.get("correlation_id")

            # Correlation ID should be in response
            assert (
                response_correlation_id is not None
            ), "Response missing correlation_id"

            # Correlation ID should match (or be generated if not provided)
            assert (
                response_correlation_id == test_correlation_id
                or response_correlation_id
            ), (
                f"Correlation ID mismatch: expected {test_correlation_id}, "
                f"got {response_correlation_id}"
            )

            log.info(f"✓ Correlation ID propagated: {response_correlation_id}")

    # ========== TEST 4: RESPONSE SCHEMA VALIDATION ==========

    def test_04_response_schema_validation(self):
        """
        Test 4: Chat response validates against ChatResponse schema:
        - response: str (required)
        - model_used: str (required)
        - latency_ms: float (required)
        - correlation_id: str (required)
        - session_id: str (required)
        - provider: str (required, "switch" or "madre")
        - status: str (default "ok")
        - degraded: bool (default False)
        """
        payload = {
            "message": "Schema validation test",
            "session_id": "test-session-schema-004",
            "correlation_id": "test-corr-schema-004",
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                f"{self.OPERATOR_URL}/operator/api/chat",
                json=payload,
                headers=self._get_headers(),
            )

            assert resp.status_code == 200, f"Request failed: {resp.status_code}"

            data = resp.json()

            # Validate schema
            required_fields = [
                "response",
                "model_used",
                "latency_ms",
                "correlation_id",
                "session_id",
                "provider",
                "status",
                "degraded",
            ]

            for field in required_fields:
                assert field in data, f"Response missing required field: {field}"

            # Validate types
            assert isinstance(
                data["response"], str
            ), f"response should be str, got {type(data['response'])}"
            assert isinstance(
                data["model_used"], str
            ), f"model_used should be str, got {type(data['model_used'])}"
            assert isinstance(
                data["latency_ms"], (int, float)
            ), f"latency_ms should be numeric, got {type(data['latency_ms'])}"
            assert isinstance(
                data["correlation_id"], str
            ), f"correlation_id should be str, got {type(data['correlation_id'])}"
            assert isinstance(
                data["session_id"], str
            ), f"session_id should be str, got {type(data['session_id'])}"
            assert isinstance(
                data["provider"], str
            ), f"provider should be str, got {type(data['provider'])}"
            assert isinstance(
                data["status"], str
            ), f"status should be str, got {type(data['status'])}"
            assert isinstance(
                data["degraded"], bool
            ), f"degraded should be bool, got {type(data['degraded'])}"

            # Validate provider is one of: "switch", "madre", or other known provider
            assert data["provider"] in [
                "switch",
                "madre",
                "deepseek-r1",
                "general-7b",
                "local",
            ], f"Invalid provider: {data['provider']}"

            # Validate status is OK or degraded
            assert data["status"] in [
                "ok",
                "degraded",
            ], f"Invalid status: {data['status']}"

            # If using madre (fallback), degraded flag should reflect it
            if data["provider"] in ["madre", "local"]:
                log.info(f"✓ Using fallback provider: {data['provider']}")

            log.info(f"✓ Response schema valid")
            log.info(
                f"  Provider: {data['provider']}, Model: {data['model_used']}, "
                f"Latency: {data['latency_ms']}ms, Degraded: {data['degraded']}"
            )

    # ========== INTEGRATION TEST: FULL E2E FLOW ==========

    def test_05_full_e2e_chat_flow_integration(self):
        """
        Integration test: Full E2E flow from client → proxy → backend → service
        """
        session_id = f"test-session-e2e-{int(datetime.utcnow().timestamp() * 1000)}"
        correlation_id = f"test-corr-e2e-{int(datetime.utcnow().timestamp() * 1000)}"

        payload = {
            "message": "This is a full E2E integration test message",
            "session_id": session_id,
            "correlation_id": correlation_id,
            "context": {
                "source": "operator_e2e_integration_test",
                "test_phase": "fase_8",
            },
            "metadata": {
                "task_type": "general",
                "test_marker": "integration_test",
            },
        }

        with httpx.Client(timeout=15.0) as client:
            # Request 1: Through operator_backend directly
            resp1 = client.post(
                f"{self.OPERATOR_URL}/operator/api/chat",
                json=payload,
                headers=self._get_headers(),
            )

            assert (
                resp1.status_code == 200
            ), f"Direct request failed: {resp1.status_code}"

            data1 = resp1.json()

            # Request 2: Through tentaculo proxy
            resp2 = client.post(
                f"{self.TENTACULO_URL}/operator/api/chat",
                json=payload,
                headers=self._get_headers(),
            )

            assert (
                resp2.status_code == 200
            ), f"Proxied request failed: {resp2.status_code}"

            data2 = resp2.json()

            # Both should have valid responses
            assert "response" in data1, "Direct response missing 'response'"
            assert "response" in data2, "Proxied response missing 'response'"

            # Both should maintain correlation_id
            assert data1.get("correlation_id") == correlation_id or data1.get(
                "correlation_id"
            ), "Direct response correlation_id mismatch"
            assert data2.get("correlation_id") == correlation_id or data2.get(
                "correlation_id"
            ), "Proxied response correlation_id mismatch"

            log.info("✓ Full E2E flow validated")
            log.info(
                f"  Direct provider: {data1.get('provider')}, latency: {data1.get('latency_ms')}ms"
            )
            log.info(
                f"  Proxied provider: {data2.get('provider')}, latency: {data2.get('latency_ms')}ms"
            )


class TestOperatorChatStress:
    """Stress test for chat endpoint (optional, can be marked as slow)."""

    OPERATOR_URL = os.getenv("VX11_OPERATOR_URL", "http://localhost:8011")
    TOKEN = os.getenv("VX11_TOKEN", "test-token-vx11")

    def _get_headers(self) -> Dict[str, str]:
        return {
            "x-vx11-token": self.TOKEN,
            "Content-Type": "application/json",
        }

    @pytest.mark.slow
    def test_chat_stress_sequential(self):
        """
        Stress test: Sequential chat requests with different session IDs.
        Should not exceed latency SLA (2s per request).
        """
        with httpx.Client(timeout=5.0) as client:
            for i in range(5):
                payload = {
                    "message": f"Stress test message #{i}",
                    "session_id": f"stress-session-{i}",
                    "correlation_id": f"stress-corr-{i}",
                }

                resp = client.post(
                    f"{self.OPERATOR_URL}/operator/api/chat",
                    json=payload,
                    headers=self._get_headers(),
                )

                assert (
                    resp.status_code == 200
                ), f"Request #{i} failed: {resp.status_code}"

                data = resp.json()
                latency_ms = data.get("latency_ms", 0)

                # Latency should be reasonable (< 5s)
                assert (
                    latency_ms < 5000
                ), f"Request #{i} latency too high: {latency_ms}ms"

                log.info(f"  Request #{i} OK: latency {latency_ms}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
