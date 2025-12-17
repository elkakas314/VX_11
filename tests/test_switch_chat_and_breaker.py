import pytest
from fastapi.testclient import TestClient

from switch.main import app as switch_app, breaker


pytestmark = pytest.mark.integration


def test_switch_chat_endpoint():
    client = TestClient(switch_app)
    resp = client.post(
        "/switch/chat", json={"messages": [{"role": "user", "content": "hola"}]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "reply" in data


def test_circuit_breaker_half_open():
    provider = "test-provider"
    breaker.record_failure(provider)
    breaker.record_failure(provider)
    breaker.record_failure(provider)
    assert (
        breaker.allow(provider) is False or breaker.state[provider]["state"] == "OPEN"
    )
    # Force half-open transition
    breaker.state[provider]["opened_at"] = (
        breaker.state[provider]["opened_at"] - breaker.reset_timeout - 1
    )
    assert breaker.allow(provider) is True
