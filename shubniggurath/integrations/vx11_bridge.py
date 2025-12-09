"""
VX11 Bridge: Comunicación HTTP entre Shub y otros módulos (Madre, Hormiguero, Switch).
"""

import httpx
import logging
from typing import Dict, Any, Optional
from config.settings import settings
from config.forensics import write_log

logger = logging.getLogger(__name__)


class VX11Bridge:
    """Puente HTTP a otros módulos VX11."""

    def __init__(self):
        self.madre_url = settings.madre_url or f"http://madre:{settings.madre_port}"
        self.hormiguero_url = settings.hormiguero_url or f"http://hormiguero:{settings.hormiguero_port}"
        self.switch_url = settings.switch_url or f"http://switch:{settings.switch_port}"
        self.token_header = settings.token_header
        self.api_token = settings.api_token

    async def notify_madre_analysis_complete(self, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Notificar a Madre que Shub completó análisis."""
        try:
            headers = {self.token_header: self.api_token}
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.madre_url}/madre/telemetry",
                    headers=headers,
                    json={
                        "event": "shub_analysis_complete",
                        "module": "shubniggurath",
                        "metrics": {
                            "lufs": analysis.get('lufs_integrated'),
                            "peak": analysis.get('peak_dbfs'),
                            "issues_count": len(analysis.get('issues', []))
                        }
                    },
                    timeout=5
                )
                if resp.status_code == 200:
                    write_log("shubniggurath", "Notified Madre of analysis")
                    return resp.json()
        except Exception as e:
            logger.warning(f"Error notifying Madre: {e}")
            write_log("shubniggurath", f"Error notifying Madre: {e}", level="WARN")
        return None

    async def check_hormiguero_health(self) -> bool:
        """Verificar health de Hormiguero."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.hormiguero_url}/health",
                    timeout=3
                )
                return resp.status_code == 200
        except:
            return False

    async def send_analysis_to_switch(self, analysis: Dict[str, Any], 
                                     audio_file: str) -> Optional[Dict[str, Any]]:
        """Enviar análisis a Switch para enrutamiento inteligente."""
        try:
            headers = {self.token_header: self.api_token}
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.switch_url}/switch/analysis-feedback",
                    headers=headers,
                    json={
                        "audio_file": audio_file,
                        "analysis": analysis,
                        "source": "shubniggurath"
                    },
                    timeout=5
                )
                if resp.status_code == 200:
                    write_log("shubniggurath", "Sent analysis to Switch")
                    return resp.json()
        except Exception as e:
            logger.warning(f"Error sending to Switch: {e}")
        return None

    async def get_madre_power_status(self) -> Optional[Dict[str, Any]]:
        """Obtener estado de poder de módulos desde Madre."""
        try:
            headers = {self.token_header: self.api_token}
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.madre_url}/madre/power/status",
                    headers=headers,
                    timeout=3
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Error getting power status from Madre: {e}")
        return None

    async def health_cascade_check(self) -> Dict[str, bool]:
        """Verificar salud de cascada VX11."""
        results = {}
        
        # Check Madre
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.madre_url}/health", timeout=3)
                results['madre'] = resp.status_code == 200
        except:
            results['madre'] = False

        # Check Hormiguero
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.hormiguero_url}/health", timeout=3)
                results['hormiguero'] = resp.status_code == 200
        except:
            results['hormiguero'] = False

        # Check Switch
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.switch_url}/health", timeout=3)
                results['switch'] = resp.status_code == 200
        except:
            results['switch'] = False

        write_log("shubniggurath", f"Health cascade: {results}")
        return results


# Instancia global
vx11_bridge = VX11Bridge()
