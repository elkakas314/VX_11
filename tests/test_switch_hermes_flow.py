import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient

from switch.main import app as switch_app, AUTH_HEADERS as SWITCH_HEADERS
from switch.hermes.main import app as hermes_app
from config.db_schema import get_session, ModelsLocal
from spawner.main import app as spawner_app, AUTH_HEADERS as SPAWNER_HEADERS
from shubniggurath.main import app as shub_app


class DummyResponse:
    def __init__(self, json_data=None, status_code=200):
        self._json = json_data or {}
        self.status_code = status_code

    def json(self):
        return self._json


class DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        self.calls = kwargs.get("calls")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None, timeout=None):
        if self.calls is not None:
            self.calls.append(url)
        return DummyResponse({"status": "ok", "url": url})

    async def get(self, url, headers=None, timeout=None):
        if self.calls is not None:
            self.calls.append(url)
        return DummyResponse({"status": "healthy"})


def test_switch_hermes_infer_calls_execute(monkeypatch):
    calls = []
    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: DummyAsyncClient(calls=calls))
    client = TestClient(switch_app)
    resp = client.post(
        "/switch/hermes/infer",
        json={"prompt": "hi", "metadata": {"task_type": "general"}, "source": "operator"},
        headers=SWITCH_HEADERS,
    )
    assert resp.status_code == 200
    assert any("/hermes/execute" in c for c in calls)


def test_hermes_execute_prunes_limit(monkeypatch):
    client = TestClient(hermes_app)
    # Registrar más de 30 modelos para disparar pruning
    for i in range(35):
        resp = client.post("/hermes/register_model", json={"name": f"m{i}", "size_mb": 10, "category": "general"})
        assert resp.status_code == 200
    session = get_session("vx11")
    try:
        count = session.query(ModelsLocal).count()
        assert count <= 30
    finally:
        session.close()


def test_spawner_sends_callback(monkeypatch):
    # Stub sandbox execution
    async def _stub(req):
        return {"status": "completed", "stdout": ""}
    monkeypatch.setattr("spawner.main._execute_in_sandbox", _stub)
    calls = []
    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: DummyAsyncClient(calls=calls))
    client = TestClient(spawner_app)
    resp = client.post(
        "/spawn",
        json={"name": "job", "cmd": "echo", "args": ["hi"]},
        headers=SPAWNER_HEADERS,
    )
    assert resp.status_code == 200
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))
    assert any("/madre/callback" in c for c in calls)


def test_shub_execute_contract():
    client = TestClient(shub_app)
    resp = client.post("/shub/execute", json={"task_id": "t1", "task_type": "audio_mix", "payload": {"path": "x"}})
    data = resp.json()
    assert resp.status_code == 200
    assert data.get("status") == "stub"
    assert data.get("engine") == "shub"
