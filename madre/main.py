"""
Madre v2 Extended: Master Orchestrator con soporte para:
- Ephemeral children (procesos cortos vía spawner)
- Conversación iterativa (madre_chat con historial)
- Tracking BD mejorado
- Container state management (P&P)
"""

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import uuid
import time
import asyncio
import logging
import httpx
import psutil
import json

from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log
from config.db_schema import (
    get_session,
    Task,
    Context,
    Report,
    Spawn,
    SystemState,
    SchedulerHistory,
    PowerEvent,
)
from config.container_state import get_active_modules, get_standby_modules, should_process
from config.context7 import Context7Generator, get_default_context7, validate_context7
from datetime import datetime
from .bridge_handler import BridgeHandler
import subprocess
import docker

log = logging.getLogger("vx11.madre")
logger = log
app = FastAPI(title="VX11 Madre v2")
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

# Session store for orchestration state
_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Bridge handler for conversational routing
_bridge_handler: Optional[BridgeHandler] = None

# Estado P&P por módulo
_MODULE_STATES: Dict[str, str] = {
    m: "active" for m in ["tentaculo_link", "madre", "switch", "hermes", "hormiguero", "manifestator", "mcp", "shub", "spawner", "operator"]
}

# Scheduler control
_SCHEDULER_TASK: Optional[asyncio.Task] = None


class ShubTaskRequest(BaseModel):
    task_kind: str
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    params: Dict[str, Any] = {}
    priority: Optional[int] = 2
    ttl: Optional[int] = 120
    context7: Optional[Dict[str, Any]] = None


class MicroPlanner:
    """
    Micro-IA de planificación que consulta a Switch para obtener feedback inicial,
    construye un plan y recomienda hijas/CLI.
    """

    def __init__(self, switch_url: str):
        self.switch_url = switch_url.rstrip("/")

    async def initial_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consulta a Switch para seleccionar modelo/estrategia rápida.
        """
        prompt = payload.get("prompt") or payload.get("query") or json.dumps(payload)
        metadata = payload.get("metadata") or {}
        metadata.setdefault("task_type", payload.get("task_type", "orchestration"))
        metadata.setdefault("mode", "planning")
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.post(
                    f"{self.switch_url}/switch/route-v5",
                    json={"prompt": prompt, "metadata": metadata, "source": "madre"},
                    headers=AUTH_HEADERS,
                )
                data = r.json()
                return {
                    "model": data.get("model"),
                    "reply": data.get("reply") or data.get("hermes"),
                    "queue_size": data.get("queue_size", 0),
                }
        except Exception as exc:
            write_log("madre", f"planner_feedback_error:{exc}", level="WARNING")
            return {"error": str(exc)}

    def build_plan(self, payload: Dict[str, Any], feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Construye un plan breve siguiendo flujo canónico:
        feedback inicial -> plan -> creación hijas -> seguimiento -> cierre.
        """
        model = feedback.get("model") or "general-7b"
        intent = payload.get("intent") or payload.get("action") or "general"
        steps = [
            {"step": "feedback_inicial", "model": model, "notes": feedback.get("reply")},
            {"step": "elaborar_plan", "intent": intent, "queue_hint": feedback.get("queue_size", 0)},
            {"step": "crear_hija", "agresividad": payload.get("aggressiveness", "normal"), "ttl": payload.get("ttl", 60)},
            {"step": "seguimiento", "signals": ["heartbeat", "stdout_tail"]},
            {"step": "cierre", "persist": ["tasks", "context", "spawns"]},
        ]
        return steps

    def recommended_tools(self, payload: Dict[str, Any]) -> List[str]:
        """
        Devuelve herramientas sugeridas para hijas (MCP/CLI) basado en metadata.
        """
        metadata = payload.get("metadata") or {}
        tools = metadata.get("tools") or []
        if payload.get("mode") == "cli":
            tools.append("cli_bridge")
        if metadata.get("task_type") == "audio":
            tools.append("shub_audio_analyzer")
        return list(dict.fromkeys(tools))


_planner = MicroPlanner(settings.switch_url)
_TASK_RETRIES: Dict[str, int] = {}


# =========== MODELS ===========

class TaskRequest(BaseModel):
    """Create and execute a task."""
    name: str
    module: str  # spawner, switch, hermes, hormiguero
    action: str  # spawn, route, exec, manage
    payload: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 1


class TaskResponse(BaseModel):
    task_id: str
    status: str
    session_id: str


class EphemeralChildRequest(BaseModel):
    """Request para crear hijo efímero."""
    name: str
    cmd: str  # Comando a ejecutar
    timeout: Optional[int] = 30
    context: Optional[Dict[str, Any]] = None
    track_in_bd: bool = True


class ShubTaskRequest(BaseModel):
    task_kind: str  # analyze|mix|master|diagnose
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    params: Dict[str, Any] = {}
    priority: Optional[int] = 2
    ttl: Optional[int] = 120


class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str


class MadreChatRequest(BaseModel):
    """Conversación iterativa con madre."""
    task_id: Optional[str] = None  # Reutilizar sesión
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class OrchestrationRequest(BaseModel):
    """High-level orchestration request."""
    action: str  # spawn, route, exec, status
    target: Optional[str] = None
    payload: Dict[str, Any]


class IntentRequest(BaseModel):
    """INTENT estructurado para que Madre procese."""
    source: str  # "operator", "hormiguero", "system", "shub", etc.
    intent_type: str  # "analyze", "plan", "execute", "optimize", etc.
    payload: Dict[str, Any]  # Datos específicos
    priority: Optional[int] = None  # Si es None, usa source default
    ttl_seconds: Optional[int] = 300  # TTL para hijas


# =========== P&P HELPERS ===========


def _load_policy(session, module: str):
    from config.db_schema import MadrePolicy

    pol = session.query(MadrePolicy).filter_by(module=module).first()
    if pol:
        return pol
    pol = MadrePolicy(module=module)
    session.add(pol)
    session.commit()
    return pol


def _record_action(session, module: str, action: str, reason: str = ""):
    from config.db_schema import MadreAction

    entry = MadreAction(module=module, action=action, reason=reason)
    session.add(entry)
    session.commit()


def _upsert_system_state(data: Dict[str, Any]):
    session = get_session("vx11")
    try:
        state = session.query(SystemState).filter_by(key="global").first()
        if not state:
            state = SystemState(key="global")
        state.value = json.dumps(data)
        state.memory_pressure = data.get("memory_pressure", 0.0)
        state.cpu_pressure = data.get("cpu_pressure", 0.0)
        state.switch_queue_level = data.get("switch_queue_level", 0.0)
        state.hermes_update_required = data.get("hermes_update_required", False)
        state.shub_pipeline_state = data.get("shub_pipeline_state", "idle")
        state.operator_active = data.get("operator_active", False)
        state.system_load_score = data.get("system_load_score", 0.0)
        state.model_rotation_state = data.get("model_rotation_state", "stable")
        state.audio_pipeline_state = data.get("audio_pipeline_state", "idle")
        state.pending_tasks = data.get("pending_tasks", 0)
        state.active_children = data.get("active_children", 0)
        state.last_operator_activity = data.get("last_operator_activity")
        state.power_mode = data.get("power_mode", "balanced")
        session.add(state)
        session.commit()
    finally:
        session.close()


# ========== POWER MANAGER ==========

class PowerManager:
    """Gestiona encendido/apagado de módulos vía Docker Engine API."""
    
    def __init__(self):
        self.docker_client = None
        self.try_docker()
    
    def try_docker(self):
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            write_log("madre", f"PowerManager: docker_unavailable:{e}")
            self.docker_client = None
    
    async def power_on(self, module: str) -> Dict[str, Any]:
        """Enciende contenedor de módulo."""
        if not self.docker_client:
            return {"status": "error", "reason": "docker_unavailable"}
        try:
            container = self.docker_client.containers.get(module)
            if container.status != "running":
                container.start()
            db = get_session("vx11")
            event = PowerEvent(module=module, action="on", reason="manual")
            event.cpu_usage = psutil.cpu_percent()
            event.ram_usage = psutil.virtual_memory().percent
            db.add(event)
            db.commit()
            db.close()
            write_log("madre", f"power_on:{module}")
            return {"status": "ok", "module": module}
        except Exception as e:
            write_log("madre", f"power_on_error:{module}:{e}", level="ERROR")
            return {"status": "error", "reason": str(e)}
    
    async def power_off(self, module: str) -> Dict[str, Any]:
        """Apaga contenedor de módulo."""
        if not self.docker_client:
            return {"status": "error", "reason": "docker_unavailable"}
        try:
            container = self.docker_client.containers.get(module)
            if container.status == "running":
                container.stop(timeout=5)
            db = get_session("vx11")
            event = PowerEvent(module=module, action="off", reason="manual")
            event.cpu_usage = psutil.cpu_percent()
            event.ram_usage = psutil.virtual_memory().percent
            db.add(event)
            db.commit()
            db.close()
            write_log("madre", f"power_off:{module}")
            return {"status": "ok", "module": module}
        except Exception as e:
            write_log("madre", f"power_off_error:{module}:{e}", level="ERROR")
            return {"status": "error", "reason": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Estado de todos los módulos."""
        if not self.docker_client:
            return {"status": "error", "reason": "docker_unavailable"}
        modules = ["tentaculo_link", "madre", "switch", "hermes", "hormiguero", "manifestator", "mcp", "shub", "spawner", "operator"]
        result = {}
        try:
            for mod in modules:
                container = self.docker_client.containers.get(mod)
                result[mod] = {
                    "status": container.status,
                    "cpu": psutil.cpu_percent(),
                    "ram": psutil.virtual_memory().percent,
                }
        except Exception as e:
            result["error"] = str(e)
        return result
    
    async def decide_auto(self) -> Dict[str, Any]:
        """Decisión automática de encendido/apagado basada en carga."""
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        actions = []
        
        # Si CPU > 80%, apagar módulos innecesarios (bajo consumo)
        if cpu > 80:
            for mod in ["hermes", "shub", "spawner"]:
                result = await self.power_off(mod)
                actions.append({"module": mod, "action": "off", "result": result.get("status")})
        
        # Si RAM > 85%, apagar manifestator (no crítico)
        if ram > 85:
            result = await self.power_off("manifestator")
            actions.append({"module": "manifestator", "action": "off", "result": result.get("status")})
        
        return {"actions": actions, "cpu": cpu, "ram": ram}


_power_manager = PowerManager()


async def _dispatch_shub_task(task: ShubTaskRequest) -> Dict[str, Any]:
    """
    Envía tarea shub_task a Spawner de forma segura.
    En testing_mode responde stub sin red.
    """
    payload = {
        "name": f"shub_{task.task_kind}",
        "cmd": "echo",
        "args": [task.task_kind],
        "intent_type": "shub_task",
        "priority": task.priority or 2,
        "ttl": task.ttl or 120,
        "purpose": f"shub_{task.task_kind}",
        "module_creator": "madre",
        "module": "shub",
        "context": {
            "task_kind": task.task_kind,
            "input_path": task.input_path,
            "output_path": task.output_path,
            "params": task.params,
        },
    }
    if getattr(settings, "testing_mode", False):
        return {"status": "queued", "spawn": payload, "testing": True}

    spawner_url = settings.spawner_url or f"http://spawner:{settings.spawner_port}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{spawner_url}/spawn", json=payload, headers=AUTH_HEADERS)
        data = resp.json() if resp.status_code == 200 else {"status": "error", "code": resp.status_code}
        data["spawn"] = payload
        return data


def _record_scheduler(action: str, reason: str, metrics: Dict[str, Any]):
    session = get_session("vx11")
    try:
        rec = SchedulerHistory(action=action, reason=reason, metrics=json.dumps(metrics))
        session.add(rec)
        session.commit()
    finally:
        session.close()


def _persist_plan(session, task_id: str, plan: List[Dict[str, Any]], feedback: Dict[str, Any]):
    """
    Guarda feedback inicial y plan tentacular en BD unificada.
    """
    try:
        ctx = Context(task_id=task_id, key="plan_v6_4", value=json.dumps(plan), scope="planning")
        fb = Context(task_id=task_id, key="feedback_switch", value=json.dumps(feedback), scope="planning")
        session.add(ctx)
        session.add(fb)
        session.commit()
    except Exception as exc:
        write_log("madre", f"persist_plan_error:{task_id}:{exc}", level="ERROR")


def set_module_state_local(module: str, state: str, reason: str = "") -> Dict[str, Any]:
    if module not in _MODULE_STATES:
        raise HTTPException(status_code=400, detail="unknown_module")
    if state not in ("off", "standby", "active"):
        raise HTTPException(status_code=400, detail="invalid_state")
    if module in ("madre", "tentaculo_link") and state == "off":
        raise HTTPException(status_code=400, detail="forbidden_state_for_core")
    _MODULE_STATES[module] = state
    session = get_session("madre")
    _record_action(session, module, state, reason)
    return {"module": module, "state": state, "reason": reason}


def evaluate_policies():
    """
    Evalúa health y ajusta estados según políticas básicas.
    """
    session = get_session("madre")
    from config.db_schema import ModuleHealth
    from config.container_state import set_state

    health = {h.module: h for h in session.query(ModuleHealth).all()}
    for module in _MODULE_STATES.keys():
        pol = _load_policy(session, module)
        h = health.get(module)
        if h and h.error_count >= pol.error_threshold:
            if module not in ("madre", "tentaculo_link"):
                set_state(module, "off")
                _record_action(session, module, "off", "health_errors")
        elif h and h.uptime_seconds > pol.idle_seconds and pol.enable_autosuspend:
            set_state(module, "standby")
            _record_action(session, module, "standby", "idle_timeout")


# =========== EPHEMERAL CHILDREN ===========

async def create_ephemeral_child(
    name: str,
    cmd: str,
    timeout: int = 30,
    context: Optional[Dict[str, Any]] = None,
    track_in_bd: bool = True,
    db_session=None,
) -> Dict[str, Any]:
    """
    Crear hijo efímero (proceso corto) vía spawner.
    Retorna: {child_id, status, stdout, stderr, exit_code}
    """
    child_id = f"child-{uuid.uuid4().hex[:8]}"
    
    spawner_url = settings.spawner_url or f"http://spawner:{settings.spawner_port}"
    try:
        async with httpx.AsyncClient(timeout=timeout or 30) as client:
            resp = await client.post(
                f"{spawner_url}/spawn",
                json={
                    "name": name,
                    "cmd": cmd,
                    "timeout": timeout,
                    "context": context or {},
                    "parent_task_id": context.get("task_id") if context else None,
                },
                headers=AUTH_HEADERS,
            )
            data = resp.json()
            status = data.get("status", "failed")
            if status != "started":
                raise RuntimeError(data)
            write_log("madre", f"ephemeral_child_started:{child_id}:{name}")
            return {
                "child_id": child_id,
                "status": status,
                "response": data,
            }
    except Exception as e:
        write_log("madre", f"ephemeral_child_failed:{child_id}:{str(e)}", level="ERROR")
        return {
            "child_id": child_id,
            "status": "failed",
            "error": str(e),
        }



async def process_pending_tasks(db_session=None):
    """Worker mínimo: marca como completed las tareas pendientes."""
    try:
        if db_session is None:
            db_session = get_session("madre")
        pending = db_session.query(Task).filter(Task.status == "pending").all()
        for t in pending:
            t.status = "completed"
            try:
                t.result = json.dumps({"ok": True})
            except Exception:
                t.result = "{\"ok\": true}"
            db_session.commit()
    except Exception as e:
        write_log("madre", f"process_pending_tasks_error:{str(e)}", level="ERROR")


# =========== CONVERSATIONAL CHAT ===========

class MadreChatSession:
    """Session para conversación iterativa con madre."""
    def __init__(self, task_id: str, db_session):
        self.task_id = task_id
        self.db_session = db_session
        self.messages: List[Dict[str, str]] = []
        self.context: Dict[str, Any] = {}
    
    def add_message(self, role: str, content: str):
        """Agregar mensaje al historial."""
        self.messages.append({"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()})
    
    def get_history(self) -> List[Dict[str, str]]:
        """Obtener historial de mensajes."""
        return self.messages
    
    async def respond(self, user_input: str, system_prompt: str = None) -> str:
        """
        Procesar entrada de usuario y generar respuesta.
        Usa switch para routeo inteligente de prompts.
        """
        self.add_message("user", user_input)
        
        # Construir prompt con contexto
        full_prompt = user_input
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{user_input}"
        
        try:
            # Routear a través de switch para seleccionar mejor proveedor
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{settings.switch_url}/switch/route",
                    json={
                        "prompt": full_prompt,
                        "task_type": "chat",
                        "context": self.context,
                    },
                    timeout=30,
                )
                result = resp.json()
                response_text = result.get("response", "No response generated")
                provider = result.get("provider", "unknown")
                
                self.add_message("assistant", response_text)
                
                # Actualizar contexto con metadatos
                self.context["last_provider"] = provider
                self.context["last_response_at"] = datetime.utcnow().isoformat()
                
                # Persistir en BD (como Context entries)
                ctx = Context(
                    task_id=self.task_id,
                    key=f"message_{len(self.messages)}",
                    value=json.dumps({"role": "assistant", "content": response_text, "provider": provider}),
                    scope="chat",
                )
                self.db_session.add(ctx)
                self.db_session.commit()
                
                write_log("madre", f"chat_response:{self.task_id}:{provider}")
                return response_text
        
        except Exception as e:
            error_msg = f"Chat error: {str(e)}"
            self.add_message("system", error_msg)
            write_log("madre", f"chat_error:{self.task_id}:{str(e)}", level="ERROR")
            return error_msg


# =========== POWER MANAGER ENDPOINTS ===========

@app.post("/madre/power/on/{module}")
async def power_on_endpoint(module: str):
    """Enciende un módulo."""
    return await _power_manager.power_on(module)


@app.post("/madre/power/off/{module}")
async def power_off_endpoint(module: str):
    """Apaga un módulo."""
    return await _power_manager.power_off(module)


@app.get("/madre/power/status")
async def power_status_endpoint():
    """Estado de todos los módulos."""
    return await _power_manager.get_status()


@app.post("/madre/power/auto-decide")
async def power_auto_decide():
    """Decisión automática basada en carga."""
    return await _power_manager.decide_auto()


# =========== AUDIO TASKS (SHUB INTEGRATION) ===========

@app.post("/madre/audio/analyze")
async def audio_analyze_task(req: ShubTaskRequest, background_tasks: BackgroundTasks):
    """Tarea de análisis de audio vía Spawner."""
    try:
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "task_kind": "analyze",
            "input_path": req.input_path,
            "output_path": req.output_path,
            "params": req.params,
            "priority": req.priority or 2,
            "ttl": req.ttl or 120
        }
        
        # Delegar a Spawner
        spawner_result = await _delegate_spawner(task_id, payload)
        
        # Registrar en BD
        db = get_session("madre")
        task = Task(
            id=task_id,
            type="audio_analyze",
            status="spawned",
            payload=json.dumps(payload),
            created_at=datetime.utcnow()
        )
        db.add(task)
        db.commit()
        
        return {"status": "spawned", "task_id": task_id, "spawner_response": spawner_result}
    except Exception as e:
        logger.error(f"audio_analyze error: {e}")
        return {"status": "error", "error": str(e)}


@app.post("/madre/audio/mix")
async def audio_mix_task(req: ShubTaskRequest):
    """Tarea de mezcla de audio."""
    try:
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "task_kind": "mix",
            "input_path": req.input_path,
            "output_path": req.output_path,
            "params": req.params,
        }
        
        spawner_result = await _delegate_spawner(task_id, payload)
        
        return {"status": "spawned", "task_id": task_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/madre/audio/master")
async def audio_master_task(req: ShubTaskRequest):
    """Tarea de masterización de audio."""
    try:
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "task_kind": "master",
            "input_path": req.input_path,
            "output_path": req.output_path,
            "params": req.params,
        }
        
        spawner_result = await _delegate_spawner(task_id, payload)
        
        return {"status": "spawned", "task_id": task_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# =========== ENDPOINTS ===========

@app.get("/health")
def health():
    return {"module": "madre", "status": "ok", "version": "v2"}


@app.post("/control")
def control(action: Optional[str] = None):
    """Control endpoint (start/stop/restart/status)."""
    return {"module": "madre", "action": action or "status", "status": "ok"}


# Metrics endpoints (adaptive optimization)
@app.get("/metrics/cpu")
async def metrics_cpu():
    """CPU metrics for madre module."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        return {"metric": "cpu", "value": cpu_percent, "unit": "percent"}
    except:
        return {"metric": "cpu", "value": 0, "unit": "percent"}


@app.get("/metrics/memory")
async def metrics_memory():
    """Memory metrics for madre module."""
    try:
        memory = psutil.virtual_memory()
        return {
            "metric": "memory",
            "value": memory.percent,
            "unit": "percent",
            "available_mb": memory.available / (1024 * 1024)
        }
    except:
        return {"metric": "memory", "value": 0, "unit": "percent"}


@app.get("/metrics/queue")
async def metrics_queue():
    """Active task and chat sessions metric."""
    db_session = get_session("madre")
    pending_tasks = db_session.query(Task).filter(Task.status == "pending").count()
    return {
        "metric": "queue",
        "value": pending_tasks + len(_SESSIONS),
        "unit": "items",
        "tasks": pending_tasks,
        "sessions": len(_SESSIONS)
    }


@app.get("/metrics/throughput")
async def metrics_throughput():
    """Task completion and chat throughput."""
    db_session = get_session("madre")
    completed_tasks = db_session.query(Task).filter(Task.status == "completed").count()
    total_messages = sum(len(s.get("messages", [])) for s in _SESSIONS.values())
    return {
        "metric": "throughput",
        "value": completed_tasks + total_messages,
        "unit": "items",
        "completed_tasks": completed_tasks,
        "chat_messages": total_messages
    }


# Autonomous monitoring loop (adaptive optimization)
_MONITORING_ACTIVE = False
_CURRENT_MODE = "BALANCED"


async def autonomous_monitor():
    """Background task: monitors load every 3-5 seconds and adjusts modes."""
    global _CURRENT_MODE, _MONITORING_ACTIVE
    _MONITORING_ACTIVE = True
    
    from config.metrics import MetricsCollector
    from config.settings import settings
    
    collector = MetricsCollector()
    
    while _MONITORING_ACTIVE:
        try:
            # Collect metrics from all modules
            all_metrics = await collector.collect_all_metrics(settings.PORTS)
            
            # Aggregate system metrics (CPU, Memory) safely
            local_metrics = all_metrics.get("local", {}) if isinstance(all_metrics, dict) else {}
            module_metrics = all_metrics.get("modules", {}) if isinstance(all_metrics, dict) else {}
            
            module_cpus = [m.get("cpu", 0) for m in module_metrics.values() if isinstance(m, dict)]
            module_mems = [m.get("memory", 0) for m in module_metrics.values() if isinstance(m, dict)]
            
            avg_module_cpu = sum(module_cpus) / len(module_cpus) if module_cpus else 0
            avg_module_mem = sum(module_mems) / len(module_mems) if module_mems else 0
            
            system_metrics = {
                "cpu_percent": local_metrics.get("cpu_percent", avg_module_cpu),
                "memory_percent": local_metrics.get("memory_percent", avg_module_mem)
            }
            
            # Calculate load score
            load_score = collector.calculate_load_score(system_metrics)
            
            # Determine mode
            new_mode = collector.get_mode(load_score)
            
            # If mode changed, notify switch and hormiguero
            if new_mode != _CURRENT_MODE:
                _CURRENT_MODE = new_mode
                
                # Send mode to switch
                try:
                    async with httpx.AsyncClient() as client:
                        switch_url = settings.switch_url or f"http://switch:{settings.switch_port}"
                        await client.post(
                            f"{switch_url}/switch/control",
                            json={"action": "set_mode", "mode": new_mode},
                            headers=AUTH_HEADERS,
                            timeout=2.0
                        )
                except:
                    pass
                
                # Send scaling command to hormiguero
                try:
                    async with httpx.AsyncClient() as client:
                        worker_count = {
                            "ECO": 2,
                            "BALANCED": 4,
                            "HIGH-PERF": 8,
                            "CRITICAL": 16
                        }.get(new_mode, 4)
                        
                        hormiguero_url = settings.hormiguero_url or f"http://hormiguero:{settings.hormiguero_port}"
                        await client.post(
                            f"{hormiguero_url}/hormiguero/control",
                            json={"action": "scale_workers", "target_count": worker_count},
                            headers=AUTH_HEADERS,
                            timeout=2.0
                        )
                except:
                    pass
                
                # Log mode change
                logger.info(f"[ADAPTIVE] Mode changed to {new_mode} (load_score={load_score:.2f})")
            
            # Sleep 3-5 seconds
            await asyncio.sleep(4)
        
        except Exception as e:
            logger.error(f"[ADAPTIVE] Monitor error: {e}")
            await asyncio.sleep(5)


@app.post("/task")
async def create_task(req: TaskRequest, db_session = Depends(lambda: get_session("madre"))):
    """Create and queue a task."""
    task_id = req.name or f"task-{uuid.uuid4().hex[:8]}"
    session_id = f"session-{int(time.time() * 1000)}"
    
    # Remove any existing task with the same uuid to avoid UNIQUE constraint errors
    existing = db_session.query(Task).filter(Task.uuid == req.name).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    # Create task in BD
    task = Task(
        uuid=task_id,
        name=req.name,
        module=req.module,
        action=req.action,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    
    # Store context
    if req.context:
        for key, value in req.context.items():
            ctx = Context(
                task_id=task_id,
                key=key,
                value=str(value),
                scope="module",
            )
            db_session.add(ctx)
        db_session.commit()
    
    write_log("madre", f"task_created:{task_id}:{req.module}:{req.action}")
    
    # Intento rápido de procesar tareas pendientes (worker minimal)
    try:
        await process_pending_tasks(db_session)
    except Exception:
        # No bloquear la creación de la task si el worker falla
        write_log("madre", f"process_pending_failed:{task_id}", level="WARNING")

    return TaskResponse(task_id=task_id, status="queued", session_id=session_id)


@app.get("/task/{task_id}")
def get_task_status(task_id: str, db_session = Depends(lambda: get_session("madre"))):
    """Get task status and details."""
    task = db_session.query(Task).filter(Task.uuid == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task_not_found")
    
    context_rows = db_session.query(Context).filter(Context.task_id == task_id).all()
    context = {c.key: c.value for c in context_rows}
    
    return {
        "task_id": task.uuid,
        "name": task.name,
        "module": task.module,
        "action": task.action,
        "status": task.status,
        "result": task.result,
        "error": task.error,
        "context": context,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }


@app.get("/tasks")
def list_tasks(limit: int = 50, status_filter: Optional[str] = None, db_session = Depends(lambda: get_session("madre"))):
    """List tasks."""
    query = db_session.query(Task).order_by(Task.updated_at.desc()).limit(limit)
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    tasks = query.all()
    return {
        "tasks": [
            {
                "task_id": t.uuid,
                "name": t.name,
                "status": t.status,
                "module": t.module,
                "action": t.action,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]
    }


@app.post("/child")
async def spawn_ephemeral_child(req: EphemeralChildRequest, db_session = Depends(lambda: get_session("madre"))):
    """Crear hijo efímero."""
    result = await create_ephemeral_child(
        name=req.name,
        cmd=req.cmd,
        timeout=req.timeout,
        context=req.context,
        track_in_bd=req.track_in_bd,
        db_session=db_session,
    )
    return result


@app.post("/chat")
async def madre_chat(req: MadreChatRequest, db_session = Depends(lambda: get_session("madre"))):
    """
    Conversación iterativa con madre.
    Reutiliza task_id si existe, sino crea uno nuevo.
    Soporta context-7 opcional (backward compatible).
    """
    task_id = req.task_id or f"chat-{uuid.uuid4().hex[:8]}"
    
    # Generar o usar context-7
    context7 = req.context if hasattr(req, 'context') and req.context else get_default_context7(task_id)
    if not validate_context7(context7):
        context7 = get_default_context7(task_id)
    
    # Obtener o crear task
    task = db_session.query(Task).filter(Task.uuid == task_id).first()
    if not task:
        task = Task(
            uuid=task_id,
            name=f"chat_{task_id[:8]}",
            module="madre",
            action="chat",
            status="running",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(task)
        db_session.commit()
    
    # Crear sesión de chat
    session = MadreChatSession(task_id, db_session)
    
    # Procesar mensajes
    responses = []
    for msg in req.messages:
        if msg.role == "user":
            response = await session.respond(msg.content, req.system_prompt)
            responses.append(response)
    
    # Actualizar task
    task.status = "completed"
    task.result = json.dumps({"messages": session.get_history(), "context7_used": context7})
    task.updated_at = datetime.utcnow()
    db_session.commit()
    
    write_log("madre", f"chat_completed:{task_id}:{len(req.messages)} messages")
    
    return {
        "task_id": task_id,
        "status": "completed",
        "responses": responses,
        "history": session.get_history(),
    }


@app.post("/orchestrate")
async def orchestrate(req: OrchestrationRequest):
    """Main orchestration endpoint."""
    action = req.action.lower()
    session_id = f"orch-{uuid.uuid4().hex[:8]}"
    write_log("madre", f"orchestrate:{action}:{req.target}")

    # Crear registro de task orquestada
    db_session = get_session("vx11")
    task_uuid = req.payload.get("task_id") if isinstance(req.payload, dict) else None
    task_uuid = task_uuid or f"task-{uuid.uuid4().hex[:8]}"
    task = Task(
        uuid=task_uuid,
        name=req.payload.get("name", f"orch_{action}") if isinstance(req.payload, dict) else f"orch_{action}",
        module="madre",
        action=action,
        status="running",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(task)
    db_session.commit()

    # Feedback inicial y plan
    feedback = await _planner.initial_feedback(req.payload if isinstance(req.payload, dict) else {})
    plan = _planner.build_plan(req.payload if isinstance(req.payload, dict) else {}, feedback)
    _persist_plan(db_session, task_uuid, plan, feedback)

    result = {"session_id": session_id, "task_id": task_uuid, "plan": plan, "feedback": feedback}

    if action == "spawn" and req.target == "spawner":
        strategy = await _ask_switch_for_strategy(req.payload or {})
        spawn_res = await _delegate_spawner(
            session_id,
            {
                **(req.payload or {}),
                "parent_task_id": task_uuid,
                "tools": _planner.recommended_tools(req.payload or {}),
                "provider": strategy.get("engine_selected"),
                "audio_pipeline": True if (strategy.get("engine_selected") in ("shub", "shub-audio") or (req.payload or {}).get("intent") == "audio") else False,
                "strategy": strategy,
            },
        )
        result["spawn"] = spawn_res
        task.status = "completed" if spawn_res.get("status") not in ("error", "failed") else "failed"
        task.result = json.dumps(spawn_res)
    elif action == "route" and req.target == "switch":
        route_res = await _delegate_switch(session_id, req.payload)
        result["route"] = route_res
        task.status = "completed" if route_res.get("status") != "error" else "failed"
        task.result = json.dumps(route_res)
    elif action == "exec" and req.target == "hermes":
        exec_res = await _delegate_hermes(session_id, req.payload)
        result["exec"] = exec_res
        task.status = "completed" if exec_res.get("status") != "error" else "failed"
        task.result = json.dumps(exec_res)
    else:
        result.update({"status": "unknown_action", "error": f"{action}/{req.target}"})
        task.status = "failed"
        task.error = result["error"]

    task.updated_at = datetime.utcnow()
    db_session.add(task)
    db_session.commit()
    db_session.close()

    return result


async def _delegate_spawner(session_id: str, payload: Dict[str, Any]):
    """Delegate to spawner service con TTL/agresividad y registro BD."""
    spawner_port = settings.PORTS.get("spawner", 8008)
    ttl = payload.get("ttl") or 90
    aggressiveness = payload.get("aggressiveness", "normal")
    tools = payload.get("tools") or []
    provider = payload.get("provider")
    try:
        async with httpx.AsyncClient(timeout=payload.get("timeout") or 20.0) as client:
            resp = await client.post(
                f"{settings.spawner_url or f'http://spawner:{spawner_port}'}/spawn",
                json={
                    "name": payload.get("name") or payload.get("task") or f"hija-{session_id[-4:]}",
                    "cmd": payload.get("cmd") or "echo",
                    "args": payload.get("args") or [],
                    "cwd": payload.get("cwd"),
                    "env": payload.get("env"),
                    "timeout": payload.get("timeout") or ttl,
                    "ttl": ttl,
                    "intent_type": payload.get("intent_type") or payload.get("task_type"),
                    "priority": payload.get("priority") or 1,
                    "purpose": payload.get("purpose") or payload.get("action"),
                    "module_creator": payload.get("module_creator") or "madre",
                    "context": {
                        "aggressiveness": aggressiveness,
                        "tools": tools,
                        "provider": provider,
                        "audio_pipeline": payload.get("audio_pipeline", False),
                        "input": payload.get("input"),
                        "output_path": payload.get("output_path"),
                    },
                    "parent_task_id": payload.get("parent_task_id"),
                },
                headers=AUTH_HEADERS,
            )
            data = resp.json()
            status = data.get("status", "error")

            # Registrar spawn en BD unificada
            session = get_session("vx11")
            try:
                spawn_rec = Spawn(
                    uuid=data.get("id") or session_id,
                    name=payload.get("name") or payload.get("task") or "hija",
                    cmd=payload.get("cmd") or "echo",
                    pid=data.get("pid"),
                    status="running" if status == "started" else status,
                    started_at=datetime.utcnow(),
                    parent_task_id=payload.get("parent_task_id"),
                    created_at=datetime.utcnow(),
                    stdout=json.dumps(data) if isinstance(data, dict) else None,
                )
                session.add(spawn_rec)
                session.commit()
            finally:
                session.close()

            write_log("madre", f"spawn_delegated:{session_id}:{status}")
            # Notificar tentaculo_link para trazabilidad
            try:
                await client.post(
                    f"{settings.tentaculo_link_url}/events/ingest",
                    json={
                        "source": "madre",
                        "type": "spawn_success" if status not in ("error", "failed") else "spawn_failure",
                        "payload": {
                            "session_id": session_id,
                            "task_id": payload.get("parent_task_id"),
                            "status": status,
                            "provider": provider,
                            "spawn": data,
                        },
                        "broadcast": True,
                    },
                    headers=AUTH_HEADERS,
                )
            except Exception:
                pass
            return {"session_id": session_id, "status": status, "spawn": data}
    except Exception as e:
        write_log("madre", f"spawn_failed:{session_id}:{str(e)}", level="ERROR")
        return {"session_id": session_id, "status": "error", "error": str(e)}


async def _delegate_switch(session_id: str, payload: Dict[str, Any]):
    """Delegate to switch service."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.switch_url}/switch/route",
                json=payload,
                headers=AUTH_HEADERS,
            )
            result = resp.json()
            write_log("madre", f"route_delegated:{session_id}")
            status_val = "ok" if result.get("status") != "error" else "error"
            if status_val == "error":
                retries = _TASK_RETRIES.get(session_id, 0)
                if retries < 2 and "breaker" not in result.get("result", ""):
                    _TASK_RETRIES[session_id] = retries + 1
                    result["retry"] = True
            return {"session_id": session_id, "status": status_val, "result": result}
    except Exception as e:
        write_log("madre", f"route_failed:{str(e)}", level="ERROR")
        retries = _TASK_RETRIES.get(session_id, 0)
        if retries < 2:
            _TASK_RETRIES[session_id] = retries + 1
            return {"session_id": session_id, "status": "error", "error": str(e), "retry": True}
        return {"session_id": session_id, "status": "error", "error": str(e)}


async def _ask_switch_for_strategy(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pregunta a Switch por estrategia/modelo para un intent.
    """
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{settings.switch_url}/switch/intent_router",
                json={"prompt": payload.get("prompt") or payload.get("text") or str(payload), "metadata": payload, "source": "madre"},
                headers=AUTH_HEADERS,
            )
            result = resp.json() if resp.status_code == 200 else {"status": "error", "code": resp.status_code}
            # Adjuntar prioridad/urgencia simples
            result["priority"] = payload.get("priority") or 1
            result["urgency"] = payload.get("urgency") or "normal"
            return result
    except Exception as exc:
        write_log("madre", f"switch_strategy_error:{exc}", level="WARNING")
        return {"status": "error", "error": str(exc)}


async def _delegate_hermes(session_id: str, payload: Dict[str, Any]):
    """Delegate to hermes service."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.hermes_url}/hermes/exec",
                json=payload,
                headers=AUTH_HEADERS,
            )
            result = resp.json()
            write_log("madre", f"exec_delegated:{session_id}")
            return {"session_id": session_id, "status": "ok", "result": result}
    except Exception as e:
        write_log("madre", f"exec_failed:{str(e)}", level="ERROR")
        return {"session_id": session_id, "status": "error", "error": str(e)}


@app.get("/status")
async def status():
    """Get madre and delegated services health."""
    status_checks = {}
    services = [
        ("spawner", settings.spawner_url or f"http://spawner:{settings.spawner_port}"),
        ("switch", settings.switch_url),
        ("hermes", settings.hermes_url),
        ("hormiguero", settings.hormiguero_url),
    ]
    
    for svc_name, base in services:
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                resp = await client.get(f"{str(base).rstrip('/')}/health")
                status_checks[svc_name] = "ok" if resp.status_code == 200 else "error"
        except Exception:
            status_checks[svc_name] = "unreachable"
    
    return {"service": "madre", "status": "ok", "delegated_services": status_checks}


@app.post("/madre/callback")
async def madre_callback(data: Dict[str, Any]):
    """
    Callback de hijas/spawner para registrar resultados.
    """
    session = get_session("vx11")
    try:
        spawn_id = data.get("id") or data.get("spawn_id")
        status_val = data.get("status")
        task_id = data.get("task_id") or data.get("parent_task_id")
        ttl = data.get("ttl")
        # Actualiza registro de spawn
        spawn_rec = session.query(Spawn).filter_by(uuid=spawn_id).first()
        if spawn_rec:
            spawn_rec.status = status_val or spawn_rec.status
            spawn_rec.result = json.dumps(data.get("result")) if data.get("result") else spawn_rec.result
            if ttl:
                spawn_rec.ttl = ttl  # type: ignore
            session.add(spawn_rec)
        # Actualiza task si aplica
        if task_id:
            task_rec = session.query(Task).filter_by(uuid=task_id).first()
            if task_rec:
                task_rec.status = "completed" if status_val not in ("error", "failed") else "failed"
                task_rec.result = json.dumps(data)
                task_rec.updated_at = datetime.utcnow()
                session.add(task_rec)
        session.commit()
        write_log("madre", f"callback_received:{spawn_id}:{status_val}")
        return {"status": "ok"}
    finally:
        session.close()


# ========== CONTAINER STATE MANAGEMENT (P&P) ==========

@app.get("/orchestration/module_states")
async def get_module_states():
    """Obtiene estado de todos los módulos (P&P orchestration)."""
    from config.container_state import get_all_states

    evaluate_policies()
    raw_states = get_all_states()
    states = {k: v.get("state") for k, v in raw_states.items()}
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z", "modules": states}


@app.post("/orchestration/set_module_state")
async def set_module_state(request: Dict[str, Any]):
    """
    Cambia estado de un módulo (off/standby/active).
    
    Body:
        {
          "module": "manifestator",
          "state": "standby"  # off, standby, active
        }
    """
    module = request.get("module")
    new_state = request.get("state")
    
    if not module or not new_state:
        return {"status": "error", "message": "module and state required"}
    
    res = set_module_state_local(module, new_state, reason="manual")
    return {"status": "ok", **res, "timestamp": datetime.utcnow().isoformat() + "Z"}


# ========== BRIDGE ENDPOINTS (Conversational Routing) ==========

class BridgeRequest(BaseModel):
    """Request to bridge handler for conversational routing."""
    action: str  # "audit_full", "scan_hive", "route_query", "spawn_cmd"
    query: Optional[str] = None  # For route_query, spawn_cmd
    context: Optional[Dict[str, Any]] = None


class OrganizeIntent(BaseModel):
    """Intent emitted by hormiguero auto-organizer."""
    type: str = "organize"
    severity: Optional[str] = "low"
    items: List[Dict[str, Any]]
    timestamp: Optional[str] = None
    canonical_version: Optional[str] = None


class HijaResponse(BaseModel):
    """Response from HIJA execution."""
    hija_id: str
    name: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


def _get_bridge_handler() -> BridgeHandler:
    """Get or create bridge handler."""
    global _bridge_handler
    if not _bridge_handler:
        madre_ports = settings.PORTS or {
            "hermes": 8003,
            "switch": 8002,
            "manifestator": 8005,
            "hormiguero": 8004,
        }
        _bridge_handler = BridgeHandler(madre_ports)
    return _bridge_handler



@app.post("/madre/bridge")
async def bridge(req: BridgeRequest):
    """
    Bridge handler: Convert conversational request to orchestrated action via HIJA.
    Supported actions:
    - audit_full: Check system drift + registry + health
    - scan_hive: Check hormiguero queen + ants
    - route_query: Send query to SmartRouter
    - spawn_cmd: Execute CLI command
    """
    bridge = _get_bridge_handler()
    
    try:
        if req.action == "audit_full":
            result = await bridge.audit_full(req.context)
        elif req.action == "scan_hive":
            result = await bridge.scan_hive(req.context)
        elif req.action == "route_query":
            if not req.query:
                raise ValueError("route_query requires 'query' field")
            result = await bridge.route_query(req.query, req.context)
        elif req.action == "spawn_cmd":
            if not req.query:
                raise ValueError("spawn_cmd requires 'query' field with command")
            result = await bridge.spawn_cmd(req.query, req.context)
        else:
            raise ValueError(f"unknown_action:{req.action}")
        
        write_log("madre", f"bridge:action={req.action}:ok")
        return {"status": "ok", **result}
    
    except Exception as e:
        write_log("madre", f"bridge_error:action={req.action}:{e}", level="ERROR")
        return {"status": "error", "error": str(e)}


@app.post("/madre/organize")
async def madre_organize(intent: OrganizeIntent):
    """Handle organize intents emitted by hormiguero auto-organizer."""
    bridge = _get_bridge_handler()
    result = await bridge.organize(intent.model_dump())
    return {"status": "ok", **result}


@app.get("/madre/hija/{hija_id}")
async def get_hija(hija_id: str):
    """Get HIJA status and result."""
    bridge = _get_bridge_handler()
    hija = await bridge.get_hija(hija_id)
    
    if not hija:
        raise HTTPException(status_code=404, detail="hija_not_found")
    
    return {
        "hija_id": hija.hija_id,
        "name": hija.name,
        "task_type": hija.task_type,
        "status": hija.status,
        "started_at": hija.started_at.isoformat(),
        "completed_at": hija.completed_at.isoformat() if hija.completed_at else None,
        "result": hija.result,
        "error": hija.error,
    }


@app.get("/madre/hijas")
async def list_hijas(status: Optional[str] = None):
    """List all HIJAS, optionally filtered by status."""
    bridge = _get_bridge_handler()
    hijas = await bridge.list_hijas(status)
    
    return {
        "count": len(hijas),
        "hijas": [
            {
                "hija_id": h.hija_id,
                "name": h.name,
                "task_type": h.task_type,
                "status": h.status,
                "started_at": h.started_at.isoformat(),
                "completed_at": h.completed_at.isoformat() if h.completed_at else None,
            }
            for h in hijas
        ],
    }


@app.post("/madre/shub/task")
async def madre_shub_task(req: ShubTaskRequest):
    """Registrar y despachar tarea de audio Shub → Spawner."""
    if getattr(settings, "testing_mode", False):
        spawn_res = await _dispatch_shub_task(req)
        return {"status": "queued", "task_id": "testing", "spawn": spawn_res}

    session = get_session("madre")
    task = None
    try:
        task = Task(
            task_id=str(uuid.uuid4()),
            intent="shub_task",
            status="pending",
            payload=json.dumps(req.model_dump()),
            source="madre",
        )
        session.add(task)
        session.commit()
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"task_creation_failed:{exc}")
    finally:
        session.close()

    spawn_res = await _dispatch_shub_task(req)
    return {"status": "queued", "task_id": task.task_id if task else None, "spawn": spawn_res}


# =========== SCHEDULER AND STATE ===========


async def _fetch_switch_queue_level() -> float:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            switch_url = settings.switch_url or f"http://switch:{settings.switch_port}"
            r = await client.get(f"{switch_url}/switch/queue/status", headers=AUTH_HEADERS)
            if r.status_code == 200:
                return float(r.json().get("size", 0))
    except Exception:
        return 0.0
    return 0.0


async def _system_state_refresh():
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=0.05)
    switch_queue = await _fetch_switch_queue_level()
    session = get_session("madre")
    pending_tasks = session.query(Task).filter(Task.status == "pending").count()
    active_children = session.query(Spawn).filter(Spawn.status == "running").count() if hasattr(Spawn, "status") else 0
    session.close()
    load_score = min(1.0, (cpu_percent / 100) * 0.5 + (memory.percent / 100) * 0.5)
    state_payload = {
        "memory_pressure": memory.percent,
        "cpu_pressure": cpu_percent,
        "switch_queue_level": switch_queue,
        "hermes_update_required": False,
        "shub_pipeline_state": "idle",
        "operator_active": True,
        "system_load_score": load_score,
        "model_rotation_state": "stable",
        "audio_pipeline_state": "idle",
        "pending_tasks": pending_tasks,
        "active_children": active_children,
        "last_operator_activity": None,
        "power_mode": settings.environment,
    }
    _upsert_system_state(state_payload)
    _record_scheduler("heartbeat", "state_refresh", state_payload)
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            await client.post(
                f"http://{getattr(settings, 'tentaculo_link_host', 'tentaculo_link')}:{getattr(settings, 'tentaculo_link_port', settings.gateway_port)}/events/ingest",
                json={"source": "madre", "type": "system_state_update", "payload": state_payload, "broadcast": True},
                headers=AUTH_HEADERS,
            )
    except Exception:
        pass


# =========== INTENT → PLAN → HIJAS FLOW (v7.0) ===========

async def _ask_switch_for_intent_refinement(intent_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Consulta Switch para refinar INTENT y obtener estrategia de planificación."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.switch_url.rstrip('/')}/switch/task",
                json={
                    "task_type": "planning",
                    "payload": intent_payload,
                    "source": "madre",
                },
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        write_log("madre", f"switch_refinement_error:{exc}", level="WARNING")
    return {"status": "stub", "strategy": "default"}


async def call_switch_for_strategy(task_payload: Dict[str, Any], task_type: str = "general") -> Dict[str, Any]:
    """
    Consulta Switch para obtener estrategia recomendada.
    Usado por Madre para decidir approach de hija.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.switch_url.rstrip('/')}/switch/task",
                json={
                    "task_type": task_type,
                    "payload": task_payload,
                    "source": "madre",
                },
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                result = resp.json()
                write_log("madre", f"strategy_consulted:{task_type}:{result.get('provider')}")
                return result
    except Exception as exc:
        write_log("madre", f"call_switch_for_strategy_error:{task_type}:{exc}", level="WARNING")
    return {"provider": "local_default", "approach": "conservative"}


async def call_switch_for_subtask(subtask_payload: Dict[str, Any], subtask_type: str = "execution", source_hija_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Consulta Switch para ejecutar subtarea desde hija.
    Retorna resultado o indicación de error para reintentar.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.switch_url.rstrip('/')}/switch/task",
                json={
                    "task_type": subtask_type,
                    "payload": subtask_payload,
                    "source": "hijas",
                    "context": {"hija_id": source_hija_id} if source_hija_id else {},
                },
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                result = resp.json()
                write_log("madre", f"subtask_executed:{subtask_type}:{result.get('status')}")
                return result
    except httpx.TimeoutException:
        write_log("madre", f"call_switch_subtask_timeout:{subtask_type}", level="WARNING")
        return {"status": "timeout", "retry": True}
    except Exception as exc:
        write_log("madre", f"call_switch_subtask_error:{subtask_type}:{exc}", level="WARNING")
        return {"status": "error", "retry": True, "error": str(exc)}
    return {"status": "unknown", "retry": False}


async def _create_daughter_task_from_intent(session, intent_req: IntentRequest) -> Dict[str, Any]:
    """Crea entrada daughter_task a partir de INTENT y consulta Switch."""
    from config.db_schema import DaughterTask, IntentLog
    
    intent_id = str(uuid.uuid4())
    
    # Guardar en intents_log
    intent_log = IntentLog(
        source=intent_req.source,
        payload_json=json.dumps(intent_req.model_dump()),
        result_status="planned",
    )
    session.add(intent_log)
    session.flush()
    
    # Refinar con Switch
    strategy = await _ask_switch_for_intent_refinement(intent_req.payload)
    
    # Crear daughter_task
    priority = intent_req.priority or PRIORITY_MAP.get(intent_req.source, PRIORITY_MAP.get("hijas"))
    task_type = "short" if intent_req.ttl_seconds and intent_req.ttl_seconds < 60 else "long"
    
    daughter_task = DaughterTask(
        intent_id=intent_id,
        source=intent_req.source,
        priority=priority,
        status="pending",
        task_type=task_type,
        description=intent_req.intent_type,
        max_retries=2 if task_type == "short" else 5,
        metadata_json=json.dumps(intent_req.payload),
        plan_json=json.dumps(strategy),
    )
    session.add(daughter_task)
    session.commit()
    
    intent_log.processed_by_madre_at = datetime.utcnow()
    session.add(intent_log)
    session.commit()
    
    return {
        "intent_id": intent_id,
        "daughter_task_id": daughter_task.id,
        "status": "pending",
        "strategy": strategy,
    }


@app.post("/madre/intent")
async def madre_intent(req: IntentRequest):
    """Procesa INTENT: consulta Switch, crea plan, genera daughter_task, encola para spawning."""
    session = get_session("vx11")
    try:
        result = await _create_daughter_task_from_intent(session, req)
        write_log("madre", f"intent_processed:{result['intent_id']}")
        return {
            "status": "ok",
            "intent_id": result["intent_id"],
            "daughter_task_id": result["daughter_task_id"],
            "plan": result.get("strategy"),
        }
    except Exception as exc:
        write_log("madre", f"intent_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()


@app.get("/madre/tasks/active")
async def madre_tasks_active(status: Optional[str] = None):
    """Lista daughter_tasks activas (pending, planning, running, retrying)."""
    from config.db_schema import DaughterTask
    session = get_session("vx11")
    try:
        statuses = status.split(",") if status else ["pending", "planning", "running", "retrying"]
        tasks = session.query(DaughterTask).filter(DaughterTask.status.in_(statuses)).all()
        return {
            "count": len(tasks),
            "tasks": [
                {
                    "id": t.id,
                    "intent_id": t.intent_id,
                    "source": t.source,
                    "priority": t.priority,
                    "status": t.status,
                    "task_type": t.task_type,
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                    "current_retry": t.current_retry,
                    "max_retries": t.max_retries,
                }
                for t in tasks
            ],
        }
    finally:
        session.close()


@app.get("/madre/hijas/active")
async def madre_hijas_active(status: Optional[str] = None):
    """Lista hijas activas (spawned, running, restarting)."""
    from config.db_schema import Daughter
    session = get_session("vx11")
    try:
        statuses = status.split(",") if status else ["spawned", "running", "restarting"]
        hijas = session.query(Daughter).filter(Daughter.status.in_(statuses)).all()
        return {
            "count": len(hijas),
            "hijas": [
                {
                    "id": h.id,
                    "task_id": h.task_id,
                    "name": h.name,
                    "purpose": h.purpose,
                    "status": h.status,
                    "mutation_level": h.mutation_level,
                    "started_at": h.started_at.isoformat() if h.started_at else None,
                }
                for h in hijas
            ],
        }
    finally:
        session.close()


@app.get("/madre/task/{task_id}")
async def madre_task_status(task_id: int):
    """Estado completo de una daughter_task + hijas asociadas."""
    from config.db_schema import DaughterTask, Daughter, DaughterAttempt
    session = get_session("vx11")
    try:
        task = session.query(DaughterTask).filter_by(id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="task_not_found")
        
        hijas = session.query(Daughter).filter_by(task_id=task_id).all()
        hija_data = []
        for hija in hijas:
            attempts = session.query(DaughterAttempt).filter_by(daughter_id=hija.id).all()
            hija_data.append({
                "id": hija.id,
                "name": hija.name,
                "status": hija.status,
                "mutation_level": hija.mutation_level,
                "attempts": [
                    {
                        "number": a.attempt_number,
                        "status": a.status,
                        "started_at": a.started_at.isoformat() if a.started_at else None,
                        "finished_at": a.finished_at.isoformat() if a.finished_at else None,
                    }
                    for a in attempts
                ],
            })
        
        return {
            "task": {
                "id": task.id,
                "source": task.source,
                "status": task.status,
                "description": task.description,
                "created_at": task.created_at.isoformat(),
                "current_retry": task.current_retry,
                "max_retries": task.max_retries,
            },
            "hijas": hija_data,
        }
    finally:
        session.close()


@app.post("/madre/task/{task_id}/cancel")
async def madre_task_cancel(task_id: int):
    """Cancela tarea y todas sus hijas."""
    from config.db_schema import DaughterTask, Daughter
    session = get_session("vx11")
    try:
        task = session.query(DaughterTask).filter_by(id=task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="task_not_found")
        
        task.status = "cancelled"
        hijas = session.query(Daughter).filter_by(task_id=task_id).all()
        for hija in hijas:
            hija.status = "killed"
        
        session.commit()
        write_log("madre", f"task_cancelled:{task_id}")
        return {"status": "ok", "task_id": task_id}
    finally:
        session.close()


async def _daughters_scheduler():
    """Background task: Procesa daughter_tasks pendientes/retrying, crea hijas, maneja TTL/reintentos."""
    from config.db_schema import DaughterTask, Daughter, DaughterAttempt
    import math
    
    while True:
        try:
            await asyncio.sleep(5)  # Ejecutar cada 5 segundos
            session = get_session("vx11")
            
            # 1. Procesar tasks pending/retrying → crear hijas + invocar Spawner
            pending_tasks = session.query(DaughterTask).filter(
                DaughterTask.status.in_(["pending", "retrying"])
            ).all()
            
            for task in pending_tasks[:3]:  # Limitar a 3 por ciclo
                task.status = "planning"
                hija = Daughter(
                    task_id=task.id,
                    name=f"hija-{task.id}-{task.current_retry}",
                    purpose=task.description,
                    ttl_seconds=int(task.metadata_json and json.loads(task.metadata_json).get("ttl_seconds", 300)) or 300,
                    status="spawned",
                    mutation_level=task.current_retry,
                    started_at=datetime.utcnow(),
                )
                session.add(hija)
                session.flush()
                
                # Registrar DaughterAttempt
                attempt = DaughterAttempt(
                    daughter_id=hija.id,
                    attempt_number=task.current_retry + 1,
                    started_at=datetime.utcnow(),
                    status="running",
                )
                session.add(attempt)
                session.commit()
                
                # NUEVO: Invocar /spawner/spawn para crear hija real
                try:
                    spawn_payload = {
                        "name": hija.name,
                        "cmd": "python",
                        "args": ["-c", "import asyncio; await asyncio.sleep(10)"],
                        "parent_task_id": str(task.id),
                        "intent_type": task.task_type,
                        "purpose": hija.purpose,
                        "ttl": hija.ttl_seconds,
                        "context": json.loads(task.metadata_json) if task.metadata_json else {},
                        "module_creator": task.source,
                    }
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        spawner_resp = await client.post(
                            f"{settings.spawner_url}/spawner/spawn",
                            json=spawn_payload,
                            headers=AUTH_HEADERS,
                        )
                    if spawner_resp.status_code == 200:
                        hija.status = "running"
                        task.status = "running"
                        write_log("madre", f"hija_spawned_real:{hija.id}:{hija.name}")
                    else:
                        hija.status = "failed"
                        hija.error_last = f"spawner_status_{spawner_resp.status_code}"
                        write_log("madre", f"spawn_failed_status:{hija.id}", level="WARN")
                except httpx.TimeoutException:
                    hija.status = "failed"
                    hija.error_last = "spawner_timeout"
                    write_log("madre", f"spawn_timeout:{hija.id}", level="WARN")
                except Exception as e:
                    hija.status = "failed"
                    hija.error_last = str(e)
                    write_log("madre", f"spawn_error:{hija.id}:{e}", level="ERROR")
                
                session.add(hija)
                session.add(task)
                session.commit()
            
            # 2. Chequear TTL expirado + reintentos con backoff exponencial
            now = datetime.utcnow()
            running_hijas = session.query(Daughter).filter(
                Daughter.status.in_(["spawned", "running", "restarting"])
            ).all()
            
            for hija in running_hijas:
                if hija.started_at:
                    age_secs = (now - hija.started_at).total_seconds()
                    if age_secs > hija.ttl_seconds:
                        hija.status = "expired"
                        task = session.query(DaughterTask).filter_by(id=hija.task_id).first()
                        
                        if task and task.current_retry < task.max_retries:
                            # Calcular backoff exponencial: min(300, 2^retry)
                            backoff_secs = min(300, 2 ** task.current_retry)
                            task.status = "retrying"
                            task.current_retry += 1
                            write_log("madre", f"hija_retry_scheduled:{hija.id}:backoff_{backoff_secs}s")
                        elif task:
                            task.status = "failed"
                            write_log("madre", f"hija_max_retries_exhausted:{hija.id}")
                        
                        session.add(task)
            
            session.commit()
            session.close()
        except Exception as exc:
            write_log("madre", f"daughters_scheduler_error:{exc}", level="ERROR")
            try:
                session.close()
            except:
                pass


# =========== PRIORITY MAP (canónico) ===========

PRIORITY_MAP = {
    "shub": 0,
    "operator": 1,
    "madre": 2,
    "hijas": 3,
}


async def scheduler_loop():
    while True:
        await _system_state_refresh()
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan hook to replace deprecated on_event handlers."""
    global _bridge_handler, _MONITORING_ACTIVE
    monitor_task = asyncio.create_task(autonomous_monitor())
    scheduler_task = asyncio.create_task(scheduler_loop())
    daughters_task = asyncio.create_task(_daughters_scheduler())
    logger.info("[ADAPTIVE] Autonomous monitoring loop started")
    logger.info("[DAUGHTERS] Scheduler launched (5s interval)")
    try:
        yield
    finally:
        _MONITORING_ACTIVE = False
        for t in (monitor_task, scheduler_task, daughters_task):
            if t:
                t.cancel()
                try:
                    await t
                except Exception:
                    pass
        if _bridge_handler:
            await _bridge_handler.close()


app.router.lifespan_context = lifespan
