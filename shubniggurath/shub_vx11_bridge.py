"""
Shub VX11 Bridge — Integración conversacional segura
Conecta Shub con Switch, Madre, MCP sin modificar VX11
"""

import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from config.settings import settings
from config.tokens import get_token

logger = logging.getLogger("shub.vx11_bridge")


class VX11ClientConfig:
    """Configuración de cliente VX11"""
    
    def __init__(
        self,
        tentaculo_url: str = "http://localhost:8000",
        madre_url: str = "http://localhost:8001",
        switch_url: str = "http://localhost:8002",
        mcp_url: str = "http://localhost:8006",
        timeout_seconds: int = 10,
    ):
        self.tentaculo_url = tentaculo_url
        self.gateway_url = tentaculo_url  # legacy alias
        self.madre_url = madre_url
        self.switch_url = switch_url
        self.mcp_url = mcp_url
        self.timeout_seconds = timeout_seconds
        self.headers = {
            settings.token_header: get_token("VX11_TENTACULO_LINK_TOKEN")
            or get_token("VX11_GATEWAY_TOKEN")
            or settings.api_token
        }


class VX11Client:
    """Cliente para comunicación con VX11"""
    
    def __init__(self, config: VX11ClientConfig):
        self.config = config
        self.http_client = httpx.AsyncClient(
            timeout=config.timeout_seconds,
            headers=config.headers
        )
        self.session_id: Optional[str] = None
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar que VX11 esté disponible"""
        try:
            response = await self.http_client.get(
                f"{self.config.tentaculo_url}/vx11/status"
            )
            if response.status_code == 200:
                return {"status": "ok", "vx11": response.json()}
            return {"status": "error", "http_code": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def send_to_madre(
        self,
        messages: list,
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Enviar chat a Madre"""
        try:
            payload = {
                "messages": messages,
                "task_id": task_id or f"shub_{datetime.utcnow().timestamp()}",
            }
            response = await self.http_client.post(
                f"{self.config.madre_url}/chat",
                json=payload,
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "http_code": response.status_code}
        except Exception as e:
            logger.error(f"Error sending to Madre: {e}")
            return {"status": "error", "error": str(e)}
    
    async def send_to_mcp(
        self,
        user_message: str,
        require_action: bool = False,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Enviar a MCP (conversational v2)"""
        try:
            payload = {
                "user_message": user_message,
                "require_action": require_action,
                "context": context or {},
            }
            response = await self.http_client.post(
                f"{self.config.mcp_url}/mcp/chat",
                json=payload,
            )
            if response.status_code == 200:
                result = response.json()
                if self.session_id is None:
                    self.session_id = result.get("session_id")
                return result
            return {"status": "error", "http_code": response.status_code}
        except Exception as e:
            logger.error(f"Error sending to MCP: {e}")
            return {"status": "error", "error": str(e)}
    
    async def route_through_switch(
        self,
        prompt: str,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Enrutar consulta a través de Switch"""
        try:
            payload = {
                "prompt": prompt,
                "context": context or {},
            }
            response = await self.http_client.post(
                f"{self.config.switch_url}/switch/route",
                json=payload,
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "http_code": response.status_code}
        except Exception as e:
            logger.error(f"Error routing through Switch: {e}")
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Cerrar cliente"""
        await self.http_client.aclose()


class VX11FlowAdapter:
    """Adaptador que traduce Shub↔VX11 flows"""
    
    def __init__(self, vx11_client: VX11Client):
        self.client = vx11_client
    
    async def shub_command_to_madre(
        self,
        shub_command: str,
        shub_args: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Convertir comando Shub a flow Madre
        Ejemplo: analyze → tarea en Madre
        """
        messages = [
            {
                "role": "system",
                "content": "You are Shub-Niggurath audio assistant",
            },
            {
                "role": "user",
                "content": f"[SHUB-COMMAND] {shub_command} {shub_args or ''}",
            },
        ]
        
        return await self.client.send_to_madre(messages)
    
    async def copilot_message_to_shub(
        self,
        copilot_message: str,
        copilot_context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Procesar mensaje de Copilot dentro de Shub
        Enruta a MCP si require_action
        """
        return await self.client.send_to_mcp(
            user_message=copilot_message,
            require_action=False,
            context=copilot_context,
        )
    
    async def shub_analysis_to_vx11(
        self,
        analysis_type: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Enviar análisis de Shub a VX11 via Switch
        Para procesamiento distribuido
        """
        prompt = f"[SHUB-ANALYSIS] {analysis_type} for project {project_id}"
        return await self.client.route_through_switch(prompt)


# ============================================================================
# SINGLETON DE CLIENTE VX11
# ============================================================================

_vx11_client_instance: Optional[VX11Client] = None


def get_vx11_client(
    config: Optional[VX11ClientConfig] = None
) -> VX11Client:
    """Obtener instancia singleton de cliente VX11"""
    global _vx11_client_instance
    if _vx11_client_instance is None:
        _vx11_client_instance = VX11Client(config or VX11ClientConfig())
    return _vx11_client_instance


# ====== Shub task helpers (HTTP bridge) ======

async def submit_shub_task(task_kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Envía tarea a Madre/Spawner vía VX11 (stub seguro).
    """
    client = get_vx11_client()
    try:
        resp = await client.http_client.post(
            f"{client.config.madre_url}/madre/shub/task",
            json={"task_kind": task_kind, **payload},
        )
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error", "code": resp.status_code}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


async def check_shub_task(task_id: str) -> Dict[str, Any]:
    """
    Consulta estado de tarea shub_task (placeholder).
    """
    client = get_vx11_client()
    try:
        resp = await client.http_client.get(f"{client.config.madre_url}/madre/hijas")
        if resp.status_code == 200:
            return resp.json()
        return {"status": "error", "code": resp.status_code}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


__all__ = [
    "VX11ClientConfig",
    "VX11Client",
    "VX11FlowAdapter",
    "get_vx11_client",
    "submit_shub_task",
    "check_shub_task",
]
