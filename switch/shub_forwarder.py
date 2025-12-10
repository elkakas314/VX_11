"""
Switch → Shub HTTP Forwarder

Router que Switch usa para despachar tareas de audio hacia Shub-Niggurath.
Mantiene HTTP-only communication sin imports directos de Shub.
"""

import logging
import httpx
from typing import Dict, Any, Optional
from enum import Enum

from config.settings import settings
from config.tokens import get_token
from config.dns_resolver import resolve_module_url

log = logging.getLogger("vx11.switch.shub_forwarder")

# Token VX11
VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class ShubRoutingDecision(Enum):
    """Decisión de routing hacia Shub."""
    ANALYZE = "analyze"
    MASTERING = "mastering"
    BATCH_SUBMIT = "batch_submit"
    REAPER_CONTROL = "reaper_control"
    SKIP = "skip"


class SwitchShubForwarder:
    """
    Forwarder que Switch usa para enviar tareas a Shub vía HTTP.
    
    Métodos:
    - route_to_shub: Enruta query hacia Shub según tipo de tarea
    - forward_analyze: Reenvía análisis a Shub
    - forward_mastering: Reenvía mastering a Shub
    - forward_batch: Reenvía batch a Shub
    """
    
    def __init__(self, shub_url: Optional[str] = None, timeout: float = 15.0):
        """
        Inicializar forwarder.
        
        Args:
            shub_url: URL base de Shub (por defecto desde config)
            timeout: Timeout en segundos para requests HTTP
        """
        self.shub_url = shub_url or resolve_module_url("shubniggurath", 8007, fallback_localhost=True)
        self.timeout = timeout
        log.info(f"SwitchShubForwarder initialized: {self.shub_url}")
    
    async def route_to_shub(
        self,
        query: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Decide si enviar query a Shub y cuál ruta usar.
        
        Args:
            query: Texto de la consulta
            context: Contexto de metadata
        
        Returns:
            {
                "status": "ok|skip",
                "routing_decision": "analyze|mastering|batch_submit|skip",
                "result": {...} si success
            }
        """
        try:
            # Determinar tipo de tarea basado en query + context
            decision = self._determine_routing(query, context)
            
            if decision == ShubRoutingDecision.SKIP:
                log.debug(f"Skipping audio routing for query: {query[:50]}")
                return {
                    "status": "skip",
                    "routing_decision": "skip",
                }
            
            # Routear según decisión
            if decision == ShubRoutingDecision.ANALYZE:
                return await self.forward_analyze(query, context)
            elif decision == ShubRoutingDecision.MASTERING:
                return await self.forward_mastering(query, context)
            elif decision == ShubRoutingDecision.BATCH_SUBMIT:
                return await self.forward_batch(query, context)
            
            return {"status": "skip", "routing_decision": "unknown"}
            
        except Exception as exc:
            log.error(f"Routing error: {exc}", exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
            }
    
    def _determine_routing(
        self,
        query: str,
        context: Dict[str, Any] = None,
    ) -> ShubRoutingDecision:
        """Determinar tipo de routing."""
        query_lower = query.lower()
        
        # Detectar intención
        if any(w in query_lower for w in ["analiza", "analyze", "scan", "examine", "audita"]):
            return ShubRoutingDecision.ANALYZE
        
        if any(w in query_lower for w in ["masteriza", "mastering", "master", "mix", "mezcla"]):
            return ShubRoutingDecision.MASTERING
        
        if any(w in query_lower for w in ["batch", "lote", "múltiple", "multiple"]):
            return ShubRoutingDecision.BATCH_SUBMIT
        
        if any(w in query_lower for w in ["reaper", "daw", "control"]):
            return ShubRoutingDecision.REAPER_CONTROL
        
        return ShubRoutingDecision.SKIP
    
    async def forward_analyze(
        self,
        query: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Forward analysis request to Shub.
        
        Endpoint Shub: POST /shub/madre/analyze
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "task_id": context.get("task_id", "switch-analyze") if context else "switch-analyze",
                    "sample_rate": context.get("sample_rate", 44100) if context else 44100,
                    "mode": context.get("mode", "mode_c") if context else "mode_c",
                    "metadata": {
                        "source": "switch",
                        "original_query": query,
                        **(context or {})
                    }
                }
                
                resp = await client.post(
                    f"{self.shub_url}/shub/madre/analyze",
                    json=payload,
                    headers=AUTH_HEADERS,
                )
                
                result = resp.json() if resp.status_code == 200 else {
                    "status": "error",
                    "error": f"HTTP {resp.status_code}",
                }
                
                log.info(f"Forward analyze: {result.get('status', '?')}")
                return {
                    "status": result.get("status", "error"),
                    "routing_decision": "analyze",
                    "result": result,
                }
                
        except Exception as exc:
            log.error(f"Forward analyze error: {exc}", exc_info=True)
            return {
                "status": "error",
                "routing_decision": "analyze",
                "error": str(exc),
            }
    
    async def forward_mastering(
        self,
        query: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Forward mastering request to Shub.
        
        Endpoint Shub: POST /shub/madre/mastering
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Necesita análisis previo
                audio_analysis = context.get("audio_analysis", {}) if context else {}
                
                payload = {
                    "task_id": context.get("task_id", "switch-mastering") if context else "switch-mastering",
                    "audio_analysis": audio_analysis,
                    "target_lufs": context.get("target_lufs", -14.0) if context else -14.0,
                    "metadata": {
                        "source": "switch",
                        "original_query": query,
                    }
                }
                
                resp = await client.post(
                    f"{self.shub_url}/shub/madre/mastering",
                    json=payload,
                    headers=AUTH_HEADERS,
                )
                
                result = resp.json() if resp.status_code == 200 else {
                    "status": "error",
                    "error": f"HTTP {resp.status_code}",
                }
                
                log.info(f"Forward mastering: {result.get('status', '?')}")
                return {
                    "status": result.get("status", "error"),
                    "routing_decision": "mastering",
                    "result": result,
                }
                
        except Exception as exc:
            log.error(f"Forward mastering error: {exc}", exc_info=True)
            return {
                "status": "error",
                "routing_decision": "mastering",
                "error": str(exc),
            }
    
    async def forward_batch(
        self,
        query: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Forward batch submission to Shub.
        
        Endpoint Shub: POST /shub/madre/batch/submit
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                file_list = context.get("file_list", []) if context else []
                
                payload = {
                    "batch_name": context.get("batch_name", "switch-batch") if context else "switch-batch",
                    "file_list": file_list,
                    "analysis_type": context.get("analysis_type", "quick") if context else "quick",
                    "priority": context.get("priority", 5) if context else 5,
                }
                
                resp = await client.post(
                    f"{self.shub_url}/shub/madre/batch/submit",
                    json=payload,
                    headers=AUTH_HEADERS,
                )
                
                result = resp.json() if resp.status_code == 200 else {
                    "status": "error",
                    "error": f"HTTP {resp.status_code}",
                }
                
                log.info(f"Forward batch: {result.get('status', '?')}")
                return {
                    "status": result.get("status", "error"),
                    "routing_decision": "batch_submit",
                    "result": result,
                }
                
        except Exception as exc:
            log.error(f"Forward batch error: {exc}", exc_info=True)
            return {
                "status": "error",
                "routing_decision": "batch_submit",
                "error": str(exc),
            }


# Global instance
_forwarder = None


def get_switch_shub_forwarder() -> SwitchShubForwarder:
    """Get or create singleton instance."""
    global _forwarder
    if _forwarder is None:
        _forwarder = SwitchShubForwarder()
    return _forwarder
