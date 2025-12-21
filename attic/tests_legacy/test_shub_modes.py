from fastapi.testclient import TestClient

from shubniggurath.main import app as shub_app


def test_shub_execute_modes():
    client = TestClient(shub_app)
    for mode in ["analyze", "mix", "master", "render"]:
        resp = client.post("/shub/execute", json={"task_id": f"t-{mode}", "task_type": "audio", "mode": mode, "payload": {}})
        data = resp.json()
        assert resp.status_code == 200
        assert data.get("status") == "ok"
        assert data.get("output", {}).get("mode") == mode
