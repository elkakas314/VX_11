from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if "operator" in sys.modules and not hasattr(sys.modules["operator"], "__path__"):
    sys.modules.pop("operator")

from operator_backend.backend.main import app, operator_state, VX11_TOKEN, settings  # noqa: E402


class DummyResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_ui_status_aggregates(monkeypatch):
    operator_state.event_history = []

    class DummyClient:
        async def get(self, url, headers=None, timeout=None):
            return DummyResp(
                200,
                {
                    "services": {
                        "tentaculo_link": {"status": "ok"},
                        "switch": {"status": "ok"},
                    }
                },
            )

    async def _dummy_get_http_client():
        return DummyClient()

    monkeypatch.setattr("operator.backend.main.get_http_client", _dummy_get_http_client)

    client = TestClient(app)
    resp = client.get("/ui/status", headers={settings.token_header: VX11_TOKEN})
    assert resp.status_code == 200
    data = resp.json()
    assert "modules" in data
    assert data["modules"].get("tentaculo_link", {}).get("status") == "ok"


def test_ui_events_registers_chat(monkeypatch):
    operator_state.event_history = []

    async def dummy_chat(message, metadata, source="operator"):
        return {"status": "ok", "echo": message, "metadata": metadata, "source": source}

    monkeypatch.setattr("operator.backend.main.switch_client.chat", dummy_chat)

    client = TestClient(app)
    body = {"message": "mezcla la voz y bajo", "mode": "mix"}
    resp = client.post(
        "/intent/chat",
        json=body,
        headers={settings.token_header: VX11_TOKEN},
    )
    assert resp.status_code == 200

    events_resp = client.get("/ui/events", headers={settings.token_header: VX11_TOKEN})
    assert events_resp.status_code == 200
    events = events_resp.json().get("events", [])
    assert events, "Events list should contain the chat intent"
    assert events[0].get("type") in {"chat", "intent"}
