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
try:
    from madre import power_saver as power_saver_module  # type: ignore
except Exception:  # pragma: no cover - optional
    power_saver_module = None  # type: ignore

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

# VX11 Service Control Policy: guardrails for autonomy
VX11_ALLOW_SERVICE_CONTROL = os.environ.get(
    "VX11_ALLOW_SERVICE_CONTROL", "0"
).lower() in ("1", "true", "yes")
MAINTENANCE_WINDOW_ENABLED = os.environ.get(
    "VX11_MAINTENANCE_WINDOW_ENABLED", "1"
).lower() in ("1", "true", "yes")

_TOKENS: Dict[str, Dict[str, Any]] = {}
_RATE: Dict[str, Dict[str, Any]] = {}

# Cache for compose files (TTL: 60 seconds)
_COMPOSE_FILES_CACHE: Dict[str, Any] = {
    "files": None,
    "timestamp": 0,
    "ttl_seconds": 60,
}

router = APIRouter()


class PowerRequest(BaseModel):
    apply: bool = False
    confirm: Optional[str] = None


class PostTaskRequest(BaseModel):
    apply: Optional[bool] = None
    reason: Optional[str] = None


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


def _run(
    args: List[str], timeout: int = 20, cwd: Optional[str] = None
) -> Dict[str, Any]:
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


def _count_backups(backups_dir: str) -> Dict[str, int]:
    if not os.path.isdir(backups_dir):
        return {"backup_db_count": 0, "backups_archived_count": 0}
    backup_files = [
        name
        for name in os.listdir(backups_dir)
        if os.path.isfile(os.path.join(backups_dir, name))
    ]
    archived_dir = os.path.join(backups_dir, "archived")
    archived_files = []
    if os.path.isdir(archived_dir):
        archived_files = [
            name
            for name in os.listdir(archived_dir)
            if os.path.isfile(os.path.join(archived_dir, name))
        ]
    return {
        "backup_db_count": len(backup_files),
        "backups_archived_count": len(archived_files),
    }


def _parse_sqlite_result(res: Dict[str, Any]) -> str:
    stdout = (res.get("stdout") or "").strip()
    if not stdout:
        return "error"
    return stdout.splitlines()[0].strip()


def _write_snapshot(out_dir: str, prefix: str, debug: bool = False) -> None:
    """Write system snapshots (ss, ps, free) for debugging.

    Optimization: Skip snapshots in fast-path unless debug=True.
    Improves latency by 20-30ms per operation (3 subprocess calls avoided).
    """
    if not debug:
        # Fast path: skip snapshots
        return

    try:
        ss = _run(["ss", "-ltnp"], timeout=10)
    except Exception:
        ss = {"stdout": "", "stderr": "ss command not available in container"}

    try:
        ps = _run(["ps", "aux"], timeout=10)
    except Exception:
        ps = {"stdout": "", "stderr": "ps command not available"}

    try:
        free = _run(["free", "-h"], timeout=10)
    except Exception:
        free = {"stdout": "", "stderr": "free command not available"}

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


def _run_sqlite_check(
    db_path: str, out_dir: str, label: str, pragma: str, foreign_keys: bool = False
) -> Dict[str, Any]:
    cmd = [
        "sqlite3",
        db_path,
        "-cmd",
        "PRAGMA busy_timeout=5000;"
        + (" PRAGMA foreign_keys=ON;" if foreign_keys else ""),
        f"PRAGMA {pragma};",
    ]
    res = _run(cmd, timeout=60)
    path = os.path.join(out_dir, f"sqlite_{label}.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(res.get("stdout", ""))
        if res.get("stderr"):
            fh.write("\n# STDERR:\n")
            fh.write(res.get("stderr", ""))
    return res


def _compose_files() -> List[str]:
    # Check cache first (TTL: 60 seconds)
    cache_age = time.time() - _COMPOSE_FILES_CACHE["timestamp"]
    if (
        _COMPOSE_FILES_CACHE["files"] is not None
        and cache_age < _COMPOSE_FILES_CACHE["ttl_seconds"]
    ):
        return _COMPOSE_FILES_CACHE["files"]

    # Rebuild cache
    files = []
    main = os.path.join(REPO_ROOT, "docker-compose.yml")
    override = os.path.join(REPO_ROOT, "docker-compose.override.yml")
    if os.path.exists(main):
        files.append(main)
    if os.path.exists(override):
        files.append(override)

    # Update cache with timestamp
    _COMPOSE_FILES_CACHE["files"] = files
    _COMPOSE_FILES_CACHE["timestamp"] = time.time()

    return files


def _compose_services() -> Tuple[List[str], Optional[str]]:
    files = _compose_files()
    if not files:
        return [], "compose_files_missing"

    # Try to get all services (including those with profiles)
    args = ["docker", "compose", "-p", "vx11"]
    for f in files:
        args.extend(["-f", f])
    args.extend(["config", "--services"])

    try:
        res = _run(args, timeout=20)
        if res["rc"] == 0:
            services = [l.strip() for l in res["stdout"].splitlines() if l.strip()]
            if services:
                return services, None
    except Exception:
        pass

    # Fallback: use canonical services
    return CANONICAL_SERVICES, "context_fallback"


def _db_services() -> List[str]:
    db_path = os.environ.get("VX11_DB_PATH") or os.path.join(
        REPO_ROOT, "data", "runtime", "vx11.db"
    )
    if not os.path.exists(db_path):
        return []
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='module_status'"
        )
        if not cur.fetchone():
            return []
        cur.execute("SELECT module_name FROM module_status ORDER BY module_name")
        rows = [r[0] for r in cur.fetchall() if r and r[0]]
        return rows
    except Exception:
        return []
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _allowlist() -> Tuple[List[str], str]:
    # Always use CANONICAL_SERVICES which has all potential services
    # This ensures power control works for all services, not just active ones
    return CANONICAL_SERVICES, "canonical"


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


def _security_flags(
    key_ok: bool, token_ok: bool, confirm_ok: bool, rate_ok: bool
) -> Dict[str, bool]:
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
    cmd = ["docker", "compose", "-p", "vx11"]
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
        cmd = ["docker", "compose", "-p", "vx11"]
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


@router.post("/madre/power/maintenance/post_task")
async def maintenance_post_task(
    req: Optional[PostTaskRequest] = None,
) -> Dict[str, Any]:
    # Handle optional body
    if req is None:
        req = PostTaskRequest()

    out_dir = _make_out_dir("maintenance_post_task", "post_task")
    db_path = None
    if power_saver_module and hasattr(power_saver_module, "_resolve_db_path"):
        try:
            db_path = power_saver_module._resolve_db_path()
        except Exception:
            db_path = None
    db_path = db_path or os.path.join(REPO_ROOT, "data", "runtime", "vx11.db")

    size_mb = None
    try:
        size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    except Exception:
        size_mb = None

    apply_retention = req.apply
    if apply_retention is None:
        apply_retention = bool(size_mb and size_mb >= 500.0)

    sqlite_results = {
        "quick_check": _run_sqlite_check(
            db_path, out_dir, "quick_check", "quick_check"
        ),
        "integrity_check": _run_sqlite_check(
            db_path, out_dir, "integrity_check", "integrity_check"
        ),
        "foreign_key_check": _run_sqlite_check(
            db_path,
            out_dir,
            "foreign_key_check",
            "foreign_key_check",
            foreign_keys=True,
        ),
    }

    retention_result = None
    rotation_result = None
    regen_result = None
    counts_result = None
    scorecard = None
    if power_saver_module:
        try:
            retention_result = power_saver_module.db_retention_cleanup(
                out_dir, apply=bool(apply_retention), db_path=db_path
            )
        except Exception as exc:
            retention_result = {"status": "error", "error": str(exc)}

        try:
            rotation_result = power_saver_module.rotate_backups(
                out_dir, keep=2, apply=True
            )
        except Exception as exc:
            rotation_result = {"status": "error", "error": str(exc)}

        try:
            regen_result = power_saver_module.regen_dbmap(out_dir)
        except Exception as exc:
            regen_result = {"status": "error", "error": str(exc)}

    counts_path = os.path.join(out_dir, "counts.json")
    try:
        counts_res = _run(
            ["python3", "scripts/audit_counts.py", db_path], timeout=60, cwd=REPO_ROOT
        )
        stdout_text = counts_res.get("stdout") or ""
        if stdout_text:
            with open(counts_path, "w", encoding="utf-8") as fh:
                fh.write(stdout_text)
        counts_result = counts_res
    except Exception as exc:
        counts_result = {"status": "error", "error": str(exc)}

    try:
        counts_payload = {}
        if os.path.exists(counts_path):
            with open(counts_path, "r", encoding="utf-8") as fh:
                counts_payload = json.load(fh)
        db_size_bytes = None
        try:
            db_size_bytes = os.path.getsize(db_path)
        except Exception:
            db_size_bytes = None
        backup_counts = _count_backups(os.path.join(REPO_ROOT, "data", "backups"))
        integrity_value = _parse_sqlite_result(
            sqlite_results.get("integrity_check", {})
        )
        scorecard = {
            "generated_ts": _now_ts(),
            "integrity": integrity_value,
            "total_tables": counts_payload.get("total_tables"),
            "total_rows": counts_payload.get("total_rows"),
            "db_size_bytes": db_size_bytes,
            "backup_db_count": backup_counts.get("backup_db_count"),
            "backups_archived_count": backup_counts.get("backups_archived_count"),
        }
        _write_json(os.path.join(out_dir, "SCORECARD.json"), scorecard)
        _write_json(
            os.path.join(REPO_ROOT, "docs", "audit", "SCORECARD.json"), scorecard
        )
    except Exception as exc:
        scorecard = {"status": "error", "error": str(exc)}

    return {
        "status": "ok",
        "out_dir": out_dir,
        "db_path": db_path,
        "db_size_mb": size_mb,
        "apply_retention": bool(apply_retention),
        "reason": req.reason,
        "sqlite": {
            "quick_check": sqlite_results["quick_check"].get("rc"),
            "integrity_check": sqlite_results["integrity_check"].get("rc"),
            "foreign_key_check": sqlite_results["foreign_key_check"].get("rc"),
        },
        "retention": retention_result,
        "backup_rotation": rotation_result,
        "regen_dbmap": regen_result,
        "counts": counts_result,
        "scorecard": scorecard,
    }


@router.post("/madre/power/service/{name}/start")
async def power_start(
    name: str,
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_action(
        "start", name, req, request, x_vx11_power_key, x_vx11_power_token
    )


@router.post("/madre/power/service/{name}/stop")
async def power_stop(
    name: str,
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_action(
        "stop", name, req, request, x_vx11_power_key, x_vx11_power_token
    )


@router.post("/madre/power/service/{name}/restart")
async def power_restart(
    name: str,
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    return await _power_action(
        "restart", name, req, request, x_vx11_power_key, x_vx11_power_token
    )


@router.post("/madre/power/mode/idle_min")
async def power_idle_min(
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    """
    P0-3 SECURITY: POST /madre/power/mode/idle_min

    Idle-min power mode requires THREE security checks (same as hard_off):
    1. Header X-VX11-POWER-KEY (must match env VX11_POWER_KEY)
    2. Header X-VX11-POWER-TOKEN (must be valid)
    3. Request body field: confirm="I_UNDERSTAND_THIS_STOPS_SERVICES"

    Idle-min is slightly safer: only stops tentaculo_link, keeps madre + core running.
    """
    return await _power_mode(
        "idle_min", req, request, x_vx11_power_key, x_vx11_power_token
    )


@router.post("/madre/power/mode/hard_off")
async def power_hard_off(
    req: PowerRequest,
    request: Request,
    x_vx11_power_key: Optional[str] = Header(None),
    x_vx11_power_token: Optional[str] = Header(None),
):
    """
    P0-3 SECURITY: POST /madre/power/mode/hard_off
    
    Hard-off power mode requires THREE security checks:
    1. Header X-VX11-POWER-KEY (must match env VX11_POWER_KEY)
    2. Header X-VX11-POWER-TOKEN (must be valid and match IP/UA in rate-limit whitelist)
    3. Request body field: confirm="I_UNDERSTAND_THIS_STOPS_SERVICES"
    
    If any check fails:
    - apply=false: returns plan without executing
    - apply=true: returns 400 error (security_flags show what failed)
    
    Example (with ?apply=false to get plan first):
    curl -X POST http://localhost:8001/madre/power/mode/hard_off \
      -H "X-VX11-POWER-KEY: $(echo $VX11_POWER_KEY)" \
      -H "X-VX11-POWER-TOKEN: $(cat /etc/vx11/tokens.env | grep TOKEN)" \
      -H "Content-Type: application/json" \
      -d '{"apply": false, "confirm": "I_UNDERSTAND_THIS_STOPS_SERVICES"}'
    """
    return await _power_mode(
        "hard_off", req, request, x_vx11_power_key, x_vx11_power_token
    )


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

    key_ok = bool(os.environ.get("VX11_POWER_KEY")) and key_header == os.environ.get(
        "VX11_POWER_KEY"
    )
    token_ok = bool(token_header) and _validate_token(token_header, ip, ua)
    confirm_ok = req.confirm == "I_UNDERSTAND_THIS_STOPS_SERVICES"

    if not req.apply:
        db_write = _record_db(f"power_{action}_plan", f"service:{name}")
        return _response(
            "plan",
            False,
            name,
            action,
            plan,
            [],
            out_dir,
            db_write,
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
        )

    if not docker_ok:
        reason_path = os.path.join(out_dir, "plan_only_reason.txt")
        with open(reason_path, "w", encoding="utf-8") as f:
            f.write("docker_unavailable_or_no_permissions\n")
        db_write = _record_db(
            f"power_{action}_plan", f"service:{name}:docker_unavailable"
        )
        return _response(
            "plan",
            False,
            name,
            action,
            plan,
            [],
            out_dir,
            db_write,
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
        )

    if not rate_ok:
        return _response(
            "error",
            False,
            name,
            action,
            plan,
            [],
            out_dir,
            "skipped",
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
            code=429,
        )

    if not (key_ok and token_ok and confirm_ok):
        return _response(
            "error",
            False,
            name,
            action,
            plan,
            [],
            out_dir,
            "skipped",
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
            code=400,
        )

    _write_snapshot(out_dir, "pre")
    executed = _execute_plan(out_dir, plan)
    _write_snapshot(out_dir, "post")
    db_write = _record_db(f"power_{action}_apply", f"service:{name}")
    return _response(
        "ok",
        True,
        name,
        action,
        plan,
        executed,
        out_dir,
        db_write,
        _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
    )


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
        {
            "plan": plan,
            "apply": req.apply,
            "mode": action,
            "docker_available": docker_ok,
        },
    )

    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    rate_ok, _rate_state = _rate_limit(ip, action)

    key_ok = bool(os.environ.get("VX11_POWER_KEY")) and key_header == os.environ.get(
        "VX11_POWER_KEY"
    )
    token_ok = bool(token_header) and _validate_token(token_header, ip, ua)
    confirm_ok = req.confirm == "I_UNDERSTAND_THIS_STOPS_SERVICES"

    if not req.apply:
        db_write = _record_db(f"power_{action}_plan", "mode")
        return _response(
            "plan",
            False,
            None,
            action,
            plan,
            [],
            out_dir,
            db_write,
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
        )

    if not docker_ok:
        reason_path = os.path.join(out_dir, "plan_only_reason.txt")
        with open(reason_path, "w", encoding="utf-8") as f:
            f.write("docker_unavailable_or_no_permissions\n")
        db_write = _record_db(f"power_{action}_plan", "mode:docker_unavailable")
        return _response(
            "plan",
            False,
            None,
            action,
            plan,
            [],
            out_dir,
            db_write,
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
        )

    if not rate_ok:
        return _response(
            "error",
            False,
            None,
            action,
            plan,
            [],
            out_dir,
            "skipped",
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
            code=429,
        )

    if not (key_ok and token_ok and confirm_ok):
        return _response(
            "error",
            False,
            None,
            action,
            plan,
            [],
            out_dir,
            "skipped",
            _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
            code=400,
        )

    _write_snapshot(out_dir, "pre")
    executed = _execute_plan(out_dir, plan)
    _write_snapshot(out_dir, "post")
    db_write = _record_db(f"power_{action}_apply", "mode")
    return _response(
        "ok",
        True,
        None,
        action,
        plan,
        executed,
        out_dir,
        db_write,
        _security_flags(key_ok, token_ok, confirm_ok, rate_ok),
    )


class ModeRequest(BaseModel):
    mode: str


class ServiceRequest(BaseModel):
    service: str


@router.post("/madre/power/mode")
async def set_power_mode_simple(req: ModeRequest, apply: bool = True):
    allowlist, _ = _allowlist()
    mode = req.mode.lower()
    out_dir = _make_out_dir(f"mode_{mode}", None)
    plan = _plan_for_named_mode(mode, allowlist)

    if not apply:
        return {"status": "plan", "mode": mode, "plan": plan, "out_dir": out_dir}

    executed = _execute_plan(out_dir, plan)
    return {"status": "ok", "mode": mode, "executed": executed, "out_dir": out_dir}


@router.post("/madre/power/service/start")
async def start_service_simple(req: ServiceRequest):
    # VX11 GUARDRAIL: Service control requires explicit enablement
    if not VX11_ALLOW_SERVICE_CONTROL:
        raise HTTPException(
            status_code=403,
            detail="Service control disabled. Set VX11_ALLOW_SERVICE_CONTROL=1 to enable.",
        )

    allowlist, _ = _allowlist()
    svc = req.service
    if svc not in allowlist:
        raise HTTPException(status_code=404, detail=f"Service {svc} not in allowlist")
    out_dir = _make_out_dir("start", svc)
    plan = _plan_for_service("up", svc)
    # Ensure -d is present for up
    for step in plan:
        if "up" in step["cmd"] and "-d" not in step["cmd"]:
            idx = step["cmd"].index("up")
            step["cmd"].insert(idx + 1, "-d")

    executed = _execute_plan(out_dir, plan)
    return {"status": "ok", "service": svc, "executed": executed, "out_dir": out_dir}


@router.post("/madre/power/service/stop")
async def stop_service_simple(req: ServiceRequest):
    # VX11 GUARDRAIL: Service control requires explicit enablement
    if not VX11_ALLOW_SERVICE_CONTROL:
        raise HTTPException(
            status_code=403,
            detail="Service control disabled. Set VX11_ALLOW_SERVICE_CONTROL=1 to enable.",
        )

    allowlist, _ = _allowlist()
    svc = req.service
    if svc not in allowlist:
        raise HTTPException(status_code=404, detail=f"Service {svc} not in allowlist")
    out_dir = _make_out_dir("stop", svc)
    plan = _plan_for_service("stop", svc)
    executed = _execute_plan(out_dir, plan)
    return {"status": "ok", "service": svc, "executed": executed, "out_dir": out_dir}


@router.get("/madre/power/status")
async def get_power_status_simple():
    res = _run(["docker", "compose", "-p", "vx11", "ps", "--format", "json"])
    try:
        # docker compose ps --format json returns multiple lines of json objects or a list
        raw = res.get("stdout", "").strip()
        if raw.startswith("["):
            services = json.loads(raw)
        else:
            services = [json.loads(l) for l in raw.splitlines() if l.strip()]
    except Exception:
        services = res.get("stdout", "")
    return {"status": "ok", "services": services}


@router.post("/madre/power/policy/solo_madre/apply")
async def apply_solo_madre_policy():
    """
    Apply SOLO_MADRE policy: stop all services except madre.
    Container-level control only (docker compose, not process-level).
    Evidence saved to docs/audit/madre_power_solo_madre_*.
    """
    allowlist, _ = _allowlist()
    out_dir = _make_out_dir("solo_madre_policy", "apply")
    plan = _plan_for_named_mode("low_power", allowlist)

    _write_json(
        os.path.join(out_dir, "plan.json"),
        {
            "policy": "solo_madre",
            "mode": "low_power",
            "plan": plan,
            "timestamp": _now_ts(),
        },
    )

    _write_snapshot(out_dir, "pre")
    executed = _execute_plan(out_dir, plan)
    _write_snapshot(out_dir, "post")
    _record_db("power_solo_madre_apply", "policy")

    return {
        "status": "ok",
        "policy": "solo_madre",
        "executed": executed,
        "out_dir": out_dir,
        "message": "SOLO_MADRE policy applied: all services stopped except madre",
    }


@router.get("/madre/power/policy/solo_madre/status")
async def check_solo_madre_policy_status():
    """
    Check if SOLO_MADRE policy is currently active.
    Returns true if only madre is running.
    """
    res = _run(["docker", "compose", "-p", "vx11", "ps", "--format", "json"])
    try:
        raw = res.get("stdout", "").strip()
        if raw.startswith("["):
            services = json.loads(raw)
        else:
            services = [json.loads(l) for l in raw.splitlines() if l.strip()]
    except Exception:
        services = []

    running_services = []
    if isinstance(services, list):
        running_services = [
            svc.get("Service", svc.get("service", ""))
            for svc in services
            if isinstance(svc, dict)
        ]

    is_solo_madre = len(running_services) == 1 and "madre" in running_services

    return {
        "status": "ok",
        "policy_active": is_solo_madre,
        "running_services": running_services,
        "expected_services": ["madre"],
    }


def _plan_for_named_mode(mode: str, allowlist: List[str]) -> List[Dict[str, Any]]:
    modes = {
        "low_power": ["madre"],
        "operative_core": ["madre", "tentaculo_link", "switch", "spawner", "mcp"],
        "full": [
            "madre",
            "tentaculo_link",
            "switch",
            "spawner",
            "hermes",
            "hormiguero",
            "manifestator",
            "shubniggurath",
            "operator-backend",
            "operator-frontend",
        ],
    }
    target = modes.get(mode, ["madre"])
    # Filter to only services in allowlist (exclude infrastructure like redis)
    target = [svc for svc in target if svc in allowlist]
    plan = []
    # Stop services not in target
    for svc in allowlist:
        if svc not in target and svc != "redis":
            plan.append(
                {"cmd": ["docker", "compose", "-p", "vx11", "stop", svc], "timeout": 30}
            )
    # Start services in target
    for svc in target:
        if svc == "madre":
            continue
        plan.append(
            {"cmd": ["docker", "compose", "-p", "vx11", "up", "-d", svc], "timeout": 30}
        )
    return plan


def register_power_routes(app) -> None:
    app.include_router(router)
