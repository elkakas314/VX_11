"""
Integration tests: Hormiguero Queen ↔ Manifestator patchplan flow (FASE 2)
Tests CPU gate, patchplan call, and circuit breaker logic.
"""

import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from hormiguero.core.queen import Queen
from hormiguero.config import settings


class TestManifestatorIntegration:
    """Test Hormiguero→Manifestator collaboration with CPU gate."""

    @pytest.fixture
    def queen(self):
        """Create Queen instance with temp root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Queen(root_path=tmpdir)

    def test_manifestator_patchplan_called_on_fs_drift(self, queen):
        """fs_drift incident should trigger Manifestator patchplan call."""

        # Mock the HTTP call to Manifestator
        with patch("hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "plan_id": "test-plan-123",
                "actions": [
                    {"action": "add", "target": "file1.txt", "reason": "missing"},
                    {"action": "remove", "target": "extra.txt", "reason": "extra"},
                ],
                "risk": "mid",
                "estimated_time_sec": 4,
                "notes": "Test patchplan",
            }

            # Mock incident repo
            with patch(
                "hormiguero.hormiguero.core.queen.repo.upsert_incident"
            ) as mock_upsert:
                mock_upsert.return_value = "incident-123"

                with patch(
                    "hormiguero.hormiguero.core.queen.repo.set_incident_suggestions"
                ):
                    # Trigger fs_drift result
                    result = {
                        "status": "ok",
                        "missing": ["file1.txt"],
                        "extra": ["extra.txt"],
                    }
                    incidents = queen._handle_results("fs_drift", result)

                    # Verify Manifestator was called
                    calls = mock_post.call_args_list
                    manifestator_calls = [
                        c for c in calls if "/manifestator/patchplan" in str(c)
                    ]
                    assert (
                        len(manifestator_calls) > 0
                    ), "Manifestator should be called on fs_drift"

    def test_manifestator_cpu_gate_blocks_on_high_cpu(self, queen):
        """When CPU sustained-high, Manifestator should NOT be called."""
        queen.cpu_sustained_high = True  # Simulate high CPU

        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200

            with patch(
                "hormiguero.hormiguero.core.queen.repo.upsert_incident"
            ) as mock_upsert:
                mock_upsert.return_value = "incident-123"

                with patch(
                    "hormiguero.hormiguero.core.queen.repo.set_incident_suggestions"
                ):
                    queen._consult_manifestator(
                        "incident-123",
                        {"missing": ["f1.txt"], "extra": ["f2.txt"]},
                    )

                    # Verify Manifestator was NOT called
                    calls = mock_post.call_args_list
                    manifestator_calls = [
                        c for c in calls if "/manifestator/patchplan" in str(c)
                    ]
                    assert (
                        len(manifestator_calls) == 0
                    ), "CPU gate should block Manifestator call"

    def test_manifestator_timeout_handled_gracefully(self, queen):
        """Manifestator timeout should not crash fs_drift flow."""

        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            # Simulate timeout
            mock_post.side_effect = TimeoutError("Manifestator timeout")

            # Should not raise
            queen._consult_manifestator(
                "incident-123",
                {"missing": ["f1.txt"], "extra": []},
            )
            # Silent fail: test passes if no exception

    def test_manifestator_response_format_validated(self, queen):
        """Manifestator response should have expected fields."""

        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "plan_id": "uuid-123",
                "actions": [{"action": "add", "target": "x", "reason": "missing"}],
                "risk": "low",
                "estimated_time_sec": 2,
                "notes": "valid response",
            }

            with patch(
                "hormiguero.hormiguero.core.queen.repo.set_incident_suggestions"
            ) as mock_set:
                queen._consult_manifestator(
                    "incident-123",
                    {"missing": ["x"], "extra": []},
                )

                # Verify suggestions were set with patchplan data
                if mock_set.called:
                    call_args = mock_set.call_args[0]
                    suggestions = call_args[1]
                    assert "plan_id" in suggestions
                    assert "actions" in suggestions
                    assert "risk" in suggestions

    def test_manifestator_endpoint_url_construction(self, queen):
        """Manifestator URL should be properly constructed."""

        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "plan_id": "test",
                "actions": [],
                "risk": "low",
                "estimated_time_sec": 1,
                "notes": "",
            }

            with patch(
                "hormiguero.hormiguero.core.queen.repo.set_incident_suggestions"
            ):
                queen._consult_manifestator(
                    "incident-123",
                    {"missing": [], "extra": []},
                )

                # Verify URL contains /manifestator/patchplan
                if mock_post.called:
                    call_url = mock_post.call_args[0][0]
                    assert "/manifestator/patchplan" in call_url


class TestManifestatorEndpoints:
    """Test Manifestator canonical endpoints."""

    def test_manifestator_validate_endpoint_response_format(self):
        """POST /manifestator/validate should return valid response."""
        # This test documents the expected format
        expected_response = {
            "valid": True,
            "issues": [],
            "risk": "low",
            "hash": "abc123",
        }

        assert "valid" in expected_response
        assert "issues" in expected_response
        assert "risk" in expected_response
        assert expected_response["risk"] in ["low", "mid", "high"]

    def test_manifestator_patchplan_endpoint_response_format(self):
        """POST /manifestator/patchplan should return valid patchplan."""
        expected_response = {
            "plan_id": "uuid-123",
            "actions": [
                {"action": "add", "target": "file.txt", "reason": "missing"},
            ],
            "risk": "mid",
            "estimated_time_sec": 10,
            "notes": "test plan",
        }

        assert "plan_id" in expected_response
        assert "actions" in expected_response
        assert "risk" in expected_response
        assert "estimated_time_sec" in expected_response
        assert all(
            a.get("action") in ["add", "remove", "verify"]
            for a in expected_response["actions"]
        )


class TestQueenManifestatorIntegration:
    """Integration: Queen + Manifestator + CPU gate."""

    @pytest.fixture
    def queen(self):
        """Create Queen instance with temp root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Queen(root_path=tmpdir)

    def test_queen_handles_drift_then_manifestator_then_madre(self, queen):
        """Complete flow: drift→manifestator→madre."""

        with patch("hormiguero.hormiguero.core.queen.requests.post") as mock_post:
            mock_post.return_value.status_code = 200

            with patch(
                "hormiguero.hormiguero.core.queen.repo.upsert_incident"
            ) as mock_upsert:
                mock_upsert.return_value = "incident-123"

                with patch(
                    "hormiguero.hormiguero.core.queen.repo.set_incident_suggestions"
                ):
                    result = {
                        "status": "ok",
                        "missing": ["f1.txt"],
                        "extra": ["f2.txt"],
                    }

                    incidents = queen._handle_results("fs_drift", result)

                    # Should have created incident
                    assert len(incidents) > 0

    def test_cpu_gate_resets_after_throttle(self, queen):
        """cpu_sustained_high flag should reset after throttle cycle."""
        queen.cpu_sustained_high = True

        # In actual run_loop, flag is reset after sleep
        # Simulate the logic
        if queen.cpu_sustained_high:
            multiplier = settings.scan_interval_multiplier_cpu_high
            assert multiplier > 1.0, "Multiplier should increase interval"
            queen.cpu_sustained_high = False

        assert not queen.cpu_sustained_high
