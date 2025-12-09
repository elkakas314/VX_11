from fastapi.testclient import TestClient
import os
import pytest
from mcp.main import app as mcp_app
from config.settings import settings

pytestmark = pytest.mark.skipif(
    not os.getenv("VX11_RUN_INTEGRATION"),
    reason="integration tests require running services"
)


def test_mcp_route_delegates_to_switch():
    client = TestClient(mcp_app)
    payload = {"action": "route", "params": {"input": "Hello test route", "mode": "auto"}}
    r = client.post("/mcp/action", json=payload)
    assert r.status_code == 200
    data = r.json()
    # should return a dict with status or engine keys
    assert isinstance(data, dict)
    assert "status" in data or "engine" in data
from fastapi.testclient import TestClient
from mcp import main as mcp_main
import switch


def test_mcp_uses_switch(monkeypatch):
    # Mock switch selection function
    monkeypatch.setattr("switch.main._select_provider_smart", lambda prompt, mode="auto": "local")
    client = TestClient(mcp_main.app)
    # basic ping to validate mcp endpoint
    resp = client.post("/mcp/action", json={"action": "ping"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("result") == "pong"
