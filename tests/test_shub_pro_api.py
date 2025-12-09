import os
import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_memory_db(monkeypatch, tmp_path):
    # Usar BD en memoria para pruebas
    monkeypatch.setenv("SHUB_PRO_DB_URL", "sqlite:///:memory:")
    # Recargar módulos para tomar el nuevo env
    if "shubniggurath.pro.project_db" in importlib.sys.modules:
        importlib.reload(importlib.import_module("shubniggurath.pro.project_db"))
    import shubniggurath.pro.interface_api as api
    importlib.reload(api)
    return api.app


def test_pipeline_endpoint(app_with_memory_db, tmp_path):
    client = TestClient(app_with_memory_db)
    from config.settings import settings

    # Crear tono temporal
    import wave, math

    sr = 44100
    samples = [0.2 * math.sin(2 * math.pi * 440 * n / sr) for n in range(sr)]
    wav_path = tmp_path / "tone.wav"
    import array

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        int16 = array.array("h", [int(s * 32767) for s in samples])
        wf.writeframes(int16.tobytes())

    headers = {settings.token_header: settings.api_token}
    payload = {"project": "demo", "track": "t1", "path": str(wav_path), "output_dir": str(tmp_path)}
    r = client.post("/pipeline", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "ok"
    assert "metrics" in data
