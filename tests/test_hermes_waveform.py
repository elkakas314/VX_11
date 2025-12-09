import os
import wave
from fastapi.testclient import TestClient
from switch.hermes.main import app, _ALLOWED_BASE
from config.settings import settings


def _make_wav(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes(b"\x00\x00" * 44100)  # 1s silencio


def test_waveform_and_spectrogram(tmp_path):
    base = _ALLOWED_BASE
    os.makedirs(base, exist_ok=True)
    wav_path = os.path.join(base, "hermes_test.wav")
    _make_wav(wav_path)
    client = TestClient(app)
    headers = {settings.token_header: settings.api_token}
    wf = client.post("/waveform", json={"path": wav_path}, headers=headers)
    assert wf.status_code == 200, wf.text
    sp = client.post("/spectrogram", json={"path": wav_path}, headers=headers)
    assert sp.status_code == 200, sp.text
