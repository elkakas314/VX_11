import asyncio
import json
import os
import subprocess
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from config.db_schema import (
    Daughter,
    DaughterAttempt,
    DaughterTask,
    IntentLog,
    Spawn,
    get_session,
)

app = FastAPI(title="VX11 Spawner - Advanced")


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


def _madre_url() -> str:
    return os.environ.get("VX11_MADRE_URL") or os.environ.get("MADRE_URL") or "http://localhost:8001"


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


def _create_task_and_daughter(session, req: SpawnRequest) -> Tuple[DaughterTask, Daughter]:
    metadata = dict(req.metadata or {})
    metadata.update(
        {
            "tool_allowlist": req.tool_allowlist or [],
            "context_ref": req.context_ref,
            "trace_id": req.trace_id,
            "parent_task_id": req.parent_task_id,
            "task_id": req.task_id,
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


def _notify_madre(daughter_id: int, status: str, payload: Dict[str, Any]) -> None:
    url = _madre_url().rstrip("/")
    endpoint = f"{url}/madre/daughter/{daughter_id}/complete"
    if status in ("failed", "expired", "killed"):
        endpoint = f"{url}/madre/daughter/{daughter_id}/fail"
    try:
        httpx.post(endpoint, json=payload, timeout=10.0)
    except Exception:
        pass


def _execute_command(cmd: str, ttl_seconds: int) -> Tuple[int, str, str, str]:
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
            task, daughter = _create_task_and_daughter(session, sub_req)
            _create_spawn(session, sub_req, str(uuid.uuid4()))
            _create_attempt(session, daughter.id, 1)
            _update_status(session, task.id, daughter.id, "running")
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

        exit_code, stdout, stderr, status = await asyncio.to_thread(
            _execute_command, cmd, ttl_seconds
        )
        session = get_session("vx11")
        try:
            spawn = session.query(Spawn).filter_by(uuid=spawn_uuid).first()
            if spawn:
                spawn.pid = None
                spawn.status = (
                    "completed" if status == "success" else "failed" if status == "error" else "timeout"
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
                session.commit()
                _notify_madre(
                    daughter_id,
                    "completed",
                    {"status": "ok", "exit_code": exit_code, "spawn_uuid": spawn_uuid},
                )
                return

            if not auto_retry or attempt_number >= max_retries:
                final_state = "expired" if status == "timeout" else "failed"
                _update_status(session, task_id, daughter_id, final_state)
                session.commit()
                _notify_madre(
                    daughter_id,
                    final_state,
                    {"status": "error", "exit_code": exit_code, "spawn_uuid": spawn_uuid},
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


@app.post("/spawn", response_model=SpawnResponse)
async def spawn(req: SpawnRequest, background_tasks: BackgroundTasks):
    if not req.name and not req.cmd:
        raise HTTPException(status_code=400, detail="name_or_cmd_required")
    if req.cmd is None:
        req.cmd = ""

    spawn_uuid = str(uuid.uuid4())
    session = get_session("vx11")
    try:
        _register_intent(session, req)
        task, daughter = _create_task_and_daughter(session, req)
        _create_spawn(session, req, spawn_uuid)
        attempt = _create_attempt(session, daughter.id, 1)
        _update_status(session, task.id, daughter.id, "running")
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
