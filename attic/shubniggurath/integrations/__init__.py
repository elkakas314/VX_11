"""VX11 Bridge - Sync with Switch, Madre, MCP"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class VX11Bridge:
    """Integration with VX11 modules"""
    
    def __init__(self, config: Dict[str, Any]):
        self.switch_url = config.get("switch_url", "http://switch:8002")
        self.madre_url = config.get("madre_url", "http://madre:8001")
        self.token = config.get("token", "vx11_default_token")
        self.headers = {"X-VX11-Token": self.token}
        self.timeout = 30
        
    async def route_audio_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send audio task to Switch for routing"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.switch_url}/switch/route",
                    headers=self.headers,
                    json=task_data,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Switch routing error: {e}")
            return {"error": str(e)}
    
    async def create_vx11_task(self, task_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create task in VX11 Madre"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.madre_url}/tasks",
                    headers=self.headers,
                    json={
                        "name": task_name,
                        "module": "shubniggurath",
                        "parameters": params,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"VX11 task creation error: {e}")
            return {"error": str(e)}
    
    async def sync_asset_to_vx11(self, asset_id: str, asset_data: Dict[str, Any]) -> bool:
        """Sync audio asset metadata to VX11 context"""
        try:
            task_data = {
                "action": "sync_asset",
                "asset_id": asset_id,
                "metadata": asset_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.create_vx11_task("sync_audio_asset", task_data)
            return True
        except Exception as e:
            logger.error(f"Asset sync error: {e}")
            return False
    
    async def health_check(self) -> Dict[str, bool]:
        """Check VX11 module health"""
        checks = {}
        
        async with httpx.AsyncClient() as client:
            # Check Switch
            try:
                resp = await client.get(f"{self.switch_url}/health", timeout=5)
                checks["switch"] = resp.status_code == 200
            except:
                checks["switch"] = False
            
            # Check Madre
            try:
                resp = await client.get(f"{self.madre_url}/health", timeout=5)
                checks["madre"] = resp.status_code == 200
            except:
                checks["madre"] = False
        
        return checks
