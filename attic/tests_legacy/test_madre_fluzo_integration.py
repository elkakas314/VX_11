"""
Tests for Madre FLUZO integration (Phase 4).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from config.settings import settings
from madre.fluzo_integration import (
    get_fluzo_hints,
    apply_fluzo_resource_limits,
    get_madre_fluzo_context,
)


@pytest.mark.asyncio
async def test_fluzo_hints_disabled_by_default():
    """Verify FLUZO hints are disabled by default."""
    orig = settings.enable_madre_fluzo
    settings.enable_madre_fluzo = False
    try:
        result = await get_fluzo_hints()
        assert result.get("status") == "disabled"
    finally:
        settings.enable_madre_fluzo = orig


@pytest.mark.asyncio
async def test_fluzo_hints_fetch_when_enabled():
    """Test fetching FLUZO hints when flag is enabled."""
    orig = settings.enable_madre_fluzo
    settings.enable_madre_fluzo = True
    try:
        with patch("madre.fluzo_integration.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "profile": "low_power",
                "signals": {"cpu_load": 0.3, "battery_pct": 45},
            }

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_client_class.return_value = mock_client

            result = await get_fluzo_hints()
            assert result.get("status") == "ok"
            assert result.get("profile") == "low_power"
    finally:
        settings.enable_madre_fluzo = orig


@pytest.mark.asyncio
async def test_apply_fluzo_resource_limits_low_power():
    """Test resource limit application for low_power profile."""
    hints = {"profile": "low_power", "signals": {}}
    config = await apply_fluzo_resource_limits(hints)
    assert config["cpu_limit"] == 0.2
    assert config["max_concurrent_hijas"] == 2
    assert config["task_timeout_ms"] == 3000


@pytest.mark.asyncio
async def test_apply_fluzo_resource_limits_balanced():
    """Test resource limit application for balanced profile."""
    hints = {"profile": "balanced", "signals": {}}
    config = await apply_fluzo_resource_limits(hints)
    assert config["cpu_limit"] == 0.5
    assert config["max_concurrent_hijas"] == 5
    assert config["task_timeout_ms"] == 5000


@pytest.mark.asyncio
async def test_apply_fluzo_resource_limits_performance():
    """Test resource limit application for performance profile."""
    hints = {"profile": "performance", "signals": {}}
    config = await apply_fluzo_resource_limits(hints)
    assert config["cpu_limit"] == 0.9
    assert config["max_concurrent_hijas"] == 10
    assert config["task_timeout_ms"] == 2000


@pytest.mark.asyncio
async def test_get_madre_fluzo_context_disabled():
    """Test full context when FLUZO is disabled."""
    orig = settings.enable_madre_fluzo
    settings.enable_madre_fluzo = False
    try:
        result = await get_madre_fluzo_context()
        assert result["status"] == "disabled"
        assert result["resource_config"] is None
    finally:
        settings.enable_madre_fluzo = orig


@pytest.mark.asyncio
async def test_get_madre_fluzo_context_enabled():
    """Test full context when FLUZO is enabled and hints are fetched."""
    orig = settings.enable_madre_fluzo
    settings.enable_madre_fluzo = True
    try:
        with patch("madre.fluzo_integration.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "profile": "balanced",
                "signals": {"cpu_load": 0.5},
            }

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            mock_client_class.return_value = mock_client

            result = await get_madre_fluzo_context()
            assert result["status"] == "ok"
            assert result["resource_config"]["profile"] == "balanced"
            assert result["resource_config"]["cpu_limit"] == 0.5
    finally:
        settings.enable_madre_fluzo = orig
