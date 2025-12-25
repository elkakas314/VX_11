"""
Test Suite: Unified Response Schema (Commit 1)

Validates canonical envelope for all /api/* endpoints:
- {ok, request_id, route_taken, degraded, errors[], data}
"""

import pytest
import json
import sys
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, ValidationError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import schema models
from operator_backend.backend.routers.canonical_api import UnifiedResponse, ErrorInfo


class TestUnifiedResponseSchema:
    """Test unified response schema validation."""

    def test_valid_unified_response_ok(self):
        """Test valid successful response."""
        response_data = {
            "ok": True,
            "request_id": "abc123",
            "route_taken": "operator_backend",
            "degraded": False,
            "errors": [],
            "data": {"status": "ok"},
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is True
        assert resp.request_id == "abc123"
        assert resp.route_taken == "operator_backend"
        assert resp.degraded is False
        assert len(resp.errors) == 0

    def test_valid_unified_response_degraded(self):
        """Test valid degraded response."""
        response_data = {
            "ok": False,
            "request_id": "def456",
            "route_taken": "degraded",
            "degraded": True,
            "errors": [{"step": "tentaculo_link", "hint": "Connection timeout (5s)"}],
            "data": None,
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is False
        assert resp.request_id == "def456"
        assert resp.route_taken == "degraded"
        assert resp.degraded is True
        assert len(resp.errors) == 1
        assert resp.errors[0].step == "tentaculo_link"

    def test_valid_unified_response_error_array(self):
        """Test response with multiple errors."""
        response_data = {
            "ok": False,
            "request_id": "ghi789",
            "route_taken": "degraded",
            "degraded": True,
            "errors": [
                {"step": "tentaculo_link", "hint": "Connection refused"},
                {"step": "madre", "hint": "Not reachable"},
            ],
            "data": None,
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is False
        assert len(resp.errors) == 2

    def test_schema_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        incomplete_data = {
            "ok": True,
            # Missing request_id
            "route_taken": "operator_backend",
        }
        with pytest.raises(ValidationError):
            UnifiedResponse(**incomplete_data)

    def test_schema_json_serialization(self):
        """Test JSON serialization of unified response."""
        response_data = {
            "ok": True,
            "request_id": "json123",
            "route_taken": "operator_backend",
            "degraded": False,
            "errors": [],
            "data": {"version": "7.0"},
        }
        resp = UnifiedResponse(**response_data)
        json_str = resp.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["ok"] is True
        assert parsed["request_id"] == "json123"
        assert parsed["data"]["version"] == "7.0"

    def test_error_info_model(self):
        """Test ErrorInfo model."""
        error = ErrorInfo(step="service_x", hint="Timed out after 2s")
        assert error.step == "service_x"
        assert error.hint == "Timed out after 2s"

    def test_route_taken_values(self):
        """Test that route_taken can be set to expected values."""
        for route in ["operator_backend", "tentaculo_link", "madre", "degraded"]:
            response_data = {
                "ok": True,
                "request_id": f"route_{route}",
                "route_taken": route,
                "degraded": False,
                "errors": [],
                "data": None,
            }
            resp = UnifiedResponse(**response_data)
            assert resp.route_taken == route


class TestResponseEnvelopeContract:
    """Test contract of unified envelope."""

    def test_ok_false_implies_errors_present(self):
        """Test that when ok=False, errors array should be populated (best practice)."""
        response_data = {
            "ok": False,
            "request_id": "contract1",
            "route_taken": "degraded",
            "degraded": True,
            "errors": [{"step": "backend", "hint": "Service unavailable"}],
            "data": None,
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is False
        assert len(resp.errors) > 0  # Best practice: errors should explain why ok=False

    def test_data_present_when_ok_true(self):
        """Test that when ok=True, data field typically contains result."""
        response_data = {
            "ok": True,
            "request_id": "contract2",
            "route_taken": "operator_backend",
            "degraded": False,
            "errors": [],
            "data": {"result": "success"},
        }
        resp = UnifiedResponse(**response_data)
        assert resp.ok is True
        assert resp.data is not None

    def test_degraded_false_means_not_fallback(self):
        """Test that degraded=False means primary route was used."""
        response_data = {
            "ok": True,
            "request_id": "contract3",
            "route_taken": "tentaculo_link",
            "degraded": False,
            "errors": [],
            "data": {"status": "primary"},
        }
        resp = UnifiedResponse(**response_data)
        assert resp.degraded is False
        assert resp.route_taken == "tentaculo_link"  # Not "degraded"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
