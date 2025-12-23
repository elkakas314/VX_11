import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure the project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import from switch
from switch.main import app

client = TestClient(app)


pytestmark = pytest.mark.integration


def test_switch_auto_returns_engine():
    r = client.post("/switch/route", json={"prompt": "hello world", "mode": "auto"})
    assert r.status_code == 200
    body = r.json()
    assert "status" in body and body["status"] in ("ok", "queued", "partial")
    if "engine" in body:
        assert body["engine"] in ("local", "deepseek", "hermes")
    else:
        assert "model" in body
