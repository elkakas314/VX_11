from fastapi.testclient import TestClient
from mcp import main as mcp_main


def test_mcp_ping():
    client = TestClient(mcp_main.app)
    r = client.post("/mcp/action", json={"action": "ping"})
    assert r.status_code == 200
    j = r.json()
    assert j.get("result") == "pong"
