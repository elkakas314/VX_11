import asyncio
import time
from fastapi.testclient import TestClient
import pytest

import tentaculo_link.main_v7 as main_v7
import config.forensics as forensics
import tentaculo_link.clients as clients_mod
import tentaculo_link.context7_middleware as context7_mod

# Disable file-based forensics logging during offline tests
main_v7.write_log = lambda *a, **k: None
# Also disable the shared forensics writer used across modules
forensics.write_log = lambda *a, **k: None
# Disable imported write_log references in modules that imported it at import-time
clients_mod.write_log = lambda *a, **k: None
context7_mod.write_log = lambda *a, **k: None


class FakeClients:
    def __init__(self):
        self.clients = {}

    async def startup(self):
        return None

    async def shutdown(self):
        return None

    async def health_check_all(self):
        return {"switch": {"status": "ok"}}

    async def route_to_switch(self, prompt: str, session_id: str = "", metadata=None):
        return {"session_id": session_id or "s1", "response": "ok"}

    async def route_to_switch_task(
        self,
        task_type: str,
        payload: dict,
        metadata=None,
        provider_hint=None,
        source: str = "operator",
    ):
        return {"task_type": task_type, "status": "ok"}


class CBOpenClients(FakeClients):
    async def route_to_switch(self, *args, **kwargs):
        return {
            "status": "service_offline",
            "module": "switch",
            "reason": "circuit_open",
        }


class TimeoutClients(FakeClients):
    async def route_to_switch(self, *args, **kwargs):
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="timeout")


def test_health_ok():
    with TestClient(main_v7.app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json().get("module") == "tentaculo_link"


def test_vx11_status_contains_version(monkeypatch):
    fake = FakeClients()
    monkeypatch.setattr(main_v7, "get_clients", lambda: fake)
    with TestClient(main_v7.app) as client:
        r = client.get("/vx11/status")
        assert r.status_code == 200
        assert "version" in r.json()


def test_protected_route_without_token_returns_401(monkeypatch):
    fake = FakeClients()
    monkeypatch.setattr(main_v7, "get_clients", lambda: fake)
    # Ensure auth enabled
    monkeypatch.setattr(main_v7.settings, "enable_auth", True)
    with TestClient(main_v7.app) as client:
        r = client.post("/operator/chat", json={"message": "hi"})
        assert r.status_code in (401, 403)


def test_invalid_intent_returns_client_error(monkeypatch):
    fake = FakeClients()
    monkeypatch.setattr(main_v7, "get_clients", lambda: fake)
    monkeypatch.setattr(main_v7.settings, "enable_auth", False)
    with TestClient(main_v7.app) as client:
        # Missing required fields -> pydantic validation error (422)
        r = client.post("/operator/task", json={})
        assert r.status_code >= 400 and r.status_code < 500


def test_routing_to_switch_is_mocked(monkeypatch):
    fake = FakeClients()
    monkeypatch.setattr(main_v7, "get_clients", lambda: fake)
    monkeypatch.setattr(main_v7.settings, "enable_auth", True)
    headers = {main_v7.settings.token_header: main_v7.VX11_TOKEN}
    with TestClient(main_v7.app) as client:
        r = client.post("/operator/chat", json={"message": "hello"}, headers=headers)
        assert r.status_code == 200
        assert r.json().get("response") == "ok"


def test_circuit_breaker_open_returns_service_offline(monkeypatch):
    fake = CBOpenClients()
    monkeypatch.setattr(main_v7, "get_clients", lambda: fake)
    monkeypatch.setattr(main_v7.settings, "enable_auth", True)
    headers = {main_v7.settings.token_header: main_v7.VX11_TOKEN}
    with TestClient(main_v7.app) as client:
        r = client.post("/operator/chat", json={"message": "hello"}, headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert (
            body.get("status") == "service_offline"
            or body.get("reason") == "circuit_open"
            or body.get("response") is None
        )


def test_timeout_propagates_503(monkeypatch):
    fake = TimeoutClients()
    monkeypatch.setattr(main_v7, "get_clients", lambda: fake)
    monkeypatch.setattr(main_v7.settings, "enable_auth", True)
    headers = {main_v7.settings.token_header: main_v7.VX11_TOKEN}
    with TestClient(main_v7.app) as client:
        r = client.post("/operator/chat", json={"message": "hello"}, headers=headers)
        assert r.status_code == 503


def test_context7_ttl_expiry(monkeypatch):
    # Replace context7 manager with a testable TTL manager
    class TTLManager:
        def __init__(self, ttl_seconds=1):
            self.sessions = {}
            self.ttl = ttl_seconds

        def add_message(self, session_id, role, content, metadata=None):
            now = time.time()
            self.sessions[session_id] = {"messages": [(role, content, now)], "ts": now}

        def get_hint_for_llm(self, session_id):
            rec = self.sessions.get(session_id)
            if not rec:
                return ""
            if time.time() - rec["ts"] > self.ttl:
                return ""
            return "hint"

    ttl = TTLManager(ttl_seconds=0.5)
    monkeypatch.setattr(main_v7, "get_context7_manager", lambda: ttl)
    fake = FakeClients()
    monkeypatch.setattr(main_v7, "get_clients", lambda: fake)
    monkeypatch.setattr(main_v7.settings, "enable_auth", True)
    headers = {main_v7.settings.token_header: main_v7.VX11_TOKEN}
    with TestClient(main_v7.app) as client:
        # add message
        r = client.post(
            "/operator/chat",
            json={"message": "hi", "session_id": "s1"},
            headers=headers,
        )
        assert r.status_code == 200
        # wait for TTL to expire
        time.sleep(0.6)
        # hint should be empty after expiry
        assert ttl.get_hint_for_llm("s1") == ""
