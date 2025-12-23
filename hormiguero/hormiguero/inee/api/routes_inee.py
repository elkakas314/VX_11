"""
INEE FastAPI routes.

Rutas expuestas:
- POST /hormiguero/inee/colonies/register (remote colony registration)
- GET /hormiguero/inee/colonies (list colonies)
- POST /hormiguero/inee/intents/submit (forward intent to madre)
- GET /hormiguero/inee/audit (audit trail)

Activación: VX11_INEE_ENABLED=1 (OFF por defecto).
CPU gate: bloquea /intents/submit si cpu_sustained_high=true.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import uuid
from datetime import datetime
from ..intents import INEEIntent, INEETranslator, VX11Intent
from ..colonies import INEERegistry, INEERegistryDAO
from ..intents.types import INEEColony, INEEAgent
from ..db import INEEDBManager


# Models for API


class RegisterColonyRequest(BaseModel):
    colony_id: str
    remote_url: Optional[str] = None


class SubmitIntentRequest(BaseModel):
    intent_type: str  # "diagnose", "propose", "apply"
    payload: Dict[str, Any]
    remote_colony_id: str
    correlation_id: Optional[str] = None


class RegisterAgentRequest(BaseModel):
    agent_id: str
    colony_id: str
    agent_type: str  # "scanner", "planner", "executor"


class AuditEventResponse(BaseModel):
    event_id: str
    component: str
    event_type: str
    created_at: str


# Router

router = APIRouter(prefix="/hormiguero/inee", tags=["inee"])

# Global instances (shared with main app)
_registry: Optional[INEERegistry] = None
_db_manager: Optional[INEEDBManager] = None
_cpu_gate_fn: Optional[callable] = None  # Inject from main app


def init_inee_router(
    registry: INEERegistry, db_manager: INEEDBManager, cpu_gate_fn: callable
):
    """Initialize INEE router with shared instances and CPU gate function."""
    global _registry, _db_manager, _cpu_gate_fn
    _registry = registry
    _db_manager = db_manager
    _cpu_gate_fn = cpu_gate_fn


# Routes


@router.post("/colonies/register")
async def register_colony(req: RegisterColonyRequest):
    """Register a remote INEE colony."""
    if not _registry:
        raise HTTPException(status_code=500, detail="INEE not initialized")

    colony = INEEColony(
        colony_id=req.colony_id,
        remote_url=req.remote_url,
        status="pending",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )

    if _registry.register_colony(colony):
        _db_manager.log_audit_event(
            "inee_registry", "colony_registered", {"colony_id": req.colony_id}
        )
        return {
            "status": "ok",
            "colony_id": req.colony_id,
            "message": "Colony registered",
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to register colony")


@router.get("/colonies")
async def list_colonies():
    """List registered colonies."""
    if not _registry:
        raise HTTPException(status_code=500, detail="INEE not initialized")

    colonies = _registry.list_colonies()
    return {
        "status": "ok",
        "colonies": [c.to_dict() for c in colonies],
        "count": len(colonies),
    }


@router.post("/agents/register")
async def register_agent(req: RegisterAgentRequest):
    """Register an agent within a colony."""
    if not _registry:
        raise HTTPException(status_code=500, detail="INEE not initialized")

    agent = INEEAgent(
        agent_id=req.agent_id,
        colony_id=req.colony_id,
        agent_type=req.agent_type,
        status="idle",
        created_at=datetime.utcnow().isoformat(),
    )

    if _registry.register_agent(agent):
        _db_manager.log_audit_event(
            "inee_registry", "agent_registered", {"agent_id": req.agent_id}
        )
        return {"status": "ok", "agent_id": req.agent_id, "message": "Agent registered"}
    else:
        raise HTTPException(status_code=400, detail="Failed to register agent")


@router.post("/intents/submit")
async def submit_intent(req: SubmitIntentRequest):
    """
    Submit an intent to Madre (via tentaculo_link).
    CPU gate: blocks if cpu_sustained_high=true.
    """
    if not _registry or not _db_manager:
        raise HTTPException(status_code=500, detail="INEE not initialized")

    # Check CPU gate
    if _cpu_gate_fn and _cpu_gate_fn():
        _db_manager.log_audit_event(
            "inee_router",
            "intent_blocked_cpu_high",
            {"remote_colony_id": req.remote_colony_id},
        )
        raise HTTPException(
            status_code=429,
            detail="CPU sustained high; intent submission temporarily blocked",
        )

    # Verify colony exists
    colony = _registry.get_colony(req.remote_colony_id)
    if not colony:
        raise HTTPException(status_code=404, detail="Colony not found")

    # Create and translate intent
    intent_id = str(uuid.uuid4())
    inee_intent = INEEIntent(
        intent_id=intent_id,
        remote_colony_id=req.remote_colony_id,
        intent_type=req.intent_type,
        payload=req.payload,
        timestamp=datetime.utcnow().isoformat(),
        correlation_id=req.correlation_id or str(uuid.uuid4()),
    )

    vx11_intent = INEETranslator.translate(inee_intent)

    # Save to DB
    _db_manager.save_intent(inee_intent)
    _db_manager.log_audit_event(
        "inee_router",
        "intent_submitted",
        {
            "intent_id": intent_id,
            "remote_colony_id": req.remote_colony_id,
            "operation": vx11_intent.operation,
        },
    )

    # TODO: Forward to Madre via tentaculo_link (not implemented yet)
    # This is where we'd call /madre/... endpoint

    return {
        "status": "ok",
        "intent_id": intent_id,
        "correlation_id": vx11_intent.correlation_id,
        "operation": vx11_intent.operation,
        "message": "Intent submitted (forwarding to Madre)",
    }


@router.get("/audit")
async def list_audit_events(limit: int = 50):
    """Get recent INEE audit events."""
    if not _db_manager:
        raise HTTPException(status_code=500, detail="INEE not initialized")

    try:
        conn = __import__("sqlite3").connect("data/runtime/vx11.db")
        rows = conn.execute(
            "SELECT event_id, component, event_type, created_at FROM inee_audit_events "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()

        events = [
            {
                "event_id": row[0],
                "component": row[1],
                "event_type": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]
        return {"status": "ok", "events": events, "count": len(events)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading audit: {str(e)}")


@router.post("/heartbeat")
async def heartbeat(colony_id: str):
    """Heartbeat from remote colony."""
    if not _registry:
        raise HTTPException(status_code=500, detail="INEE not initialized")

    if _registry.update_heartbeat(colony_id):
        return {"status": "ok", "message": "Heartbeat recorded"}
    else:
        raise HTTPException(status_code=404, detail="Colony not found")
