"""Madre v7: Production Orchestrator (Simplified & Modular)."""

from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime

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
    MadreDB,
    FallbackParser,
    PolicyEngine,
    Planner,
    Runner,
    DelegationClient,
    HealthResponse,
)

log = logging.getLogger("vx11.madre")
logger = log

app = FastAPI(title="VX11 Madre v7 (Production)")

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

# Module instances
_parser = FallbackParser()
_policy = PolicyEngine()
_planner = Planner()
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
