#!/usr/bin/env python3
"""
VX11 Stability P0 Suite - P0 Tests (FASE 4)

Unit tests for critical harness functionality:
- Health check HTTP code parsing
- docker_down_services cleanup
- Stability score bounds
- Flow check functionality
"""

import sys
from pathlib import Path
from unittest import mock
import pytest

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.vx11_stability_p0 import (
    health_check,
    docker_down_services,
    calculate_stability_p0_pct,
    flow_check,
    docker_stats,
    _parse_memory_to_mib,
)
from tests._vx11_base import vx11_base_url


class TestHealthCheckHttpCodeParsing:
    """Test health_check HTTP code parsing (P0 #1 from DeepSeek)."""

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_health_check_parses_http_200_as_success(self, mock_run_cmd):
        """Health check should succeed on HTTP 200."""
        # Simulate curl response: stdout is the HTTP code
        mock_run_cmd.return_value = (0, "200", "")

        success, latency_ms = health_check(vx11_base_url() + "/madre/health")

        assert success is True
        assert latency_ms > 0

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_health_check_parses_http_404_as_failure(self, mock_run_cmd):
        """Health check should fail on HTTP 404."""
        mock_run_cmd.return_value = (0, "404", "")

        success, latency_ms = health_check(vx11_base_url() + "/madre/health")

        assert success is False

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_health_check_parses_http_2xx_as_success(self, mock_run_cmd):
        """Health check should succeed on any 2xx code."""
        for code in ["200", "201", "202", "204", "299"]:
            mock_run_cmd.return_value = (0, code, "")
            success, _ = health_check(vx11_base_url() + "/madre/health")
            assert success is True, f"HTTP {code} should succeed"

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_health_check_retry_on_timeout(self, mock_run_cmd):
        """Health check should retry on timeout."""
        # First 2 attempts: timeout, third: success
        mock_run_cmd.side_effect = [
            (124, "", "timeout"),
            (124, "", "timeout"),
            (0, "200", ""),
        ]

        success, latency_ms = health_check(
            vx11_base_url() + "/madre/health", max_retries=3
        )

        assert success is True
        assert mock_run_cmd.call_count == 3


class TestDockerDownServicesCleanup:
    """Test docker_down_services cleanup (P0 #2 from DeepSeek)."""

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_docker_down_calls_stop_and_remove(self, mock_run_cmd):
        """docker_down should call stop, kill, and rm."""
        mock_run_cmd.return_value = (0, "", "")

        rc, msg = docker_down_services(["switch", "hermes"])

        # Should call: stop, kill, rm (+ verify) for each service
        assert rc == 0
        assert "stopped" in msg.lower()
        assert (
            mock_run_cmd.call_count >= 4
        )  # At least stop + kill + rm + verify per service


class TestStabilityScoreBounds:
    """Test that stability score stays within 0-100 bounds."""

    def test_stability_score_perfect_case(self):
        """Perfect test case should score 100%."""
        score = calculate_stability_p0_pct(
            tests_pass=True,
            health_ok=True,
            restarts_increased=False,
            oom_killed=False,
            mem_peak_mib=100.0,
            mem_limit_mib=512.0,
            mem_threshold_mib=400.0,
        )
        assert score == 100.0

    def test_stability_score_worst_case(self):
        """Worst case should score 0%."""
        score = calculate_stability_p0_pct(
            tests_pass=False,
            health_ok=False,
            restarts_increased=True,
            oom_killed=True,
            mem_peak_mib=1000.0,
            mem_limit_mib=512.0,
            mem_threshold_mib=400.0,
        )
        assert score == 0.0

    def test_stability_score_partial_failure(self):
        """Partial failure should score between 0-100."""
        score = calculate_stability_p0_pct(
            tests_pass=True,
            health_ok=False,
            restarts_increased=False,
            oom_killed=False,
            mem_peak_mib=300.0,
            mem_limit_mib=512.0,
            mem_threshold_mib=400.0,
        )
        # 40% (tests) + 0 (health) + 15% (restarts) + 15% (OOM) + 10% (mem) = 80%
        assert 0.0 <= score <= 100.0
        assert score == 80.0

    def test_stability_score_bounds_always_valid(self):
        """Score should always be within [0, 100]."""
        test_cases = [
            (True, True, False, False, 50.0, 512.0),
            (False, True, True, False, 100.0, 512.0),
            (True, False, False, True, 200.0, 256.0),
            (False, False, True, True, 512.0, 256.0),
        ]

        for tests_pass, health_ok, restarts_inc, oom, mem_peak, mem_limit in test_cases:
            score = calculate_stability_p0_pct(
                tests_pass=tests_pass,
                health_ok=health_ok,
                restarts_increased=restarts_inc,
                oom_killed=oom,
                mem_peak_mib=mem_peak,
                mem_limit_mib=mem_limit,
            )
            assert 0.0 <= score <= 100.0, f"Score {score} out of bounds"


class TestFlowCheckFunctionality:
    """Test flow_check HTTP endpoint testing."""

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_flow_check_success_200(self, mock_run_cmd):
        """Flow check should succeed on HTTP 200."""
        mock_run_cmd.return_value = (0, '{"status": "ok"}\n200', "")

        result = flow_check(vx11_base_url() + "/madre/status", "test-endpoint")

        assert result["success"] is True
        assert result["http_code"] == 200
        assert result["payload_hash"] is not None

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_flow_check_failure_404(self, mock_run_cmd):
        """Flow check should fail on HTTP 404."""
        mock_run_cmd.return_value = (0, "not found\n404", "")

        result = flow_check(vx11_base_url() + "/madre/status", "test-endpoint")

        assert result["success"] is False
        assert result["http_code"] == 404


class TestMemoryParsing:
    """Test memory string parsing utility."""

    def test_parse_memory_mib(self):
        """Parse MiB format."""
        assert _parse_memory_to_mib("123.4MiB") == 123.4
        assert _parse_memory_to_mib("0MiB") == 0.0

    def test_parse_memory_gib(self):
        """Parse GiB format."""
        assert _parse_memory_to_mib("1.5GiB") == 1.5 * 1024
        assert _parse_memory_to_mib("1GiB") == 1024.0

    def test_parse_memory_invalid(self):
        """Parse invalid format."""
        assert _parse_memory_to_mib("invalid") == 0.0
        assert _parse_memory_to_mib("") == 0.0


class TestDockerStatsJSONParsing:
    """Test docker_stats JSON parsing robustness."""

    @mock.patch("scripts.vx11_stability_p0.run_cmd")
    def test_docker_stats_parses_json(self, mock_run_cmd):
        """docker_stats should parse JSON output."""
        mock_run_cmd.return_value = (
            0,
            '{"MemUsage":"123.4MiB / 512MiB","CPUPerc":"1.5%","MemPerc":"24.1%"}',
            "",
        )

        stats = docker_stats("switch")

        assert stats["mem_mib"] == 123.4
        assert stats["cpu_pct"] == 1.5
        assert stats["mem_pct"] == 24.1


@pytest.mark.unit
class TestP0CriticalPaths:
    """Unit test markers for P0 critical functionality."""

    def test_p0_marker(self):
        """This test is marked as P0 critical."""
        assert True
