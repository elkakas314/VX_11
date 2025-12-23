import os
import sys
from fastapi.testclient import TestClient

# Ensure the project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import settings
from switch.main import app

# ensure no deepseek key for simulating fallback
settings.deepseek_api_key = None

client = TestClient(app)


def test_switch_deepseek_fallback_when_no_key():
    r = client.post(
        "/switch/route",
        json={"prompt": "this is a long prompt to prefer deep reasoning in real world"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "queued", "partial")
    if "engine" in body:
        assert body["engine"] in ("local", "hermes", "deepseek")
    else:
        assert "model" in body
