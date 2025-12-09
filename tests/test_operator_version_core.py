from pathlib import Path
import sys

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if "operator" in sys.modules and not hasattr(sys.modules["operator"], "__path__"):
    sys.modules.pop("operator")

from operator_backend.backend.main import app, settings  # noqa: E402


client = TestClient(app)
HEADERS = {settings.token_header: "vx11-local-token"}


def test_ui_status_includes_version():
    resp = client.get("/ui/status", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("version") == "7.1-core"
    assert "modules" in data
