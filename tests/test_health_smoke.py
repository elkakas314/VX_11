"""
Smoke tests básicos de /health para módulos núcleo VX11 v6.7.
No tocan Shub ni audio.
"""

from pathlib import Path
import sys
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if "operator" in sys.modules and not hasattr(sys.modules["operator"], "__path__"):
    sys.modules.pop("operator")


def _check_health(app, headers=None):
    client = TestClient(app)
    resp = client.get("/health", headers=headers or {})
    assert resp.status_code == 200
    status_val = resp.json().get("status")
    assert status_val in {"ok", "healthy", True}


def test_tentaculo_link_health():
    from tentaculo_link.main import app
    _check_health(app)


def test_madre_health():
    from madre.main import app
    _check_health(app)


def test_switch_health():
    from switch.main import app, VX11_TOKEN, settings
    _check_health(app, {settings.token_header: VX11_TOKEN})


def test_hermes_health():
    from switch.hermes.main import app, VX11_TOKEN, settings
    _check_health(app, {settings.token_header: VX11_TOKEN})


def test_hormiguero_health():
    from hormiguero.main import app, VX11_TOKEN, settings
    _check_health(app, {settings.token_header: VX11_TOKEN})


def test_mcp_health():
    from mcp.main import app, VX11_TOKEN, settings
    _check_health(app, {settings.token_header: VX11_TOKEN})


def test_spawner_health():
    from spawner.main import app
    _check_health(app)


def test_operator_backend_health():
    from operator_backend.backend.main import app
    _check_health(app)


def test_manifestator_health():
    from manifestator.main import app, VX11_TOKEN, settings
    _check_health(app, {settings.token_header: VX11_TOKEN})
