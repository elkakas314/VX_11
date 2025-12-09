"""
HTTP Clients para Operator → otros módulos VX11.
Soporta autenticación centralizada y manejo de errores.
"""

import httpx
from typing import Dict, Any, Optional
from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class BaseClient:
    """Base HTTP client con autenticación y manejo de errores."""
    
    def __init__(self, base_url: str, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, headers=AUTH_HEADERS)
    
    async def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST con JSON body."""
        url = f"{self.base_url}{path}"
        try:
            resp = await self.client.post(url, json=payload)
            try:
                return resp.json() if resp.status_code in (200, 201) else {"status": "error", "code": resp.status_code, "raw": resp.text}
            except Exception:
                return {"raw": resp.text, "status": resp.status_code}
        except Exception as exc:
            write_log("operator", f"client_post_error:{url}:{exc}", level="ERROR")
            return {"status": "error", "error": str(exc)}
    
    async def get(self, path: str) -> Dict[str, Any]:
        """GET request."""
        url = f"{self.base_url}{path}"
        try:
            resp = await self.client.get(url)
            try:
                return resp.json() if resp.status_code == 200 else {"status": "error", "code": resp.status_code}
            except Exception:
                return {"raw": resp.text, "status": resp.status_code}
        except Exception as exc:
            write_log("operator", f"client_get_error:{url}:{exc}", level="ERROR")
            return {"status": "error", "error": str(exc)}


class MadreClient(BaseClient):
    """Cliente para Madre (orquestación, planes)."""
    
    def __init__(self):
        base = getattr(settings, "madre_url", f"http://madre:{settings.madre_port}")
        super().__init__(base)
    
    async def list_plans(self) -> Dict[str, Any]:
        """Listar planes orquestados."""
        return await self.get("/orchestrate/plans")
    
    async def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Obtener detalles de un plan."""
        return await self.get(f"/orchestrate/plans/{plan_id}")
    
    async def get_plan_status(self, plan_id: str) -> Dict[str, Any]:
        """Obtener estado de ejecución de un plan."""
        return await self.get(f"/orchestrate/plans/{plan_id}/status")
    
    async def create_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crear nuevo plan desde Operator."""
        return await self.post("/orchestrate", payload)


class SpawnerClient(BaseClient):
    """Cliente para Spawner (procesos efímeros/hijas)."""
    
    def __init__(self):
        base = getattr(settings, "spawner_url", f"http://spawner:{settings.spawner_port}")
        super().__init__(base)
    
    async def list_spawns(self) -> Dict[str, Any]:
        """Listar hijas activas/recientes."""
        return await self.get("/spawn/list")
    
    async def get_spawn(self, spawn_id: str) -> Dict[str, Any]:
        """Obtener detalles de una hija."""
        return await self.get(f"/spawn/status/{spawn_id}")
    
    async def kill_spawn(self, spawn_id: str) -> Dict[str, Any]:
        """Terminar una hija."""
        return await self.post(f"/spawn/kill/{spawn_id}", {})
    
    async def get_spawn_logs(self, spawn_id: str) -> Dict[str, Any]:
        """Obtener logs de una hija."""
        return await self.get(f"/spawn/output/{spawn_id}")


class SwitchAdminClient(BaseClient):
    """Cliente administrativo para Switch (cola, modelos, admin)."""
    
    def __init__(self):
        base = getattr(settings, "switch_url", f"http://switch:{settings.switch_port}")
        super().__init__(base)
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Estado de la cola prioritaria."""
        return await self.get("/switch/queue/status")
    
    async def get_queue_next(self) -> Dict[str, Any]:
        """Próxima tarea en cola."""
        return await self.get("/switch/queue/next")
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Modelos disponibles."""
        return await self.get("/switch/models/available")
    
    async def set_default_model(self, model_id: str) -> Dict[str, Any]:
        """Cambiar modelo por defecto."""
        return await self.post("/switch/admin/set_default_model", {"model_id": model_id})
    
    async def preload_model(self, model_id: str) -> Dict[str, Any]:
        """Precalentar modelo."""
        return await self.post("/switch/admin/preload_model", {"model_id": model_id})


class HermesAdminClient(BaseClient):
    """Cliente administrativo para Hermes (modelos, CLI registry)."""
    
    def __init__(self):
        base = getattr(settings, "hermes_url", f"http://hermes:{settings.hermes_port}")
        super().__init__(base)
    
    async def list_models(self) -> Dict[str, Any]:
        """Listar modelos disponibles (local + registry)."""
        return await self.get("/hermes/list")
    
    async def list_cli(self) -> Dict[str, Any]:
        """Listar CLI registrados."""
        return await self.get("/hermes/cli/list")
    
    async def get_model_stats(self) -> Dict[str, Any]:
        """Estadísticas de modelos cargados."""
        return await self.get("/hermes/models/stats")


class MCPAdminClient(BaseClient):
    """Cliente administrativo para MCP (auditoría, sandbox)."""
    
    def __init__(self):
        base = getattr(settings, "mcp_url", f"http://mcp:{settings.mcp_port}")
        super().__init__(base)
    
    async def list_audit_logs(self) -> Dict[str, Any]:
        """Listar logs de auditoría sandbox."""
        return await self.get("/mcp/audit/logs")
    
    async def list_sandbox_exec(self) -> Dict[str, Any]:
        """Listar ejecuciones en sandbox."""
        return await self.get("/mcp/sandbox/executions")
    
    async def get_audit_violations(self) -> Dict[str, Any]:
        """Listar violaciones de seguridad detectadas."""
        return await self.get("/mcp/audit/violations")


class HormigueroAdminClient(BaseClient):
    """Cliente administrativo para Hormiguero (tareas Reina, eventos)."""
    
    def __init__(self):
        base = getattr(settings, "hormiguero_url", f"http://hormiguero:{settings.hormiguero_port}")
        super().__init__(base)
    
    async def list_queen_tasks(self) -> Dict[str, Any]:
        """Listar tareas clasificadas por Reina."""
        return await self.get("/hormiguero/queen_tasks")
    
    async def list_events(self) -> Dict[str, Any]:
        """Listar eventos de Hormiguero/Reina."""
        return await self.get("/hormiguero/events")
    
    async def get_queen_task(self, task_id: str) -> Dict[str, Any]:
        """Obtener detalles de tarea Reina."""
        return await self.get(f"/hormiguero/queen_tasks/{task_id}")


# Clientes existentes (mantener compatibilidad)

class ShubClient(BaseClient):
    def __init__(self):
        base = getattr(settings, "shub_url", f"http://shubniggurath:{settings.shub_port}")
        super().__init__(base)
    
    async def run_mode_c(self, project_name: str, track_name: str, payload: Dict[str, Any]):
        return await self.post("/shub/run_mode_c", {"project_name": project_name, "track_name": track_name, "payload": payload})


class ManifestatorClient(BaseClient):
    def __init__(self):
        base = getattr(settings, "manifestator_url", f"http://manifestator:{settings.manifestator_port}")
        super().__init__(base)
    
    async def semantic_validate(self, manifest: str):
        return await self.post("/api/manifest/validate", {"manifest": manifest})


class SwitchClient(BaseClient):
    def __init__(self):
        base = getattr(settings, "switch_url", f"http://switch:{settings.switch_port}")
        super().__init__(base)
    
    async def chat(self, message: str, metadata: Dict[str, Any], source: str = "operator", provider_hint: str = None):
        payload = {
            "messages": [{"role": "user", "content": message}],
            "metadata": metadata or {},
            "provider_hint": provider_hint,
        }
        return await self.post("/switch/chat", payload)


class HermesClient(BaseClient):
    def __init__(self):
        base = getattr(settings, "hermes_url", f"http://hermes:{settings.hermes_port}")
        super().__init__(base)
    
    async def waveform(self, path: str):
        return await self.post("/hermes/waveform", {"path": path})
