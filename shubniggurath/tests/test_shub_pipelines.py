import asyncio

from shubniggurath.core.registry import get_engine


def test_mix_pipeline_basic():
    engine = get_engine()
    stems = {"vox": [0.1, 0.2], "drums": [0.0, -0.1, 0.3]}
    result = asyncio.get_event_loop().run_until_complete(engine.mix(stems, {}))
    assert result["validation"]["vox"] == 2
    assert "mixed" in result


def test_event_ready_stub():
    engine = get_engine()
    result = asyncio.get_event_loop().run_until_complete(engine.event_ready({"source": "test"}))
    assert result["status"] == "ready"
