from fastapi.testclient import TestClient
from madre.main import app, _MODULE_STATES
from config.db_schema import get_session, ModuleHealth
from config.settings import settings


def test_madre_sets_off_on_errors():
    session = get_session("madre")
    # ensure health entry
    h = session.query(ModuleHealth).filter_by(module="hermes").first()
    if not h:
        h = ModuleHealth(module="hermes", status="error", error_count=5)
        session.add(h)
    else:
        h.error_count = 5
    session.commit()

    client = TestClient(app)
    headers = {settings.token_header: settings.api_token}
    res = client.get("/orchestration/module_states", headers=headers)
    assert res.status_code == 200
    assert res.json()["modules"].get("hermes") == "off"

    # reset state to avoid leaking to other tests
    _MODULE_STATES["hermes"] = "active"
