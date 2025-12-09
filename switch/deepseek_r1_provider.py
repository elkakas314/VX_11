"""DeepSeek R1 Audio AI Provider for Switch"""

import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class DeepSeekR1AudioProvider:
    """DeepSeek R1 reasoning model for advanced audio analysis"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or ""
        self.base_url = base_url or "https://api.deepseek.com/v1"
        self.model = "deepseek-r1"
        self.timeout = 120
        
    async def analyze_audio_with_reasoning(
        self,
        analysis_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use DeepSeek R1 for deep audio analysis reasoning"""
        
        if not self.api_key:
            logger.warning("DeepSeek API key not configured")
            return {"error": "DeepSeek not configured"}
        
        prompt = f"""
        Analyze the following audio characteristics and provide recommendations:
        - Loudness: {analysis_data.get('loudness_lufs')} LUFS
        - BPM: {analysis_data.get('bpm')}
        - Key: {analysis_data.get('key')}
        - Dynamic Range: {analysis_data.get('dynamic_range')}
        - Signal-to-Noise Ratio: {analysis_data.get('snr')} dB
        
        Provide:
        1. Audio quality assessment
        2. Recommended processing chain
        3. Mastering target loudness
        4. Potential issues to address
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 1.0,  # R1 uses temperature 1.0
                        "thinking": {"type": "enabled", "budget_tokens": 4000},
                    },
                    timeout=self.timeout,
                )
                
                result = response.json()
                
                return {
                    "success": True,
                    "reasoning": result.get("choices", [{}])[0].get("message", {}).get("content"),
                    "model": self.model,
                }
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_mastering_chain(
        self,
        project_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Use DeepSeek R1 to reason about optimal mastering chain"""
        
        if not self.api_key:
            return {"error": "DeepSeek not configured"}
        
        prompt = f"""
        Design an optimal mastering chain for:
        - Genre: {project_metadata.get('genre')}
        - Target: {project_metadata.get('target', 'streaming')}
        - Style: {project_metadata.get('style')}
        
        Specify each processing stage with:
        1. Plugin type
        2. Parameter settings
        3. Reasoning
        """
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 1.0,
                    },
                    timeout=self.timeout,
                )
                
                result = response.json()
                
                return {
                    "success": True,
                    "mastering_chain": result.get("choices", [{}])[0].get("message", {}).get("content"),
                }
        except Exception as e:
            logger.error(f"Mastering chain error: {e}")
            return {"success": False, "error": str(e)}
