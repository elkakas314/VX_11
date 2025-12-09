import asyncio
from switch import adapters


def test_select_provider_returns_string():
    res = asyncio.run(adapters.select_provider("Hello world"))
    assert isinstance(res, str)


def test_select_provider_with_docker_hint():
    # Accept either docker_cli or a fallback provider
    res = asyncio.run(adapters.select_provider("list docker containers"))
    assert isinstance(res, str)
