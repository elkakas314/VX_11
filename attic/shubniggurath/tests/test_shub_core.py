import asyncio

from shubniggurath.core.registry import get_engine


def test_engine_health():
    engine = get_engine()
    health = asyncio.get_event_loop().run_until_complete(engine.health())
    assert health["status"] == "ok"
    assert "pipelines" in health


def test_engine_analyze_basic():
    engine = get_engine()
    audio = [0.0, 0.5, -0.25, 0.1]
    result = asyncio.get_event_loop().run_until_complete(engine.analyze(audio, 48000, {"style": "test"}))
    assert "analysis" in result
    assert result["analysis"]["peak"] == 0.5
