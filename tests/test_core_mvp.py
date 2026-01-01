"""
VX11 CORE MVP: Pytest Test Suite

Tests for /vx11/* endpoints (single entrypoint)
Running against http://localhost:8000 with token vx11-test-token
"""

import pytest
import httpx
import json
from typing import Dict, Any

# Configuration
HOST = "http://localhost:8000"
TOKEN = "vx11-test-token"
HEADERS = {"X-VX11-Token": TOKEN, "Content-Type": "application/json"}
WRONG_TOKEN = "wrong-token"


@pytest.fixture
def client():
    """HTTP client for tests."""
    return httpx.Client(base_url=HOST, timeout=15.0)


# ============ AUTH TESTS ============


def test_vx11_intent_no_token(client):
    """Test: POST /vx11/intent without token should return 401."""
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "chat",
            "text": "test",
            "require": {"switch": False, "spawner": False},
        },
    )
    assert resp.status_code == 401
    assert "auth_required" in resp.text or resp.status_code == 401


def test_vx11_intent_wrong_token(client):
    """Test: POST /vx11/intent with wrong token should return 403."""
    headers = {"X-VX11-Token": WRONG_TOKEN, "Content-Type": "application/json"}
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "chat",
            "text": "test",
            "require": {"switch": False, "spawner": False},
        },
        headers=headers,
    )
    assert resp.status_code == 403
    assert "forbidden" in resp.text or resp.status_code == 403


# ============ CORE FUNCTIONALITY TESTS ============


def test_vx11_intent_sync_execution(client):
    """Test: POST /vx11/intent with require.switch=false returns DONE."""
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "chat",
            "text": "Analyze system state",
            "require": {"switch": False, "spawner": False},
            "priority": "P0",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    
    assert "correlation_id" in body
    assert body["status"] == "DONE"
    assert body["mode"] == "MADRE"
    assert body["provider"] == "fallback_local"
    assert body["degraded"] == False
    assert body["error"] is None


def test_vx11_intent_off_by_policy(client):
    """Test: POST /vx11/intent with require.switch=true returns off_by_policy."""
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "exec",
            "text": "Execute via switch",
            "require": {"switch": True, "spawner": False},
            "priority": "P1",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    
    assert body["status"] == "ERROR"
    assert body["error"] == "off_by_policy"
    assert body["mode"] == "FALLBACK"
    assert "SOLO_MADRE" in body["response"]["policy"]


def test_vx11_intent_spawner_path(client):
    """Test: POST /vx11/intent with require.spawner=true returns QUEUED."""
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "spawn",
            "text": "Spawn a task",
            "require": {"switch": False, "spawner": True},
            "priority": "P1",
            "payload": {"task_name": "test_spawn"},
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    
    assert body["status"] == "QUEUED"
    assert body["mode"] == "SPAWNER"
    assert body["provider"] == "spawner"
    assert "task_id" in body["response"]
    
    # Store correlation_id for result query test
    return body["correlation_id"]


def test_vx11_result_query(client):
    """Test: GET /vx11/result/{id} returns result."""
    # First, create a spawner intent
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "spawn",
            "require": {"switch": False, "spawner": True},
            "payload": {"task_name": "test"},
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    correlation_id = resp.json()["correlation_id"]
    
    # Query result
    resp = client.get(f"/vx11/result/{correlation_id}", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    
    assert body["correlation_id"] == correlation_id
    assert body["status"] in ["QUEUED", "RUNNING", "DONE"]
    assert "result" in body or body["result"] is not None


def test_vx11_status_endpoint(client):
    """Test: GET /vx11/status returns policy info."""
    resp = client.get("/vx11/status", headers=HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    
    assert "mode" in body
    assert body["mode"] in ["solo_madre", "windowed", "full"]
    assert "policy" in body
    assert "madre_available" in body
    assert isinstance(body["madre_available"], bool)


def test_health_endpoint(client):
    """Test: GET /health works without token."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    
    assert body["status"] == "ok"
    assert "module" in body
    assert "version" in body


# ============ CONTRACT VALIDATION TESTS ============


def test_intent_response_contract(client):
    """Test: Response conforms to CoreIntentResponse contract."""
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "chat",
            "text": "test",
            "require": {"switch": False, "spawner": False},
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    
    # Required fields per contract
    assert "correlation_id" in body
    assert "status" in body
    assert "mode" in body
    assert "provider" in body
    assert "degraded" in body
    assert "timestamp" in body
    
    # Type checks
    assert isinstance(body["correlation_id"], str)
    assert body["status"] in ["QUEUED", "RUNNING", "DONE", "ERROR"]
    assert body["mode"] in ["MADRE", "SWITCH", "FALLBACK", "SPAWNER"]
    assert isinstance(body["degraded"], bool)


def test_error_response_format(client):
    """Test: off_by_policy error response format."""
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "exec",
            "require": {"switch": True},
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    
    # Error response contract
    assert body["error"] == "off_by_policy"
    assert isinstance(body["response"], dict)
    assert "reason" in body["response"]
    assert "policy" in body["response"]


# ============ INTEGRATION TESTS ============


def test_full_sync_flow(client):
    """Test: Full flow from intent to result."""
    # Create intent
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "chat",
            "text": "Full flow test",
            "require": {"switch": False, "spawner": False},
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    intent_resp = resp.json()
    correlation_id = intent_resp["correlation_id"]
    
    # For sync execution, should already be DONE
    assert intent_resp["status"] == "DONE"
    
    # Query result anyway
    resp = client.get(f"/vx11/result/{correlation_id}", headers=HEADERS)
    assert resp.status_code == 200
    result_resp = resp.json()
    
    assert result_resp["correlation_id"] == correlation_id
    assert result_resp["status"] in ["DONE", "QUEUED"]


def test_policy_enforcement_in_flow(client):
    """Test: Policy enforced consistently across flow."""
    # Request switch (should be denied)
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "exec",
            "require": {"switch": True},
            "text": "Request switch",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    
    # Must be denied with off_by_policy
    assert body["error"] == "off_by_policy"
    assert "SOLO_MADRE" in body["response"]["policy"]
    
    # Compare with allowed request
    resp = client.post(
        "/vx11/intent",
        json={
            "intent_type": "exec",
            "require": {"switch": False},
            "text": "Request allowed",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    
    # Should be allowed
    assert body["status"] == "DONE"
    assert body["error"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
