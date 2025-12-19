import json
import os
import secrets
import sqlite3
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from madre.core.db import MadreDB  # type: ignore
except Exception:  # pragma: no cover - optional
    MadreDB = None  # type: ignore

REPO_ROOT = os.environ.get("VX11_REPO_ROOT") or "/home/elkakas314/vx11"
if not os.path.isdir(REPO_ROOT):
    REPO_ROOT = str(Path(__file__).resolve().parents[1])

AUDIT_BASE = os.path.join(REPO_ROOT, "docs", "audit")

TOKEN_TTL_SECONDS = 60
RATE_LIMIT_PER_MIN = 6
BLOCK_SECONDS = 60
HARD_OFF_LIMIT = 1
HARD_OFF_BLOCK_SECONDS = 300

CANONICAL_SERVICES = [
    "tentaculo_link",
    "madre",
    "switch",
    "hermes",
    "hormiguero",
    "manifestator",
    "mcp",
    "shubniggurath",
    "spawner",
    "operator-backend",
    "operator-frontend",
]

_TOKENS: Dict[str, Dict[str, Any]] = {}
_RATE: Dict[str, Dict[str, Any]] = {}

router = APIRouter()


class PowerRequest(BaseModel):
    apply: bool = False
    confirm: Optional[str] = None


def _now_ts() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _safe_name(name: Optional[str]) -> str:
    if not name:
        return "none"
    return "".join(c for c in name if c.isalnum() or c in ("-", "_"))[:64] or "none"


def _make_out_dir(action: str, service: Optional[str]) -> str:
    ts = _now_ts()
    base = AUDIT_BASE
    os.makedirs(base, exist_ok=True)
    out_dir = os.path.join(base, f"madre_power_{action}_{_safe_name(service)}_{ts}")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _run(args: List[str], timeout: int = 20, cwd: Optional[str] = None) -> Dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        args,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed_ms = int((time.time() - started) * 1000)
    return {
        "rc": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "cmd": args,
        "elapsed_ms": elapsed_ms,
    }


def _write_snapshot(out_dir: str, prefix: str) -> None:
    ss = _run(["ss", "-ltnp"], timeout=10)
    ps = _run(["ps", "aux"], timeout=10)
    free = _run(["free", "-h"], timeout=10)

    with open(os.path.join(out_dir, f"{prefix}_ss.txt"), "w", encoding="utf-8") as f:
        f.write(ss.get("stdout", ""))
        if ss.get("stderr"):
            f.write("\n# STDERR\n")
            f.write(ss.get("stderr", ""))

    ps_lines = ps.get("stdout", "").splitlines()
    with open(os.path.join(out_dir, f"{prefix}_ps.txt"), "w", encoding="utf-8") as f:
        for line in ps_lines[:100]:
            f.write(line + "\n")
        if ps.get("stderr"):
            f.write("\n# STDERR\n")
            f.write(ps.get("stderr", ""))

    with open(os.path.join(out_dir, f"{prefix}_free.txt"), "w", encoding="utf-8") as f:
        f.write(free.get("stdout", ""))
        if free.get("stderr"):
            f.write("\n# STDERR\n")
            f.write(free.get("stderr", ""))


def _compose_files() -> List[str]:
    files = []
    main = os.path.join(REPO_ROOT, "docker-compose.yml")
    override = os.path.join(REPO_ROOT, "docker-compose.override.yml")
    if os.path.exists(main):
        files.append(main)
    if os.path.exists(override):
        files.append(override)
    return files


def _compose_services() -> Tuple[List[str], Optional[str]]:
    files = _compose_files()
    if not files:
        return [], "compose_files_missing"
    args = ["docker", "compose"]
    for f in files:
        args.extend(["-f", f])
    args.extend(["config", "--services"])
    try:
        res = _run(args, timeout=20)
    except Exception as e:
        return [], f"compose_error:{e}"
    if res["rc"] != 0:
        return [], "compose_failed"
    services = [l.strip() for l in res["stdout"].splitlines() if l.strip()]
    return services, None


def _db_services() -> List[str]:
    db_path = os.environ.get("VX11_DB_PATH") or os.path.join(REPO_ROOT, "data", "runtime", "vx11.db")
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='module_status'")
        if not cur.fetchone():
            return []
        cur.execute("SELECT module_name FROM module_status ORDER BY module_name")
        rows = [r[0] for r in cur.fetchall() if r and r[0]]
        return rows
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _allowlist() -> Tuple[List[str], str]:
    services, err = _compose_services()
    if services:
        return services, "compose"
    db_services = _db_services()
    if db_services:
        return db_services, "db"
    return CANONICAL_SERVICES, "context"


def _token_key(ip: str, ua: str) -> str:
    return f"{ip}:{ua}"


def _issue_token(ip: str, ua: str) -> Dict[str, Any]:
    token = secrets.token_urlsafe(16)
    expires_at = datetime.utcnow() + timedelta(seconds=TOKEN_TTL_SECONDS)
    _TOKENS[token] = {"ip": ip, "ua": ua, "expires_at": expires_at}
    return {"token": token, "expires_at": expires_at.isoformat() + "Z"}


def _validate_token(token: str, ip: str, ua: str) -> bool:
    rec = _TOKENS.get(token)
    if not rec:
        return False
    if rec["ip"] != ip or rec["ua"] != ua:
        return False
    if datetime.utcnow() > rec["expires_at"]:
        _TOKENS.pop(token, None)
        return False
    return True


def _rate_key(ip: str, action: str) -> str:
    return f"{ip}:{action}"


def _rate_limit(ip: str, action: str) -> Tuple[bool, Dict[str, Any]]:
    now = time.time()
    key = _rate_key(ip, action)
    limit = HARD_OFF_LIMIT if action == "hard_off" else RATE_LIMIT_PER_MIN
    block_seconds = HARD_OFF_BLOCK_SECONDS if action == "hard_off" else BLOCK_SECONDS
    state = _RATE.get(key, {"window_start": now, "count": 0, "blocked_until": 0})

    if now < state.get("blocked_until", 0):
        return False, state

    if now - state["window_start"] > 60:
        state["window_start"] = now
        state["count"] = 0

    state["count"] += 1
    if state["count"] > limit:
        state["blocked_until"] = now + block_seconds
        _RATE[key] = state
        return False, state

    _RATE[key] = state
    return True, state


def _record_db(action: str, reason: str) -> str:
    if MadreDB is None:
        return "skipped"
    try:
        MadreDB.record_action(module="madre", action=action, reason=reason)
        return "ok"
    except Exception:
        return "skipped"


def _docker_available() -> bool:
    try:
        res = _run(["docker", "compose", "version"], timeout=10)
    except Exception:
        return False
    return res.get("rc") == 0


def _security_flags(key_ok: bool, token_ok: bool, confirm_ok: bool, rate_ok: bool) -> Dict[str, bool]:
    return {
        "key": key_ok,
        "token": token_ok,
        "confirm": confirm_ok,
        "rate_ok": rate_ok,
    }


def _response(
    status: str,
    apply: bool,
    service: Optional[str],
    action: str,
    plan: List[Dict[str, Any]],
    executed: List[Dict[str, Any]],
    out_dir: str,
    db_write: str,
    security: Dict[str, bool],
    code: int = 200,
) -> JSONResponse:
    payload = {
        "status": status,
        "apply": apply,
        "service": service,
        "action": action,
        "plan": plan,
        "executed": executed,
        "out_dir": out_dir,
        "timestamp": _now_ts(),
        "db_write": db_write,
        "security": security,
    }
    return JSONResponse(status_code=code, content=payload)


def _ensure_service(service: str, allowlist: List[str]) -> None:
    if service not in allowlist:
        raise HTTPException(status_code=404, detail="service_not_allowed")


def _plan_for_service(action: str, service: str) -> List[Dict[str, Any]]:
    files = _compose_files()
    cmd = ["docker", "compose"]
    for f in files:
        cmd.extend(["-f", f])
    cmd.append(action)
    cmd.append(service)
    return [{"cmd": cmd, "timeout": 30}]


def _plan_for_mode(action: str, allowlist: List[str]) -> List[Dict[str, Any]]:
    files = _compose_files()
    cmds = []
    for svc in allowlist:
        if action == "idle_min" and svc == "madre":
            continue
        cmd = ["docker", "compose"]
        for f in files:
            cmd.extend(["-f", f])
        cmd.append("stop")
        cmd.append(svc)
        cmds.append({"cmd": cmd, "timeout": 30})
    return cmds


def _execute_plan(out_dir: str, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    executed = []
    for idx, step in enumerate(plan):
        cmd = step.get("cmd", [])
        timeout = int(step.get("timeout", 20))
        res = _run(cmd, timeout=timeout)
        stdout_path = os.path.join(out_dir, f"cmd_{idx}_stdout.txt")
        stderr_path = os.path.join(out_dir, f"cmd_{idx}_stderr.txt")
        with open(stdout_path, "w", encoding="utf-8") as f:
            f.write(res.get("stdout", ""))
        with open(stderr_path, "w", encoding="utf-8") as f:
            f.write(res.get("stderr", ""))
        executed.append(
            {
                "rc": res.get("rc"),
                "cmd": res.get("cmd"),
                "stdout_path": stdout_path,
                "stderr_path": stderr_path,
                "elapsed_ms": res.get("elapsed_ms"),
            }
        )
    return executed


@router.get("/madre/power/services")
async def power_services() -> Dict[str, Any]:
    allowlist, source = _allowlist()
    return {"status": "ok", "allowlist": allowlist, "source": source}


@router.get("/madre/power/token")
async def power_token(request: Request) -> Dict[str, Any]:
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    issued = _issue_token(ip, ua)
    return {"status": "ok", **issued}


@router.post("/madre/power/service/{name}/start")
async def power_start(
    name: str,
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_action("start", name, req, request, x_vx11_power_key, x_vx11_power_token)


@router.post("/madre/power/service/{name}/stop")
async def power_stop(
    name: str,
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_action("stop", name, req, request, x_vx11_power_key, x_vx11_power_token)


@router.post("/madre/power/service/{name}/restart")
async def power_restart(
    name: str,
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_action("restart", name, req, request, x_vx11_power_key, x_vx11_power_token)


@router.post("/madre/power/mode/idle_min")
async def power_idle_min(
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_mode("idle_min", req, request, x_vx11_power_key, x_vx11_power_token)


@router.post("/madre/power/mode/hard_off")
async def power_hard_off(
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_mode("hard_off", req, request, x_vx11_power_key, x_vx11_power_token)


async def _power_action(
    action: str,
    name: str,
    req: PowerRequest,
    request: Request,
    key_header: Optional[str],
    token_header: Optional[str],
):
    allowlist, _ = _allowlist()
    _ensure_service(name, allowlist)

    out_dir = _make_out_dir(action, name)
    plan = _plan_for_service(action, name)
    docker_ok = _docker_available()
    _write_json(
        os.path.join(out_dir, "plan.json"),
        {"plan": plan, "apply": req.apply, "docker_available": docker_ok},
    )

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    rate_ok, _rate_state = _rate_limit(ip, action)

    key_ok = bool(os.environ.get("VX11_POWER_KEY")) and key_header == os.environ.get("VX11_POWER_KEY")
    token_ok = bool(token_header) and _validate_token(token_header, ip, ua)
    confirm_ok = (req.confirm == "I_UNDERSTAND_THIS_STOPS_SERVICES")

    if not req.apply:
        db_write = _record_db(f"power_{action}_plan", f"service:{name}")
        return _response("plan", False, name, action, plan, [], out_dir, db_write, _security_flags(key_ok, token_ok, confirm_ok, rate_ok))

    if not docker_ok:
        reason_path = os.path.join(out_dir, "plan_only_reason.txt")
        with open(reason_path, "w", encoding="utf-8") as f:
            f.write("docker_unavailable_or_no_permissions\n")
        db_write = _record_db(f"power_{action}_plan", f"service:{name}:docker_unavailable")
        return _response("plan", False, name, action, plan, [], out_dir, db_write, _security_flags(key_ok, token_ok, confirm_ok, rate_ok))

    if not rate_ok:
        return _response("error", False, name, action, plan, [], out_dir, "skipped", _security_flags(key_ok, token_ok, confirm_ok, rate_ok), code=429)

    if not (key_ok and token_ok and confirm_ok):
        return _response("error", False, name, action, plan, [], out_dir, "skipped", _security_flags(key_ok, token_ok, confirm_ok, rate_ok), code=400)

    _write_snapshot(out_dir, "pre")
    executed = _execute_plan(out_dir, plan)
    _write_snapshot(out_dir, "post")
    db_write = _record_db(f"power_{action}_apply", f"service:{name}")
    return _response("ok", True, name, action, plan, executed, out_dir, db_write, _security_flags(key_ok, token_ok, confirm_ok, rate_ok))


async def _power_mode(
    action: str,
    req: PowerRequest,
    request: Request,
    key_header: Optional[str],
    token_header: Optional[str],
):
    allowlist, _ = _allowlist()
    out_dir = _make_out_dir(action, None)
    plan = _plan_for_mode(action, allowlist)
    docker_ok = _docker_available()
    _write_json(
        os.path.join(out_dir, "plan.json"),
        {"plan": plan, "apply": req.apply, "mode": action, "docker_available": docker_ok},
    )

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    rate_ok, _rate_state = _rate_limit(ip, action)

    key_ok = bool(os.environ.get("VX11_POWER_KEY")) and key_header == os.environ.get("VX11_POWER_KEY")
    token_ok = bool(token_header) and _validate_token(token_header, ip, ua)
    confirm_ok = (req.confirm == "I_UNDERSTAND_THIS_STOPS_SERVICES")

    if not req.apply:
        db_write = _record_db(f"power_{action}_plan", "mode")
        return _response("plan", False, None, action, plan, [], out_dir, db_write, _security_flags(key_ok, token_ok, confirm_ok, rate_ok))

    if not docker_ok:
        reason_path = os.path.join(out_dir, "plan_only_reason.txt")
        with open(reason_path, "w", encoding="utf-8") as f:
            f.write("docker_unavailable_or_no_permissions\n")
        db_write = _record_db(f"power_{action}_plan", "mode:docker_unavailable")
        return _response("plan", False, None, action, plan, [], out_dir, db_write, _security_flags(key_ok, token_ok, confirm_ok, rate_ok))

    if not rate_ok:
        return _response("error", False, None, action, plan, [], out_dir, "skipped", _security_flags(key_ok, token_ok, confirm_ok, rate_ok), code=429)

    if not (key_ok and token_ok and confirm_ok):
        return _response("error", False, None, action, plan, [], out_dir, "skipped", _security_flags(key_ok, token_ok, confirm_ok, rate_ok), code=400)

    _write_snapshot(out_dir, "pre")
    executed = _execute_plan(out_dir, plan)
    _write_snapshot(out_dir, "post")
    db_write = _record_db(f"power_{action}_apply", "mode")
    return _response("ok", True, None, action, plan, executed, out_dir, db_write, _security_flags(key_ok, token_ok, confirm_ok, rate_ok))


def register_power_routes(app) -> None:
    app.include_router(router)
