import asyncio
import json
import os
import subprocess
import uuid
from contextlib import asynccontextmanager  # P1-1: Add for reaper job
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from config.db_schema import (
    Daughter,
    DaughterAttempt,
    DaughterTask,
    HijasRuntime,
    HijasState,
    IntentLog,
    Spawn,
    get_session,
)

# NOTE: decouple from tentaculo_link.db.events_metrics to avoid circular import
# spawner runs independently; will re-enable when db/events is refactored
# from tentaculo_link.db.events_metrics import log_event


def log_event(*args, **kwargs):
    """Stub: minimal event logging"""
    pass


app = FastAPI(title="VX11 Spawner - Advanced")

# ============ P1-1: CONFIGURATION ============
# Read reaper interval from ENV; default 60s for production (use 5s only in testing)
REAPER_INTERVAL_SECONDS = int(
    os.environ.get("VX11_SPAWNER_REAPER_INTERVAL_SECONDS", "60")
)


# ============ P1-1: TTL/REAPER BACKGROUND JOB ============
async def _reaper_job():
    """
    P1-1: Background job that periodically cleans expired daughters.
    Interval: VX11_SPAWNER_REAPER_INTERVAL_SECONDS env var (default: 60s production, 5s testing).
    """
    while True:
        try:
            await asyncio.sleep(REAPER_INTERVAL_SECONDS)  # Configurable interval
            session = get_session("vx11")
            try:
                now = _now()
                from datetime import timedelta

                # Find daughters past their TTL (started_at + ttl_seconds < now)
                # Only process daughters that are not yet marked as reaped/killed
                expired = (
                    session.query(Daughter)
                    .filter(
                        Daughter.status.in_(
                            ["spawned", "running", "completed", "expired"]
                        ),
                        Daughter.started_at != None,
                        Daughter.started_at + timedelta(seconds=Daughter.ttl_seconds)
                        < now,
                    )
                    .all()
                )

                if expired:
                    for daughter in expired:
                        daughter.status = "reaped"
                        session.add(daughter)
                    session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()
        except Exception:
            # Swallow exceptions in reaper to keep it running
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: start reaper background task."""
    # Start reaper job
    reaper_task = asyncio.create_task(_reaper_job())
    try:
        yield
    finally:
        reaper_task.cancel()
        try:
            await reaper_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="VX11 Spawner - Advanced", lifespan=lifespan)


class SpawnRequest(BaseModel):
    name: Optional[str] = None
    cmd: Optional[str] = None
    task_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    intent: str = "spawn"
    task_type: Optional[str] = None
    description: Optional[str] = None
    ttl_seconds: int = Field(default=300, ge=1)
    mutation_level: int = Field(default=0, ge=0)
    tool_allowlist: Optional[List[str]] = None
    context_ref: Optional[str] = None
    trace_id: Optional[str] = None
    source: str = "switch"
    metadata: Optional[Dict[str, Any]] = None
    max_retries: int = Field(default=2, ge=0)
    auto_retry: bool = True
    subtasks: Optional[List[Dict[str, Any]]] = None


class SpawnResponse(BaseModel):
    status: str
    spawn_uuid: str
    daughter_id: int
    daughter_task_id: int
    attempt_id: int
    name: str
    cmd: str
    ttl_seconds: int
    mutation_level: int
    trace_id: Optional[str] = None


def _now() -> datetime:
    return datetime.utcnow()


def _events_enabled() -> bool:
    return os.environ.get("VX11_EVENTS_ENABLED", "false").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def _log_spawn_event(summary: str, payload: Dict[str, Any]) -> None:
    if not _events_enabled():
        return
    log_event(
        event_type="spawn",
        summary=summary,
        module="spawner",
        severity="info",
        payload=payload,
    )


def _madre_url() -> str:
    return (
        os.environ.get("VX11_MADRE_URL")
        or os.environ.get("MADRE_URL")
        or "http://localhost:8001"
    )


def _serialize(obj: Any) -> str:
    if obj is None:
        return ""
    try:
        return json.dumps(obj, ensure_ascii=True)
    except Exception:
        return json.dumps({"value": str(obj)}, ensure_ascii=True)


def _register_intent(session, req: SpawnRequest) -> None:
    payload = {
        "intent": req.intent,
        "task_id": req.task_id,
        "parent_task_id": req.parent_task_id,
        "trace_id": req.trace_id,
        "task_type": req.task_type,
        "metadata": req.metadata or {},
    }
    entry = IntentLog(
        source=req.source or "spawner",
        payload_json=_serialize(payload),
        created_at=_now(),
        result_status="planned",
        notes="spawner_spawn_request",
    )
    session.add(entry)


def _create_task_and_daughter(
    session, req: SpawnRequest, spawn_uuid: str
) -> Tuple[DaughterTask, Daughter]:
    metadata = dict(req.metadata or {})
    metadata.update(
        {
            "tool_allowlist": req.tool_allowlist or [],
            "context_ref": req.context_ref,
            "trace_id": req.trace_id,
            "parent_task_id": req.parent_task_id,
            "task_id": req.task_id,
            "spawn_uuid": spawn_uuid,  # P0-1: Persist spawn_uuid in metadata
        }
    )
    task = DaughterTask(
        intent_id=req.trace_id or req.task_id or req.parent_task_id,
        source=req.source or "spawner",
        priority=3,
        status="running",
        task_type=req.task_type or "long",
        description=req.description or req.intent,
        created_at=_now(),
        updated_at=_now(),
        max_retries=req.max_retries,
        current_retry=0,
        metadata_json=_serialize(metadata),
        plan_json=None,
    )
    session.add(task)
    session.flush()

    daughter = Daughter(
        task_id=task.id,
        name=req.name or f"hija-{task.id}-mut{req.mutation_level}",
        purpose=req.description or req.intent,
        tools_json=_serialize(req.tool_allowlist or []),
        ttl_seconds=req.ttl_seconds,
        started_at=_now(),
        last_heartbeat_at=_now(),
        status="spawned",
        mutation_level=req.mutation_level,
        error_last=None,
        spawn_uuid=spawn_uuid,  # P0-1: Persist spawn_uuid directly to column
    )
    session.add(daughter)
    session.flush()
    return task, daughter


def _create_spawn(session, req: SpawnRequest, spawn_uuid: str) -> Spawn:
    spawn = Spawn(
        uuid=spawn_uuid,
        name=req.name or f"spawn-{spawn_uuid[:8]}",
        cmd=req.cmd or "",
        pid=None,
        status="pending",
        started_at=None,
        ended_at=None,
        exit_code=None,
        stdout=None,
        stderr=None,
        parent_task_id=req.parent_task_id or req.task_id,
        created_at=_now(),
    )
    session.add(spawn)
    return spawn


def _create_attempt(session, daughter_id: int, attempt_number: int) -> DaughterAttempt:
    attempt = DaughterAttempt(
        daughter_id=daughter_id,
        attempt_number=attempt_number,
        started_at=_now(),
        finished_at=None,
        status="running",
        error_message=None,
        tokens_used_cli=0,
        tokens_used_local=0,
        switch_model_used=None,
        cli_provider_used=None,
        created_at=_now(),
    )
    session.add(attempt)
    session.flush()
    return attempt


def _init_hijas_records(
    session,
    req: SpawnRequest,
    task: DaughterTask,
    daughter: Daughter,
    spawn_uuid: str,
    attempt_id: int,
) -> None:
    name = f"hija-{daughter.id}"
    existing_runtime = session.query(HijasRuntime).filter_by(name=name).first()
    if not existing_runtime:
        meta = {
            "spawn_uuid": spawn_uuid,
            "task_id": task.id,
            "daughter_id": daughter.id,
            "attempt_id": attempt_id,
            "trace_id": req.trace_id,
            "source": req.source,
        }
        birth_context = {
            "intent": req.intent,
            "task_type": req.task_type,
            "parent_task_id": req.parent_task_id,
            "task_id": req.task_id,
        }
        runtime = HijasRuntime(
            name=name,
            state="running",
            pid=None,
            last_heartbeat=_now(),
            meta_json=_serialize(meta),
            birth_context=_serialize(birth_context),
            intent_type=req.intent,
            ttl=req.ttl_seconds,
            purpose=req.description or req.intent,
            module_creator=req.source or "spawner",
            born_at=_now(),
        )
        session.add(runtime)

    existing_state = (
        session.query(HijasState).filter_by(hija_id=str(daughter.id)).first()
    )
    if not existing_state:
        state = HijasState(
            hija_id=str(daughter.id),
            module="spawner",
            status="running",
            cpu_usage=0.0,
            ram_usage=0.0,
            pid=None,
            created_at=_now(),
            updated_at=_now(),
        )
        session.add(state)


def _update_hijas_records(
    session,
    daughter_id: int,
    status: str,
    death_context: Optional[Dict[str, Any]] = None,
) -> None:
    now = _now()
    name = f"hija-{daughter_id}"
    runtime = session.query(HijasRuntime).filter_by(name=name).first()
    if runtime:
        runtime.state = status
        if status in ("completed", "failed", "expired", "cancelled"):
            runtime.died_at = now
            if death_context is not None:
                runtime.death_context = _serialize(death_context)
        session.add(runtime)

    state = session.query(HijasState).filter_by(hija_id=str(daughter_id)).first()
    if state:
        state.status = status
        state.updated_at = now
        session.add(state)


def _update_status(session, task_id: int, daughter_id: int, status: str) -> None:
    task = session.query(DaughterTask).filter_by(id=task_id).first()
    if task:
        task.status = status
        task.updated_at = _now()
        if status in ("completed", "failed", "expired", "cancelled"):
            task.finished_at = _now()
        session.add(task)
    daughter = session.query(Daughter).filter_by(id=daughter_id).first()
    if daughter:
        daughter.status = status
        if status in ("finished", "failed", "expired", "killed"):
            daughter.ended_at = _now()
        session.add(daughter)
    _update_hijas_records(session, daughter_id, status)


def _notify_madre(daughter_id: int, status: str, payload: Dict[str, Any]) -> None:
    url = _madre_url().rstrip("/")
    endpoint = f"{url}/madre/daughter/{daughter_id}/complete"
    if status in ("failed", "expired", "killed"):
        endpoint = f"{url}/madre/daughter/{daughter_id}/fail"
    try:
        httpx.post(endpoint, json=payload, timeout=10.0)
    except Exception:
        pass


def _execute_command(
    cmd: str, ttl_seconds: int, task_type: Optional[str] = None
) -> Tuple[int, str, str, str]:
    """Execute command with appropriate interpreter based on task_type.

    task_type can be: 'shell' (default), 'python', 'bash', etc.
    For python: uses 'python3' interpreter
    For bash: uses '/bin/bash' explicitly
    For shell (default): uses shell=True
    """
    # Choose shell and command based on task_type
    if task_type == "python":
        # Run code as Python script
        proc = subprocess.Popen(
            ["python3", "-c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    elif task_type == "bash":
        # Run code as bash script
        proc = subprocess.Popen(
            ["/bin/bash", "-c", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    else:
        # Default: shell execution
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    try:
        stdout, stderr = proc.communicate(timeout=ttl_seconds)
        exit_code = proc.returncode
        status = "success" if exit_code == 0 else "error"
        return exit_code, stdout, stderr, status
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        return -1, stdout, stderr, "timeout"


def _spawn_subtasks(req: SpawnRequest, parent_task_id: int) -> int:
    if not req.subtasks:
        return 0
    created = 0
    session = get_session("vx11")
    try:
        for idx, payload in enumerate(req.subtasks):
            sub_name = payload.get("name") or f"subtask-{parent_task_id}-{idx}"
            sub_req = SpawnRequest(
                name=sub_name,
                cmd=payload.get("cmd"),
                task_id=req.task_id,
                parent_task_id=str(parent_task_id),
                intent=payload.get("intent") or req.intent,
                task_type=payload.get("task_type") or req.task_type,
                description=payload.get("description"),
                ttl_seconds=payload.get("ttl_seconds") or req.ttl_seconds,
                mutation_level=payload.get("mutation_level") or req.mutation_level,
                tool_allowlist=payload.get("tool_allowlist") or req.tool_allowlist,
                context_ref=payload.get("context_ref") or req.context_ref,
                trace_id=payload.get("trace_id") or req.trace_id,
                source=req.source,
                metadata=payload.get("metadata") or req.metadata,
                max_retries=payload.get("max_retries") or req.max_retries,
                auto_retry=payload.get("auto_retry", req.auto_retry),
                subtasks=None,
            )
            _register_intent(session, sub_req)
            spawn_uuid = str(
                uuid.uuid4()
            )  # P0-1: Generate UUID before creating daughter
            task, daughter = _create_task_and_daughter(
                session, sub_req, spawn_uuid
            )  # P0-1: Pass spawn_uuid
            _create_spawn(session, sub_req, spawn_uuid)
            attempt = _create_attempt(session, daughter.id, 1)
            _update_status(session, task.id, daughter.id, "running")
            _init_hijas_records(
                session, sub_req, task, daughter, spawn_uuid, attempt.id
            )
            created += 1
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    return created


async def _run_spawn_lifecycle(
    spawn_uuid: str,
    task_id: int,
    daughter_id: int,
    attempt_id: int,
    cmd: str,
    ttl_seconds: int,
    max_retries: int,
    auto_retry: bool,
    mutation_level: int,
    task_type: Optional[str] = None,
) -> None:
    attempt_number = 1
    current_mutation = mutation_level
    while True:
        session = get_session("vx11")
        try:
            spawn = session.query(Spawn).filter_by(uuid=spawn_uuid).first()
            if spawn:
                spawn.status = "running"
                spawn.started_at = spawn.started_at or _now()
                session.add(spawn)
                session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        _log_spawn_event(
            "spawn_running",
            {
                "spawn_uuid": spawn_uuid,
                "task_id": task_id,
                "daughter_id": daughter_id,
                "attempt_id": attempt_id,
                "attempt_number": attempt_number,
                "cmd": cmd,
            },
        )

        exit_code, stdout, stderr, status = await asyncio.to_thread(
            _execute_command, cmd, ttl_seconds, task_type
        )
        session = get_session("vx11")
        try:
            spawn = session.query(Spawn).filter_by(uuid=spawn_uuid).first()
            if spawn:
                spawn.pid = None
                spawn.status = (
                    "completed"
                    if status == "success"
                    else "failed" if status == "error" else "timeout"
                )
                spawn.started_at = spawn.started_at or _now()
                spawn.ended_at = _now()
                spawn.exit_code = exit_code
                spawn.stdout = stdout
                spawn.stderr = stderr
                session.add(spawn)

            attempt = session.query(DaughterAttempt).filter_by(id=attempt_id).first()
            if attempt:
                attempt.status = status
                attempt.finished_at = _now()
                attempt.error_message = stderr[:500] if stderr else None
                session.add(attempt)

            if status == "success":
                _update_status(session, task_id, daughter_id, "completed")
                _update_hijas_records(
                    session,
                    daughter_id,
                    "completed",
                    {
                        "exit_code": exit_code,
                        "stdout": stdout[:500],
                        "stderr": stderr[:500],
                    },
                )
                session.commit()
                _log_spawn_event(
                    "spawn_done",
                    {
                        "spawn_uuid": spawn_uuid,
                        "task_id": task_id,
                        "daughter_id": daughter_id,
                        "attempt_id": attempt_id,
                        "exit_code": exit_code,
                        "status": "completed",
                    },
                )
                _notify_madre(
                    daughter_id,
                    "completed",
                    {"status": "ok", "exit_code": exit_code, "spawn_uuid": spawn_uuid},
                )
                return

            if not auto_retry or attempt_number >= max_retries:
                final_state = "expired" if status == "timeout" else "failed"
                _update_status(session, task_id, daughter_id, final_state)
                _update_hijas_records(
                    session,
                    daughter_id,
                    final_state,
                    {
                        "exit_code": exit_code,
                        "stdout": stdout[:500],
                        "stderr": stderr[:500],
                    },
                )
                session.commit()
                _log_spawn_event(
                    "spawn_error",
                    {
                        "spawn_uuid": spawn_uuid,
                        "task_id": task_id,
                        "daughter_id": daughter_id,
                        "attempt_id": attempt_id,
                        "exit_code": exit_code,
                        "status": final_state,
                    },
                )
                _notify_madre(
                    daughter_id,
                    final_state,
                    {
                        "status": "error",
                        "exit_code": exit_code,
                        "spawn_uuid": spawn_uuid,
                    },
                )
                return

            attempt_number += 1
            current_mutation += 1
            daughter = session.query(Daughter).filter_by(id=daughter_id).first()
            if daughter:
                daughter.mutation_level = current_mutation
                daughter.status = "mutated"
                session.add(daughter)
            task = session.query(DaughterTask).filter_by(id=task_id).first()
            if task:
                task.current_retry = attempt_number - 1
                task.status = "retrying"
                task.updated_at = _now()
                session.add(task)
            session.commit()
        except Exception:
            session.rollback()
            return
        finally:
            session.close()

        session = get_session("vx11")
        try:
            attempt = _create_attempt(session, daughter_id, attempt_number)
            session.commit()
            attempt_id = attempt.id
        except Exception:
            session.rollback()
            return
        finally:
            session.close()


@app.get("/health")
def health():
    return {"status": "ok", "service": "spawner", "version": "v7.0"}


# P0-2: Process management endpoints
@app.get("/process/{daughter_id}")
async def query_process(daughter_id: int):
    """Query status of a spawned daughter process."""
    session = get_session("vx11")
    try:
        daughter = session.query(Daughter).filter(Daughter.id == daughter_id).first()
        if not daughter:
            raise HTTPException(
                status_code=404, detail=f"Daughter {daughter_id} not found"
            )

        task = (
            session.query(DaughterTask)
            .filter(DaughterTask.id == daughter.task_id)
            .first()
        )
        return {
            "status": "ok",
            "daughter_id": daughter.id,
            "spawn_uuid": daughter.spawn_uuid,
            "name": daughter.name,
            "purpose": daughter.purpose,
            "status": daughter.status,
            "started_at": (
                daughter.started_at.isoformat() if daughter.started_at else None
            ),
            "ended_at": daughter.ended_at.isoformat() if daughter.ended_at else None,
            "last_heartbeat_at": (
                daughter.last_heartbeat_at.isoformat()
                if daughter.last_heartbeat_at
                else None
            ),
            "ttl_seconds": daughter.ttl_seconds,
            "task_type": task.task_type if task else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        session.close()


@app.get("/process/uuid/{spawn_uuid}")
async def query_by_uuid(spawn_uuid: str):
    """Query daughter by spawn_uuid."""
    session = get_session("vx11")
    try:
        daughter = (
            session.query(Daughter).filter(Daughter.spawn_uuid == spawn_uuid).first()
        )
        if not daughter:
            raise HTTPException(
                status_code=404, detail=f"spawn_uuid {spawn_uuid} not found"
            )

        task = (
            session.query(DaughterTask)
            .filter(DaughterTask.id == daughter.task_id)
            .first()
        )
        return {
            "status": "ok",
            "daughter_id": daughter.id,
            "spawn_uuid": daughter.spawn_uuid,
            "name": daughter.name,
            "purpose": daughter.purpose,
            "status": daughter.status,
            "started_at": (
                daughter.started_at.isoformat() if daughter.started_at else None
            ),
            "ended_at": daughter.ended_at.isoformat() if daughter.ended_at else None,
            "ttl_seconds": daughter.ttl_seconds,
            "task_type": task.task_type if task else None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        session.close()


@app.delete("/kill/{daughter_id}")
async def kill_daughter(daughter_id: int):
    """Kill/terminate a spawned daughter process."""
    session = get_session("vx11")
    try:
        daughter = session.query(Daughter).filter(Daughter.id == daughter_id).first()
        if not daughter:
            raise HTTPException(
                status_code=404, detail=f"Daughter {daughter_id} not found"
            )

        # Mark as killed if still running
        if daughter.status in ["spawned", "running", "retrying", "mutated"]:
            daughter.status = "killed"
            daughter.ended_at = _now()
            session.add(daughter)

            # Also update task
            task = (
                session.query(DaughterTask)
                .filter(DaughterTask.id == daughter.task_id)
                .first()
            )
            if task:
                task.status = "killed"
                task.finished_at = _now()
                session.add(task)

            # Update hijas records
            _update_hijas_records(
                session, daughter_id, "killed", {"killed_by": "api_endpoint"}
            )
            session.commit()

        return {
            "status": "ok",
            "action": "kill",
            "daughter_id": daughter_id,
            "new_status": daughter.status,
            "timestamp": _now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        session.close()


@app.post("/spawn", response_model=SpawnResponse)
async def spawn(req: SpawnRequest, background_tasks: BackgroundTasks):
    if not req.name and not req.cmd:
        raise HTTPException(status_code=400, detail="name_or_cmd_required")
    if req.cmd is None:
        req.cmd = ""

    spawn_uuid = str(uuid.uuid4())  # P0-1: Generate UUID early
    session = get_session("vx11")
    try:
        _register_intent(session, req)
        task, daughter = _create_task_and_daughter(
            session, req, spawn_uuid
        )  # P0-1: Pass spawn_uuid
        _create_spawn(session, req, spawn_uuid)
        attempt = _create_attempt(session, daughter.id, 1)
        _update_status(session, task.id, daughter.id, "running")
        _init_hijas_records(session, req, task, daughter, spawn_uuid, attempt.id)
        session.commit()
        task_id = task.id
        daughter_id = daughter.id
        attempt_id = attempt.id
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        session.close()

    if req.subtasks:
        await asyncio.to_thread(_spawn_subtasks, req, task_id)

    if req.cmd:
        background_tasks.add_task(
            _run_spawn_lifecycle,
            spawn_uuid,
            task_id,
            daughter_id,
            attempt_id,
            req.cmd,
            req.ttl_seconds,
            req.max_retries,
            req.auto_retry,
            req.mutation_level,
            req.task_type,
        )

    _log_spawn_event(
        "spawn_created",
        {
            "spawn_uuid": spawn_uuid,
            "daughter_id": daughter_id,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "cmd": req.cmd,
            "ttl_seconds": req.ttl_seconds,
        },
    )

    return SpawnResponse(
        status="accepted",
        spawn_uuid=spawn_uuid,
        daughter_id=daughter_id,
        daughter_task_id=task_id,
        attempt_id=attempt_id,
        name=req.name or f"spawn-{spawn_uuid[:8]}",
        cmd=req.cmd,
        ttl_seconds=req.ttl_seconds,
        mutation_level=req.mutation_level,
        trace_id=req.trace_id,
    )


@app.post("/spawner/create", response_model=SpawnResponse)
async def spawn_compat_create(req: SpawnRequest, background_tasks: BackgroundTasks):
    return await spawn(req, background_tasks)


@app.post("/spawner/spawn", response_model=SpawnResponse)
async def spawn_compat_spawn(req: SpawnRequest, background_tasks: BackgroundTasks):
    return await spawn(req, background_tasks)
