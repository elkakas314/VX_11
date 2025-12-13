"""
Test Suite: Event Correlation Tracker
======================================

Tests the EventCorrelationTracker for DAG visualization support.
"""

from tentaculo_link.main_v7 import EventCorrelationTracker
import time


class TestEventCorrelationTracker:
    """Test EventCorrelationTracker class."""

    def test_tracker_initialization(self):
        """Tracker should initialize with empty state."""
        tracker = EventCorrelationTracker(max_nodes=50)
        assert tracker.nodes == {}
        assert tracker.edges == {}
        assert tracker.max_nodes == 50

    def test_add_event_creates_node(self):
        """Adding event should create node in graph."""
        tracker = EventCorrelationTracker()
        event = {
            "type": "system.alert",
            "alert_id": "alert_123",
            "severity": "L3",
            "timestamp": int(time.time() * 1000),
            "_nature": "incident",
        }
        tracker.add_event(event)
        assert "alert_123" in tracker.nodes
        assert tracker.nodes["alert_123"]["type"] == "system.alert"

    def test_add_multiple_events(self):
        """Should track multiple events as nodes."""
        tracker = EventCorrelationTracker()
        for i in range(5):
            event = {
                "type": "system.alert",
                "alert_id": f"alert_{i}",
                "severity": f"L{(i % 4) + 1}",
                "timestamp": int(time.time() * 1000),
                "_nature": "incident",
            }
            tracker.add_event(event)
        assert len(tracker.nodes) == 5

    def test_add_correlation(self):
        """Adding correlation should create edge in graph."""
        tracker = EventCorrelationTracker()
        tracker.add_event({
            "type": "system.alert",
            "alert_id": "alert_1",
            "timestamp": int(time.time() * 1000),
            "_nature": "incident",
        })
        tracker.add_event({
            "type": "madre.decision.explained",
            "decision_id": "dec_1",
            "timestamp": int(time.time() * 1000),
            "_nature": "decision",
        })
        tracker.add_correlation("alert_1", "dec_1", strength=0.8)
        
        assert "alert_1" in tracker.edges
        assert tracker.edges["alert_1"]["dec_1"] == 0.8

    def test_correlation_strength_normalized(self):
        """Correlation strength should be clamped to 0-1."""
        tracker = EventCorrelationTracker()
        tracker.add_correlation("a", "b", strength=1.5)
        assert tracker.edges["a"]["b"] == 1.0  # Clamped to 1.0

    def test_get_graph_structure(self):
        """get_graph should return correct structure."""
        tracker = EventCorrelationTracker()
        
        # Add events
        for i in range(3):
            tracker.add_event({
                "type": "system.alert",
                "alert_id": f"alert_{i}",
                "timestamp": int(time.time() * 1000),
                "_nature": "incident",
            })
        
        # Add correlations
        tracker.add_correlation("alert_0", "alert_1", 0.9)
        tracker.add_correlation("alert_1", "alert_2", 0.7)
        
        graph = tracker.get_graph()
        
        assert "nodes" in graph
        assert "edges" in graph
        assert "total_nodes" in graph
        assert "total_edges" in graph
        assert graph["total_nodes"] == 3
        assert len(graph["edges"]) == 2

    def test_cleanup_old_nodes_when_exceeds_max(self):
        """Should remove old nodes when exceeding max_nodes."""
        tracker = EventCorrelationTracker(max_nodes=10)
        
        # Add 15 events
        for i in range(15):
            event = {
                "type": "system.alert",
                "alert_id": f"alert_{i}",
                "timestamp": int(time.time() * 1000) + i * 100,
                "_nature": "incident",
            }
            tracker.add_event(event)
        
        # Should keep ~80% of max_nodes (8 nodes)
        assert len(tracker.nodes) <= 10
        assert len(tracker.nodes) >= 8

    def test_node_with_custom_id_extraction(self):
        """Should extract event ID from various event types."""
        tracker = EventCorrelationTracker()
        
        events = [
            {"type": "system.alert", "alert_id": "a1", "timestamp": int(time.time() * 1000), "_nature": "incident"},
            {"type": "madre.decision.explained", "decision_id": "d1", "timestamp": int(time.time() * 1000), "_nature": "decision"},
            {"type": "forensic.snapshot.created", "snapshot_id": "s1", "timestamp": int(time.time() * 1000), "_nature": "forensic"},
        ]
        
        for event in events:
            tracker.add_event(event)
        
        assert "a1" in tracker.nodes
        assert "d1" in tracker.nodes
        assert "s1" in tracker.nodes

    def test_graph_with_no_events(self):
        """get_graph should handle empty graph gracefully."""
        tracker = EventCorrelationTracker()
        graph = tracker.get_graph()
        
        assert graph["total_nodes"] == 0
        assert graph["total_edges"] == 0
        assert len(graph["nodes"]) == 0
        assert len(graph["edges"]) == 0

    def test_node_attributes_preserved(self):
        """Node attributes should be preserved in graph."""
        tracker = EventCorrelationTracker()
        event = {
            "type": "system.alert",
            "alert_id": "alert_1",
            "severity": "L4",
            "timestamp": 1234567890,
            "_nature": "incident",
        }
        tracker.add_event(event)
        
        graph = tracker.get_graph()
        node = graph["nodes"][0]
        
        assert node["type"] == "system.alert"
        assert node["severity"] == "L4"
        assert node["nature"] == "incident"
        assert node["timestamp"] == 1234567890


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
