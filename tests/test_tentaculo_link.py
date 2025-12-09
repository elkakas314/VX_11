from fastapi.testclient import TestClient

from tentaculo_link.main import app, VX11_TOKEN
from config.settings import settings


client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("module") == "tentaculo_link"


def test_status_endpoint():
    resp = client.get("/vx11/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("ok") is True
    assert "ports" in data


def test_websocket_basic_echo():
    original_auth = settings.enable_auth
    settings.enable_auth = False  # simplify local test auth
    try:
        with client.websocket_connect("/ws?channel=event") as websocket:
            first = websocket.receive_json()
            assert first.get("channel") == "control"
            websocket.send_json(
                {"channel": "event", "type": "test", "target": "tester", "payload": {"hello": "world"}}
            )
            data = websocket.receive_json()
            assert data.get("channel") == "event"
    finally:
        settings.enable_auth = original_auth


def test_event_ingest_with_token():
    headers = {settings.token_header: VX11_TOKEN}
    resp = client.post(
        "/events/ingest",
        json={"source": "pytest", "type": "status", "payload": {"ok": True}, "broadcast": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json().get("status") == "received"
