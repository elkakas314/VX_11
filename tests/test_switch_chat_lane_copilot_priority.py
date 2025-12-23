import pytest
from fastapi.testclient import TestClient

from switch.main import app as switch_app
from switch.cli_concentrator import registry as cli_registry


@pytest.mark.integration
def test_switch_chat_uses_copilot_when_usable(monkeypatch):
    monkeypatch.setenv("VX11_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("VX11_COPILOT_CLI_ENABLED", "1")

    monkeypatch.setattr(
        cli_registry.CLIRegistry,
        "_detect_copilot_command",
        lambda self: {"command": "copilot-cli", "args_template": "chat {prompt}"},
    )
    monkeypatch.setattr(
        cli_registry.CLIRegistry,
        "_check_copilot_auth",
        lambda self, cmd: True,
    )
    cli_registry._registry = None

    client = TestClient(switch_app)
    resp = client.post(
        "/switch/chat",
        json={"messages": [{"role": "user", "content": "hola"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("engine_used") == "copilot_cli"
    assert data.get("used_cli") is True


@pytest.mark.integration
def test_switch_chat_falls_back_to_local_when_copilot_unusable(monkeypatch):
    monkeypatch.setenv("VX11_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("VX11_COPILOT_CLI_ENABLED", "1")

    monkeypatch.setattr(
        cli_registry.CLIRegistry,
        "_detect_copilot_command",
        lambda self: {"command": "copilot-cli", "args_template": "chat {prompt}"},
    )
    monkeypatch.setattr(
        cli_registry.CLIRegistry,
        "_check_copilot_auth",
        lambda self, cmd: False,
    )
    cli_registry._registry = None

    client = TestClient(switch_app)
    resp = client.post(
        "/switch/chat",
        json={"messages": [{"role": "user", "content": "hola"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("engine_used") == "general-7b"
    assert data.get("used_cli") is False
    assert data.get("fallback_reason")
