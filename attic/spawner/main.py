"""
Spawner v6.3 - Hijas efímeras con autoconsciencia y control P&P.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx
from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel

from config.settings import settings
from config.tokens import get_token, load_tokens
from config.forensics import write_log
from config.db_schema import get_session, HijasRuntime, SystemEvents

load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}
ALLOWED_COMMANDS = {"echo", "python", "node", "ls", "cat", "bash"}


def check_token(x_vx11_token: str = Header(None)):
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=401, detail="auth_required")
    return True


app = FastAPI(title="Spawner v6.3")

SPAWNS: Dict[str, Dict[str, Any]] = {}
MAX_ACTIVE = int(os.environ.get("SPAWNER_MAX_ACTIVE", "5"))


class SpawnRequest(BaseModel):
    name: str
    cmd: str
    args: Optional[List[str]] = []
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: Optional[int] = 60
    parent_task_id: Optional[str] = None
    intent_type: Optional[str] = None
    priority: Optional[int] = 1
    ttl: Optional[int] = 60
    purpose: Optional[str] = None
    module_creator: Optional[str] = "madre"
    context: Optional[Dict[str, Any]] = None
    aggressiveness: Optional[str] = "normal"
    module: Optional[str] = "generic"


class SpawnResponse(BaseModel):
    id: Optional[str]
    status: str
    pid: Optional[int] = None
    error: Optional[str] = None


def _persist_hija(spawn_id: str, data: Dict[str, Any]):
    session = get_session("vx11")
    try:
        rec = HijasRuntime(
            name=data.get("name"),
            state="running",
            pid=data.get("pid"),
            meta_json=json.dumps(
                {
                    **(data.get("context") or {}),
                    "aggressiveness": data.get("aggressiveness"),
                    "module": data.get("module"),
                }
            ),
            birth_context=json.dumps(data.get("birth_context") or {}),
            intent_type=data.get("intent_type"),
            ttl=data.get("ttl", 60),
            purpose=data.get("purpose"),
            module_creator=data.get("module_creator"),
            born_at=datetime.utcnow(),
        )
        session.add(rec)
        session.commit()
        SPAWNS[spawn_id]["db_id"] = rec.id
    except Exception as exc:
        write_log("spawner", f"persist_error:{spawn_id}:{exc}", level="ERROR")
    finally:
        session.close()


def _update_hija_db(spawn_id: str, state: str, death_context: Optional[Dict[str, Any]] = None, killed_by: str = None):
    session = get_session("vx11")
    try:
        rec_id = SPAWNS.get(spawn_id, {}).get("db_id")
        if rec_id:
            rec = session.query(HijasRuntime).filter_by(id=rec_id).first()
            if rec:
                rec.state = state
                rec.died_at = datetime.utcnow()
                rec.death_context = json.dumps(death_context or {})
                rec.killed_by = killed_by
                session.add(rec)
                session.commit()
    except Exception as exc:
        write_log("spawner", f"update_error:{spawn_id}:{exc}", level="ERROR")
    finally:
        session.close()


def _record_event(source: str, event_type: str, payload: Dict[str, Any], severity: str = "info"):
    session = get_session("vx11")
    try:
        ev = SystemEvents(source=source, event_type=event_type, payload=json.dumps(payload), severity=severity)
        session.add(ev)
        session.commit()
    except Exception:
        pass
    finally:
        session.close()


async def _execute_in_sandbox(req: SpawnRequest) -> Dict[str, Any]:
    """
    Delegar ejecución al MCP sandbox para evitar ejecuciones locales.
    """
    mcp_port = settings.PORTS.get("mcp", 8006)
    payload = {
        "cmd": req.cmd,
        "args": req.args or [],
        "cwd": req.cwd or "/app/sandbox",
        "env": req.env or {},
        "timeout": req.timeout or req.ttl or 60,
        "context": req.context or {},
    }
    async with httpx.AsyncClient(timeout=payload["timeout"] + 5) as client:
        resp = await client.post(
            f"http://127.0.0.1:{mcp_port}/mcp/sandbox/exec_cmd",
            json=payload,
            headers=AUTH_HEADERS,
        )
        return resp.json()


async def _notify_tentaculo(event_type: str, payload: Dict[str, Any]):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"http://{getattr(settings, 'tentaculo_link_host', 'tentaculo_link')}:{getattr(settings, 'tentaculo_link_port', settings.gateway_port)}/events/ingest",
                json={"source": "spawner", "type": event_type, "payload": payload, "broadcast": True},
                headers=AUTH_HEADERS,
            )
    except Exception:
        pass


async def _notify_madre(spawn_id: str, data: Dict[str, Any]):
    """
    Callback a Madre con resultado de spawn.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{settings.madre_url.rstrip('/')}/madre/callback",
                json={
                    "spawn_id": spawn_id,
                    "status": data.get("status"),
                    "task_id": data.get("parent_task_id"),
                    "result": data.get("result"),
                    "provider": (data.get("context") or {}).get("provider"),
                    "shub": data.get("shub"),
                    "ttl": "infinite" if data.get("persistent_initialized") else data.get("ttl"),
                    "started_at": data.get("started_at"),
                },
                headers=AUTH_HEADERS,
            )
    except Exception:
        pass


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/spawn")
async def spawn(req: SpawnRequest, ok=Depends(check_token)) -> SpawnResponse:
    if len(SPAWNS) >= MAX_ACTIVE:
        write_log("spawner", "spawn_denied:capacity", level="WARN")
        return SpawnResponse(id=None, status="denied", error="capacity_reached")

    base_cmd = (req.cmd.split() or [""])[0]
    if base_cmd not in ALLOWED_COMMANDS:
        write_log("spawner", f"spawn_denied:{req.name}:{base_cmd}", level="WARN")
        return SpawnResponse(id=None, status="denied", error="command_not_allowed")

    spawn_id = uuid.uuid4().hex
    try:
        sandbox_res = await _execute_in_sandbox(req)
        # Si es pipeline de audio, delegar a Shub
        if req.context and req.context.get("audio_pipeline"):
            async with httpx.AsyncClient(timeout=req.timeout or 30) as client:
                shub_payload = {
                    "task_id": req.parent_task_id or spawn_id,
                    "task_type": "audio",
                    "payload": {
                        "input": req.context.get("input"),
                        "output_path": req.context.get("output_path"),
                        "metadata": req.context,
                    },
                }
                shub_resp = await client.post(
                    f"{settings.shub_url.rstrip('/')}/shub/execute",
                    json=shub_payload,
                    headers=AUTH_HEADERS,
                )
                sandbox_res["shub"] = shub_resp.json()
        # calcular duración (inicio a fin de ejecución sandbox/shub)
        started = datetime.fromisoformat(datetime.utcnow().isoformat())
        try:
            started = datetime.fromisoformat(sandbox_res.get("started_at")) if sandbox_res.get("started_at") else datetime.utcnow()
        except Exception:
            started = datetime.utcnow()
        SPAWNS.setdefault(spawn_id, {})  # ensure dict exists if referenced later
        duration = (datetime.utcnow() - started).total_seconds()
        if duration <= 0:
            duration = 0.001
        SPAWNS[spawn_id]["duration_sec"] = duration
    except Exception as e:
        write_log("spawner", f"spawn_failed:{req.name}:{str(e)}", level="ERROR")
        return SpawnResponse(id=None, status="failed", error=str(e))

    persistent = bool(req.context and req.context.get("audio_pipeline") and req.context.get("task_type") == "render")

    SPAWNS[spawn_id] = {
        "id": spawn_id,
        "name": req.name,
        "cmd": [req.cmd] + (req.args or []),
        "started_at": datetime.utcnow().isoformat(),
        "parent_task_id": req.parent_task_id,
        "intent_type": req.intent_type,
        "ttl": req.ttl or 60,
        "purpose": req.purpose,
        "module_creator": req.module_creator,
        "context": req.context,
        "aggressiveness": req.aggressiveness,
        "result": sandbox_res,
        "status": sandbox_res.get("status", "completed"),
    }
    # Métricas básicas
    SPAWNS[spawn_id]["duration_sec"] = 0
    SPAWNS[spawn_id]["pipeline"] = "shub" if req.context and req.context.get("audio_pipeline") else "generic"
    SPAWNS[spawn_id]["persistent_initialized"] = persistent

    _persist_hija(spawn_id, SPAWNS[spawn_id])
    if not SPAWNS[spawn_id]["persistent_initialized"]:
        _update_hija_db(spawn_id, "completed", {"stdout": sandbox_res.get("stdout"), "stderr": sandbox_res.get("stderr")})
    _record_event("spawner", "creation", {"id": spawn_id, "name": req.name})
    asyncio.create_task(_notify_tentaculo("spawn_created", {"id": spawn_id, "name": req.name}))
    asyncio.create_task(_notify_madre(spawn_id, SPAWNS[spawn_id]))

    write_log("spawner", f"spawned_sandbox:{spawn_id}:{req.name}")
    return SpawnResponse(id=spawn_id, status="completed", pid=None)


@app.get("/spawn/list")
def list_spawns(ok=Depends(check_token)):
    out = []
    for spawn_id, s in SPAWNS.items():
        out.append(
            {
                "id": spawn_id,
                "name": s["name"],
                "pid": None,
                "running": False,
                "started_at": s.get("started_at"),
                "ttl": s.get("ttl"),
                "status": s.get("status", "completed"),
            }
        )
    return out


@app.get("/spawn/status/{spawn_id}")
def get_spawn(spawn_id: str, ok=Depends(check_token)):
    s = SPAWNS.get(spawn_id)
    if not s:
        return {"error": "not_found"}
    return {
        "id": s["id"],
        "name": s["name"],
        "pid": None,
        "running": False,
        "exit_code": 0,
        "started_at": s.get("started_at"),
        "status": s.get("status", "completed"),
        "result": s.get("result"),
    }


@app.post("/spawn/kill/{spawn_id}")
def kill_spawn(spawn_id: str, ok=Depends(check_token)):
    s = SPAWNS.get(spawn_id)
    if not s:
        return {"error": "not_found"}
    _update_hija_db(spawn_id, "killed", {"reason": "manual_kill"}, "madre")
    SPAWNS.pop(spawn_id, None)
    _record_event("spawner", "termination", {"id": spawn_id})
    return {"id": spawn_id, "status": "killed"}


@app.post("/spawn/kill_all")
def kill_all(ok=Depends(check_token)):
    ids = list(SPAWNS.keys())
    for sid in ids:
        kill_spawn(sid)
    return {"killed": ids}


@app.get("/spawn/output/{spawn_id}")
def get_spawn_output(spawn_id: str, ok=Depends(check_token)):
    s = SPAWNS.get(spawn_id)
    if not s:
        return {"error": "not_found"}
    result = s.get("result") or {}
    return {
        "id": spawn_id,
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "status": s.get("status", "completed"),
    }


@app.post("/spawner/spawn")
async def spawner_spawn_hija(req: SpawnRequest, ok=Depends(check_token)):
    """
    Endpoint mejorado: crea Daughter + DaughterAttempt en BD.
    Requiere: parent_task_id (FK a DaughterTask), purpose.
    """
    from config.db_schema import DaughterTask, Daughter, DaughterAttempt
    
    if not req.parent_task_id:
        raise HTTPException(status_code=400, detail="parent_task_id required")
    
    session = get_session("vx11")
    try:
        task = session.query(DaughterTask).filter_by(id=int(req.parent_task_id)).first()
        if not task:
            raise HTTPException(status_code=404, detail="parent_task not found")
        
        # Crear hija en BD
        hija = Daughter(
            task_id=task.id,
            name=req.name,
            purpose=req.purpose or req.intent_type or "generic",
            tools_json=json.dumps(req.context or {}),
            ttl_seconds=req.ttl or 300,
            status="spawned",
            mutation_level=task.current_retry,
        )
        session.add(hija)
        session.flush()
        
        # Crear DaughterAttempt
        attempt = DaughterAttempt(
            daughter_id=hija.id,
            attempt_number=1,
            started_at=datetime.utcnow(),
            status="running",
        )
        session.add(attempt)
        session.commit()
        
        write_log("spawner", f"spawner_spawn_hija:{hija.id}:{task.id}")
        
        # Ejecutar sandbox (como antes)
        sandbox_res = await _execute_in_sandbox(req)
        
        # Actualizar status a running (sandbox confirma)
        hija.status = "running"
        session.add(hija)
        session.commit()
        
        return {
            "status": "ok",
            "daughter_id": hija.id,
            "attempt_id": attempt.id,
            "spawn_id": hija.name,
            "task_id": task.id,
            "result": sandbox_res,
        }
    except HTTPException:
        raise
    except Exception as exc:
        write_log("spawner", f"spawner_spawn_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()


@app.post("/spawner/report")
async def spawner_report_attempt(
    daughter_id: int,
    attempt_number: int,
    status: str,
    tokens_used_cli: Optional[int] = 0,
    tokens_used_local: Optional[int] = 0,
    switch_model_used: Optional[str] = None,
    cli_provider_used: Optional[str] = None,
    error_message: Optional[str] = None,
    ok=Depends(check_token),
):
    """
    Report final de execution de hija.
    Actualiza DaughterAttempt con métricas.
    """
    from config.db_schema import DaughterAttempt, Daughter
    
    session = get_session("vx11")
    try:
        attempt = session.query(DaughterAttempt).filter_by(
            daughter_id=daughter_id,
            attempt_number=attempt_number,
        ).first()
        
        if not attempt:
            raise HTTPException(status_code=404, detail="attempt not found")
        
        attempt.status = status
        attempt.finished_at = datetime.utcnow()
        attempt.tokens_used_cli = tokens_used_cli
        attempt.tokens_used_local = tokens_used_local
        attempt.switch_model_used = switch_model_used
        attempt.cli_provider_used = cli_provider_used
        attempt.error_message = error_message
        
        session.add(attempt)
        
        # Actualizar Daughter status (si success, marcar finished)
        hija = session.query(Daughter).filter_by(id=daughter_id).first()
        if hija:
            if status == "completed":
                hija.status = "finished"
            elif status == "failed":
                hija.status = "failed"
                hija.error_last = error_message
            session.add(hija)
        
        session.commit()
        
        write_log("spawner", f"spawner_report:{daughter_id}:{attempt_number}:{status}")
        
        return {
            "status": "ok",
            "daughter_id": daughter_id,
            "attempt_number": attempt_number,
            "reported_status": status,
        }
    except HTTPException:
        raise
    except Exception as exc:
        write_log("spawner", f"spawner_report_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()


@app.post("/spawner/heartbeat")
async def spawner_heartbeat(daughter_id: int, ok=Depends(check_token)):
    """
    Heartbeat de hija activa.
    Actualiza last_heartbeat_at para TTL tracking.
    """
    from config.db_schema import Daughter
    
    session = get_session("vx11")
    try:
        hija = session.query(Daughter).filter_by(id=daughter_id).first()
        if not hija:
            raise HTTPException(status_code=404, detail="daughter not found")
        
        hija.last_heartbeat_at = datetime.utcnow()
        session.add(hija)
        session.commit()
        
        write_log("spawner", f"spawner_heartbeat:{daughter_id}")
        
        return {
            "status": "ok",
            "daughter_id": daughter_id,
            "heartbeat_at": hija.last_heartbeat_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        write_log("spawner", f"spawner_heartbeat_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        session.close()


@app.post("/spawn/cleanup")
def cleanup_old_spawns(ok=Depends(check_token)):
    removed = list(SPAWNS.keys())
    for spawn_id in removed:
        SPAWNS.pop(spawn_id, None)
    write_log("spawner", f"cleanup:{len(removed)}_spawns")
    return {"cleaned": removed}
