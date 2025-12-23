from switch.cli_concentrator.providers.copilot_cli import CopilotCLIProvider
from switch.cli_concentrator.schemas import ProviderConfig


def test_copilot_provider_exec_mock(monkeypatch):
    monkeypatch.setenv("VX11_MOCK_PROVIDERS", "1")
    config = ProviderConfig(
        provider_id="copilot_cli",
        kind="copilot_cli",
        priority=1,
        enabled=True,
        command="copilot-cli",
        args_template="chat {prompt}",
        auth_state="ok",
    )
    provider = CopilotCLIProvider(config)
    resp = provider.call("hola", metadata={})
    assert resp.get("success") is True
    assert resp.get("engine") == "copilot_cli"
    assert isinstance(resp.get("latency_ms"), int)
    assert "reply" in resp
