"""Tentáculo Link + Shub Gateway Integration"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TentaculoShubGateway:
    """Tentáculo Link gateway for Shub audio requests"""
    
    def __init__(self, config: Dict[str, Any]):
        self.shub_url = config.get("shub_url", "http://shubniggurath:8007")
        self.token = config.get("token", "vx11_token")
        
    async def route_audio_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Route audio request from Tentáculo to Shub"""
        
        import httpx
        
        request_type = message.get("type", "analyze")
        
        try:
            async with httpx.AsyncClient() as client:
                endpoint_map = {
                    "analyze": "/shub/analyze",
                    "mastering": "/shub/engines/ai_mastering/process",
                    "eq": "/shub/engines/eq_generator/process",
                }
                
                endpoint = endpoint_map.get(request_type, "/shub/analyze")
                
                response = await client.post(
                    f"{self.shub_url}{endpoint}",
                    headers={"X-VX11-Token": self.token},
                    json=message.get("data", {}),
                    timeout=60,
                )
                
                result = response.json()
                
                # Encapsulate in Tentáculo format
                return {
                    "raw": str(result),
                    "module": "shubniggurath",
                    "timestamp": str(__import__("datetime").datetime.utcnow()),
                }
        except Exception as e:
            logger.error(f"Gateway routing error: {e}")
            return {
                "raw": f"Error: {str(e)}",
                "error": True,
            }
