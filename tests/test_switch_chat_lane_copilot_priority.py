from fastapi.testclient import TestClient

from switch.main import app as switch_app
from switch.cli_concentrator import registry as cli_registry
from switch.cli_concentrator.schemas import ProviderConfig


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


def test_switch_chat_falls_back_to_local_when_copilot_unusable(monkeypatch):
    monkeypatch.setenv("VX11_MOCK_PROVIDERS", "1")
    monkeypatch.setenv("VX11_COPILOT_CLI_ENABLED", "1")

    def _load_only_unusable_copilot(self):
        self.providers = {
            "copilot_cli": ProviderConfig(
                provider_id="copilot_cli",
                kind="copilot_cli",
                priority=1,
                enabled=True,
                command="copilot-cli",
                args_template="chat {prompt}",
                auth_state="needs_login",
                tags=["language", "general"],
            )
        }

    monkeypatch.setattr(cli_registry.CLIRegistry, "_load_providers", _load_only_unusable_copilot)
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
