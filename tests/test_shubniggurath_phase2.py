"""Test Switch + Hermes audio integration with Shub"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_switch_audio_routing():
    """Test audio task routing through Switch"""
    from switch.switch_audio_router import ShubAudioRouter
    
    config = {
        "token": "test_token",
        "shub_url": "http://shubniggurath:8007",
    }
    
    router = ShubAudioRouter(config)
    
    # Test engine selection
    characteristics = {
        "loudness": -20,
        "percussiveness": 0.8,
        "bpm": 150,
    }
    
    best_engine = await router.select_best_engine(characteristics)
    assert best_engine == "transient_detector"


@pytest.mark.asyncio
async def test_quality_check():
    """Test audio quality checking"""
    from switch.switch_audio_router import ShubAudioRouter
    
    router = ShubAudioRouter({})
    
    analysis = {
        "loudness_lufs": -23,
        "signal_to_noise_ratio": 40,
        "clipping_count": 0,
    }
    
    quality = await router.quality_check(analysis)
    
    assert quality["quality_score"] > 0.5
    assert quality["priority"] == "normal"


@pytest.mark.asyncio
async def test_hermes_shub_provider():
    """Test Hermes Shub audio provider"""
    from hermes.hermes_shub_provider import ShubAudioProvider
    
    provider = ShubAudioProvider({})
    
    assert await provider.is_available()
    
    # Test analyze operation
    result = await provider.execute_operation("analyze", {})
    assert result["success"]
    assert "analysis" in result


@pytest.mark.asyncio
async def test_hermes_eq_generation():
    """Test EQ generation via Hermes"""
    from hermes.hermes_shub_provider import ShubAudioProvider
    
    provider = ShubAudioProvider({})
    
    result = await provider.execute_operation("generate_eq", {})
    
    assert result["success"]
    assert "eq_bands" in result
    assert len(result["eq_bands"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
