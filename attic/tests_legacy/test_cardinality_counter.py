"""
Test Suite: Event Cardinality Counter
======================================

Tests the EventCardinalityCounter implementation for event frequency tracking.
"""

import time
from tentaculo_link.main_v7 import EventCardinalityCounter


class TestEventCardinalityCounter:
    """Test EventCardinalityCounter class."""

    def test_counter_initialization(self):
        """Counter should initialize with empty state."""
        counter = EventCardinalityCounter()
        assert counter.counters == {}
        assert isinstance(counter.window_start, float)

    def test_increment_single_event(self):
        """Incrementing should increase counter for event type."""
        counter = EventCardinalityCounter()
        counter.increment("system.alert")
        assert counter.counters["system.alert"] == 1

    def test_increment_multiple_events(self):
        """Incrementing multiple times should accumulate."""
        counter = EventCardinalityCounter()
        for _ in range(5):
            counter.increment("system.alert")
        assert counter.counters["system.alert"] == 5

    def test_increment_multiple_types(self):
        """Counter should track multiple event types separately."""
        counter = EventCardinalityCounter()
        counter.increment("system.alert")
        counter.increment("system.alert")
        counter.increment("madre.decision.explained")
        counter.increment("madre.decision.explained")
        counter.increment("madre.decision.explained")
        
        assert counter.counters["system.alert"] == 2
        assert counter.counters["madre.decision.explained"] == 3

    def test_get_stats_returns_copy(self):
        """get_stats should return a copy, not reference."""
        counter = EventCardinalityCounter()
        counter.increment("system.alert")
        stats1 = counter.get_stats()
        stats1["system.alert"] = 999  # Modify copy
        stats2 = counter.get_stats()
        assert stats2["system.alert"] == 1  # Original unchanged

    def test_get_stats_with_rate_calculation(self):
        """get_stats_with_rate should calculate events/min."""
        counter = EventCardinalityCounter()
        counter.increment("system.alert")
        counter.increment("system.alert")
        
        stats = counter.get_stats_with_rate()
        assert "system.alert" in stats
        assert "count" in stats["system.alert"]
        assert "rate_per_min" in stats["system.alert"]
        assert stats["system.alert"]["count"] == 2

    def test_get_stats_with_rate_non_zero_elapsed(self):
        """Rate calculation should handle elapsed time > 0."""
        counter = EventCardinalityCounter()
        counter.increment("system.alert")
        time.sleep(0.1)  # Ensure some elapsed time
        
        stats = counter.get_stats_with_rate()
        rate = stats["system.alert"]["rate_per_min"]
        assert rate > 0  # Should have positive rate

    def test_window_reset_after_60_seconds(self):
        """get_stats should reset window after 60+ seconds."""
        counter = EventCardinalityCounter()
        counter.increment("system.alert")
        
        # Manually set window start to 61 seconds ago
        counter.window_start = time.time() - 61
        
        stats = counter.get_stats()
        assert stats["system.alert"] == 1  # Returns old count
        assert counter.counters == {}  # Counter reset
        assert counter.window_start > time.time() - 1  # New window started

    def test_memory_efficiency(self):
        """Counter should use minimal memory."""
        counter = EventCardinalityCounter()
        for i in range(1000):
            counter.increment(f"event_{i % 6}")  # 6 unique types
        
        # Should only track 6 types, not 1000
        assert len(counter.counters) == 6

    def test_concurrent_increments(self):
        """Counter should handle sequential increments accurately."""
        counter = EventCardinalityCounter()
        event_types = [
            "system.alert",
            "system.correlation.updated",
            "forensic.snapshot.created",
            "madre.decision.explained",
            "switch.tension.updated",
            "shub.action.narrated",
        ]
        
        for event_type in event_types:
            for _ in range(10):
                counter.increment(event_type)
        
        for event_type in event_types:
            assert counter.counters[event_type] == 10

    def test_zero_elapsed_time_handling(self):
        """Rate calculation should handle zero elapsed time safely."""
        counter = EventCardinalityCounter()
        counter.increment("system.alert")
        counter.window_start = time.time()  # Just started, ~0 elapsed
        
        stats = counter.get_stats_with_rate()
        # Should not crash even with minimal elapsed time
        assert "system.alert" in stats
        assert stats["system.alert"]["rate_per_min"] >= 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
