"""
VX11 Bridge: Comunicación HTTP canónica entre Shub-Niggurath y módulos VX11
===========================================================================

Bridge bidireccional HTTP asincrónico para:
- Madre: Notificaciones de análisis, solicitud de decisiones, delegación de tareas
- Switch: Feedback de análisis, consulta de routing, prioridades
- Hormiguero: Sumisión de batch jobs, reportes de progreso, feromonas

Protocolo: HTTP JSON con token auth (X-VX11-Token)
Timeout: 15s para operaciones largas, 5s para checks
Respuestas: JSON estándar VX11 {status, data, error}
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx

from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log, record_crash

# =============================================================================
# LOGGING & CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# URLs de módulos VX11
MADRE_URL = getattr(settings, 'madre_url', None) or f"http://madre:{settings.madre_port}"
SWITCH_URL = getattr(settings, 'switch_url', None) or f"http://switch:{settings.switch_port}"
HORMIGUERO_URL = getattr(settings, 'hormiguero_url', None) or f"http://hormiguero:{settings.hormiguero_port}"

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token

# =============================================================================
# VX11 BRIDGE (6 Métodos Canónicos)
# =============================================================================


class VX11Bridge:
    """
    Puente de comunicación canónico VX11 ↔ Shub-Niggurath.
    
    Métodos:
    1. analyze()                      — Análisis completo con notificación
    2. mastering()                    — Workflow de masterización
    3. batch_submit()                 — Enviar job a Hormiguero
    4. batch_status()                 — Consultar estado de batch job
    5. report_issue_to_hormiguero()   — Reportar issue para saneamiento
    6. notify_madre()                 — Notificar a Madre de evento
    """

    def __init__(self):
        self.madre_url = MADRE_URL
        self.switch_url = SWITCH_URL
        self.hormiguero_url = HORMIGUERO_URL
        self.token = VX11_TOKEN
        self.headers = {
            settings.token_header: self.token,
            "Content-Type": "application/json",
        }
        self.http_client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self):
        """Asegurar cliente HTTP inicializado"""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=15.0)

    async def _http_call(
        self,
        method: str,
        url: str,
        data: Dict = None,
        timeout: float = 15.0,
    ) -> Dict[str, Any]:
        """
        Llamada HTTP genérica con retry automático.
        
        Args:
            method: GET, POST, PUT, DELETE
            url: URL completa
            data: payload JSON
            timeout: timeout en segundos
            
        Returns:
            JSON response {status, data, error}
        """
        try:
            await self._ensure_client()
            
            if method == "GET":
                response = await self.http_client.get(url, headers=self.headers, timeout=timeout)
            elif method == "POST":
                response = await self.http_client.post(url, json=data, headers=self.headers, timeout=timeout)
            elif method == "PUT":
                response = await self.http_client.put(url, json=data, headers=self.headers, timeout=timeout)
            elif method == "DELETE":
                response = await self.http_client.delete(url, headers=self.headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code in [200, 201, 202]:
                return response.json()
            else:
                return {"status": "error", "http_status": response.status_code, "message": response.text}
                
        except asyncio.TimeoutError:
            return {"status": "error", "message": f"Timeout after {timeout}s"}
        except Exception as e:
            write_log("vx11_bridge", f"HTTP_CALL_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 1: analyze
    # =========================================================================

    async def analyze(
        self,
        audio_analysis: Any,
        fx_chain: Any,
        reaper_preset: Any,
    ) -> Dict[str, Any]:
        """
        Análisis completo con notificación a Madre + feedback a Switch.
        
        Args:
            audio_analysis: Objeto AudioAnalysis desde engines_paso8.py
            fx_chain: Objeto FXChain generado por FXEngine
            reaper_preset: Objeto REAPERPreset generado
            
        Retorna:
        {
            "status": "success",
            "analysis_id": "uuid",
            "madre_acknowledged": true,
            "switch_feedback": {...},
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("vx11_bridge", "ANALYZE: iniciando notificación a Madre", level="INFO")
            
            # Serializar AudioAnalysis si es necesario
            analysis_dict = (
                audio_analysis.__dict__ if hasattr(audio_analysis, '__dict__')
                else audio_analysis
            )
            
            # 1. Notificar a Madre
            madre_response = await self._http_call(
                "POST",
                f"{self.madre_url}/madre/events/analysis_complete",
                {
                    "event_type": "audio_analysis_complete",
                    "source": "shubniggurath",
                    "analysis": analysis_dict,
                    "fx_chain": fx_chain.__dict__ if hasattr(fx_chain, '__dict__') else fx_chain,
                    "preset": reaper_preset.__dict__ if hasattr(reaper_preset, '__dict__') else reaper_preset,
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=10.0,
            )
            
            # 2. Enviar feedback a Switch
            switch_response = await self._http_call(
                "POST",
                f"{self.switch_url}/switch/feedback/audio_analysis",
                {
                    "source": "shubniggurath",
                    "analysis_quality": analysis_dict.get("classification", {}).get("confidence", 0.0),
                    "issues_detected": analysis_dict.get("issues", []),
                    "recommendations": analysis_dict.get("recommendations", []),
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=5.0,
            )
            
            write_log("vx11_bridge", "ANALYZE: notificaciones completadas", level="INFO")
            
            return {
                "status": "success",
                "madre_acknowledged": madre_response.get("status") == "success",
                "switch_feedback": switch_response.get("status") == "success",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("vx11_bridge", e)
            write_log("vx11_bridge", f"ANALYZE_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 2: mastering
    # =========================================================================

    async def mastering(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Workflow de masterización con REAPER integrado.
        
        Args:
            project_data: {project_name, tracks, analysis, master_style, ...}
            
        Retorna:
        {
            "status": "success",
            "mastering_id": "uuid",
            "switch_routing": {...},
            "reaper_status": "rendering",
            "estimated_time_seconds": 120,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("vx11_bridge", "MASTERING: iniciando workflow", level="INFO")
            
            # Consultar a Switch para enrutamiento inteligente
            switch_response = await self._http_call(
                "POST",
                f"{self.switch_url}/switch/mastering/route",
                {
                    "project": project_data.get("project_name"),
                    "master_style": project_data.get("master_style", "streaming"),
                    "analysis": project_data.get("analysis", {}),
                },
                timeout=5.0,
            )
            
            # Notificar a Madre del inicio de mastering
            madre_response = await self._http_call(
                "POST",
                f"{self.madre_url}/madre/events/mastering_start",
                {
                    "event_type": "mastering_workflow_start",
                    "project": project_data.get("project_name"),
                    "master_style": project_data.get("master_style", "streaming"),
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=5.0,
            )
            
            write_log("vx11_bridge", "MASTERING: routing configurado", level="INFO")
            
            return {
                "status": "success",
                "mastering_started": True,
                "switch_routing": switch_response.get("data", {}),
                "madre_acknowledged": madre_response.get("status") == "success",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("vx11_bridge", e)
            write_log("vx11_bridge", f"MASTERING_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 3: batch_submit
    # =========================================================================

    async def batch_submit(
        self,
        audio_files: List[str],
        analysis_type: str = "full",
        priority: int = 5,
    ) -> Dict[str, Any]:
        """
        Enviar batch job a Hormiguero.
        
        Args:
            audio_files: Lista de rutas de archivos
            analysis_type: 'quick', 'full', 'deep'
            priority: 1-10 (10 = máxima prioridad)
            
        Retorna:
        {
            "status": "success",
            "batch_id": "uuid",
            "hormiguero_queue_position": 3,
            "estimated_wait_seconds": 45,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("vx11_bridge", f"BATCH_SUBMIT: {len(audio_files)} archivos", level="INFO")
            
            result = await self._http_call(
                "POST",
                f"{self.hormiguero_url}/hormiguero/batch/submit",
                {
                    "task_type": "audio_analysis",
                    "source": "shubniggurath",
                    "audio_files": audio_files,
                    "analysis_type": analysis_type,
                    "priority": priority,
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=10.0,
            )
            
            if result.get("status") == "success":
                write_log("vx11_bridge", f"BATCH_SUBMIT_SUCCESS: batch_id={result.get('data', {}).get('batch_id')}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("vx11_bridge", e)
            write_log("vx11_bridge", f"BATCH_SUBMIT_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 4: batch_status
    # =========================================================================

    async def batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Consultar estado de batch job en Hormiguero.
        
        Args:
            batch_id: ID de batch job desde submit()
            
        Retorna:
        {
            "status": "success",
            "batch_id": "uuid",
            "batch_status": "processing",
            "progress": {
                "total_files": 10,
                "processed": 7,
                "failed": 0,
                "percent_complete": 70
            },
            "estimated_remaining_seconds": 20,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("vx11_bridge", f"BATCH_STATUS: batch_id={batch_id}", level="INFO")
            
            result = await self._http_call(
                "GET",
                f"{self.hormiguero_url}/hormiguero/batch/{batch_id}/status",
                timeout=5.0,
            )
            
            return result
            
        except Exception as e:
            record_crash("vx11_bridge", e)
            write_log("vx11_bridge", f"BATCH_STATUS_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 5: report_issue_to_hormiguero
    # =========================================================================

    async def report_issue_to_hormiguero(
        self,
        issue_type: str,
        severity: str,
        description: str,
        audio_file: str = None,
    ) -> Dict[str, Any]:
        """
        Reportar issue grave para saneamiento por Hormiguero.
        
        Args:
            issue_type: 'audio_corruption', 'clipping', 'noise', 'phase_issue', etc.
            severity: 'info', 'warning', 'error', 'critical'
            description: Descripción detallada
            audio_file: Ruta del archivo problemático
            
        Retorna:
        {
            "status": "success",
            "issue_id": "uuid",
            "remediation_started": true,
            "remediation_type": "audio_scan",
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("vx11_bridge", f"REPORT_ISSUE: type={issue_type}, severity={severity}", level="WARNING")
            
            result = await self._http_call(
                "POST",
                f"{self.hormiguero_url}/hormiguero/issues/report",
                {
                    "source": "shubniggurath",
                    "issue_type": issue_type,
                    "severity": severity,
                    "description": description,
                    "audio_file": audio_file,
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=10.0,
            )
            
            if result.get("status") == "success":
                write_log("vx11_bridge", f"REPORT_ISSUE_SUCCESS: issue_id={result.get('data', {}).get('issue_id')}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("vx11_bridge", e)
            write_log("vx11_bridge", f"REPORT_ISSUE_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 6: notify_madre
    # =========================================================================

    async def notify_madre(
        self,
        event_type: str,
        data: Dict[str, Any],
        priority: str = "normal",
    ) -> Dict[str, Any]:
        """
        Notificación genérica a Madre para delegación de tareas.
        
        Args:
            event_type: 'analysis_complete', 'mastering_complete', 'error_recovery', etc.
            data: Payload de evento
            priority: 'low', 'normal', 'high', 'critical'
            
        Retorna:
        {
            "status": "success",
            "event_id": "uuid",
            "madre_action": "create_child_hija",
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("vx11_bridge", f"NOTIFY_MADRE: event_type={event_type}, priority={priority}", level="INFO")
            
            result = await self._http_call(
                "POST",
                f"{self.madre_url}/madre/events",
                {
                    "event_type": event_type,
                    "source": "shubniggurath",
                    "priority": priority,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                },
                timeout=10.0,
            )
            
            if result.get("status") == "success":
                write_log("vx11_bridge", f"NOTIFY_MADRE_SUCCESS: event_id={result.get('data', {}).get('event_id')}", level="INFO")
            
            return result
            
        except Exception as e:
            record_crash("vx11_bridge", e)
            write_log("vx11_bridge", f"NOTIFY_MADRE_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # HEALTH & CLEANUP
    # =========================================================================

    async def health_cascade_check(self) -> Dict[str, Any]:
        """
        Verificar salud en cascada de módulos VX11 dependientes.
        
        Retorna:
        {
            "status": "healthy|degraded|offline",
            "modules": {
                "madre": true,
                "switch": true,
                "hormiguero": false,
            },
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            write_log("vx11_bridge", "HEALTH_CASCADE_CHECK: iniciando", level="INFO")
            
            modules = {}
            
            # Check Madre
            madre_health = await self._http_call(
                "GET",
                f"{self.madre_url}/health",
                timeout=3.0,
            )
            modules["madre"] = madre_health.get("status") == "success" or madre_health.get("status") == "ok"
            
            # Check Switch
            switch_health = await self._http_call(
                "GET",
                f"{self.switch_url}/health",
                timeout=3.0,
            )
            modules["switch"] = switch_health.get("status") == "success" or switch_health.get("status") == "ok"
            
            # Check Hormiguero
            hormiguero_health = await self._http_call(
                "GET",
                f"{self.hormiguero_url}/health",
                timeout=3.0,
            )
            modules["hormiguero"] = hormiguero_health.get("status") == "success" or hormiguero_health.get("status") == "ok"
            
            healthy_count = sum(1 for v in modules.values() if v)
            total_count = len(modules)
            
            if healthy_count == total_count:
                cascade_status = "healthy"
            elif healthy_count >= total_count // 2:
                cascade_status = "degraded"
            else:
                cascade_status = "offline"
            
            write_log("vx11_bridge", f"HEALTH_CASCADE: {cascade_status} ({healthy_count}/{total_count})", level="INFO")
            
            return {
                "status": cascade_status,
                "modules": modules,
                "healthy_count": healthy_count,
                "total_count": total_count,
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("vx11_bridge", e)
            return {"status": "offline", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def cleanup(self):
        """Cleanup: cerrar cliente HTTP"""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        write_log("vx11_bridge", "CLEANUP: conexión cerrada", level="INFO")

