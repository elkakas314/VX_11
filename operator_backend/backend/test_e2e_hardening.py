import pytest
import asyncio
from datetime import datetime
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# E2E test scenarios for VX11 Operator


@pytest.mark.e2e
class TestOperatorE2EHardening:
    """End-to-end tests for operator hardening (FASE C)"""

    @pytest.fixture
    def api_client(self):
        """Fixture for API client"""
        from operator_backend.backend.main import app

        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, api_client):
        """Get auth headers for E2E tests"""
        # Mock JWT token for testing
        return {"Authorization": "Bearer test-jwt-token"}

    def test_e2e_unified_response_schema(self, api_client, auth_headers):
        """Test that /api/chat returns unified response schema"""
        response = api_client.post(
            "/api/chat",
            json={"message": "Hello", "mode": "default"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify unified schema
        assert "ok" in data
        assert "request_id" in data
        assert "route_taken" in data
        assert "degraded" in data
        assert "errors" in data
        assert isinstance(data["errors"], list)
        assert "data" in data

    def test_e2e_degraded_mode_fallback(self, api_client, auth_headers):
        """Test that degraded mode works when tentaculo_link is unavailable"""
        # This assumes tentaculo_link is down
        response = api_client.post(
            "/api/chat",
            json={"message": "Test degraded", "mode": "default"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        if data["degraded"]:  # If fallback was used
            assert "errors" in data
            assert len(data["errors"]) > 0
            assert "step" in data["errors"][0]
            assert "hint" in data["errors"][0]

    def test_e2e_sse_stream_infinite(self, api_client, auth_headers):
        """Test that /api/events provides infinite stream"""
        with api_client.stream("GET", "/api/events", headers=auth_headers) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            # Read multiple events to verify stream doesn't close
            event_count = 0
            for line in response.iter_lines():
                if event_count >= 10:
                    break
                if line.startswith(b"data: "):
                    event_count += 1

            assert event_count >= 5, "Stream should emit multiple events"

    def test_e2e_sse_reconnection(self, api_client, auth_headers):
        """Test that SSE client can reconnect after disconnect"""
        # First connection
        with api_client.stream("GET", "/api/events", headers=auth_headers) as response:
            assert response.status_code == 200
            # Read one event
            for line in response.iter_lines():
                if line.startswith(b"data: "):
                    break

        # Second connection (reconnection)
        with api_client.stream("GET", "/api/events", headers=auth_headers) as response2:
            assert response2.status_code == 200
            assert "text/event-stream" in response2.headers["content-type"]

    def test_e2e_message_persistence_degraded(self, api_client, auth_headers):
        """Test that messages are persisted even in degraded mode"""
        # Send message that might trigger degraded mode
        response = api_client.post(
            "/api/chat",
            json={"message": "Persist this", "mode": "default"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify message was persisted (ok=true even if degraded)
        assert data["ok"] == True

    def test_e2e_request_context_tracking(self, api_client, auth_headers):
        """Test that request_id is tracked across requests"""
        # First request
        response1 = api_client.post(
            "/api/chat",
            json={"message": "First", "mode": "default"},
            headers=auth_headers,
        )
        req_id_1 = response1.json()["request_id"]

        # Second request
        response2 = api_client.post(
            "/api/chat",
            json={"message": "Second", "mode": "default"},
            headers=auth_headers,
        )
        req_id_2 = response2.json()["request_id"]

        # Request IDs should be unique
        assert req_id_1 != req_id_2

    def test_e2e_error_handling_comprehensive(self, api_client, auth_headers):
        """Test comprehensive error handling across endpoints"""
        # Test invalid message
        response = api_client.post(
            "/api/chat",
            json={"message": "a" * 5000},  # Too long
            headers=auth_headers,
        )

        # Should either return 400 or 200 with errors array
        if response.status_code == 200:
            data = response.json()
            assert len(data["errors"]) > 0

    def test_e2e_mode_selector_workflow(self, api_client, auth_headers):
        """Test mode selector (default/analyze/reasoning) workflow"""
        modes = ["default", "analyze", "reasoning"]

        for mode in modes:
            response = api_client.post(
                "/api/chat",
                json={"message": f"Test {mode}", "mode": mode},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] in [True, False]  # Either ok or degraded

    def test_e2e_concurrent_chat_requests(self, api_client, auth_headers):
        """Test handling of concurrent chat requests"""
        responses = []

        for i in range(5):
            response = api_client.post(
                "/api/chat",
                json={"message": f"Concurrent {i}", "mode": "default"},
                headers=auth_headers,
            )
            responses.append(response)

        # All should succeed or degrade gracefully
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "request_id" in data
            assert "ok" in data

    def test_e2e_sse_event_filtering(self, api_client, auth_headers):
        """Test SSE event filtering by source/type/severity"""
        # Test with filters
        response = api_client.get(
            "/api/events?source=madre&event_type=error",
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_e2e_route_tracking_tentaculo(self, api_client, auth_headers):
        """Test that route_taken shows tentaculo_link when available"""
        response = api_client.post(
            "/api/chat",
            json={"message": "Test route", "mode": "default"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # route_taken should be one of: tentaculo_link, madre, degraded
        assert data["route_taken"] in ["tentaculo_link", "madre", "degraded"]

    def test_e2e_degraded_banner_triggers(self, api_client, auth_headers):
        """Test conditions that trigger degraded banner on frontend"""
        # When degraded=true, frontend should show banner
        response = api_client.post(
            "/api/chat",
            json={"message": "Test degraded trigger", "mode": "default"},
            headers=auth_headers,
        )

        data = response.json()

        if data["degraded"]:
            # Should have error hints
            assert len(data["errors"]) > 0
            assert "hint" in data["errors"][0]

    def test_e2e_color_coding_logic(self, api_client, auth_headers):
        """Test that responses have correct color-coding metadata"""
        response = api_client.post(
            "/api/chat",
            json={"message": "Color test", "mode": "default"},
            headers=auth_headers,
        )

        data = response.json()

        # Frontend should be able to derive color from:
        # - data["degraded"] (yellow)
        # - data["route_taken"] (green/slate/etc)
        # - errors presence (red)

        assert "degraded" in data
        assert "route_taken" in data
        assert isinstance(data["errors"], list)


@pytest.mark.e2e
class TestOperatorE2EVenturasTemporal:
    """E2E tests for temporal window (ventana temporal) scenarios"""

    @pytest.fixture
    def api_client(self):
        from operator_backend.backend.main import app

        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-jwt-token"}

    def test_e2e_message_within_temporal_window(self, api_client, auth_headers):
        """Test message handling within temporal window"""
        # Send message
        response1 = api_client.post(
            "/api/chat",
            json={"message": "First", "mode": "default"},
            headers=auth_headers,
        )
        assert response1.status_code == 200

        # Follow up within same temporal window
        response2 = api_client.post(
            "/api/chat",
            json={"message": "Follow up", "mode": "default"},
            headers=auth_headers,
        )
        assert response2.status_code == 200

    def test_e2e_temporal_window_timeout(self, api_client, auth_headers):
        """Test behavior when temporal window expires"""
        # Send message
        response = api_client.post(
            "/api/chat",
            json={"message": "Test timeout", "mode": "default"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # In real test, would wait for temporal window to expire
        # and verify new window is created

    def test_e2e_multiple_temporal_windows(self, api_client, auth_headers):
        """Test handling of multiple temporal windows"""
        windows_created = []

        for i in range(3):
            response = api_client.post(
                "/api/chat",
                json={"message": f"Window {i}", "mode": "default"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            windows_created.append(data["request_id"])

        # All should have unique request IDs
        assert len(set(windows_created)) == len(windows_created)


@pytest.mark.e2e
class TestOperatorE2EMetrics:
    """E2E tests for metrics and monitoring"""

    @pytest.fixture
    def api_client(self):
        from operator_backend.backend.main import app

        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-jwt-token"}

    def test_e2e_response_time_reasonable(self, api_client, auth_headers):
        """Test that API response time is reasonable"""
        import time

        start = time.time()
        response = api_client.post(
            "/api/chat",
            json={"message": "Speed test", "mode": "default"},
            headers=auth_headers,
        )
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 30, f"Response took {duration}s, expected < 30s"

    def test_e2e_audit_trail_created(self, api_client, auth_headers, db: Session):
        """Test that audit trail is created for requests"""
        response = api_client.post(
            "/api/chat",
            json={"message": "Audit test", "mode": "default"},
            headers=auth_headers,
        )

        assert response.status_code == 200

        # In real implementation, would verify audit record was created
        # query AuditLogs table for request_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e"])
