import asyncio
from tentaculo_link import main_v7


def test_health_sync():
    # Call the health endpoint function directly
    resp = asyncio.run(main_v7.health())
    assert isinstance(resp, dict)
    assert resp.get("status") == "ok"
    assert resp.get("module") == "tentaculo_link"
