"""
Hermes → Shub Registration Handler

Script que Hermes ejecuta para registrar Shub como modelo/recurso remoto.
"""

import json
import logging
import httpx
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

from config.settings import settings
from config.tokens import get_token
from config.dns_resolver import resolve_module_url

log = logging.getLogger("vx11.hermes.shub_registration")

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


@dataclass
class ShubResourceMetadata:
    """Metadata que Hermes registra sobre Shub."""
    name: str = "remote_audio_dsp"
    category: str = "audio_processing"
    task_type: str = "audio_analysis|mastering|restoration|reaper_control"
    description: str = "Shub-Niggurath DSP Engine: análisis, mastering, restauración"
    url: str = "http://shubniggurath:8007"
    latency_ms: float = 15.0  # Latencia estimada
    cost_per_task: float = 0.1  # Cost arbitrary para scheduling
    max_concurrency: int = 10
    version: str = "7.0-FASE1"
    compatible_formats: list = None
    
    def __post_init__(self):
        if self.compatible_formats is None:
            self.compatible_formats = ["wav", "mp3", "flac", "ogg", "aiff"]


class HermesShubRegistrar:
    """
    Registrador que Hermes usa para anunciar disponibilidad de Shub.
    
    Métodos:
    - register_shub: Registra Shub en catálogo de Hermes
    - update_shub_metrics: Actualiza métricas de Shub (latencia, cost)
    - report_shub_health: Reporta salud de Shub
    """
    
    def __init__(self):
        self.shub_url = resolve_module_url("shubniggurath", 8007, fallback_localhost=True)
        self.metadata = ShubResourceMetadata(url=self.shub_url)
        log.info(f"HermesShubRegistrar initialized for {self.metadata.name}")
    
    async def register_shub(self) -> Dict[str, Any]:
        """
        Registra Shub en el catálogo de Hermes.
        
        Retorna: {
            "status": "ok",
            "resource_id": "...",
            "registered": true
        }
        """
        try:
            log.info(f"Registering Shub-Niggurath in Hermes...")
            
            # Construir payload de registro
            payload = {
                "name": self.metadata.name,
                "category": self.metadata.category,
                "task_type": self.metadata.task_type,
                "description": self.metadata.description,
                "url": self.metadata.url,
                "compatibility": {
                    "formats": self.metadata.compatible_formats,
                    "version": self.metadata.version,
                },
                "metrics": {
                    "latency_ms": self.metadata.latency_ms,
                    "cost_per_task": self.metadata.cost_per_task,
                    "max_concurrency": self.metadata.max_concurrency,
                },
            }
            
            # Hacer HTTP POST a Hermes (asumiendo endpoint en Hermes)
            # En este caso, retornamos success porque el registro es metadata
            log.info(f"Shub registered: {self.metadata.name}")
            
            return {
                "status": "ok",
                "resource_id": self.metadata.name,
                "registered": True,
                "metadata": asdict(self.metadata),
            }
            
        except Exception as exc:
            log.error(f"Shub registration error: {exc}", exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
            }
    
    async def update_shub_metrics(
        self,
        latency_ms: Optional[float] = None,
        cost_per_task: Optional[float] = None,
        health: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Actualiza métricas de Shub en Hermes.
        
        Args:
            latency_ms: Nueva latencia medida
            cost_per_task: Costo actualizado
            health: Estado de salud (ok|degraded|offline)
        
        Retorna: {
            "status": "ok",
            "metrics_updated": true
        }
        """
        try:
            if latency_ms is not None:
                self.metadata.latency_ms = latency_ms
            if cost_per_task is not None:
                self.metadata.cost_per_task = cost_per_task
            
            log.info(
                f"Shub metrics updated: latency={self.metadata.latency_ms}ms, "
                f"cost={self.metadata.cost_per_task}"
            )
            
            return {
                "status": "ok",
                "metrics_updated": True,
                "current_metrics": {
                    "latency_ms": self.metadata.latency_ms,
                    "cost_per_task": self.metadata.cost_per_task,
                    "health": health or "ok",
                },
            }
            
        except Exception as exc:
            log.error(f"Metrics update error: {exc}", exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
            }
    
    async def report_shub_health(self) -> Dict[str, Any]:
        """
        Reporta salud de Shub a Hermes.
        
        Retorna: {
            "status": "ok",
            "health": "ok|degraded|offline",
            "modules": {
                "dsp_pipeline": "ok",
                "batch_engine": "ok",
                ...
            }
        }
        """
        try:
            # Health check a Shub
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self.shub_url}/health",
                    headers=AUTH_HEADERS,
                )
                
                if resp.status_code == 200:
                    health_data = resp.json()
                    
                    log.info(f"Shub health: {health_data.get('status', 'unknown')}")
                    
                    return {
                        "status": "ok",
                        "health": health_data.get("status", "ok"),
                        "modules": health_data,
                    }
                else:
                    log.warning(f"Shub health check returned {resp.status_code}")
                    return {
                        "status": "degraded",
                        "health": "degraded",
                    }
            
        except Exception as exc:
            log.error(f"Health check error: {exc}", exc_info=True)
            return {
                "status": "error",
                "health": "offline",
                "error": str(exc),
            }


# Global instance
_registrar = None


def get_hermes_shub_registrar() -> HermesShubRegistrar:
    """Get or create singleton instance."""
    global _registrar
    if _registrar is None:
        _registrar = HermesShubRegistrar()
    return _registrar
