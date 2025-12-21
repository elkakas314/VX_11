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
                write_log(
                    "hormiguero",
                    f"scan_loop_iteration:incidents={result.get('total_incidents')}",
                )
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


# ============ TASK API (testing stubs) ============
_TASK_STORE = {}


@app.post("/hormiguero/task")
async def create_task(payload: dict, ok=Depends(check_token)):
    """Create a simple task (testing stub)."""
    import uuid

    tid = str(uuid.uuid4())
    _TASK_STORE[tid] = {
        "task_id": tid,
        "task_type": payload.get("task_type"),
        "payload": payload.get("payload"),
        "status": "created",
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"status": "created", "task_id": tid}


@app.get("/hormiguero/tasks")
async def list_tasks(ok=Depends(check_token)):
    """List created tasks (testing stub)."""
    return list(_TASK_STORE.values())


@app.get("/report")
async def get_recent_incidents(limit: int = 50, ok=Depends(check_token)):
    """Get recent incidents (last N)."""
    from config.db_schema import get_session, Incident

    session = get_session("vx11")
    try:
        incidents = (
            session.query(Incident)
            .order_by(Incident.detected_at.desc())
            .limit(limit)
            .all()
        )
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
                    "last_scan_at": (
                        state.last_scan_at.isoformat() if state.last_scan_at else None
                    ),
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


# ============ PASO 5: Mutant Ants + Pheromones ============


@app.post("/hormiguero/colony/create")
async def create_colony(req: dict, ok=Depends(check_token)):
    """
    Crear nueva colonia de hormigas mutantes (PASO 5).

    Input:
      {
        "size": 8,
        "mutation_level": 0
      }

    Output:
      {
        "status": "ok",
        "colony_id": "col_...",
        "ants": [...]
      }
    """
    from hormiguero.ants_mutant import get_queen_brain

    try:
        queen = get_queen_brain()
        size = req.get("size", 8)
        mutation_level = req.get("mutation_level", 0)

        colony = await queen.create_colony(size=size, mutation_level=mutation_level)

        write_log("hormiguero", f"colony_created_api:{colony.id}:size={size}")
        return {
            "status": "ok",
            "colony_id": colony.id,
            "size": colony.size,
            "mutation_level": mutation_level,
            "ants_count": len(colony.ants),
        }
    except Exception as e:
        write_log("hormiguero", f"create_colony_error:{e}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/hormiguero/colony/{colony_id}/cycle")
async def execute_colony_cycle(colony_id: str, ok=Depends(check_token)):
    """
    Ejecutar ciclo de actividad de colonia (PASO 5).

    Cada hormiga:
    1. Escanea zona asignada
    2. Detecta drift
    3. Deposita feromonas
    4. Reporta resultados

    Output:
      {
        "status": "ok",
        "scan_results": [...],
        "decision": {...},
        "colony_status": {...}
      }
    """
    from hormiguero.ants_mutant import get_queen_brain

    try:
        queen = get_queen_brain()
        result = await queen.execute_colony_cycle(colony_id)

        write_log(
            "hormiguero",
            f"colony_cycle:{colony_id}:drift={result['decision']['drift_detected']}",
        )
        return result
    except Exception as e:
        write_log("hormiguero", f"colony_cycle_error:{colony_id}:{e}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hormiguero/colony/{colony_id}")
async def get_colony_status(colony_id: str, ok=Depends(check_token)):
    """Obtener estado de colonia específica."""
    from hormiguero.ants_mutant import get_queen_brain

    try:
        queen = get_queen_brain()
        status = await queen.get_colony_status(colony_id)

        if status is None:
            raise HTTPException(status_code=404, detail="Colony not found")

        return {"status": "ok", "colony": status}
    except HTTPException:
        raise
    except Exception as e:
        write_log("hormiguero", f"get_colony_error:{colony_id}:{e}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hormiguero/colonies")
async def list_colonies(ok=Depends(check_token)):
    """Listar todas las colonias activas."""
    from hormiguero.ants_mutant import get_queen_brain

    try:
        queen = get_queen_brain()
        colonies = await queen.list_colonies()

        write_log("hormiguero", f"list_colonies:{len(colonies)}")
        return {
            "status": "ok",
            "count": len(colonies),
            "colonies": colonies,
        }
    except Exception as e:
        write_log("hormiguero", f"list_colonies_error:{e}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
