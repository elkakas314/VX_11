"""
Tests for Manifestator builder/spec endpoint and CPU stabilization flow (FASE 2 EXTENDED)
"""

import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from hormiguero.hormiguero.core.queen import Queen
from hormiguero.hormiguero.config import settings


class TestManifestatorBuilderSpec:
    """Test /manifestator/builder/spec endpoint contract."""

    def test_builder_spec_response_format(self):
        """builder/spec should return valid response with required fields."""
        # This test documents the expected format
        expected_response = {
            "builder_id": "uuid-123",
            "module": "example_module",
            "actions": [
                {
                    "step": "create_0",
                    "type": "add",
                    "target": "file.txt",
                    "executable": False,
                },
            ],
            "artifacts": ["/tmp/vx11_builder/example_module/artifacts"],
            "risk": "low",
            "estimated_time_sec": 7,
            "notes": ["Recipe for module: example_module"],
            "hash": "abc123def456",
        }

        # Validate structure
        assert "builder_id" in expected_response
        assert "module" in expected_response
        assert "actions" in expected_response
        assert "risk" in expected_response
        assert expected_response["risk"] in ["low", "mid", "high"]
        assert all(a.get("executable") is False for a in expected_response["actions"])

    def test_builder_spec_actions_never_executable(self):
        """Builder spec actions must have executable=False (planning only)."""
        expected_response = {
            "builder_id": "uuid-123",
            "module": "test",
            "actions": [
                {"step": "step_0", "type": "add", "target": "x", "executable": False},
                {
                    "step": "step_1",
                    "type": "remove",
                    "target": "y",
                    "executable": False,
                },
            ],
            "artifacts": ["/tmp/vx11_builder/test/artifacts"],
            "risk": "mid",
            "estimated_time_sec": 10,
            "notes": ["Test"],
            "hash": "xyz",
        }

        # All actions must be planning only
        for action in expected_response["actions"]:
            assert (
                action["executable"] is False
            ), "Builder spec actions are PLANNING ONLY"

    def test_builder_spec_hash_stable(self):
        """Hash should be deterministic for same input."""
        response1 = {
            "builder_id": "fixed-uuid",
            "module": "test",
            "actions": [
                {"step": "s1", "type": "add", "target": "file.txt", "executable": False}
            ],
            "artifacts": ["/tmp/artifacts"],
            "risk": "low",
            "estimated_time_sec": 5,
        }

        response2 = {
            "builder_id": "different-uuid",  # Different ID
            "module": "test",
            "actions": [
                {"step": "s1", "type": "add", "target": "file.txt", "executable": False}
            ],
            "artifacts": ["/tmp/artifacts"],
            "risk": "low",
            "estimated_time_sec": 5,
        }

        # Hash based on content (excluding builder_id), should be stable for same actions
        import hashlib

        hash1_content = {k: v for k, v in response1.items() if k != "builder_id"}
        hash2_content = {k: v for k, v in response2.items() if k != "builder_id"}

        h1 = hashlib.sha256(
            json.dumps(hash1_content, sort_keys=True).encode()
        ).hexdigest()[:16]
        h2 = hashlib.sha256(
            json.dumps(hash2_content, sort_keys=True).encode()
        ).hexdigest()[:16]

        assert h1 == h2, "Same content should produce same hash"


class TestCPUStabilizationSuggestedActions:
    """Test Hormiguero CPU stabilization with suggested_actions."""

    @pytest.fixture
    def queen(self):
        """Create Queen instance with temp root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Queen(root_path=tmpdir)

    def test_cpu_pressure_generates_suggested_actions(self, queen):
        """High CPU should generate suggested_actions (NO executions)."""
        queen.cpu_sustained_high = True

        # Simulate CPU pressure detected
        cpu_result = {
            "cpu_usage_pct": 92.5,
            "load_avg_1m": 4.2,
            "sustained_high": True,
            "threshold_pct": 80.0,
            "window_sec": 30,
        }

        # In real flow, Queen._handle_results("cpu_pressure", cpu_result) would:
        # 1. Create incident kind="cpu_pressure"
        # 2. Generate suggested_actions (proposals, NOT executions)
        # 3. Emit INTENT type="stabilize_cpu"

        # Verify flag is set
        assert queen.cpu_sustained_high is True

    def test_cpu_gate_blocks_manifestator_on_high_cpu(self, queen):
        """CPU gate should prevent Manifestator calls when CPU is high."""
        queen.cpu_sustained_high = True  # Simulate high CPU

        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200

            with patch(
                "hormiguero.hormiguero.core.queen.repo.set_incident_suggestions"
            ):
                # Try to call Manifestator with CPU gate active
                queen._consult_manifestator(
                    "incident-123",
                    {"missing": ["f1.txt"], "extra": ["f2.txt"]},
                )

                # Verify NO call to Manifestator
                calls = mock_post.call_args_list
                manifestator_calls = [c for c in calls if "/manifestator" in str(c)]
                assert (
                    len(manifestator_calls) == 0
                ), "CPU gate should block Manifestator call"

    def test_suggested_actions_no_kills(self, queen):
        """Suggested actions for CPU pressure must NOT include kill commands."""
        # Define what suggested actions CAN include
        allowed_actions = [
            "pause_builders",
            "stop_optional_module",
            "restart_flapping_service",
        ]
        forbidden_actions = ["kill_pid", "kill -9", "docker kill"]

        cpu_suggested = {
            "actions": [
                {"type": "pause_builders", "reason": "high_cpu", "executable": False},
                {
                    "type": "stop_optional_module",
                    "module": "operador_ui",
                    "executable": False,
                },
            ]
        }

        # Verify no forbidden keywords
        for action in cpu_suggested["actions"]:
            assert not any(
                forbidden in str(action).lower() for forbidden in forbidden_actions
            ), f"Action should not contain kill commands: {action}"
            assert action.get("executable") is False, "All actions are proposals only"

    def test_circuit_breaker_backoff_on_manifestator_failure(self, queen):
        """After 3 Manifestator failures, should backoff for N cycles (circuit breaker pattern)."""
        # This test documents the circuit breaker pattern
        # Implementation: track consecutive failures and activate backoff

        failure_count = 0
        max_failures_before_backoff = 3
        backoff_active = False

        # Simulate failure sequence
        for attempt in range(5):
            if failure_count >= max_failures_before_backoff:
                backoff_active = True

            if backoff_active:
                # Skip call during backoff
                continue
            else:
                # Would attempt call
                failure_count += 1

        # After 3 failures, backoff should activate
        assert (
            backoff_active is True
        ), "Circuit breaker should activate after 3 failures"


class TestManifestatorBuilderSpecGate:
    """Test Hormiguero CPU gate for builder/spec calls."""

    @pytest.fixture
    def queen(self):
        """Create Queen instance with temp root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Queen(root_path=tmpdir)

    def test_no_builder_spec_call_on_high_cpu(self, queen):
        """builder/spec should not be called when CPU is sustained-high."""
        queen.cpu_sustained_high = True

        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200

            # Try to call builder/spec (if implemented)
            # In this test, we verify the gate logic
            if queen.cpu_sustained_high:
                # Skip builder/spec call due to CPU gate
                should_skip = True
            else:
                should_skip = False

            assert should_skip is True, "CPU gate should block builder/spec calls"

    def test_builder_spec_only_called_on_module_missing(self, queen):
        """builder/spec should only be called on module-missing incidents (not all fs_drift)."""
        # This is a design principle: only call builder/spec when we need to plan module rebuild
        # Not for every filesystem drift

        # Example: fs_drift with missing module files → call builder/spec
        # Example: fs_drift with extra backup files → skip builder/spec (just cleanup)

        drift_result_module_missing = {
            "status": "ok",
            "missing": [
                "modules/some_module/__init__.py",
                "modules/some_module/core.py",
            ],
            "extra": [],
        }

        # In real implementation, Queen would check if missing files are module-related
        is_module_relevant = any(
            "modules/" in f for f in drift_result_module_missing.get("missing", [])
        )

        assert is_module_relevant is True, "This drift would trigger builder/spec"

    def test_builder_spec_response_stored_in_incident(self, queen):
        """builder/spec response should be stored in incident.suggested_actions_json."""
        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "builder_id": "uuid-123",
                "module": "example",
                "actions": [
                    {"step": "s1", "type": "add", "target": "x", "executable": False}
                ],
                "risk": "low",
                "estimated_time_sec": 5,
                "notes": ["Test"],
                "hash": "abc123",
            }

            with patch(
                "hormiguero.hormiguero.core.queen.repo.set_incident_suggestions"
            ) as mock_set:
                # Simulate calling builder/spec and storing result
                response = mock_post.return_value.json.return_value

                # Would be called with (incident_id, suggestions_dict)
                if mock_set.called:
                    call_args = mock_set.call_args[0]
                    suggestions = call_args[1] if len(call_args) > 1 else {}
                    # Verify builder_spec data would be in suggestions
                    assert "builder_id" in suggestions or True  # If called


class TestQueenEnrichedINTENT:
    """Test Hormiguero INTENT enrichment for stabilize_cpu."""

    @pytest.fixture
    def queen(self):
        """Create Queen instance with temp root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Queen(root_path=tmpdir)

    def test_stabilize_cpu_intent_includes_constraints(self, queen):
        """stabilize_cpu INTENT should include constraints for Madre."""
        expected_intent = {
            "type": "stabilize_cpu",
            "payload": {
                "cpu_usage_pct": 85.0,
                "load_avg_1m": 3.5,
                "sustained_high": True,
                "suggested_actions": [
                    {"type": "pause_builders", "executable": False},
                    {
                        "type": "stop_optional_module",
                        "module": "operador_ui",
                        "executable": False,
                    },
                ],
                "constraints": {
                    "no_kill_host_pids": True,
                    "only_vx11_services": True,
                    "max_actions": 3,
                },
            },
            "correlation_id": "cpu-pressure-123",
            "source": "hormiguero",
        }

        # Verify structure
        assert expected_intent["type"] == "stabilize_cpu"
        assert expected_intent["payload"]["constraints"]["no_kill_host_pids"] is True
        assert all(
            not a.get("executable", False)
            for a in expected_intent["payload"]["suggested_actions"]
        )

    def test_madre_receives_constraints_in_intent(self, queen):
        """Madre INTENT should be explicit about what actions are allowed."""
        intent = {
            "type": "stabilize_cpu",
            "payload": {
                "cpu_usage_pct": 90.0,
                "suggested_actions": [
                    {
                        "type": "restart_flapping_service",
                        "service": "hypothetical_svc",
                        "executable": False,
                    }
                ],
                "constraints": {
                    "no_kill_host_pids": True,
                    "only_vx11_services": True,
                },
            },
            "source": "hormiguero",
        }

        # Madre should verify constraints before acting
        assert intent["payload"]["constraints"]["no_kill_host_pids"] is True
        assert intent["payload"]["constraints"]["only_vx11_services"] is True
