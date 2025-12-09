"""Switch integration with Shub audio routing"""

import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ShubAudioRouter:
    """Audio task router for Switch"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.token = config.get("token", "vx11_token")
        self.shub_url = config.get("shub_url", "http://shubniggurath:8007")
        self.headers = {"X-VX11-Token": self.token}
        
    async def route_audio_analysis(self, asset_id: str, file_path: str) -> Dict[str, Any]:
        """Route audio to Shub analyzer"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.shub_url}/shub/analyze",
                    headers=self.headers,
                    json={
                        "asset_id": asset_id,
                        "file_path": file_path,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    timeout=60,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Audio routing error: {e}")
            return {"error": str(e)}
    
    async def select_best_engine(self, audio_characteristics: Dict[str, Any]) -> str:
        """Select best engine based on audio analysis"""
        # Adaptive routing based on audio characteristics
        loudness = audio_characteristics.get("loudness", -23)
        percussiveness = audio_characteristics.get("percussiveness", 0.5)
        bpm = audio_characteristics.get("bpm", 120)
        
        if percussiveness > 0.7:
            return "transient_detector"
        elif loudness < -30:
            return "dynamics_processor"
        elif bpm > 140:
            return "batch_processor"
        else:
            return "analyzer"
    
    async def quality_check(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Check audio quality and determine priority"""
        loudness = analysis_result.get("loudness_lufs", 0)
        snr = analysis_result.get("signal_to_noise_ratio", 0)
        clipping = analysis_result.get("clipping_count", 0)
        
        quality_score = 1.0
        issues = []
        
        if loudness > -10:
            quality_score -= 0.1
            issues.append("Too loud - potential clipping")
        elif loudness < -35:
            quality_score -= 0.1
            issues.append("Too quiet - low signal level")
        
        if snr < 20:
            quality_score -= 0.2
            issues.append("Poor SNR - high noise floor")
        
        if clipping > 10:
            quality_score -= 0.3
            issues.append("Clipping detected")
        
        return {
            "quality_score": max(0, quality_score),
            "issues": issues,
            "priority": "high" if quality_score < 0.5 else "normal",
        }
