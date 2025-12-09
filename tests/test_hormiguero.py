from fastapi.testclient import TestClient
from hormiguero import main as hormiguero_main


client = TestClient(hormiguero_main.app)


def test_create_and_list_task():
    # Create a task
    payload = {"task_type": "test", "payload": {"x": 1}}
    r = client.post("/hormiguero/task", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "created"
    tid = data["task_id"]

    # List tasks and ensure the created task appears
    r2 = client.get("/hormiguero/tasks")
    assert r2.status_code == 200
    items = r2.json()
    assert any(t["task_id"] == tid for t in items)
