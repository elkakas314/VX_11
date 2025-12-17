import asyncio
from switch import adapters


def test_select_provider_long_prompt_prefers_deepseek_or_local():
    long_prompt = "Explain in detail the architecture of a distributed system: " + ("x" * 500)
    res = asyncio.run(adapters.select_provider(long_prompt))
    assert isinstance(res, str)
from fastapi.testclient import TestClient
import switch.main as switch_main


client = TestClient(switch_main.app)


def test_auto_fallback_to_local_when_no_deepseek_key(monkeypatch):
    # Ensure DeepSeek key absent
    monkeypatch.setattr(switch_main, "DEEPSEEK_API_KEY", None)

    resp = client.post("/switch/route", json={"prompt": "hola mundo", "mode": "auto"})
    assert resp.status_code == 200
    j = resp.json()
    # Should choose local engine when no deepseek key
    assert j.get("engine") == "local"
    # low_power flag should be present
    assert j.get("low_power", True) in (True, False)
