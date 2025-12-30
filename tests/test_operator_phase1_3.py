"""
Operator backend P0/P1 behavior tests aligned to current API.
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
    monkeypatch.setattr(module.settings, "enable_auth", False)


def test_modules_list(client):
    response = client.get("/operator/api/modules")
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert isinstance(data["modules"], dict)


def test_settings_read_only_by_default(client):
    response = client.get("/operator/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["read_only"] is True
    assert data["policy"] == "solo_madre"


def test_settings_update_blocked_by_policy(client):
    response = client.post("/operator/api/settings", json={"chat": {"temperature": 0.9}})
    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "OFF_BY_POLICY"


def test_chat_blocked_by_policy(client):
    response = client.post("/operator/api/chat", json={"message": "test"})
    assert response.status_code == 403
    data = response.json()
    assert data["status"] == "OFF_BY_POLICY"


def test_settings_update_allowed_when_window_active(client, monkeypatch):
    async def active_window(_: str):
        return {"mode": "window_active", "services": ["switch"]}

    monkeypatch.setattr(module, "_get_window_status", active_window)

    response = client.post("/operator/api/settings", json={"chat": {"temperature": 0.4}})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["settings"]["chat"]["temperature"] == 0.4
