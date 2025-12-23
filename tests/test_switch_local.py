from fastapi.testclient import TestClient
from switch import main as switch_main


def test_switch_local_route():
    client = TestClient(switch_main.app)
    payload = {"prompt": "hello", "mode": "local"}
    r = client.post("/switch/route", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert j.get("engine") == "local" or j.get("model")
