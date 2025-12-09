"""
Hormiguero v7.0 - Main FastAPI Application
Queen + Ants orchestration for system monitoring and incident management.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, Header, HTTPException

from config.tokens import load_tokens, get_token
from config.forensics import write_log
from config.settings import settings
from hormiguero.hormiguero_v7 import AntColony

load_tokens()

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)


def check_token(x_vx11_token: str = Header(None)):
    """Token validation."""
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=401, detail="unauthorized")
    return True


# ============ LIFESPAN ============

_colony: Optional[AntColony] = None
_scan_task: Optional[asyncio.Task] = None
SCAN_INTERVAL_SECONDS = 60  # Hormigas escanean cada 60 segundos


async def _scan_loop():
    """Background task: periodic scanning."""
    global _colony
    while True:
        try:
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)
            if _colony:
                result = await _colony.scan_cycle()
                write_log("hormiguero", f"scan_loop_iteration:incidents={result.get('total_incidents')}")
        except Exception as exc:
            write_log("hormiguero", f"scan_loop_error:{exc}", level="ERROR")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: startup/shutdown."""
    global _colony, _scan_task
    _colony = AntColony()
    _scan_task = asyncio.create_task(_scan_loop())
    write_log("hormiguero", "startup:colony_initialized")
    try:
        yield
    finally:
        if _scan_task:
            _scan_task.cancel()
            try:
                await _scan_task
            except Exception:
                pass
        write_log("hormiguero", "shutdown:colony_stopped")


# ============ APP ============

app = FastAPI(
    title="Hormiguero v7.0",
    description="Queen + Ants system monitoring",
    lifespan=lifespan,
)


# ============ ENDPOINTS ============

@app.get("/health")
async def health():
    """Health check (no auth required)."""
    return {"status": "ok", "service": "hormiguero"}


@app.post("/scan")
async def trigger_scan(ok=Depends(check_token)):
    """Trigger immediate scan cycle."""
    global _colony
    if not _colony:
        raise HTTPException(status_code=503, detail="colony_not_initialized")
    
    try:
        result = await _colony.scan_cycle()
        return {
            "status": "ok",
            "total_incidents": result.get("total_incidents"),
            "queen_decisions": result.get("queen_decisions"),
        }
    except Exception as exc:
        write_log("hormiguero", f"scan_endpoint_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/report")
async def get_recent_incidents(limit: int = 50, ok=Depends(check_token)):
    """Get recent incidents (last N)."""
    from config.db_schema import get_session, Incident
    
    session = get_session("vx11")
    try:
        incidents = session.query(Incident).order_by(Incident.detected_at.desc()).limit(limit).all()
        return {
            "count": len(incidents),
            "incidents": [
                {
                    "id": inc.id,
                    "ant_id": inc.ant_id,
                    "type": inc.incident_type,
                    "severity": inc.severity,
                    "location": inc.location,
                    "status": inc.status,
                    "detected_at": inc.detected_at.isoformat(),
                    "queen_decision": inc.queen_decision,
                }
                for inc in incidents
            ],
        }
    finally:
        session.close()


@app.get("/queen/status")
async def queen_status(ok=Depends(check_token)):
    """Get Queen and Ant status."""
    from config.db_schema import get_session, HormigaState
    
    session = get_session("vx11")
    try:
        ant_states = session.query(HormigaState).all()
        return {
            "queen": {
                "status": "active",
                "ants_count": len(ant_states),
            },
            "ants": [
                {
                    "id": state.ant_id,
                    "role": state.role,
                    "status": state.status,
                    "last_scan_at": state.last_scan_at.isoformat() if state.last_scan_at else None,
                    "mutation_level": state.mutation_level,
                    "cpu_percent": state.cpu_percent,
                    "ram_percent": state.ram_percent,
                }
                for state in ant_states
            ],
        }
    finally:
        session.close()


@app.post("/queen/dispatch")
async def queen_dispatch_intent(incident_id: int, ok=Depends(check_token)):
    """Manually trigger Reina decision for an incident."""
    from config.db_schema import get_session, Incident
    
    global _colony
    if not _colony:
        raise HTTPException(status_code=503, detail="colony_not_initialized")
    
    session = get_session("vx11")
    try:
        incident = session.query(Incident).filter_by(id=incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="incident_not_found")
        
        decision = await _colony.queen._classify_and_decide(incident)
        await _colony.queen._execute_decision(decision)
        
        return {
            "status": "ok",
            "incident_id": incident_id,
            "decision": decision,
        }
    finally:
        session.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
