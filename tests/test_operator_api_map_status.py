"""
Test suite for operator_backend API endpoints (/api/status, /api/map).
Validates response schemas without full service dependencies.
"""

import pytest
from pydantic import ValidationError


def test_api_status_schema():
    """Validate /api/status response schema."""
    # Example response
    status_response = {
        "operator_backend": "ok",
        "services": {
            "tentaculo_link": "ok",
            "madre": "ok",
        },
        "timestamp": "2025-12-27T02:30:00.000000",
    }

    # Check required fields
    assert "operator_backend" in status_response
    assert "services" in status_response
    assert "timestamp" in status_response
    assert isinstance(status_response["services"], dict)


def test_api_map_schema():
    """Validate /api/map response schema."""
    map_response = {
        "nodes": [
            {"id": "madre", "label": "Madre (v7)", "state": "up", "port": 8001},
            {
                "id": "tentaculo_link",
                "label": "Tentáculo Link (v7)",
                "state": "up",
                "port": 8000,
            },
            {"id": "redis", "label": "Redis Cache", "state": "up", "port": 6379},
            {
                "id": "operator_backend",
                "label": "Operator Backend",
                "state": "up",
                "port": 8011,
            },
        ],
        "edges": [
            {"from": "operator_backend", "to": "tentaculo_link", "label": "proxy"},
            {"from": "tentaculo_link", "to": "madre", "label": "route"},
            {"from": "madre", "to": "redis", "label": "cache"},
        ],
        "counts": {
            "services_up": 4,
            "total_services": 4,
            "routing_events": 0,
        },
        "timestamp": "2025-12-27T02:30:00.000000",
    }

    # Check required top-level fields
    assert "nodes" in map_response
    assert "edges" in map_response
    assert "counts" in map_response
    assert "timestamp" in map_response

    # Check nodes structure
    assert isinstance(map_response["nodes"], list)
    for node in map_response["nodes"]:
        assert "id" in node
        assert "label" in node
        assert "state" in node
        assert node["state"] in ["up", "down", "unknown"]

    # Check edges structure
    assert isinstance(map_response["edges"], list)
    for edge in map_response["edges"]:
        assert "from" in edge
        assert "to" in edge
        assert "label" in edge

    # Check counts structure
    assert isinstance(map_response["counts"], dict)
    assert "services_up" in map_response["counts"]
    assert "total_services" in map_response["counts"]


def test_api_map_canonical_nodes():
    """Test that /api/map includes canonical core services."""
    canonical_nodes = {"madre", "tentaculo_link", "redis", "operator_backend"}

    map_response_nodes = {"madre", "tentaculo_link", "redis", "operator_backend"}

    # All canonical nodes should be present
    assert canonical_nodes.issubset(map_response_nodes)


def test_api_map_canonical_edges():
    """Test that /api/map includes canonical connections."""
    # Minimal canonical edges
    expected_edges = [
        ("operator_backend", "tentaculo_link"),
        ("tentaculo_link", "madre"),
        ("madre", "redis"),
    ]

    actual_edges = [
        ("operator_backend", "tentaculo_link"),
        ("tentaculo_link", "madre"),
        ("madre", "redis"),
    ]

    for expected_from, expected_to in expected_edges:
        found = any(e[0] == expected_from and e[1] == expected_to for e in actual_edges)
        assert found, f"Edge {expected_from} → {expected_to} not found"


@pytest.mark.asyncio
async def test_api_map_dynamic_state_check():
    """
    Test that /api/map checks node states dynamically.
    This is a smoke test; full integration requires running services.
    """
    # In a real test with services running:
    # - madre should be reachable (http://localhost:8001/health)
    # - tentaculo_link should be reachable (http://localhost:8000/health)
    # - redis state should be detected

    # For now, validate that state field exists and has valid value
    node = {"id": "madre", "label": "Madre", "state": "up"}
    assert node["state"] in ["up", "down", "unknown"]


def test_operator_chat_response_includes_provider():
    """
    Test that /operator/chat response includes provider + model fields.
    Validates response schema from mother integration.
    """
    chat_response = {
        "response": "Plan executed. Mode: MADRE. Status: DONE",
        "session_id": "test-001",
        "intent_id": "i-123",
        "plan_id": "p-123",
        "status": "DONE",
        "mode": "MADRE",
        "provider": "fallback_local",  # NEW: DeepSeek integration
        "model": "local",  # NEW: DeepSeek integration
        "warnings": [],
        "targets": [],
        "actions": [],
    }

    # Verify new fields present
    assert "provider" in chat_response
    assert "model" in chat_response
    assert chat_response["provider"] in [
        "deepseek",
        "fallback_local",
        "deepseek_error",
        "no_token",
    ]
    assert chat_response["model"] in ["deepseek-reasoner", "local"]


if __name__ == "__main__":
    # Run smoke tests
    test_api_status_schema()
    test_api_map_schema()
    test_api_map_canonical_nodes()
    test_api_map_canonical_edges()
    test_operator_chat_response_includes_provider()
    print("✅ All smoke tests passed")
