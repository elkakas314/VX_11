"""
P0 tests for Operator backend auth + status contract.
"""

import pytest
from fastapi.testclient import TestClient

from tests.utils.operator_backend import load_operator_backend

module = load_operator_backend()
app = module.app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def stub_tentaculo(monkeypatch):
    async def fake_core(_: str):
        return {
            "status": "ok",
            "services": {
                "madre": {"status": "UP"},
                "redis": {"status": "UP"},
                "tentaculo_link": {"status": "UP"},
            },
        }

    async def fake_window(_: str):
        return {
            "mode": "solo_madre",
            "services": ["madre", "redis"],
            "ttl_seconds": None,
        }

    monkeypatch.setattr(module, "_get_core_health", fake_core)
    monkeypatch.setattr(module, "_get_window_status", fake_window)


# ============ TESTS ============


def test_health_no_auth_required(client, monkeypatch):
    monkeypatch.setattr(module.settings, "enable_auth", True)
    response = client.get("/operator/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "operator_backend"


def test_status_requires_auth(client, monkeypatch):
    monkeypatch.setattr(module.settings, "enable_auth", True)
    response = client.get("/operator/api/status")
    assert response.status_code == 401


def test_status_allows_token(client, monkeypatch):
    monkeypatch.setattr(module.settings, "enable_auth", True)
    response = client.get(
        "/operator/api/status",
        headers={module.TOKEN_HEADER: module.VX11_TOKEN},
    )
    assert response.status_code == 200
    data = response.json()
    assert "policy" in data
    assert "core_services" in data
    assert "timestamp" in data


def test_status_no_auth_mode(client, monkeypatch):
    monkeypatch.setattr(module.settings, "enable_auth", False)
    response = client.get("/operator/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
