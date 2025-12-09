import asyncio
from fastapi.testclient import TestClient
from switch import main as switch_main


def test_select_local_fallback(monkeypatch):
    # ensure deepseek returns failure so selector falls back to local
    async def fake_deepseek(prompt, opts=None):
        return {"ok": False, "error": "no_key"}

    monkeypatch.setattr("config.deepseek.call_deepseek", lambda *a, **k: {"ok": False, "error": "no_key"})

    # call switch route with preference for deepseek but expect local fallback
    client = TestClient(switch_main.app)
    resp = client.post("/switch/route", json={"prompt": "hello", "providers": ["deepseek", "local"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("engine") == "local"
    assert "result" in data


def test_multi_provider_roundtrip(monkeypatch):
    # Force hermes to be unavailable and deepseek to be ok
    monkeypatch.setattr("config.deepseek.call_deepseek", lambda *a, **k: {"ok": True, "result": {"reply": "deep"}})
    client = TestClient(switch_main.app)
    resp = client.post("/switch/route", json={"prompt": "run this", "providers": ["hermes", "deepseek", "local"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("engine") in ("deepseek", "local", "hermes")
