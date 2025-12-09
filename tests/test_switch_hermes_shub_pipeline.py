import os
import uuid

import pytest
from fastapi.testclient import TestClient

from switch.main import PRIORITY_MAP, ModelPool, ModelState, _should_use_cli
from switch.hermes.main import _best_models_for
from madre.main import app as madre_app, ShubTaskRequest
from config.db_schema import get_session, ModelsLocal


def test_priority_order():
    assert PRIORITY_MAP["shub"] < PRIORITY_MAP["operator"] < PRIORITY_MAP["madre"]


def test_should_use_cli():
    assert _should_use_cli({"mode": "cli"}, 0, "m") is True
    assert _should_use_cli({"task_type": "cli_only"}, 0, "m") is True
    assert _should_use_cli({"allow_cli_fallback": True}, 6, "m") is True
    assert _should_use_cli({}, 0, "m") is False


def test_modelpool_rejects_large_models():
    pool = ModelPool(limit=5)
    pool.register(ModelState(name="too_big", size_mb=3000))
    assert "too_big" not in pool.available


def test_best_models_filtering(tmp_path):
    session = get_session("vx11")
    name = f"audio-{uuid.uuid4().hex[:6]}"
    try:
        m = ModelsLocal(name=name, path=str(tmp_path / f"{name}.bin"), size_mb=1500, category="audio", status="available")
        session.add(m)
        session.commit()
        models = _best_models_for("audio", 2048)
        assert any(item["name"] == name for item in models)
    finally:
        session.query(ModelsLocal).filter(ModelsLocal.name == name).delete()
        session.commit()
        session.close()


def test_madre_shub_task_testing(monkeypatch):
    monkeypatch.setattr("config.settings.settings.testing_mode", True, raising=False)
    client = TestClient(madre_app)
    payload = {"task_kind": "analyze", "input_path": "/tmp/file.wav"}
    res = client.post("/madre/shub/task", json=payload, headers={"X-VX11-Token": os.environ.get("VX11_LOCAL_TOKEN", "vx11-local-token")})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "queued"
    assert body["spawn"]["spawn"]["context"]["task_kind"] == "analyze"
