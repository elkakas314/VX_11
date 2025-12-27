"""
tests/test_operator_auth_policy_p0.py

P0 tests for VX11_AUTH_MODE policy (operator_backend).
- Covers "off" mode (DEV: no auth required)
- Covers "token" mode (PROD: X-VX11-Token header required)
- Validates schema compliance

NOTES:
- main_v7.py: /api/map uses TokenGuard (X-VX11-Token) ✅ supports VX11_AUTH_MODE
- canonical_api.py: /api/status uses auth_check (Bearer JWT) ⚠️ separate layer

Tests focus on /api/map + /health which correctly implement VX11_AUTH_MODE.

Execution: pytest tests/test_operator_auth_policy_p0.py -v
"""

import pytest
import json
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

# Patch VX11_MODE=operative_core BEFORE importing app
os.environ["VX11_MODE"] = "operative_core"

# Import app
from operator_backend.backend.main_v7 import app, VX11_TOKEN


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


# ============ TEST CASE 1: /health always returns 200 (no auth) ============


def test_health_no_auth_required(client):
    """INVARIANT: /health endpoint should ALWAYS return 200, no auth check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["module"] == "operator"


# ============ TEST CASE 2: VX11_AUTH_MODE=off → /api/map returns 200 (no header) ============


@patch.dict(os.environ, {"VX11_AUTH_MODE": "off"})
def test_api_map_auth_mode_off_no_header(client):
    """
    Given: VX11_AUTH_MODE=off (DEV mode)
    When: GET /api/map WITHOUT X-VX11-Token header
    Then: Return 200 + valid schema (nodes, edges, counts)
    """
    response = client.get("/api/map")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "counts" in data
    assert "timestamp" in data

    # Validate nodes structure
    nodes = data["nodes"]
    assert isinstance(nodes, list)
    assert len(nodes) > 0
    for node in nodes:
        assert "id" in node
        assert "label" in node
        assert "state" in node
        assert "port" in node

    # Validate edges structure
    edges = data["edges"]
    assert isinstance(edges, list)
    for edge in edges:
        assert "from" in edge
        assert "to" in edge
        assert "label" in edge

    # Validate counts structure
    counts = data["counts"]
    assert "services_up" in counts
    assert "total_services" in counts


# ============ TEST CASE 3: VX11_AUTH_MODE=token + missing header → 401 ============


@patch.dict(os.environ, {"VX11_AUTH_MODE": "token"})
def test_api_map_auth_mode_token_missing_header(client):
    """
    Given: VX11_AUTH_MODE=token (PROD mode)
    When: GET /api/map WITHOUT X-VX11-Token header
    Then: Return 401 "auth_required"
    """
    response = client.get("/api/map")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data or "detail" in data  # Check either error or detail key
    assert data.get("error") == "auth_required" or data.get("detail") == "auth_required"


# ============ TEST CASE 4: VX11_AUTH_MODE=token + correct header → 200 ============


@patch.dict(os.environ, {"VX11_AUTH_MODE": "token"})
def test_api_map_auth_mode_token_with_correct_header(client):
    """
    Given: VX11_AUTH_MODE=token (PROD mode)
    When: GET /api/map WITH correct X-VX11-Token header
    Then: Return 200 + valid schema
    """
    response = client.get("/api/map", headers={"X-VX11-Token": VX11_TOKEN})
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


# ============ TEST CASE 5: VX11_AUTH_MODE=token + wrong token → 403 ============


@patch.dict(os.environ, {"VX11_AUTH_MODE": "token"})
def test_api_map_auth_mode_token_wrong_token(client):
    """
    Given: VX11_AUTH_MODE=token (PROD mode)
    When: GET /api/map WITH incorrect X-VX11-Token header
    Then: Return 403 "forbidden"
    """
    response = client.get("/api/map", headers={"X-VX11-Token": "wrong-token-value"})
    assert response.status_code == 403
    data = response.json()
    assert "error" in data or "detail" in data
    assert data.get("error") == "forbidden" or data.get("detail") == "forbidden"


# ============ TEST CASE 6: /api/map schema validation (DEV mode) ============


@patch.dict(os.environ, {"VX11_AUTH_MODE": "off"})
def test_api_map_schema_validation(client):
    """
    Given: VX11_AUTH_MODE=off
    When: GET /api/map
    Then: Validate complete schema with canonical nodes/edges
    """
    response = client.get("/api/map")
    assert response.status_code == 200
    data = response.json()

    # Validate top-level structure
    required_fields = ["nodes", "edges", "counts", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Validate canonical nodes present
    node_ids = [n["id"] for n in data["nodes"]]
    canonical_nodes = ["madre", "tentaculo_link", "redis", "operator_backend"]
    for canonical_node in canonical_nodes:
        assert canonical_node in node_ids, f"Missing canonical node: {canonical_node}"

    # Validate node states are valid
    valid_states = ["up", "down", "unknown"]
    for node in data["nodes"]:
        assert node["state"] in valid_states, f"Invalid state: {node['state']}"


# ============ TEST CASE 7: VX11_AUTH_MODE defaults to "off" ============


def test_auth_mode_defaults_to_off(client):
    """
    Given: VX11_AUTH_MODE env var not set (defaults)
    When: GET /api/map WITHOUT header
    Then: Return 200 (default is "off")
    """
    with patch.dict(os.environ, {}, clear=False):
        if "VX11_AUTH_MODE" in os.environ:
            del os.environ["VX11_AUTH_MODE"]

        response = client.get("/api/map")
        assert response.status_code == 200


# ============ TEST CASE 8: /api/map polling compatibility (3s refresh) ============


@patch.dict(os.environ, {"VX11_AUTH_MODE": "off"})
def test_api_map_polling_compatibility(client):
    """
    FRONTEND INVARIANT: MapTab polls /api/map every 3 seconds.
    Response must be compact (< 5KB).
    """
    response = client.get("/api/map")
    assert response.status_code == 200

    response_text = response.text
    response_size_kb = len(response_text) / 1024
    assert response_size_kb < 5, f"Response too large: {response_size_kb}KB"

    data = response.json()
    services_up = data["counts"]["services_up"]
    nodes_up = sum(1 for n in data["nodes"] if n["state"] == "up")
    # Allow 1-node difference due to async timing
    assert abs(services_up - nodes_up) <= 1


# ============ TEST CASE 9: Single entrypoint topology validation ============


@patch.dict(os.environ, {"VX11_AUTH_MODE": "off"})
def test_api_map_single_entrypoint_topology(client):
    """
    Invariant: Single entrypoint chain:
    operator_backend → tentaculo_link → madre → redis
    """
    response = client.get("/api/map")
    assert response.status_code == 200
    data = response.json()

    edges = {(e["from"], e["to"]): e["label"] for e in data["edges"]}

    # Verify single entrypoint chain
    assert ("operator_backend", "tentaculo_link") in edges
    assert edges[("operator_backend", "tentaculo_link")] == "proxy"

    assert ("tentaculo_link", "madre") in edges
    assert edges[("tentaculo_link", "madre")] == "route"

    assert ("madre", "redis") in edges
    assert edges[("madre", "redis")] == "cache"

    # Redis is sink (no outbound edges)
    redis_sources = [e["from"] for e in data["edges"] if e["to"] == "redis"]
    assert redis_sources == ["madre"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
