"""
Test Suite: Event Validation Middleware
========================================

Tests the canonical event validation pipeline in Tentáculo Link.
Validates:
- Schema compliance
- Required fields
- Type validation
- Payload size limits
- Non-canonical event rejection
- Normalization (timestamp, schema_version)
"""

import json
import time
import pytest
from pathlib import Path
import sys

# Add tentaculo_link to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import validation functions from tentaculo_link/main_v7.py
from tentaculo_link.main_v7 import (
    CANONICAL_EVENT_SCHEMAS,
    CANONICAL_EVENT_WHITELIST,
    validate_event_schema,
    normalize_event,
    validate_event_type,
)


class TestCanonicalEventWhitelist:
    """Test the canonical event whitelist."""

    def test_whitelist_has_6_events(self):
        """Verify exactly 6 canonical events."""
        assert len(CANONICAL_EVENT_WHITELIST) == 6

    def test_whitelist_contains_all_required_events(self):
        """Verify all required events are in whitelist."""
        required = {
            "system.alert",
            "system.correlation.updated",
            "forensic.snapshot.created",
            "madre.decision.explained",
            "switch.tension.updated",
            "shub.action.narrated",
        }
        assert CANONICAL_EVENT_WHITELIST == required

    def test_validate_event_type_accepts_canonical(self):
        """Verify validate_event_type accepts canonical events."""
        for event_type in CANONICAL_EVENT_WHITELIST:
            assert validate_event_type(event_type) is True

    def test_validate_event_type_rejects_non_canonical(self):
        """Verify validate_event_type rejects non-canonical events."""
        fake_events = [
            "custom.event",
            "madre.request.made",
            "switch.routing.changed",
            "unknown.type",
        ]
        for event_type in fake_events:
            assert validate_event_type(event_type) is False


class TestSystemAlertEvent:
    """Test system.alert event validation."""

    def test_valid_system_alert(self):
        """Valid system.alert event should pass."""
        event = {
            "type": "system.alert",
            "alert_id": "alert_123",
            "severity": "L3",
            "message": "Test alert",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is not None
        assert result["type"] == "system.alert"

    def test_system_alert_missing_alert_id(self):
        """system.alert without alert_id should fail."""
        event = {
            "type": "system.alert",
            "severity": "L3",
            "message": "Test alert",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None

    def test_system_alert_invalid_severity_type(self):
        """system.alert with invalid severity type should fail."""
        event = {
            "type": "system.alert",
            "alert_id": "alert_123",
            "severity": 123,  # Should be str
            "message": "Test alert",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None

    def test_system_alert_oversized_payload(self):
        """system.alert with payload > 2KB should fail."""
        event = {
            "type": "system.alert",
            "alert_id": "alert_123",
            "severity": "L3",
            "message": "x" * 3000,  # Huge message
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None


class TestSystemCorrelationEvent:
    """Test system.correlation.updated event validation."""

    def test_valid_system_correlation(self):
        """Valid system.correlation.updated event should pass."""
        event = {
            "type": "system.correlation.updated",
            "correlation_id": "corr_456",
            "related_events": ["event_1", "event_2"],
            "strength": 0.95,
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is not None
        assert result["type"] == "system.correlation.updated"

    def test_correlation_invalid_strength_type(self):
        """correlation with non-numeric strength should fail."""
        event = {
            "type": "system.correlation.updated",
            "correlation_id": "corr_456",
            "related_events": ["event_1"],
            "strength": "high",  # Should be number
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None

    def test_correlation_missing_related_events(self):
        """correlation without related_events should fail."""
        event = {
            "type": "system.correlation.updated",
            "correlation_id": "corr_456",
            "strength": 0.95,
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None


class TestForensicSnapshotEvent:
    """Test forensic.snapshot.created event validation."""

    def test_valid_forensic_snapshot(self):
        """Valid forensic.snapshot.created event should pass."""
        event = {
            "type": "forensic.snapshot.created",
            "snapshot_id": "snap_789",
            "reason": "post-incident-analysis",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is not None
        assert result["type"] == "forensic.snapshot.created"

    def test_snapshot_oversized(self):
        """forensic.snapshot with payload > 1KB should fail."""
        event = {
            "type": "forensic.snapshot.created",
            "snapshot_id": "snap_789",
            "reason": "x" * 2000,  # Oversized
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None


class TestMadreDecisionEvent:
    """Test madre.decision.explained event validation."""

    def test_valid_madre_decision(self):
        """Valid madre.decision.explained event should pass."""
        event = {
            "type": "madre.decision.explained",
            "decision_id": "dec_111",
            "summary": "Route to Switch",
            "confidence": 0.87,
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is not None
        assert result["type"] == "madre.decision.explained"

    def test_madre_decision_invalid_confidence(self):
        """madre.decision with non-numeric confidence should fail."""
        event = {
            "type": "madre.decision.explained",
            "decision_id": "dec_111",
            "summary": "Route to Switch",
            "confidence": "high",  # Should be number
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None


class TestSwitchTensionEvent:
    """Test switch.tension.updated event validation."""

    def test_valid_switch_tension(self):
        """Valid switch.tension.updated event should pass."""
        event = {
            "type": "switch.tension.updated",
            "value": 45,
            "components": {"load": 0.5, "complexity": 0.3, "risk": 0.2},
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is not None
        assert result["type"] == "switch.tension.updated"

    def test_switch_tension_invalid_value_type(self):
        """switch.tension with non-int value should fail."""
        event = {
            "type": "switch.tension.updated",
            "value": "45",  # Should be int
            "components": {"load": 0.5},
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None

    def test_switch_tension_invalid_components_type(self):
        """switch.tension with non-dict components should fail."""
        event = {
            "type": "switch.tension.updated",
            "value": 45,
            "components": "high",  # Should be dict
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None


class TestShubActionEvent:
    """Test shub.action.narrated event validation."""

    def test_valid_shub_action(self):
        """Valid shub.action.narrated event should pass."""
        event = {
            "type": "shub.action.narrated",
            "action": "execute_query",
            "reason": "optimization_needed",
            "next_step": "await_results",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is not None
        assert result["type"] == "shub.action.narrated"

    def test_shub_action_missing_next_step(self):
        """shub.action without next_step should fail."""
        event = {
            "type": "shub.action.narrated",
            "action": "execute_query",
            "reason": "optimization_needed",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None


class TestNonCanonicalEvents:
    """Test rejection of non-canonical events."""

    def test_non_canonical_event_rejected(self):
        """Non-canonical event should be rejected."""
        event = {
            "type": "custom.malicious.event",
            "data": "anything",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None

    def test_missing_type_field(self):
        """Event without type field should be rejected."""
        event = {
            "data": "anything",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None

    def test_none_type_field(self):
        """Event with None type should be rejected."""
        event = {
            "type": None,
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None

    def test_empty_string_type(self):
        """Event with empty string type should be rejected."""
        event = {
            "type": "",
            "timestamp": int(time.time() * 1000),
        }
        result = validate_event_schema(event)
        assert result is None


class TestNormalization:
    """Test event normalization."""

    def test_normalize_adds_timestamp_if_missing(self):
        """normalize_event should add timestamp if missing."""
        event = {
            "type": "system.alert",
            "alert_id": "test_123",
            "severity": "L3",
            "message": "test",
        }
        normalized = normalize_event(event)
        assert "timestamp" in normalized
        assert isinstance(normalized["timestamp"], int)
        assert normalized["timestamp"] > 0

    def test_normalize_preserves_existing_timestamp(self):
        """normalize_event should preserve existing timestamp."""
        ts = int(time.time() * 1000)
        event = {
            "type": "system.alert",
            "alert_id": "test_123",
            "severity": "L3",
            "message": "test",
            "timestamp": ts,
        }
        normalized = normalize_event(event)
        assert normalized["timestamp"] == ts

    def test_normalize_adds_schema_version(self):
        """normalize_event should add _schema_version tag."""
        event = {
            "type": "system.alert",
            "alert_id": "test_123",
            "severity": "L3",
            "message": "test",
            "timestamp": int(time.time() * 1000),
        }
        normalized = normalize_event(event)
        assert "_schema_version" in normalized
        assert normalized["_schema_version"] == "v1.0"

    def test_normalize_is_idempotent(self):
        """normalize_event should be safe to call multiple times."""
        event = {
            "type": "system.alert",
            "alert_id": "test_123",
            "severity": "L3",
            "message": "test",
            "timestamp": int(time.time() * 1000),
        }
        norm1 = normalize_event(event)
        norm2 = normalize_event(norm1)
        assert norm1["_schema_version"] == norm2["_schema_version"]
        assert norm1["timestamp"] == norm2["timestamp"]


class TestValidationPipeline:
    """Test the complete validation pipeline."""

    def test_valid_event_passes_both_stages(self):
        """Valid event should pass both schema and normalization."""
        event = {
            "type": "system.alert",
            "alert_id": "test_456",
            "severity": "L3",
            "message": "pipeline_test",
            "timestamp": int(time.time() * 1000),
        }
        schema_result = validate_event_schema(event)
        assert schema_result is not None
        normalized = normalize_event(schema_result)
        assert normalized is not None
        assert normalized["_schema_version"] == "v1.0"

    def test_invalid_event_fails_schema_stage(self):
        """Invalid event should fail at schema stage."""
        event = {
            "type": "custom.event",
            "data": "anything",
        }
        schema_result = validate_event_schema(event)
        assert schema_result is None

    def test_all_canonical_events_pass_validation(self):
        """All canonical events should pass validation."""
        test_events = [
            {
                "type": "system.alert",
                "alert_id": "a1",
                "severity": "L3",
                "message": "test",
                "timestamp": int(time.time() * 1000),
            },
            {
                "type": "system.correlation.updated",
                "correlation_id": "c1",
                "related_events": [],
                "strength": 0.5,
                "timestamp": int(time.time() * 1000),
            },
            {
                "type": "forensic.snapshot.created",
                "snapshot_id": "s1",
                "reason": "test",
                "timestamp": int(time.time() * 1000),
            },
            {
                "type": "madre.decision.explained",
                "decision_id": "d1",
                "summary": "test",
                "confidence": 0.8,
                "timestamp": int(time.time() * 1000),
            },
            {
                "type": "switch.tension.updated",
                "value": 50,
                "components": {},
                "timestamp": int(time.time() * 1000),
            },
            {
                "type": "shub.action.narrated",
                "action": "test",
                "reason": "test",
                "next_step": "test",
                "timestamp": int(time.time() * 1000),
            },
        ]
        for event in test_events:
            result = validate_event_schema(event)
            assert result is not None, f"Failed for {event['type']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
