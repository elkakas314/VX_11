import wave
import math
from fastapi.testclient import TestClient
from shubniggurath.main import app
from shubniggurath.dsp_pipeline import analyze_audio
from config.settings import settings


def _make_tone(path: str, seconds: float = 1.0, freq: float = 440.0, sr: int = 44100):
    frames = bytearray()
    for n in range(int(sr * seconds)):
        val = int(0.2 * 32767 * math.sin(2 * math.pi * freq * n / sr))
        frames += val.to_bytes(2, byteorder="little", signed=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(frames))


def test_analyze_audio(tmp_path):
    wav = tmp_path / "tone.wav"
    _make_tone(str(wav))
    res = analyze_audio(str(wav))
    assert res["status"] == "ok"
    assert "rms" in res and "lufs" in res


def test_mode_c_endpoint(tmp_path):
    wav = tmp_path / "tone.wav"
    _make_tone(str(wav))
    client = TestClient(app)
    headers = {settings.token_header: settings.api_token}
    payload = {"project_name": "demo", "track_name": "tone", "audio_path": str(wav)}
    r = client.post("/v1/mode_c/run", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "ok"
    assert data["metrics"]["status"] == "ok"
