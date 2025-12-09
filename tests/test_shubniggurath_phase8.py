"""Test DeepSeek R1 audio provider"""

import pytest


@pytest.mark.asyncio
async def test_deepseek_provider_initialization():
    """Test DeepSeek R1 provider"""
    from switch.deepseek_r1_provider import DeepSeekR1AudioProvider
    
    provider = DeepSeekR1AudioProvider(api_key="test_key")
    assert provider.model == "deepseek-r1"


@pytest.mark.asyncio
async def test_deepseek_without_key():
    """Test DeepSeek without API key"""
    from switch.deepseek_r1_provider import DeepSeekR1AudioProvider
    
    provider = DeepSeekR1AudioProvider()
    
    result = await provider.analyze_audio_with_reasoning({
        "loudness_lufs": -23.5,
        "bpm": 120,
    })
    
    assert "error" in result or "success" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
