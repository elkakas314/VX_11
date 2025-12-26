"""
Test Suite: /api/chat Enhanced with Unified Response (Commit 2)

Validates unified response schema in chat endpoint.
"""

import pytest
from operator_backend.backend.routers.canonical_api import UnifiedResponse, ErrorInfo


class TestChatUnifiedResponse:
    """Test /api/chat returns unified response envelope."""

    def test_chat_response_schema_ok(self):
        """Test successful chat response with unified envelope."""
        response_data = {
            "ok": True,
            "request_id": "chat001",
            "route_taken": "tentaculo_link",
            "degraded": False,
            "errors": [],
            "data": {
                "session_id": "sess-123",
                "response": "Hello, this is the answer!",
                "tool_calls": None,
            },
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is True
        assert resp.request_id == "chat001"
        assert resp.route_taken == "tentaculo_link"
        assert resp.degraded is False
        # ensure data exists before subscripting; support dict or object-style access
        assert resp.data is not None
        if isinstance(resp.data, dict):
            assert resp.data["session_id"] == "sess-123"
        else:
            assert getattr(resp.data, "session_id", None) == "sess-123"

    def test_chat_response_degraded(self):
        """Test degraded chat response."""
        response_data = {
            "ok": True,
            "request_id": "chat002",
            "route_taken": "degraded",
            "degraded": True,
            "errors": [{"step": "tentaculo_link", "hint": "Connection timeout"}],
            "data": {
                "session_id": "sess-456",
                "response": "[DEGRADED] Received: Hello. Services not fully available.",
                "tool_calls": None,
            },
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is True  # ALWAYS persist and return ok=true
        assert resp.degraded is True
        assert resp.route_taken == "degraded"
        assert len(resp.errors) == 1

    def test_chat_response_error_validation(self):
        """Test chat response when validation fails."""
        response_data = {
            "ok": False,
            "request_id": "chat003",
            "route_taken": "operator_backend",
            "degraded": False,
            "errors": [{"step": "input_validation", "hint": "message is required"}],
            "data": None,
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is False
        assert resp.errors[0].step == "input_validation"

    def test_chat_response_error_message_too_long(self):
        """Test chat response when message exceeds 4KB limit."""
        response_data = {
            "ok": False,
            "request_id": "chat004",
            "route_taken": "operator_backend",
            "degraded": False,
            "errors": [
                {
                    "step": "input_validation",
                    "hint": "message too long (max 4KB, got 5000 bytes)",
                }
            ],
            "data": None,
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is False
        assert "too long" in resp.errors[0].hint

    def test_chat_response_always_persists(self):
        """Test that chat message is persisted even in degraded mode."""
        # Degraded mode returns ok=true because message was persisted
        response_data = {
            "ok": True,
            "request_id": "chat005",
            "route_taken": "degraded",
            "degraded": True,
            "errors": [{"step": "tentaculo_link", "hint": "Service down"}],
            "data": {
                "session_id": "sess-789",
                "response": "[DEGRADED] Fallback response",
                "tool_calls": None,
            },
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is True
        assert resp.data is not None
        assert resp.data["session_id"] == "sess-789"

    def test_chat_response_route_taken_tracking(self):
        """Test route_taken field tracks which service handled request."""
        for route in ["operator_backend", "tentaculo_link", "degraded"]:
            response_data = {
                "ok": True,
                "request_id": f"chat_route_{route}",
                "route_taken": route,
                "degraded": route == "degraded",
                "errors": (
                    []
                    if route != "degraded"
                    else [{"step": "routing", "hint": "fallback"}]
                ),
                "data": {"session_id": "test", "response": "ok", "tool_calls": None},
            }
            resp = UnifiedResponse(**response_data)
            assert resp.route_taken == route


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
