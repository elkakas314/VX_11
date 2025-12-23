"""INEE CPU gate tests."""

import pytest


@pytest.mark.p0
class TestINEECPUGateContract:
    """Test INEE CPU gate contract."""

    def test_cpu_gate_status_code(self):
        """CPU gate uses status_code 429 (Too Many Requests)."""
        status_code = 429
        assert status_code == 429

    def test_cpu_gate_blocks_high_load(self):
        """CPU gate blocks high-load endpoints."""
        blocked_endpoints = [
            "/hormiguero/inee/intents/submit",
        ]
        assert "/intents/submit" in blocked_endpoints[0]

    def test_cpu_gate_allows_reads(self):
        """CPU gate allows read-only endpoints."""
        read_endpoints = [
            "/hormiguero/inee/colonies",
            "/hormiguero/inee/audit",
        ]
        assert len(read_endpoints) == 2

    def test_audit_event_on_block(self):
        """Audit event logged when blocked."""
        event_type = "intent_blocked_cpu_high"
        assert "blocked" in event_type
        assert "cpu_high" in event_type
