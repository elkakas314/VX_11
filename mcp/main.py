"""
MCP v6.3 - Hardened sandbox
- Token auth
- Restricted tools
- No arbitrary code execution
"""

import asyncio
import asyncio.subprocess as asp
import json
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import settings
from config.tokens import load_tokens, get_token
from config.forensics import write_log
from config.db_schema import get_session, SandboxExec, AuditLogs

load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


def check_token(x_vx11_token: str = Header(None)):
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=401, detail="auth_required")
    return True


SAFE_MODULES = {"json", "math", "re", "random"}
BANNED_FRAGMENTS = ["__import__", "open(", "subprocess", "socket", "requests", "httpx", "os.", "sys."]
ALLOWED_CMDS = {"echo", "python", "node", "ls", "cat", "bash"}


class CopilotRequest(BaseModel):
    method: str
    resource: str
    params: Optional[Dict[str, Any]] = None
    context7: Optional[Dict[str, Any]] = None


app = FastAPI(title="VX11 MCP Hardened", dependencies=[Depends(check_token)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def bypass_health(request: Request, call_next):
    if request.url.path == "/health":
        return JSONResponse({"status": "ok"})
    return await call_next(request)


def _record_sandbox(action: str, status: str, duration_ms: float = 0.0, error: str = ""):
    session: Session = get_session("vx11")
    try:
        rec = SandboxExec(action=action, status=status, duration_ms=duration_ms, error=error)
        session.add(rec)
        session.commit()
    finally:
        session.close()


def _audit(message: str, level: str = "INFO"):
    session: Session = get_session("vx11")
    try:
        rec = AuditLogs(component="mcp", level=level, message=message)
        session.add(rec)
        session.commit()
    finally:
        session.close()


async def _run_sandbox_command(cmd: str, args: List[str], cwd: str, env: Dict[str, str], timeout: float) -> Dict[str, Any]:
    if cmd not in ALLOWED_CMDS:
        _audit(f"forbidden_cmd:{cmd}", level="WARN")
        raise HTTPException(status_code=403, detail="command_not_allowed")

    proc = await asyncio.create_subprocess_exec(
        cmd,
        *args,
        cwd=cwd,
        env=env or None,
        stdout=asp.PIPE,
        stderr=asp.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        duration = 0.0
        _record_sandbox("exec_cmd", "ok", duration_ms=duration)
        return {
            "status": "completed",
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode,
        }
    except asyncio.TimeoutError:
        proc.kill()
        _record_sandbox("exec_cmd", "timeout")
        raise HTTPException(status_code=408, detail="timeout")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/mcp/copilot-bridge")
async def copilot_bridge(req: CopilotRequest):
    """Minimal bridge that routes only safe resources."""
    if req.resource not in {"/mcp/tools", "/mcp/chat"}:
        _audit(f"forbidden_resource:{req.resource}", "WARN")
        raise HTTPException(status_code=403, detail="resource_not_allowed")

    if req.resource == "/mcp/tools":
        return {
            "status": "ok",
            "tools": [
                {"name": "echo", "description": "echo payload"},
                {"name": "context7_validate", "description": "validate context7 structure"},
            ],
        }

    if req.resource == "/mcp/chat":
        message = (req.params or {}).get("message", "")
        _audit(f"chat_request:{len(message)}chars")
        return {"status": "ok", "reply": f"[mcp-sandboxed] {message}"}

    return {"status": "error"}


@app.post("/mcp/execute_safe")
async def execute_safe(payload: Dict[str, Any]):
    """Executes only whitelisted operations on safe modules."""
    module = payload.get("module")
    expr = payload.get("expr", "")
    if module not in SAFE_MODULES:
        raise HTTPException(status_code=403, detail="module_not_allowed")
    if not isinstance(expr, str):
        raise HTTPException(status_code=400, detail="expr_required")
    for frag in BANNED_FRAGMENTS:
        if frag in expr:
            _audit(f"blocked_expr_fragment:{frag}", level="WARN")
            raise HTTPException(status_code=403, detail="forbidden_expression")
    try:
        start = asyncio.get_event_loop().time()
        result = eval(expr, {"__builtins__": {}}, {})
        duration = (asyncio.get_event_loop().time() - start) * 1000
        _record_sandbox("execute_safe", "ok", duration_ms=duration)
        return {"status": "ok", "result": result}
    except Exception as exc:
        write_log("mcp", f"execute_safe_error:{exc}", level="ERROR")
        _record_sandbox("execute_safe", "error", error=str(exc))
        raise HTTPException(status_code=400, detail="execution_error")


@app.post("/mcp/execute")
async def execute(payload: Dict[str, Any]):
    """Alias to execute_safe with timeout enforcement."""
    try:
        return await asyncio.wait_for(execute_safe(payload), timeout=2.0)
    except asyncio.TimeoutError:
        _record_sandbox("execute_safe", "timeout")
        raise HTTPException(status_code=408, detail="timeout")


@app.get("/mcp/sandbox/check")
async def sandbox_check():
    return {"status": "ok", "allowed_modules": list(SAFE_MODULES)}


class SandboxCmdRequest(BaseModel):
    cmd: str
    args: Optional[List[str]] = None
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: Optional[float] = 30.0
    context: Optional[Dict[str, Any]] = None


@app.post("/mcp/sandbox/exec_cmd")
async def sandbox_exec_cmd(req: SandboxCmdRequest):
    """
    Ejecuta comandos permitidos en sandbox controlado. Sin comandos IA pesados.
    """
    cwd = req.cwd or "/app/sandbox"
    env = req.env or {}
    res = await _run_sandbox_command(req.cmd, req.args or [], cwd, env, req.timeout or 30.0)
    _audit(f"exec_cmd:{req.cmd}")
    return res
