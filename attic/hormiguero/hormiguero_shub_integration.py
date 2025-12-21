"""Hormiguero + Shub Parallel Processing"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class HormigueroShubIntegration:
    """Parallel processing orchestration via Hormiguero + Shub engines"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.hormiguero_url = config.get("hormiguero_url", "http://hormiguero:8004")
        self.shub_url = config.get("shub_url", "http://shubniggurath:8007")
        self.token = config.get("token", "vx11_token")
        
    async def parallel_engine_processing(
        self,
        assets: List[str],
        engines: List[str],
    ) -> Dict[str, Any]:
        """Execute parallel processing across multiple engines"""
        
        import httpx
        import asyncio
        
        tasks = []
        
        # Create task for each asset-engine combination
        for asset in assets:
            for engine in engines:
                task = self._process_asset_engine(asset, engine)
                tasks.append(task)
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "total_tasks": len(tasks),
            "completed": sum(1 for r in results if not isinstance(r, Exception)),
            "results": results,
        }
    
    async def _process_asset_engine(self, asset: str, engine: str) -> Dict[str, Any]:
        """Process single asset through single engine"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.shub_url}/shub/engines/{engine}/process",
                    headers={"X-VX11-Token": self.token},
                    json={"asset_id": asset},
                    timeout=120,
                )
                return response.json()
        except Exception as e:
            logger.error(f"Process error: {e}")
            return {"error": str(e)}
