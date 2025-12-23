import httpx
from fastapi.testclient import TestClient

from switch.hermes.main import app as hermes_app
from config.db_schema import ModelRegistry, get_session


def test_hermes_discover_offline_fallback(monkeypatch):
    async def fake_get(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    monkeypatch.setenv("VX11_HERMES_DOWNLOAD_ENABLED", "0")

    client = TestClient(hermes_app)
    resp = client.post("/hermes/discover", json={"apply": True, "allow_web": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in ("ok", "error")
    results = data.get("results") or {}
    web = results.get("tier3_web") or []
    assert results.get("download_attempted") is False
    assert web
    assert "download_url" in web[0]

    session = get_session("vx11")
    try:
        name = web[0].get("model_id") or web[0].get("model_name")
        entry = session.query(ModelRegistry).filter_by(name=name).first()
        assert entry is not None
    finally:
        if web:
            name = web[0].get("model_id") or web[0].get("model_name")
            if name:
                session.query(ModelRegistry).filter_by(name=name).delete()
                session.commit()
        session.close()
