"""Shub + VX11 Integration Tests"""

import pytest
import asyncio
from shubniggurath.core import ShubCoreInitializer, DSPEngine
from shubniggurath.engines import EngineRegistry


@pytest.mark.asyncio
async def test_shub_initialization():
    """Test core initialization"""
    config = {
        "reaper": {"host": "localhost", "port": 7899},
        "vx11": {"url": "http://switch:8002", "token": "test_token"},
    }
    
    initializer = ShubCoreInitializer(config)
    status = await initializer.initialize()
    
    assert status["status"] == "initialized"
    assert "components" in status


@pytest.mark.asyncio
async def test_dsp_engine():
    """Test DSP engine"""
    import numpy as np
    
    engine = DSPEngine(sample_rate=48000)
    audio = np.random.randn(48000)
    
    result = await engine.analyze_audio(audio)
    
    assert result.loudness_lufs < 0
    assert result.bpm > 0
    assert result.key in ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


@pytest.mark.asyncio
async def test_engine_registry():
    """Test engine registry"""
    registry = EngineRegistry()
    engines = registry.list_engines()
    
    assert len(engines) == 10
    assert "analyzer" in engines
    assert "ai_mastering" in engines
    
    health = await registry.health_check()
    assert all(health.values())


@pytest.mark.asyncio
async def test_analyzer_engine():
    """Test analyzer engine"""
    from shubniggurath.engines import AnalyzerEngine
    
    engine = AnalyzerEngine()
    result = await engine.process({})
    
    assert result.success
    assert "loudness" in result.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
