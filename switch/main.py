"""
VX11 Switch v6.3 - PASO 3
Router IA con Hermes integration, GA optimization, warm-up y Shub routing.

Features:
- Hermes integration: CLI registry, model scanners, selection
- GA optimizer: población evoluciona según fitness
- Warm-up engine: precalienta modelos en startup
- Shub router: detecta audio/DSP y enruta hacia Shubniggurath
"""

import asyncio
import json
import heapq
import time
import sqlite3
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import httpx
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from config.tokens import load_tokens, get_token
from config.forensics import write_log
from config.db_schema import get_session, TaskQueue, ModelRegistry, CLIRegistry, SystemState

# PASO 3: Importar componentes nuevos
from switch.ga_optimizer import GeneticAlgorithmOptimizer, GAIndividual
from switch.warm_up import WarmUpEngine
from switch.shub_router import ShubRouter, AudioDomain
from switch.hermes import CLISelector, CLIFusion, ExecutionMode, get_metrics_collector

# FASE 6: Importar Shub Forwarder (Wiring)
from switch.shub_forwarder import get_switch_shub_forwarder

# Logger
log = logging.getLogger("vx11.switch")

# Cargar tokens
load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

# Prioridades canónicas (menor número = mayor prioridad)
PRIORITY_MAP = {
    "shub": 0,
    "operator": 1,
    "tentaculo_link": 1,
    "madre": 2,
    "hijas": 3,
    "default": 4,
}


class RouteRequest(BaseModel):
    prompt: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = "operator"


class ModelSpec(BaseModel):
    name: str
    category: str = "general"
    size_mb: int = 500
    status: str = "available"  # available|active|warm|deprecated


@dataclass(order=True)
class QueueRecord:
    priority: int
    enqueued_at: float
    db_id: int = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)


class PersistentPriorityQueue:
    """
    Cola prioritaria persistente respaldada por task_queue en la BD unificada.
    """

    def __init__(self):
        self._heap: List[QueueRecord] = []
        self._lock = asyncio.Lock()
        self._bootstrap()

    def _bootstrap(self):
        session = get_session("vx11")
        try:
            rows = (
                session.query(TaskQueue)
                .filter(TaskQueue.status == "queued")
                .order_by(TaskQueue.enqueued_at.asc())
                .all()
            )
            for row in rows:
                self._heap.append(
                    QueueRecord(
                        priority=row.priority,
                        enqueued_at=row.enqueued_at.timestamp() if row.enqueued_at else time.time(),
                        db_id=row.id,
                        payload=json.loads(row.payload),
                    )
                )
            heapq.heapify(self._heap)
        finally:
            session.close()

    async def put(self, payload: Dict[str, Any], priority: int) -> int:
        async with self._lock:
            session = get_session("vx11")
            try:
                rec = TaskQueue(
                    source=payload.get("source", "unknown"),
                    priority=priority,
                    payload=json.dumps(payload),
                    status="queued",
                    enqueued_at=datetime.utcnow(),
                )
                session.add(rec)
                session.commit()
                db_id = rec.id
            finally:
                session.close()

            heapq.heappush(
                self._heap,
                QueueRecord(priority=priority, enqueued_at=time.time(), db_id=db_id, payload=payload),
            )
            return db_id

    async def get(self) -> Optional[QueueRecord]:
        async with self._lock:
            if not self._heap:
                return None
            record = heapq.heappop(self._heap)
            session = get_session("vx11")
            try:
                row = session.query(TaskQueue).filter(TaskQueue.id == record.db_id).first()
                if row:
                    row.status = "dequeued"
                    row.dequeued_at = datetime.utcnow()
                    session.add(row)
                    session.commit()
            finally:
                session.close()
            return record

    def snapshot(self) -> List[Dict[str, Any]]:
        return [
            {
                "priority": it.priority,
                "payload": it.payload,
                "enqueued_at": it.enqueued_at,
                "task_id": it.db_id,
            }
            for it in sorted(self._heap, key=lambda x: (x.priority, x.enqueued_at))
        ]


@dataclass
class ModelState:
    name: str
    category: str = "general"
    size_mb: int = 500
    status: str = "available"
    warm: bool = False
    last_used: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    kind: str = "general"  # audio|nlp|mix|cli-helper


class ModelPool:
    """
    Administra modelo activo/precalentado y sincroniza con Hermes/BD.
    """

    def __init__(self, limit: int = 30):
        self.limit = limit
        self.available: Dict[str, ModelState] = {}
        self.active: Optional[str] = None
        self.warm: Optional[str] = None
        self.last_operator_ping: float = 0.0
        self._seed_defaults()
        self.refresh_from_db()

    def _seed_defaults(self):
        self.register(ModelState(name="general-7b", category="general", size_mb=700))
        self.register(ModelState(name="audio-engineering", category="audio", size_mb=800, warm=True))
        # Registrar Shub como proveedor audio standby
        self.register(ModelState(name="shub-audio", category="audio", size_mb=200, status="standby", kind="audio"))
        self.set_active("general-7b")
        self.preload("audio-engineering")

    def refresh_from_db(self):
        """Carga modelos disponibles desde model_registry (<2GB)."""
        session = get_session("vx11")
        try:
            rows = (
                session.query(ModelRegistry)
                .filter(ModelRegistry.available == True)  # noqa: E712
                .filter(ModelRegistry.size_bytes <= 2 * 1024 * 1024 * 1024)
                .order_by(ModelRegistry.score.desc())
                .limit(self.limit)
                .all()
            )
            for r in rows:
                if r.name not in self.available:
                    self.register(
                        ModelState(
                            name=r.name,
                            category=r.type or "general",
                            size_mb=int(r.size_bytes / (1024 * 1024)),
                            tags=json.loads(r.tags) if r.tags else [],
                        )
                    )
        except Exception as exc:
            write_log("switch", f"model_registry_sync_error:{exc}", level="WARNING")
        finally:
            session.close()

    def register(self, model: ModelState):
        if model.size_mb > 2048:
            write_log("switch", f"skip_model_gt_2gb:{model.name}:{model.size_mb}")
            return
        if len(self.available) >= self.limit:
            evicted = next(iter(self.available.keys()))
            self.available.pop(evicted, None)
            write_log("switch", f"evicted_model:{evicted}")
        self.available[model.name] = model

    def set_active(self, name: str):
        if name not in self.available:
            raise ValueError("model_not_found")
        if self.active:
            self.available[self.active].status = "available"
        self.active = name
        self.available[name].status = "active"
        self.available[name].last_used = time.time()

    def preload(self, name: str):
        if name not in self.available:
            raise ValueError("model_not_found")
        self.warm = name
        self.available[name].warm = True
        self.available[name].status = "warm"

    def list_available(self) -> List[Dict[str, Any]]:
        return [m.__dict__ for m in self.available.values()]

    def pick_for_metadata(self, metadata: Dict[str, Any], source: str = "unknown") -> str:
        now = time.time()
        if source == "operator":
            self.last_operator_ping = now
            if self.active != "general-7b":
                self.set_active("general-7b")
        elif source == "shub" or metadata.get("task_type") == "audio":
            target = "shub-audio" if "shub-audio" in self.available else "audio-engineering"
            if target in self.available:
                self.set_active(target)
        elif self.warm and (now - self.last_operator_ping) > 300:
            # Si Operator inactivo, rotar hacia modelo precalentado
            try:
                self.set_active(self.warm)
            except Exception:
                pass

        category = metadata.get("category") or metadata.get("task_type") or "general"
        desired_kind = metadata.get("model_kind") or ("audio" if category == "audio" else "general")
        if self.active and self.available.get(self.active, ModelState(self.active)).category == category:
            self.available[self.active].last_used = now
            return self.active

        # prefer warm model of same category/kind
        if self.warm:
            warm_state = self.available.get(self.warm)
            if warm_state and warm_state.category == category and warm_state.size_mb <= 2048:
                self.set_active(self.warm)
                return self.warm

        # pick smallest candidate that matches category/kind and size <2GB
        candidates = [
            m for m in self.available.values()
            if m.category == category and m.size_mb <= 2048 and (m.kind == desired_kind or m.kind == "general")
        ]
        if candidates:
            best = sorted(candidates, key=lambda m: (m.size_mb, -m.last_used))[0]
            self.set_active(best.name)
            return best.name

        # fallback: usar activo o precalentado
        if self.active:
            return self.active
        if self.warm:
            return self.warm
        return next(iter(self.available.keys()), "auto")


queue = PersistentPriorityQueue()
models = ModelPool()


class CircuitBreaker:
    """
    Circuit breaker simple por proveedor.
    Estados: CLOSED -> HALF_OPEN -> CLOSED / OPEN.
    """

    def __init__(self, max_failures: int = 3, reset_timeout: int = 30):
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.state: Dict[str, Dict[str, Any]] = {}

    def allow(self, provider: str) -> bool:
        info = self.state.get(provider, {"state": "CLOSED", "failures": 0, "opened_at": 0})
        if info["state"] == "OPEN":
            if time.time() - info["opened_at"] > self.reset_timeout:
                info["state"] = "HALF_OPEN"
                self.state[provider] = info
                return True
            return False
        return True

    def record_success(self, provider: str):
        info = self.state.get(provider, {"state": "CLOSED", "failures": 0, "opened_at": 0})
        if info.get("state") == "HALF_OPEN":
            info["state"] = "CLOSED"
        info["failures"] = 0
        self.state[provider] = info

    def record_failure(self, provider: str):
        info = self.state.get(provider, {"state": "CLOSED", "failures": 0, "opened_at": 0})
        info["failures"] += 1
        if info["failures"] >= self.max_failures:
            info["state"] = "OPEN"
            info["opened_at"] = time.time()
        self.state[provider] = info


breaker = CircuitBreaker()
throttle_window_seconds = 5
throttle_limits = {"shub-audio": 5, "hermes": 10, "local": 10}
throttle_state: Dict[str, List[float]] = {}
scoring_state: Dict[str, Dict[str, Any]] = {}
CHAT_DB_PATH = settings.database_url.replace("sqlite:///", "") if "sqlite" in settings.database_url else "/app/data/runtime/vx11.db"
LATENCY_EMA: Dict[str, float] = {}


def _ensure_chat_stats_table():
    try:
        conn = sqlite3.connect(CHAT_DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_providers_stats (
                provider TEXT PRIMARY KEY,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                avg_latency_ms REAL DEFAULT 0
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _update_chat_stats(provider: str, success: bool, latency_ms: float):
    try:
        conn = sqlite3.connect(CHAT_DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT success_count, fail_count, avg_latency_ms FROM chat_providers_stats WHERE provider=?", (provider,))
        row = cur.fetchone()
        succ, fail, avg = row if row else (0, 0, 0.0)
        if success:
            succ += 1
        else:
            fail += 1
        total = max(1, succ + fail)
        new_avg = (avg * (total - 1) + latency_ms) / total
        cur.execute(
            "INSERT OR REPLACE INTO chat_providers_stats (provider, success_count, fail_count, avg_latency_ms) VALUES (?, ?, ?, ?)",
            (provider, succ, fail, new_avg),
        )
        conn.commit()
    except Exception as exc:
        write_log("switch", f"chat_stats_error:{provider}:{exc}", level="WARNING")
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _get_chat_stats(provider: str) -> Dict[str, Any]:
    try:
        conn = sqlite3.connect(CHAT_DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT success_count, fail_count, avg_latency_ms FROM chat_providers_stats WHERE provider=?", (provider,))
        row = cur.fetchone()
        if not row:
            return {"success": 0, "fail": 0, "avg_latency_ms": 0.0}
        return {"success": row[0], "fail": row[1], "avg_latency_ms": row[2]}
    except Exception:
        return {"success": 0, "fail": 0, "avg_latency_ms": 0.0}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _update_system_state(queue_size: int):
    session: Session = get_session("vx11")
    try:
        state = session.query(SystemState).filter_by(key="switch").first()
        if not state:
            state = SystemState(key="switch")
        state.value = json.dumps(
            {
                "queue_size": queue_size,
                "active_model": models.active,
                "warm_model": models.warm,
                "scoring": scoring_state,
            }
        )
        state.switch_queue_level = float(queue_size)
        state.operator_active = (time.time() - models.last_operator_ping) < 300
        state.updated_at = datetime.utcnow()
        session.add(state)
        session.commit()
    except Exception as exc:
        write_log("switch", f"system_state_update_error:{exc}", level="WARNING")
    finally:
        session.close()


def _get_cli_registry() -> List[Dict[str, Any]]:
    """
    Obtiene CLIs registrados por Hermes desde la tabla unificada.
    """
    session: Session = get_session("vx11")
    try:
        rows = session.query(CLIRegistry).all()
        return [
            {
                "name": r.name,
                "bin_path": r.bin_path,
                "available": r.available,
                "updated_at": r.updated_at.isoformat() if getattr(r, "updated_at", None) else None,
                "cli_type": r.cli_type,
            }
            for r in rows
        ]
    except Exception as exc:
        write_log("switch", f"cli_registry_error:{exc}", level="WARNING")
        return []
    finally:
        session.close()


def check_token(x_vx11_token: str = Header(None), request: Request = None):
    # Allow healthcheck without token to keep container healthy in local dev
    if request and (request.url.path == "/health" or request.url.path.startswith("/metrics")):
        return True
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=401, detail="auth_required")
    return True


app = FastAPI(title="VX11 Switch v6.3", dependencies=[Depends(check_token)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PASO 3: Inicializar GA, Warm-up, Shub Router
ga_optimizer: Optional[GeneticAlgorithmOptimizer] = None
warm_up_engine: Optional[WarmUpEngine] = None
shub_router: Optional[ShubRouter] = None
cli_selector: Optional[CLISelector] = None
cli_fusion: Optional[CLIFusion] = None


@app.on_event("startup")
async def _startup_consumer():
    """Startup completo con GA, Warm-up y Hermes integration"""
    global ga_optimizer, warm_up_engine, shub_router, cli_selector, cli_fusion
    
    _ensure_chat_stats_table()
    
    # Inicializar GA Optimizer
    log.info("Inicializando GA Optimizer...")
    ga_optimizer = GeneticAlgorithmOptimizer(
        population_size=10,
        engine_ids=["local_gguf", "deepseek_r1", "cli", "shub"],
        persistence_path="switch/ga_population.json"
    )
    log.info(f"GA: {ga_optimizer.get_population_summary()}")
    
    # Inicializar Warm-up Engine
    log.info("Inicializando Warm-up Engine...")
    warm_up_engine = WarmUpEngine(
        hermes_endpoint=settings.hermes_url or "http://switch:8003"
    )
    warmup_results = await warm_up_engine.warmup_startup()
    log.info(f"Warm-up completado: {warmup_results}")
    
    # Inicializar Shub Router
    log.info("Inicializando Shub Router...")
    shub_router = ShubRouter(
        shub_endpoint=settings.shub_url or "http://switch:8007"
    )
    
    # Inicializar CLI Selector y Fusion
    log.info("Inicializando Hermes CLI components...")
    cli_selector = CLISelector()
    cli_fusion = CLIFusion()
    
    # Iniciar consumer loop
    asyncio.create_task(_consumer_loop())
    
    # Iniciar warmup periódico en background
    asyncio.create_task(warm_up_engine.warmup_periodic())
    
    log.info("✓ Switch v6.3 (PASO 3) completamente inicializado")


@app.on_event("shutdown")
async def _shutdown():
    """Cleanup en shutdown"""
    global ga_optimizer
    if ga_optimizer:
        ga_optimizer._persist()
        log.info("GA Population persistida")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "module": "switch",
        "active_model": models.active,
        "warm_model": models.warm,
        "queue_size": len(queue.snapshot()),
    }


@app.get("/metrics{suffix:path}")
async def metrics_stub(suffix: str = ""):
    """Lightweight stub to silence missing metrics probes."""
    return {"status": "ok", "module": "switch", "metrics": "stub", "path": suffix or "/metrics"}


# PASO 3: GA Optimizer endpoints
@app.get("/switch/ga/status")
async def ga_status():
    """Retorna estado del GA Optimizer"""
    if not ga_optimizer:
        return {"error": "GA no inicializado"}
    return {
        "enabled": True,
        "population_summary": ga_optimizer.get_population_summary(),
        "elite_weights": ga_optimizer.get_best_weights(),
        "history_length": len(ga_optimizer.history),
    }


@app.post("/switch/ga/evolve")
async def ga_evolve():
    """Dispara evolución de población GA (normalmente automático)"""
    if not ga_optimizer:
        return {"error": "GA no inicializado"}
    ga_optimizer.evolve()
    return {
        "status": "ok",
        "generation": ga_optimizer.generation,
        "population_summary": ga_optimizer.get_population_summary(),
    }


# PASO 3: Warm-up endpoints
@app.get("/switch/warmup/status")
async def warmup_status():
    """Retorna estado del Warm-up Engine"""
    if not warm_up_engine:
        return {"error": "Warm-up no inicializado"}
    return warm_up_engine.get_health()


@app.post("/switch/warmup/manual")
async def warmup_manual():
    """Ejecuta precalentamiento manual"""
    if not warm_up_engine:
        return {"error": "Warm-up no inicializado"}
    results = await warm_up_engine.warmup_startup()
    return {
        "status": "ok",
        "results": results,
        "health": warm_up_engine.get_health(),
    }


# PASO 3: Shub Router endpoints
@app.post("/switch/shub/detect")
async def shub_detect(req: RouteRequest):
    """Detecta si una tarea debe ir a Shub y retorna plan de enrutamiento"""
    if not shub_router:
        return {"error": "Shub Router no inicializado"}
    
    should_route = shub_router.should_route_to_shub(
        req.prompt,
        req.metadata
    )
    
    if not should_route:
        return {
            "should_route_to_shub": False,
            "reason": "No se detectó tarea de audio",
        }
    
    domain = shub_router.detect_audio_domain(req.prompt, req.metadata)
    payload = shub_router.build_shub_payload(req.prompt, domain, req.metadata)
    endpoint = shub_router.get_shub_endpoint(domain)
    
    return {
        "should_route_to_shub": True,
        "domain": domain.value if domain else None,
        "endpoint": endpoint,
        "payload": payload,
    }


@app.post("/switch/shub/route")
async def shub_route(req: RouteRequest):
    """
    Enruta tarea hacia Shub si es audio/DSP.
    Si no es audio, retorna error.
    """
    if not shub_router:
        return {"error": "Shub Router no inicializado"}
    
    should_route = shub_router.should_route_to_shub(req.prompt, req.metadata)
    
    if not should_route:
        return {
            "status": "not_audio",
            "error": "Esta tarea no es de audio/DSP",
        }
    
    domain = shub_router.detect_audio_domain(req.prompt, req.metadata)
    payload = shub_router.build_shub_payload(req.prompt, domain, req.metadata)
    endpoint = shub_router.get_shub_endpoint(domain)
    
    try:
        async with httpx.AsyncClient(timeout=60.0, headers=AUTH_HEADERS) as client:
            resp = await client.post(
                endpoint,
                json=payload,
                headers=AUTH_HEADERS,
            )
            
            if resp.status_code == 200:
                shub_result = resp.json()
                return {
                    "status": "ok",
                    "domain": domain.value if domain else None,
                    "endpoint": endpoint,
                    "result": shub_result,
                }
            else:
                return {
                    "status": "error",
                    "code": resp.status_code,
                    "detail": resp.text[:200],
                }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }



def _should_use_cli(metadata: Dict[str, Any], queue_size: int, model_name: str) -> bool:
    if metadata.get("mode") == "cli" or metadata.get("prefer_cli"):
        return True
    if metadata.get("task_type") in {"cli", "cli_only"}:
        return True
    if queue_size > 5 and metadata.get("allow_cli_fallback"):
        return True
    if not model_name:
        return True
    return False


def _throttle(provider: str) -> bool:
    now = time.time()
    limit = throttle_limits.get(provider, 10)
    window = throttle_state.setdefault(provider, [])
    # Drop timestamps outside window
    window = [ts for ts in window if now - ts < throttle_window_seconds]
    throttle_state[provider] = window
    if len(window) >= limit:
        return False
    window.append(now)
    throttle_state[provider] = window
    return True


def _peek_throttle_state(provider: str) -> float:
    """
    Consulta disponibilidad sin consumir ventana. Devuelve 1.0 si disponible, 0.5 si saturado.
    """
    now = time.time()
    limit = throttle_limits.get(provider, 10)
    window = throttle_state.get(provider, [])
    window = [ts for ts in window if now - ts < throttle_window_seconds]
    return 1.0 if len(window) < limit else 0.5


def _record_scoring(provider: str, latency_ms: float, status_ok: bool):
    state = scoring_state.setdefault(provider, {"latencies": [], "failures": 0, "success": 0})
    state["latencies"] = (state["latencies"] + [latency_ms])[-50:]
    if status_ok:
        state["success"] += 1
    else:
        state["failures"] += 1
    scoring_state[provider] = state
    _update_latency_stats(provider, latency_ms)


def _update_latency_stats(provider: str, latency_ms: float):
    """
    Actualiza EMA de latencia con factor 0.3.
    """
    prev = LATENCY_EMA.get(provider)
    factor = 0.3
    if prev is None:
        LATENCY_EMA[provider] = latency_ms
    else:
        LATENCY_EMA[provider] = prev * (1 - factor) + latency_ms * factor


def _score_provider(provider: str) -> float:
    """
    Score combinado: latencia inversa + success rate + disponibilidad throttle/breaker.
    """
    stats = scoring_state.get(provider, {"success": 0, "fail": 0})
    total = stats["success"] + stats["fail"]
    success_rate = stats["success"] / total if total else 1.0
    latency = LATENCY_EMA.get(provider, 1000.0)
    latency_score = 1 / max(1.0, latency)
    throttle_ok = _peek_throttle_state(provider)
    breaker_ok = 0.0 if not breaker.allow(provider) else 1.0
    return (success_rate * 0.5) + (latency_score * 0.3) + (throttle_ok * 0.1) + (breaker_ok * 0.1)


async def _shub_is_healthy() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0, headers=AUTH_HEADERS) as client:
            resp = await client.get(f"{settings.shub_url.rstrip('/')}/health")
            data = resp.json()
            return resp.status_code == 200 and data.get("status") == "healthy"
    except Exception:
        return False


async def _pick_provider(req: RouteRequest) -> str:
    """
    Selección ligera de proveedor/modelo con control de breaker y salud de Shub.
    """
    model_name = models.pick_for_metadata(req.metadata, req.source or "unknown")
    # Audio -> preferir Shub si sano y breaker cerrado
    if (req.source == "shub" or (req.metadata or {}).get("task_type") == "audio") and await _shub_is_healthy():
        candidate = "shub-audio" if "shub-audio" in models.available else model_name
        if breaker.allow(candidate):
            return candidate
    # Circuit breaker: si modelo actual está abierto, fallback a warm/active
    if not breaker.allow(model_name):
        if models.warm and breaker.allow(models.warm):
            return models.warm
        if models.active and breaker.allow(models.active):
            return models.active
    return model_name


async def _process_task(task: Dict[str, Any]):
    """
    Consumidor de cola: delega a Hermes o Shub según proveedor.
    """
    provider = task.get("provider") or task.get("model")
    if not _throttle(provider or "default"):
        write_log("switch", f"throttle_drop:{provider}", level="WARNING")
        await asyncio.sleep(0.1)
        return {"status": "throttled"}
    payload = {
        "command": task.get("prompt"),
        "metadata": task.get("metadata") or {},
        "selection": {"model": provider, "source": task.get("source"), "provider": "shub" if provider == "shub-audio" else provider},
    }
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=15.0, headers=AUTH_HEADERS) as client:
            if provider == "shub-audio":
                resp = await client.post(
                    f"{settings.shub_url.rstrip('/')}/shub/execute",
                    json={
                        "task_type": "audio",
                        "task_id": task.get("task_id") or task.get("session_id"),
                        "payload": payload,
                    },
                )
            else:
                resp = await client.post(f"{settings.hermes_url.rstrip('/')}/hermes/execute", json=payload)
            latency_ms = (time.time() - start) * 1000
            ok = resp.status_code == 200
            if ok:
                breaker.record_success(provider or "unknown")
            else:
                breaker.record_failure(provider or "unknown")
            _record_scoring(provider or "unknown", latency_ms, ok)
            return resp.json()
    except Exception as exc:
        breaker.record_failure(provider or "unknown")
        write_log("switch", f"consumer_error:{provider}:{exc}", level="ERROR")
        return {"status": "error", "error": str(exc)}


async def _consumer_loop():
    """
    Background consumer: procesa cola con backoff ligero.
    """
    while True:
        item = await queue.get()
        if not item:
            await asyncio.sleep(0.25)
            continue
        task = item.payload
        result = await _process_task(task)
        # Persist result in task_queue
        session = get_session("vx11")
        try:
            row = session.query(TaskQueue).filter(TaskQueue.id == item.db_id).first()
            if row:
                row.status = "completed" if result and result.get("status") not in ("error", "failed") else "failed"
                row.result = json.dumps(result)
                row.updated_at = datetime.utcnow()
                session.add(row)
                session.commit()
        except Exception as exc:
            write_log("switch", f"queue_result_persist_error:{exc}", level="WARNING")
        finally:
            session.close()
        await asyncio.sleep(0.1)


@app.post("/switch/route-v5")
async def route_v5(req: RouteRequest):
    priority = PRIORITY_MAP.get(req.source or "default", PRIORITY_MAP["default"])
    task_payload = req.model_dump()
    model_name = await _pick_provider(req)
    task_payload["provider"] = model_name
    db_id = await queue.put(task_payload, priority)
    queue_size = len(queue.snapshot())
    _update_system_state(queue_size)

    response = {
        "status": "queued",
        "model": model_name,
        "queue_size": queue_size,
        "task_queue_id": db_id,
    }

    use_cli = _should_use_cli(req.metadata or {}, queue_size, model_name)
    if use_cli:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    f"{settings.hermes_url.rstrip('/')}/hermes/cli/execute",
                    json={"prompt": req.prompt, "metadata": {**req.metadata, "source": req.source}},
                    headers=AUTH_HEADERS,
                )
                response["hermes"] = r.json()
                response["cli_fallback"] = True
        except Exception as exc:
            response["hermes_error"] = str(exc)
            response["cli_fallback"] = True
    else:
        response["reply"] = f"[{model_name}] {req.prompt}"
    write_log("switch", f"route_v5:{req.source}:{model_name}:cli={use_cli}")
    return response


@app.post("/switch/route")
async def route_compat(req: RouteRequest):
    """Compatibilidad hacia route_v5."""
    return await route_v5(req)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    provider: Optional[str] = None
    provider_hint: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


@app.post("/switch/chat")
async def switch_chat(req: ChatRequest):
    """
    Chat estable: stub IA local + CLI remoto (selección híbrida).
    Integración Shub: si task_type==audio o provider_hint==shub, delega a Shub pipeline.
    Integración Madre: si task_type==system, delega a Madre.
    Integración Manifestator: si task_type==drift|audit, delega a Manifestator.
    """
    provider_hint = (req.provider_hint or req.provider or "").strip().lower() or None
    task_type = req.metadata.get("task_type", "").strip().lower() if req.metadata else ""
    
    # Detectar tarea de sistema → delegar a Madre
    if task_type == "system" or provider_hint == "madre":
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=30.0, headers=AUTH_HEADERS) as client:
                madre_payload = {
                    "messages": [m.model_dump() for m in req.messages],
                    "metadata": req.metadata or {},
                    "action": req.metadata.get("action") if req.metadata else None,
                }
                resp = await client.post(
                    f"{settings.madre_url.rstrip('/')}/madre/route-system",
                    json=madre_payload,
                    headers=AUTH_HEADERS,
                )
                if resp.status_code == 200:
                    madre_result = resp.json()
                    latency_ms = (time.monotonic() - start) * 1000
                    _record_scoring("madre", latency_ms=latency_ms, status_ok=True)
                    write_log("switch", f"chat:system_delegated_to_madre:latency={latency_ms}ms")
                    return {
                        "status": "ok",
                        "provider": "madre",
                        "content": madre_result.get("content", ""),
                        "latency_ms": latency_ms,
                    }
        except Exception as exc:
            write_log("switch", f"chat:madre_delegation_error:{exc}", level="WARNING")
    
    # Detectar tarea de análisis de estructura (manifestator)
    if task_type in ("drift", "audit", "manifest") or provider_hint == "manifestator":
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=30.0, headers=AUTH_HEADERS) as client:
                manifest_payload = {
                    "messages": [m.model_dump() for m in req.messages],
                    "metadata": req.metadata or {},
                    "action": req.metadata.get("action") if req.metadata else "analyze",
                }
                resp = await client.post(
                    f"{settings.manifestator_url.rstrip('/')}/detect-drift",
                    json=manifest_payload,
                    headers=AUTH_HEADERS,
                )
                if resp.status_code == 200:
                    manifest_result = resp.json()
                    latency_ms = (time.monotonic() - start) * 1000
                    _record_scoring("manifestator", latency_ms=latency_ms, status_ok=True)
                    write_log("switch", f"chat:drift_delegated_to_manifestator:latency={latency_ms}ms")
                    return {
                        "status": "ok",
                        "provider": "manifestator",
                        "content": manifest_result.get("details", ""),
                        "latency_ms": latency_ms,
                    }
        except Exception as exc:
            write_log("switch", f"chat:manifestator_delegation_error:{exc}", level="WARNING")
    
    # Detectar si es tarea de audio → delegar a Shub
    if task_type == "audio" or provider_hint in ("shub", "shub-audio"):
        try:
            start = time.monotonic()
            
            # Usar Shub Forwarder (FASE 6 Wiring)
            forwarder = get_switch_shub_forwarder()
            prompt_text = req.messages[0].content if req.messages else ""
            
            shub_result = await forwarder.route_to_shub(
                query=prompt_text,
                context=req.metadata or {}
            )
            
            if shub_result.get("status") in ("ok", "skip"):
                latency_ms = (time.monotonic() - start) * 1000
                _record_scoring("shub-audio", latency_ms=latency_ms, status_ok=True)
                _update_chat_stats("shub-audio", True, latency_ms)
                usage = _get_chat_stats("shub-audio")
                usage["score"] = _score_provider("shub-audio")
                write_log("switch", f"chat:audio_delegated_to_shub:latency={latency_ms}ms:decision={shub_result.get('routing_decision')}")
                
                # Si routing_decision es skip, continuar con fallback
                if shub_result.get("routing_decision") != "skip":
                    return {
                        "status": "ok",
                        "provider": "shub-audio",
                        "content": str(shub_result.get("result", {})),
                        "usage": usage,
                        "latency_ms": latency_ms,
                    }
            else:
                write_log("switch", f"chat:shub_error:{shub_result.get('status')}", level="WARNING")
        except Exception as exc:
            write_log("switch", f"chat:shub_delegation_error:{exc}", level="WARNING")
    
    # Fallback: chat híbrido local + CLI
    provider = _select_chat_backend(provider_hint)
    if not _throttle(provider):
        return {"status": "throttled"}
    start = time.monotonic()
    if provider == "cli":
        reply_obj = _cli_chat([m.model_dump() for m in req.messages])
    else:
        reply_obj = _local_llm_chat([m.model_dump() for m in req.messages])
    latency_ms = (time.monotonic() - start) * 1000
    _record_scoring(provider, latency_ms=latency_ms, status_ok=True)
    _update_chat_stats(provider, True, latency_ms)
    usage = _get_chat_stats(provider)
    usage["score"] = _score_provider(provider)
    return {
        "status": "ok",
        "provider": provider,
        "content": reply_obj.get("content", ""),
        "usage": usage,
        "latency_ms": latency_ms,
    }


class TaskRequest(BaseModel):
    task_type: str  # "audio-engineer", "summarization", "code-analysis", "audio-analysis", etc.
    payload: Dict[str, Any]  # Datos específicos de la tarea
    source: Optional[str] = "operator"  # "shub", "operator", "madre", "hija"
    provider_hint: Optional[str] = None  # Sugerencia de proveedor ("local", "shub", "cli")


@app.post("/switch/task")
async def switch_task(req: TaskRequest):
    """
    Ejecución de tareas estructuradas con prioridades.
    Lógica: Local-first para tareas, CLI-fallback si no hay modelo local.
    """
    import hashlib
    from config.db_schema import ModelUsageStat, SwitchQueueV2
    
    start = time.monotonic()
    task_type = req.task_type.strip().lower()
    source = req.source.strip().lower() if req.source else "unknown"
    priority = PRIORITY_MAP.get(source, PRIORITY_MAP["default"])
    
    # Generar payload_hash para dedup
    payload_hash = hashlib.sha256(
        json.dumps(req.payload, sort_keys=True).encode()
    ).hexdigest()
    
    # Registrar en queue
    session = get_session("vx11")
    try:
        queue_entry = SwitchQueueV2(
            source=source,
            priority=priority,
            task_type=task_type,
            payload_hash=payload_hash,
            status="queued",
            created_at=datetime.utcnow(),
        )
        session.add(queue_entry)
        session.commit()
        queue_id = queue_entry.id
    finally:
        session.close()
    
    # Seleccionar proveedor (local-first)
    provider_used = None
    result = None
    
    try:
        # 1) Buscar modelo local para task_type
        session = get_session("vx11")
        try:
            local_model = (
                session.query(ModelRegistry)
                .filter(ModelRegistry.type == task_type)
                .filter(ModelRegistry.available == True)  # noqa: E712
                .order_by(ModelRegistry.score.desc())
                .first()
            )
        finally:
            session.close()
        
        if local_model:
            # Invocar modelo local (stub simple)
            provider_used = local_model.name
            result = {
                "status": "ok",
                "provider": provider_used,
                "task_type": task_type,
                "response": f"Stub response from {provider_used}",
            }
        else:
            # 2) Fallback a CLI si no hay modelo local
            # Solicitar al hermes qué CLI está disponible
            try:
                async with httpx.AsyncClient(timeout=5.0, headers=AUTH_HEADERS) as client:
                    hermes_resp = await client.get(
                        f"{settings.hermes_url.rstrip('/')}/hermes/models/best",
                        params={"task_type": task_type, "max_size_mb": 2048},
                        headers=AUTH_HEADERS,
                    )
                    if hermes_resp.status_code == 200:
                        hermes_data = hermes_resp.json()
                        candidates = hermes_data.get("models", [])
                        if candidates:
                            chosen = candidates[0]
                            provider_used = chosen.get("name", "fallback")
                            result = {
                                "status": "ok",
                                "provider": provider_used,
                                "task_type": task_type,
                                "response": f"Response from {provider_used}",
                            }
            except Exception as e:
                write_log("switch", f"task_hermes_fallback_error:{e}", level="WARNING")
            
            # Si aún no hay resultado, fallback stub
            if not result:
                provider_used = "stub"
                result = {
                    "status": "stub",
                    "task_type": task_type,
                    "response": "Task completed (stub mode)",
                }
        
        # Registrar uso
        latency_ms = int((time.monotonic() - start) * 1000)
        session = get_session("vx11")
        try:
            usage_stat = ModelUsageStat(
                model_or_cli_name=provider_used or "unknown",
                kind="local" if local_model else "cli",
                task_type=task_type,
                tokens_used=0,
                latency_ms=latency_ms,
                success=True,
            )
            session.add(usage_stat)
            session.commit()
        finally:
            session.close()
        
        # Actualizar queue_entry a "done"
        session = get_session("vx11")
        try:
            entry = session.query(SwitchQueueV2).filter_by(id=queue_id).first()
            if entry:
                entry.status = "done"
                entry.finished_at = datetime.utcnow()
                session.add(entry)
                session.commit()
        finally:
            session.close()
        
        return {
            "status": "ok",
            "task_type": task_type,
            "provider": provider_used,
            "result": result,
            "latency_ms": latency_ms,
            "queue_id": queue_id,
        }
    
    except Exception as e:
        write_log("switch", f"task_error:{task_type}:{e}", level="ERROR")
        
        # Marcar como error en queue
        session = get_session("vx11")
        try:
            entry = session.query(SwitchQueueV2).filter_by(id=queue_id).first()
            if entry:
                entry.status = "error"
                entry.error_message = str(e)
                entry.finished_at = datetime.utcnow()
                session.add(entry)
                session.commit()
        finally:
            session.close()
        
        return {
            "status": "error",
            "error": str(e),
            "task_type": task_type,
            "queue_id": queue_id,
        }


@app.post("/switch/select_model")
async def select_model(req: RouteRequest):
    """
    Alias liviano para selección de modelo.
    Reusa la lógica de route_v5 sin ejecutar nada más.
    """
    result = await route_v5(req)
    return {"engine_selected": result.get("model"), "score": result.get("score"), "scores_per_engine": result.get("scores_per_engine")}


@app.post("/switch/hermes/select_engine")
async def hermes_select_engine(req: RouteRequest):
    """
    Alias: select_engine → select_model (compatibilidad VX11 documentada).
    Reusa la lógica de route_v5 y retorna scores de engine selection.
    """
    return await select_model(req)


@app.post("/switch/intent_router")
async def intent_router(req: RouteRequest):
    """
    Router de intents: reutiliza scoring de route_v5.
    """
    return await route_v5(req)


@app.post("/switch/hermes/infer")
async def hermes_infer(req: RouteRequest):
    """
    Enrutador de inferencia hacia Hermes conservando scoring de Switch.
    """
    # Seleccionar modelo vía Switch y luego delegar a Hermes
    selection = await route_v5(req)
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=AUTH_HEADERS) as client:
            resp = await client.post(
                f"{settings.hermes_url.rstrip('/')}/hermes/execute",
                json={"command": req.prompt, "metadata": req.metadata, "selection": selection},
            )
            hermes_payload = resp.json() if resp.status_code == 200 else {"status": "error", "code": resp.status_code}
    except Exception as exc:
        hermes_payload = {"status": "error", "error": str(exc)}
    return {"selection": selection, "hermes": hermes_payload}


@app.get("/switch/queue/status")
async def queue_status():
    return {"size": len(queue.snapshot()), "items": queue.snapshot()}


class PreloadRequest(BaseModel):
    model_name: str


@app.post("/switch/admin/preload_model")
async def preload_model(req: PreloadRequest):
    try:
        models.preload(req.model_name)
        write_log("switch", f"preload:{req.model_name}")
        return {"status": "ok", "warm": models.warm}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/switch/model/hot_reload")
async def hot_reload_models():
    """
    Recarga modelos desde registry sin reiniciar módulo.
    """
    try:
        session = get_session("vx11")
        rows = session.query(ModelRegistry).filter_by(available=True).all()
        count = 0
        for row in rows:
            model = ModelState(
                name=row.name,
                category=row.type or "general",
                size_mb=int(row.size_bytes / (1024 * 1024)),
                tags=json.loads(row.tags) if row.tags else [],
            )
            models.register(model)
            count += 1
        session.close()
        write_log("switch", f"hot_reload:models_reloaded:{count}")
        return {"status": "ok", "models_loaded": count, "active": models.active, "warm": models.warm}
    except Exception as e:
        write_log("switch", f"hot_reload_error:{e}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))


class DefaultModelRequest(BaseModel):
    model_name: str


@app.post("/switch/admin/set_default_model")
async def set_default_model(req: DefaultModelRequest):
    try:
        models.set_active(req.model_name)
        write_log("switch", f"set_default:{req.model_name}")
        return {"status": "ok", "active": models.active, "warm": models.warm}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/switch/models/available")
async def models_available():
    models.refresh_from_db()
    return {
        "models": models.list_available(),
        "active": models.active,
        "warm": models.warm,
        "cli_registry": _get_cli_registry(),
    }


@app.get("/switch/queue/next")
async def queue_next():
    item = await queue.get()
    if not item:
        return {"status": "empty"}
    return {"status": "ok", "payload": item.payload, "priority": item.priority, "task_queue_id": item.db_id}
def _local_llm_chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Stub de modelo local 7B/7A.
    TODO: conectar con motor local real (llama.cpp/gguf) en fase posterior.
    """
    text = messages[-1].get("content", "") if messages else ""
    write_log("switch", "local_llm_chat_called")
    return {"content": f"[local-7b] {text}"}


def _cli_chat(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Stub de CLI remoto de chat.
    TODO: integrar proveedor externo con token budget/latencia real.
    """
    text = messages[-1].get("content", "") if messages else ""
    write_log("switch", "cli_chat_called")
    return {"content": f"[cli-remote] {text}"}


def _select_chat_backend(provider_hint: Optional[str]) -> str:
    """
    Selección simple: respeta hint si no está en breaker; prioriza CLI si latencia media es baja.
    """
    if provider_hint and breaker.allow(provider_hint):
        return provider_hint
    cli_stats = _get_chat_stats("cli")
    local_stats = _get_chat_stats("local")
    cli_ok = breaker.allow("cli")
    if cli_ok and cli_stats.get("avg_latency_ms", 0) < 800:
        return "cli"
    return "local"
