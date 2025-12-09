"""
Tests for dynamic optimization and adaptive load scoring.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from config.metrics import MetricsCollector, MetricsBuffer
from config.settings import settings


class TestMetricsCollector:
    """Test metrics collection framework."""
    
    def test_load_score_calculation_low(self):
        """Test load score calculation for low load."""
        collector = MetricsCollector()
        metrics = {"cpu_percent": 10.0, "memory_percent": 20.0}
        score = collector.calculate_load_score(metrics)
        # (10 * 0.6 + 20 * 0.4) / 100 = 0.14
        assert 0.13 < score < 0.15
        assert score >= 0.0
        assert score <= 1.0
    
    def test_load_score_calculation_medium(self):
        """Test load score calculation for medium load."""
        collector = MetricsCollector()
        metrics = {"cpu_percent": 50.0, "memory_percent": 50.0}
        score = collector.calculate_load_score(metrics)
        # (50 * 0.6 + 50 * 0.4) / 100 = 0.5
        assert 0.49 < score < 0.51
    
    def test_load_score_calculation_high(self):
        """Test load score calculation for high load."""
        collector = MetricsCollector()
        metrics = {"cpu_percent": 90.0, "memory_percent": 80.0}
        score = collector.calculate_load_score(metrics)
        # (90 * 0.6 + 80 * 0.4) / 100 = 0.86
        assert 0.85 < score < 0.87
    
    def test_load_score_clamping(self):
        """Test that load score is clamped to [0.0, 1.0]."""
        collector = MetricsCollector()
        metrics = {"cpu_percent": 150.0, "memory_percent": 200.0}
        score = collector.calculate_load_score(metrics)
        assert score == 1.0
        
        metrics = {"cpu_percent": -10.0, "memory_percent": -5.0}
        score = collector.calculate_load_score(metrics)
        assert score == 0.0
    
    def test_mode_determination_eco(self):
        """Test ECO mode determination (low load)."""
        collector = MetricsCollector()
        mode = collector.get_mode(0.25)
        assert mode == "ECO"
    
    def test_mode_determination_balanced(self):
        """Test BALANCED mode determination (medium-low load)."""
        collector = MetricsCollector()
        mode = collector.get_mode(0.45)
        assert mode == "BALANCED"
    
    def test_mode_determination_high_perf(self):
        """Test HIGH-PERF mode determination (medium-high load)."""
        collector = MetricsCollector()
        mode = collector.get_mode(0.75)
        assert mode == "HIGH-PERF"
    
    def test_mode_determination_critical(self):
        """Test CRITICAL mode determination (very high load)."""
        collector = MetricsCollector()
        mode = collector.get_mode(0.90)
        assert mode == "CRITICAL"
    
    def test_mode_thresholds(self):
        """Test exact mode threshold boundaries."""
        collector = MetricsCollector()
        
        # ECO threshold: 0.3
        assert collector.get_mode(0.29) == "ECO"
        assert collector.get_mode(0.30) == "BALANCED"
        
        # BALANCED threshold: 0.6
        assert collector.get_mode(0.59) == "BALANCED"
        assert collector.get_mode(0.60) == "HIGH-PERF"
        
        # HIGH-PERF threshold: 0.85
        assert collector.get_mode(0.84) == "HIGH-PERF"
        assert collector.get_mode(0.85) == "CRITICAL"


class TestMetricsBuffer:
    """Test metrics buffer and windowing."""
    
    def test_buffer_append_and_average(self):
        """Test buffer append and average calculation."""
        buffer = MetricsBuffer(max_size=5)
        buffer.append({"value": 10.0})
        buffer.append({"value": 20.0})
        buffer.append({"value": 30.0})
        
        avg = buffer.average("value")
        assert avg == 20.0
    
    def test_buffer_circular_eviction(self):
        """Test buffer evicts oldest entries when full."""
        buffer = MetricsBuffer(max_size=3)
        buffer.append({"id": 1})
        buffer.append({"id": 2})
        buffer.append({"id": 3})
        buffer.append({"id": 4})  # Should evict id=1
        
        assert len(buffer.data) == 3
        ids = [d["id"] for d in buffer.data]
        assert ids == [2, 3, 4]
    
    def test_buffer_empty_average(self):
        """Test average on empty buffer."""
        buffer = MetricsBuffer(max_size=5)
        avg = buffer.average("value")
        assert avg is None


class TestAdaptiveModesIntegration:
    """Integration tests for adaptive mode transitions."""
    
    @pytest.mark.asyncio
    async def test_mode_transition_sequence(self):
        """Test realistic mode transition sequence."""
        collector = MetricsCollector()
        
        # Simulate load progression
        loads = [
            (0.15, "ECO"),       # Low
            (0.45, "BALANCED"),  # Medium-low
            (0.70, "HIGH-PERF"), # High
            (0.90, "CRITICAL"),  # Very high
            (0.60, "HIGH-PERF"), # Back down to high
            (0.40, "BALANCED"),  # Back to medium-low
        ]
        
        for load_score, expected_mode in loads:
            mode = collector.get_mode(load_score)
            assert mode == expected_mode
    
    def test_provider_profiles_defined(self):
        """Test that all mode profiles are properly defined."""
        from switch.main import MODE_PROFILES
        
        required_modes = ["ECO", "BALANCED", "HIGH-PERF", "CRITICAL"]
        for mode in required_modes:
            assert mode in MODE_PROFILES
            profile = MODE_PROFILES[mode]
            assert "preferred_providers" in profile
            assert "timeout_ms" in profile
            assert "max_workers" in profile
            assert len(profile["preferred_providers"]) > 0
            assert profile["timeout_ms"] > 0
            assert profile["max_workers"] > 0
    
    def test_eco_vs_critical_profiles(self):
        """Test that ECO and CRITICAL profiles are appropriately different."""
        from switch.main import MODE_PROFILES
        
        eco = MODE_PROFILES["ECO"]
        critical = MODE_PROFILES["CRITICAL"]
        
        # CRITICAL should have more workers and higher timeout
        assert critical["max_workers"] > eco["max_workers"]
        assert critical["timeout_ms"] > eco["timeout_ms"]


class TestLoadScoringFormula:
    """Test the load scoring formula and weights."""
    
    def test_cpu_weight_60_percent(self):
        """Test that CPU has 60% weight in load score."""
        collector = MetricsCollector()
        
        # 100% CPU, 0% Memory -> score should be ~0.6
        metrics = {"cpu_percent": 100.0, "memory_percent": 0.0}
        score = collector.calculate_load_score(metrics)
        assert 0.59 < score < 0.61
    
    def test_memory_weight_40_percent(self):
        """Test that Memory has 40% weight in load score."""
        collector = MetricsCollector()
        
        # 0% CPU, 100% Memory -> score should be ~0.4
        metrics = {"cpu_percent": 0.0, "memory_percent": 100.0}
        score = collector.calculate_load_score(metrics)
        assert 0.39 < score < 0.41
    
    def test_combined_weights(self):
        """Test combined CPU and memory weights."""
        collector = MetricsCollector()
        
        # 60% CPU, 40% Memory -> score should be ~0.52
        metrics = {"cpu_percent": 60.0, "memory_percent": 40.0}
        score = collector.calculate_load_score(metrics)
        expected = (60 * 0.6 + 40 * 0.4) / 100
        assert abs(score - expected) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
