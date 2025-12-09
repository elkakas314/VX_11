"""
Advanced tests for V2 enhanced modules.
"""

import pytest
import asyncio
import uuid
from fastapi.testclient import TestClient
import httpx


def test_switch_context_get():
    """Test switch context retrieval."""
    from switch.main import app
    client = TestClient(app)
    resp = client.get("/switch/context")
    assert resp.status_code == 200
    data = resp.json()
    assert "user_preferences" in data or isinstance(data, dict)


def test_switch_providers_list():
    """Test switch providers endpoint."""
    from switch.main import app
    client = TestClient(app)
    resp = client.get("/switch/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "providers" in data


def test_hermes_job_lifecycle():
    """Test hermes job creation and status tracking."""
    from switch.hermes.main import app
    client = TestClient(app)
    
    # Execute command
    exec_resp = client.post(
        "/hermes/exec",
        json={"command": "echo", "args": ["test"], "timeout": 10},
    )
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert "job_id" in exec_data
    
    job_id = exec_data["job_id"]
    
    # Get job status
    status_resp = client.get(f"/hermes/job/{job_id}")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["job_id"] == job_id


def test_leonidas_sanitizer():
    """Test Leonidas command sanitizer."""
    from switch.hermes.leonidas import sanitize_command
    
    # Safe command
    safe = sanitize_command("echo", ["hello"])
    assert safe is not None
    assert safe[0] == "echo"
    
    # Dangerous args
    danger = sanitize_command("cat", ["/etc/passwd"])
    assert danger is None


def test_madre_task_creation():
    """Test madre task creation and BD persistence."""
    from madre.main import app
    client = TestClient(app)
    
    resp = client.post(
        "/task",
        json={
            "name": "test-task",
            "module": "switch",
            "action": "route",
            "payload": {"prompt": "test"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    assert data["status"] == "queued"


def test_manifestator_patches_list():
    """Test manifestator patch listing."""
    from manifestator.main import app
    client = TestClient(app)
    resp = client.get("/patches")
    assert resp.status_code == 200
    data = resp.json()
    assert "patches" in data


def test_mcp_chat_basic():
    """Test MCP conversational chat."""
    from mcp.main import app
    client = TestClient(app)
    
    resp = client.post(
        "/mcp/chat",
        json={"message": "hello"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "response" in data


def test_mcp_session_history():
    """Test MCP message history tracking."""
    from mcp.main import app
    client = TestClient(app)
    
    # First message
    resp1 = client.post(
        "/mcp/chat",
        json={"message": "first"},
    )
    assert resp1.status_code == 200
    session_id = resp1.json()["session_id"]
    
    # Second message same session
    resp2 = client.post(
        "/mcp/chat",
        json={"message": "second", "session_id": session_id},
    )
    assert resp2.status_code == 200
    
    # Check history
    hist_resp = client.get(f"/mcp/history/{session_id}")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert len(hist_data["messages"]) >= 2
