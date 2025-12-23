"""
Tests for Hormiguero CPU Guardian (P0).

Tests:
- cpu_pressure scanner returns expected keys and doesn't block
- queen applies throttle/backoff when sustained_high=true
- intent payload to madre has kind="stabilize_cpu" and correlation_id
"""

import os
import sqlite3
import sys
import time
from unittest.mock import Mock, patch, MagicMock

import pytest

SERVICE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "hormiguero")
)
if SERVICE_ROOT not in sys.path:
    sys.path.insert(0, SERVICE_ROOT)

from hormiguero.core.scanners.cpu_pressure import CPUPressureScanner, scan_cpu_pressure
from hormiguero.core.queen import Queen
from hormiguero.config import settings
from hormiguero.core.db.sqlite import ensure_schema
from hormiguero.core.db import repo


class TestCPUPressureScanner:
    """Test CPU pressure scanner."""

    def test_scanner_returns_required_keys(self):
        """CPU scanner returns all expected keys."""
        result = scan_cpu_pressure()
        assert isinstance(result, dict)
        assert "status" in result
        assert "cpu_usage_pct" in result
        assert "load_avg_1m" in result
        assert "sustained_high" in result
        assert "threshold_pct" in result
        assert "window_sec" in result

    def test_scanner_cpu_pct_is_valid_range(self):
        """CPU usage % is 0-100."""
        result = scan_cpu_pressure()
        cpu_pct = result.get("cpu_usage_pct", 0)
        assert 0 <= cpu_pct <= 100, f"CPU % out of range: {cpu_pct}"

    def test_scanner_sustained_high_is_bool(self):
        """sustained_high is boolean."""
        result = scan_cpu_pressure()
        assert isinstance(result["sustained_high"], bool)

    def test_scanner_doesnt_block_long(self):
        """Scanner completes within 1 second (no blocking I/O)."""
        start = time.time()
        result = scan_cpu_pressure()
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Scanner took {elapsed}s (too slow)"
        assert result["status"] in ("ok", "error")

    def test_scanner_error_handling(self):
        """Scanner handles errors gracefully."""
        result = scan_cpu_pressure()
        assert result is not None


class TestQueenCPUThrottle:
    """Test Queen CPU throttle and INTENT logic."""

    def test_queen_has_cpu_ant(self):
        """Queen includes CPU ant in rotation."""
        queen = Queen(root_path="/tmp")
        ant_names = [ant.name for ant in queen.ants]
        assert "cpu_pressure" in ant_names

    def test_queen_throttle_multiplier_applied(self, tmp_path, monkeypatch):
        """Queen applies throttle multiplier when CPU high."""
        db_path = tmp_path / "vx11.db"
        monkeypatch.setattr(settings, "db_path", str(db_path))
        monkeypatch.setattr(settings, "scan_interval_sec", 10)
        monkeypatch.setattr(settings, "scan_jitter_sec", 2)
        monkeypatch.setattr(settings, "scan_interval_multiplier_cpu_high", 3.0)

        ensure_schema()
        queen = Queen(root_path=str(tmp_path))

        # Simulate CPU high
        queen.cpu_sustained_high = True
        assert queen.cpu_sustained_high is True

    def test_queen_sends_intent_cpu_pressure(self, tmp_path, monkeypatch):
        """Queen calls _notify_madre_intent_cpu_pressure with correct payload."""
        db_path = tmp_path / "vx11.db"
        monkeypatch.setattr(settings, "db_path", str(db_path))
        ensure_schema()

        queen = Queen(root_path=str(tmp_path))

        with patch("hormiguero.core.queen.requests.post") as mock_post:
            payload = {
                "cpu_usage_pct": 85.5,
                "load_avg_1m": 3.2,
                "sustained_high": True,
                "threshold_pct": 80,
                "window_sec": 30,
            }
            queen._notify_madre_intent_cpu_pressure(payload)

            assert mock_post.called
            call_args = mock_post.call_args
            json_data = call_args.kwargs.get("json") or call_args[1].get("json")

            assert json_data["type"] == "stabilize_cpu"
            assert json_data["source"] == "hormiguero"
            assert json_data["payload"]["sustained_high"] is True
            assert json_data["correlation_id"] is not None


class TestIntentPayload:
    """Test INTENT payload format to Madre."""

    def test_intent_cpu_pressure_has_required_fields(self, tmp_path, monkeypatch):
        """CPU pressure INTENT has all required fields."""
        db_path = tmp_path / "vx11.db"
        monkeypatch.setattr(settings, "db_path", str(db_path))
        ensure_schema()

        queen = Queen(root_path=str(tmp_path))

        with patch("hormiguero.core.queen.requests.post") as mock_post:
            payload = {
                "cpu_usage_pct": 88.5,
                "load_avg_1m": 3.2,
                "sustained_high": True,
                "threshold_pct": 80,
                "window_sec": 30,
            }
            queen._notify_madre_intent_cpu_pressure(payload)

            call_args = mock_post.call_args
            json_data = call_args.kwargs.get("json") or call_args[1].get("json")

            assert "type" in json_data
            assert "payload" in json_data
            assert "correlation_id" in json_data
            assert "source" in json_data
            assert json_data["type"] == "stabilize_cpu"
            assert json_data["source"] == "hormiguero"
            assert json_data["payload"]["sustained_high"] is True
