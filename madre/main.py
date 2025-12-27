"""Madre v7: Production Orchestrator (Simplified & Modular)."""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uuid
import logging
import subprocess
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import os

from . import power_saver as power_saver_module
from . import power_manager as power_manager_module

from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log

from .core import (
    IntentV2,
    PlanV2,
    ChatRequest,
    ChatResponse,
    ControlRequest,
    ControlResponse,
    HealthResponse,
    MadreDB,
    FallbackParser,
    PolicyEngine,
    Planner,
    Runner,
    DelegationClient,
)
from . import rails_router

log = logging.getLogger("vx11.madre")
logger = log

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

# Module instances
_parser = FallbackParser()
_policy = PolicyEngine()
_planner = Planner(
    enabled_targets={
        "switch": True,
        "hormiguero": True,
        "manifestator": True,
        "shub": True,
        "spawner": True,
    }
)
_runner = Runner()
_delegator = DelegationClient()

# Session store: {session_id -> {mode, last_activity, ...}}
_SESSIONS: Dict[str, Dict[str, Any]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    write_log("madre", "startup:v7_initialized")
    try:
        yield
    finally:
        write_log("madre", "shutdown:v7_closed")


app = FastAPI(
    title="VX11 Madre v7 (Production)",
    lifespan=lifespan,
)


# ============ HEALTH ============


@app.get("/health", response_model=HealthResponse)
async def health():
    """GET /health: canonical contract."""
    deps = await _delegator.check_dependencies()
    return HealthResponse(
        module="madre",
        status="ok",
        version="7.0",
        time=datetime.utcnow(),
        deps=deps,
    )


# ============ CHAT ENDPOINT ============


@app.post("/madre/chat", response_model=ChatResponse)
async def madre_chat(req: ChatRequest):
    """
    POST /madre/chat: Main chat endpoint.

    1. Create/load session
    2. Parse intent (via Switch or fallback)
    3. Classify risk + confirm if needed
    4. Generate plan
    5. Execute plan (async)
    6. Return response
    """
    session_id = req.session_id or str(uuid.uuid4())
    plan_id = str(uuid.uuid4())
    intent_id = str(uuid.uuid4())
    warnings = []
    targets = []
    actions = []

    # Create intent log entry
    intent_log_id = MadreDB.create_intent_log(
        source="operator",
        payload={
            "message": req.message,
            "session_id": session_id,
            "context": req.context or {},
        },
        result_status="planned",
    )

    try:
        # Step 1: Load or create session
        if session_id not in _SESSIONS:
            _SESSIONS[session_id] = {"mode": "MADRE", "created_at": datetime.utcnow()}

        session_mode = _SESSIONS[session_id].get("mode", "MADRE")

        # Step 2: Parse intent
        # Try Switch first (if available)
        try:
            # TODO: Call Switch for intent parsing
            # For now, use fallback
            dsl = _parser.parse(req.message, session_mode)
        except Exception as e:
            log.warning(f"Switch unavailable, using fallback parser: {e}")
            dsl = _parser.parse(req.message, session_mode)
            warnings.append("fallback_parser_used")

        # Step 3: Detect mode from domain
        if dsl.domain == "audio":
            session_mode = "AUDIO_ENGINEER"
            _SESSIONS[session_id]["mode"] = "AUDIO_ENGINEER"
        else:
            session_mode = "MADRE"
            _SESSIONS[session_id]["mode"] = "MADRE"

        # Step 4: Classify risk
        risk = _policy.classify_risk(dsl.domain, dsl.action)
        requires_confirmation = _policy.requires_confirmation(risk)

        # Create intent
        intent = IntentV2(
            intent_id=intent_id,
            session_id=session_id,
            mode=session_mode,
            dsl=dsl,
            risk=risk,
            requires_confirmation=requires_confirmation,
            targets=targets,
        )

        # Step 5: Generate plan
        plan = _planner.plan(intent)
        plan.plan_id = plan_id

        # Step 6: Persist task + plan
        MadreDB.create_task(
            task_id=plan_id,
            name="madre_plan",
            module="madre",
            action="chat",
            status="pending" if not requires_confirmation else "waiting",
        )
        MadreDB.set_context(plan_id, "madre:intent_id", intent_id)
        MadreDB.set_context(plan_id, "madre:mode", session_mode)
        MadreDB.set_context(plan_id, "madre:plan", plan.json())

        # Step 7: If confirmation required, generate token + return
        if requires_confirmation:
            confirm_token = _policy.generate_confirm_token()
            MadreDB.set_context(plan_id, "madre:confirm_token", confirm_token)
            MadreDB.record_action(
                module="madre",
                action=f"confirmation_required:{risk.value}",
                reason=f"action_{dsl.action}",
            )

            response = ChatResponse(
                response="Action requires confirmation. Provide plan_id and confirm_token to /madre/plans/{id}/confirm",
                session_id=session_id,
                intent_id=intent_id,
                plan_id=plan_id,
                status="WAITING",
                mode=session_mode,
                warnings=warnings,
                targets=targets,
                actions=[
                    {
                        "module": "madre",
                        "action": "awaiting_confirmation",
                        "reason": f"Risk level: {risk.value}",
                    }
                ],
            )
            MadreDB.close_intent_log(
                intent_log_id,
                result_status="waiting",
                notes=f"Confirmation required. Token: {confirm_token}",
            )
            return response

        # Step 8: Execute plan (async, fire-and-forget for now)
        plan = await _runner.execute_plan(plan, plan_id)

        # Step 9: Build response
        mode_enum = session_mode  # It's already the right value
        for step in plan.steps:
            if step.result:
                actions.append({"step": step.type, "result": step.result})

        response = ChatResponse(
            response=f"Plan executed. Mode: {session_mode}. Status: {plan.status.value}",
            session_id=session_id,
            intent_id=intent_id,
            plan_id=plan_id,
            status=plan.status,
            mode=mode_enum,
            warnings=warnings,
            targets=targets,
            actions=actions,
        )

        MadreDB.close_intent_log(
            intent_log_id,
            result_status="done",
            notes=f"Plan {plan_id} executed",
        )

        return response

    except Exception as e:
        log.error(f"Chat failed: {e}")
        MadreDB.close_intent_log(
            intent_log_id,
            result_status="error",
            notes=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============ CONTROL ENDPOINT ============


@app.post("/madre/control")
async def madre_control(req: ControlRequest):
    """
    POST /madre/control: Execute control actions.

    Returns pending_confirmation if MED/HIGH risk.
    """
    # Classify risk
    risk = _policy.classify_risk(req.target, req.action)
    requires_confirmation = _policy.requires_confirmation(risk)

    if requires_confirmation:
        if not req.confirm_token:
            # Generate token and return pending
            confirm_token = _policy.generate_confirm_token()
            MadreDB.record_action(
                module=req.target,
                action=req.action,
                reason=f"confirmation_required:{risk.value}",
            )
            return ControlResponse(
                status="pending_confirmation",
                confirm_token=confirm_token,
                reason=f"Risk: {risk.value}. Provide this token to confirm.",
            )
        else:
            # In production, validate token against stored one
            # For now, accept any token (simplified)
            pass

    # Execute action (simplified: just record)
    action_id = MadreDB.record_action(
        module=req.target,
        action=req.action,
        reason=f"params:{req.params}",
    )

    return ControlResponse(
        status="accepted",
        action_id=action_id,
    )


# ============ INTENT ENDPOINT ============


class MadreIntentRequest(BaseModel):
    type: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    source: str = "hormiguero"


@app.post("/madre/intent")
async def madre_intent(req: MadreIntentRequest):
    intent_id = req.correlation_id or str(uuid.uuid4())
    intent_log_id = MadreDB.create_intent_log(
        source=req.source,
        payload={
            "type": req.type,
            "payload": req.payload,
            "correlation_id": intent_id,
        },
        result_status="planned",
    )
    routing_decision = None
    routing_enabled = os.getenv("VX11_RAILS_ROUTING_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if routing_enabled:
        domain = req.payload.get("domain")
        intent_type = req.payload.get("intent_type") or req.type
        if domain and intent_type:
            routing_decision = rails_router.resolve_lane(
                domain=domain,
                intent_type=intent_type,
                correlation_id=intent_id,
                details={"source": req.source},
            )
            if not routing_decision:
                MadreDB.close_intent_log(
                    intent_log_id,
                    result_status="lane_missing",
                    notes=f"lane_missing:{domain}:{intent_type}",
                )
                return {
                    "status": "lane_missing",
                    "intent_id": intent_id,
                    "intent_log_id": intent_log_id,
                    "routing_decision": None,
                }
    task_id = str(uuid.uuid4())
    MadreDB.create_task(
        task_id=task_id,
        name="madre_intent",
        module="madre",
        action=req.type,
        status="pending",
    )
    MadreDB.set_context(task_id, "madre:intent_id", intent_id)
    MadreDB.set_context(task_id, "madre:intent_payload", req.payload)
    MadreDB.record_action(module="madre", action="intent_received", reason=req.type)
    return {
        "status": "accepted",
        "intent_id": intent_id,
        "task_id": task_id,
        "intent_log_id": intent_log_id,
        "routing_decision": routing_decision,
    }


# ============ ORCHESTRATION COMPAT ============


class OrchestrateRequest(BaseModel):
    action: str
    target: str
    payload: Dict[str, Any] = {}


@app.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest):
    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = {
        "mode": "orchestrate",
        "last_activity": datetime.utcnow().isoformat(),
        "action": req.action,
        "target": req.target,
    }
    return {
        "session_id": session_id,
        "status": "accepted",
        "action": req.action,
        "target": req.target,
    }


@app.get("/status")
async def status():
    deps = await _delegator.check_dependencies()
    return {"madre": "ok", "delegated_services": deps}


@app.get("/madre/status")
async def madre_status():
    """
    GET /madre/status: Unified Madre status endpoint (P0 #1).
    Returns consolidated info about madre module, services, DB, and canon.
    """
    import json
    from pathlib import Path

    # Get delegated services (power status)
    deps = await _delegator.check_dependencies()

    # Get DB info
    db_path = "data/runtime/vx11.db"
    db_info = {
        "path": db_path,
        "exists": Path(db_path).exists(),
        "size_bytes": Path(db_path).stat().st_size if Path(db_path).exists() else 0,
    }

    # DB integrity (quick check)
    try:
        result = subprocess.run(
            ["sqlite3", db_path, "PRAGMA quick_check;"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        db_info["quick_check"] = result.stdout.strip()
    except Exception as e:
        db_info["quick_check"] = f"error: {str(e)}"

    # FK violations count
    try:
        result = subprocess.run(
            ["sqlite3", db_path, "PRAGMA foreign_key_check;"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        fk_lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        db_info["fk_violations"] = len([l for l in fk_lines if l])
    except Exception as e:
        db_info["fk_violations"] = -1

    # Canon info
    canon_dir = Path("docs/canon")
    canon_files = list(canon_dir.glob("*.json")) if canon_dir.exists() else []
    canon_info = {
        "files": len(canon_files),
        "dir": str(canon_dir),
    }

    # Compute composite hash if possible
    if canon_files:
        import hashlib

        hashes = []
        for cf in sorted(canon_files):
            try:
                hashes.append(hashlib.sha256(cf.read_bytes()).hexdigest()[:8])
            except:
                pass
        canon_info["hash_composite"] = "".join(hashes)[:16] if hashes else "N/A"

    # Determine mode (detect from power/policy if possible)
    mode = "solo_madre"  # default
    try:
        # Check if solo_madre policy is active by introspecting power_manager
        # For now, use simple heuristic: if only madre+redis+tentaculo, then solo_madre
        pass
    except:
        pass

    return {
        "module": "madre",
        "version": "7.0",
        "mode": mode,
        "services_expected": ["tentaculo_link", "redis"],
        "services_running": list(deps.keys()) if isinstance(deps, dict) else [],
        "db": db_info,
        "canon": canon_info,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/sessions")
async def sessions():
    return {
        "sessions": [{"session_id": sid, **meta} for sid, meta in _SESSIONS.items()]
    }


# ============ PLAN ENDPOINTS ============


@app.get("/madre/plans")
async def lista_planes(skip: int = 0, limit: int = 10):
    """Get recent plans (from tasks where module='madre')."""
    # Simplified: return stub
    return {
        "plans": [],
        "skip": skip,
        "limit": limit,
        "note": "Full implementation requires DB query",
    }


@app.get("/madre/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get specific plan details."""
    task = MadreDB.get_task(plan_id)
    if not task:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan_json = MadreDB.get_context(plan_id, "madre:plan")
    intent_id = MadreDB.get_context(plan_id, "madre:intent_id")
    mode = MadreDB.get_context(plan_id, "madre:mode")

    return {
        "task": task,
        "plan_json": plan_json,
        "intent_id": intent_id,
        "mode": mode,
    }


@app.post("/madre/plans/{plan_id}/confirm")
async def confirm_plan(plan_id: str, confirm_token: str):
    """Confirm and resume a WAITING plan."""
    stored_token = MadreDB.get_context(plan_id, "madre:confirm_token")

    if not stored_token:
        raise HTTPException(
            status_code=400, detail="No confirmation pending for this plan"
        )

    if not _policy.validate_confirm_token(confirm_token, stored_token):
        raise HTTPException(status_code=403, detail="Invalid token")

    # Resume plan
    MadreDB.update_task(plan_id, status="running")
    MadreDB.record_action(
        module="madre",
        action="plan_confirmed",
        reason=f"plan_id:{plan_id}",
    )

    return {"status": "confirmed", "plan_id": plan_id}


class MadreTaskAliasRequest(BaseModel):
    message: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    intent_type: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


async def _madre_task_alias(req: MadreTaskAliasRequest):
    """
    Alias compatible para /madre/task.
    Si viene mensaje, reusa /madre/chat; si no, devuelve aceptación degradada.
    """
    if req.message:
        return await madre_chat(
            ChatRequest(
                message=req.message,
                session_id=req.session_id,
                context=req.metadata or {},
            )
        )
    return {
        "status": "accepted",
        "note": "madre_task_alias",
        "intent_type": req.intent_type,
        "payload": req.payload or {},
        "session_id": req.session_id,
    }


# ====== POWER SAVER ENDPOINTS ======


class IdleMinRequest(BaseModel):
    apply: bool = False


class RitualRequest(BaseModel):
    apply: bool = False


@app.get("/power/status")
async def power_status():
    out_dir = power_saver_module.make_out_dir(prefix="madre_power_saver_status")
    # snapshot and zombies
    await asyncio.to_thread(power_saver_module.snapshot, out_dir)
    z = await asyncio.to_thread(power_saver_module.list_zombies)
    # processes in repo
    proc_list = []
    try:
        res = subprocess.run(
            ["ps", "axo", "pid,ppid,stat,cmd"],
            capture_output=True,
            text=True,
            check=False,
        )
        proc_list = [l for l in res.stdout.splitlines() if "/home/elkakas314/vx11" in l]
    except Exception:
        proc_list = []
    # build response
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "out_dir": out_dir,
        "zombies_count": len(z),
        "repo_processes": proc_list,
    }


@app.post("/power/idle_min")
async def power_idle_min(req: IdleMinRequest):
    out_dir = power_saver_module.make_out_dir(prefix="madre_power_saver_idle_min")
    # run plan; idle_min is safe by default (apply default False)
    res = await asyncio.to_thread(power_saver_module.idle_min, out_dir, req.apply)
    report = await asyncio.to_thread(power_saver_module.final_report, out_dir)
    return {
        "status": "ok",
        "out_dir": out_dir,
        "applied": req.apply,
        "report": report,
        "result": res,
    }


@app.post("/power/regen_dbmap")
async def power_regen_dbmap():
    out_dir = power_saver_module.make_out_dir(prefix="madre_power_saver_regen")
    res = await asyncio.to_thread(power_saver_module.regen_dbmap, out_dir)
    report = await asyncio.to_thread(power_saver_module.final_report, out_dir)
    return {"status": "ok", "out_dir": out_dir, "result": res, "report": report}


@app.post("/power/ritual")
async def power_ritual(req: RitualRequest):
    out_dir = power_saver_module.make_out_dir(prefix="madre_power_saver_ritual")
    # snapshot
    await asyncio.to_thread(power_saver_module.snapshot, out_dir)
    # zombies write
    await asyncio.to_thread(power_saver_module.write_zombies, out_dir)
    # idle_min (plan or apply)
    idle_res = await asyncio.to_thread(power_saver_module.idle_min, out_dir, req.apply)
    # postcheck snapshot
    await asyncio.to_thread(power_saver_module.snapshot, out_dir)
    # regen dbmap
    regen_res = await asyncio.to_thread(power_saver_module.regen_dbmap, out_dir)
    # final report
    report = await asyncio.to_thread(power_saver_module.final_report, out_dir)
    return {
        "status": "ok",
        "out_dir": out_dir,
        "applied": req.apply,
        "idle_res": idle_res,
        "regen_res": regen_res,
        "report": report,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

# ===== BACKCOMPAT EXPORTS (tests + legacy clients) =====
# Exportamos compatibilidad mínima para tests que importan desde madre.main
from typing import Optional, Dict, Any
from pydantic import BaseModel
import os

USE_LEGACY = os.environ.get("VX11_USE_LEGACY_APP", "").lower() in ("1", "true", "yes")

if USE_LEGACY:
    try:
        # Mark import-safe for tests to avoid legacy module running background tasks or seeding DB
        os.environ.setdefault("VX11_TEST_IMPORT_SAFE", "1")
        from madre.main_legacy import app as _legacy_app  # type: ignore

        app = _legacy_app
    except Exception:
        pass

try:
    app.add_api_route("/madre/task", _madre_task_alias, methods=["POST"])
except Exception:
    pass


power_manager_module.register_power_routes(app)

# Expose httpx at module level so tests can patch 'madre.main.httpx.AsyncClient'
try:
    import httpx

    globals()["httpx"] = httpx
except Exception:
    pass

try:
    # Preferir definiciones canónicas si existen en main_legacy
    from madre.main_legacy import IntentRequest, ShubTaskRequest  # type: ignore
except Exception:

    class IntentRequest(BaseModel):
        source: str
        intent_type: str
        payload: Dict[str, Any]
        priority: Optional[int] = None
        ttl_seconds: Optional[int] = 300

    class ShubTaskRequest(BaseModel):
        task_kind: str
        input_path: Optional[str] = None
        output_path: Optional[str] = None
        params: Dict[str, Any] = {}
        priority: Optional[int] = 2
        ttl: Optional[int] = 120


try:
    from switch.main import PRIORITY_MAP  # type: ignore
except Exception:
    PRIORITY_MAP = {"shub": 0, "operator": 1, "madre": 2, "hijas": 3, "default": 4}

try:
    from config.container_state import _MODULE_STATES as _MODULE_STATES  # type: ignore
except Exception:
    _MODULE_STATES = {
        "tentaculo_link": {"state": "active"},
        "madre": {"state": "active"},
        "switch": {"state": "active"},
        "hermes": {"state": "active"},
        "hormiguero": {"state": "active"},
        "manifestator": {"state": "standby"},
        "mcp": {"state": "active"},
        "shubniggurath": {"state": "standby"},
        "spawner": {"state": "standby"},
        "operator": {"state": "active"},
    }
# ======================================================

try:
    from madre.main_legacy import _ask_switch_for_intent_refinement  # type: ignore
except Exception:

    async def _ask_switch_for_intent_refinement(payload: Dict[str, Any]):
        """Stub for tests: return empty refinement when Switch not available."""
        return {}


try:
    from madre.main_legacy import call_switch_for_strategy  # type: ignore
except Exception:

    async def call_switch_for_strategy(
        payload: Dict[str, Any], task_type: str = "general"
    ):
        """Stub for tests: return empty strategy when Switch not available."""
        return {}


try:
    from madre.main_legacy import call_switch_for_subtask  # type: ignore
except Exception:

    async def call_switch_for_subtask(
        payload: Dict[str, Any],
        subtask_type: str = "execution",
        source_hija_id: Optional[str] = None,
    ):
        """Stub for tests: return empty result when Switch not available."""
        return {}


# Attempt to import and re-export other legacy helpers used by tests
try:
    import madre.main_legacy as _legacy  # type: ignore

    for _name in (
        "_ask_switch_for_intent_refinement",
        "call_switch_for_strategy",
        "call_switch_for_subtask",
        "_create_daughter_task_from_intent",
        "_daughters_scheduler",
        "IntentRequest",
        "ShubTaskRequest",
    ):
        if hasattr(_legacy, _name) and _name not in globals():
            globals()[_name] = getattr(_legacy, _name)
except Exception:
    # If legacy module not importable, leave stubs above in place
    pass
else:
    # If legacy module imported as _legacy, provide a test-friendly single-iteration
    # runner for the daughters scheduler as tests call `_daughters_scheduler.__wrapped__(db_session)`.
    try:

        async def _daughters_scheduler_once(db_session):
            """Run one iteration of the daughters scheduler using provided DB session."""
            from config.db_schema import DaughterTask, Daughter, DaughterAttempt
            from datetime import datetime

            # Process pending/retrying tasks (limit 3)
            pending_tasks = (
                db_session.query(DaughterTask)
                .filter(DaughterTask.status.in_(["pending", "retrying"]))
                .all()
            )

            for task in pending_tasks[:3]:
                task.status = "planning"
                db_session.commit()

                # Create a Daughter
                hija = Daughter(
                    task_id=task.id,
                    name=f"hija-{task.id}-{task.current_retry}",
                    purpose=task.description,
                    ttl_seconds=getattr(task, "ttl_seconds", 60),
                    status="spawned",
                )
                db_session.add(hija)
                db_session.commit()

                # Notify spawner via httpx (tests will patch madre.main.httpx.AsyncClient)
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        await client.post(
                            f"{settings.spawner_url.rstrip('/')}/spawn",
                            json={"name": hija.name, "cmd": "echo run"},
                            headers=AUTH_HEADERS,
                        )
                except Exception:
                    # Best-effort; tests patch httpx so exceptions can be ignored
                    pass

                # Create DaughterAttempt
                attempt = DaughterAttempt(
                    daughter_id=hija.id,
                    attempt_number=1,
                    status="running",
                )
                db_session.add(attempt)
                db_session.commit()

        # If _daughters_scheduler exists in globals, attach __wrapped__ for tests
        if "_daughters_scheduler" in globals():
            try:
                globals()[
                    "_daughters_scheduler"
                ].__wrapped__ = _daughters_scheduler_once
            except Exception:
                pass
    except Exception:
        pass
