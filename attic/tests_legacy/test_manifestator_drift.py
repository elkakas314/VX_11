from fastapi.testclient import TestClient
from manifestator import main as manifestator_main


def test_drift_endpoint():
    client = TestClient(manifestator_main.app)
    r = client.get("/drift")
    assert r.status_code == 200
    data = r.json()
    assert "expected_modules" in data or "real_modules" in data
