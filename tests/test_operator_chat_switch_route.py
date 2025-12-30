from fastapi.testclient import TestClient

import tentaculo_link.main_v7 as tentaculo


class StubSwitchClient:
    async def post(self, path, payload, timeout=None):
        return {
            "status": "ok",
            "response": "stubbed switch response",
            "model": "switch_stub",
        }


class StubClients:
    def get_client(self, name):
        if name == "switch":
            return StubSwitchClient()
        return None


def test_operator_chat_routes_to_switch(monkeypatch):
    monkeypatch.setattr(tentaculo, "get_clients", lambda: StubClients())
    client = TestClient(tentaculo.app)
    headers = {tentaculo.settings.token_header: tentaculo.VX11_TOKEN}
    resp = client.post(
        "/operator/api/chat",
        json={"message": "ping", "session_id": "test_session"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("fallback_source") == "switch_cli_copilot"
    assert data.get("degraded") is False
    assert data.get("response") == "stubbed switch response"
