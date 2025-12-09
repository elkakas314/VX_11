from fastapi.testclient import TestClient
from switch.hermes.main import app as hermes_app


def test_hermes_available():
    client = TestClient(hermes_app)
    r = client.get("/hermes/available")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data or "binaries" in data
    assert "binaries" in data
    # binaries values should be booleans
    bins = data["binaries"]
    assert isinstance(bins, dict)
    for k, v in bins.items():
        assert isinstance(v, bool)
