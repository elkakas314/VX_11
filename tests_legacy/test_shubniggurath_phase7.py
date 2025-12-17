"""Test VX11 cross-integrations with Shub"""

import pytest


@pytest.mark.asyncio
async def test_mcp_shub_bridge():
    """Test MCP + Shub bridge"""
    from mcp.mcp_shub_bridge import MCPShubBridge
    
    config = {
        "shub_url": "http://shubniggurath:8007",
        "token": "test_token",
    }
    
    bridge = MCPShubBridge(config)
    
    # Test audio analysis command
    result = await bridge.handle_audio_command("analyze this audio", {})
    assert "response" in result


@pytest.mark.asyncio
async def test_hormiguero_shub_integration():
    """Test Hormiguero + Shub parallel processing"""
    from hormiguero.hormiguero_shub_integration import HormigueroShubIntegration
    
    config = {
        "hormiguero_url": "http://hormiguero:8004",
        "shub_url": "http://shubniggurath:8007",
        "token": "test_token",
    }
    
    integration = HormigueroShubIntegration(config)
    assert integration.shub_url == "http://shubniggurath:8007"


@pytest.mark.asyncio
async def test_tentaculo_shub_gateway():
    """Test Tentáculo Link + Shub gateway"""
    from tentaculo_link.tentaculo_shub_gateway import TentaculoShubGateway
    
    config = {
        "shub_url": "http://shubniggurath:8007",
        "token": "test_token",
    }
    
    gateway = TentaculoShubGateway(config)
    assert gateway.shub_url == "http://shubniggurath:8007"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
