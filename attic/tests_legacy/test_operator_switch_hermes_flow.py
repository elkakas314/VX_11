import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if "operator" in sys.modules and not hasattr(sys.modules["operator"], "__path__"):
    sys.modules.pop("operator")

"""
Ajuste VX11 v6.6 – anti-caos / drift / auditoría flujos (2025-12-05)

Smoke test que valida que Operator Backend enruta intents hacia Switch/Hermes
sin romper imports ni headers obligatorios.
"""
from fastapi.testclient import TestClient

from operator_backend.backend.main_v7 import app, VX11_TOKEN, settings


class DummyResp:
    def __init__(self, status_code: int = 200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"status": "ok", "echo": True}

    def json(self):
        return self._payload


class DummyHttpClient:
    def __init__(self):
        self.posts = []

    async def post(self, url: str, json=None, headers=None):
        self.posts.append({"url": url, "json": json, "headers": headers})
        return DummyResp(200, {"status": "ok", "proxy": True})

    async def get(self, url: str, headers=None):
        return DummyResp(200, {"status": "ok"})


def test_operator_intent_proxy(monkeypatch):
    """Test that /intent endpoint routes to switch with proper metadata enrichment."""
    calls = {}

    # Mock the SwitchClient class to track calls
    class MockSwitchClient:
        async def query_chat(self, messages, task_type, metadata):
            calls["messages"] = messages
            calls["task_type"] = task_type
            calls["metadata"] = metadata
            print(f"MockSwitchClient received metadata: {metadata}")
            return {"status": "ok", "proxy": True}

    # Patch the SwitchClient import in operator_backend.backend.main_v7
    monkeypatch.setattr(
        "operator_backend.backend.main_v7.SwitchClient",
        lambda: MockSwitchClient(),
    )

    client = TestClient(app)
    payload = {
        "intent_type": "chat",
        "data": {"message": "mezcla la voz"},
        "target": "switch",
        "metadata": {},
    }
    resp = client.post(
        "/intent",
        json=payload,
        headers={settings.token_header: VX11_TOKEN},
    )
    print(f"Response status: {resp.status_code}")
    print(f"Calls dict: {calls}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert calls["messages"][0]["content"] == "mezcla la voz"
    assert (
        calls["metadata"].get("mode") == "mix"
    ), f"Expected mode=mix, got {calls['metadata']}"
    assert calls["metadata"].get(
        "mix_ops"
    ), "Mixing ops must be derived for mezcla mode"


def test_operator_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"
