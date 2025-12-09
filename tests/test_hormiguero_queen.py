from fastapi.testclient import TestClient
from hormiguero.main import app as horm_app


def test_hormiguero_health():
    client = TestClient(horm_app)
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
