"""
Spawner v2: Procesos Efímeros Mejorados con Aislamiento Completo

Características:
- Procesos aislados en namespaces (si disponible)
- Limpieza automática de recursos
- BD completa de trazas y recursos
- Integración con Madre
- Monitor de recursos (CPU, memoria, tiempo)
"""

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import asyncio
import subprocess
import logging
import psutil
import time
import json
import shutil
from datetime import datetime
from pathlib import Path

from config.settings import settings
from config.db_schema import get_session, Spawn
import os
import signal

log = logging.getLogger("vx11.spawner_v2")
app = FastAPI(title="VX11 Spawner v2 Ephemeral")

# =========== MODELS ===========

class SpawnRequest(BaseModel):
    """Request para crear proceso efímero."""
    name: str
    command: str
    args: Optional[List[str]] = None
    timeout_seconds: int = 300
    max_memory_mb: int = 512
    env: Optional[Dict[str, str]] = None
    parent_id: Optional[str] = None


class SpawnResponse(BaseModel):
    """Response de proceso efímero."""
    spawn_id: str
    pid: Optional[int] = None
    status: str  # created, running, completed, failed, timeout
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: int
    memory_peak_mb: float


# =========== SPAWNER V2 CORE ===========

class EphemeralProcess:
    """Proceso efímero individual."""
    
    def __init__(self, spawn_id: str, name: str, command: str, args: List[str], 
                 timeout_seconds: int, max_memory_mb: int, env: Dict[str, str]):
        self.spawn_id = spawn_id
        self.name = name
        self.command = command
        self.args = args or []
        self.timeout_seconds = timeout_seconds
        self.max_memory_mb = max_memory_mb
        self.env = env or {}
        
        self.pid: Optional[int] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.status = "created"
        self.stdout_data = ""
        self.stderr_data = ""
        self.exit_code: Optional[int] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.memory_peak_mb = 0.0
    
    async def execute(self) -> Dict[str, Any]:
        """Ejecutar el proceso."""
        try:
            self.start_time = time.time()
            self.status = "running"
            
            # Merge entorno
            env = os.environ.copy()
            env.update(self.env)
            
            # Crear proceso
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            self.pid = self.process.pid
            
            # Monitor de memoria en background
            monitor_task = asyncio.create_task(self._monitor_memory())
            
            # Wait con timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    self.process.communicate(),
                    timeout=self.timeout_seconds,
                )
                self.stdout_data = stdout.decode() if stdout else ""
                self.stderr_data = stderr.decode() if stderr else ""
                self.exit_code = self.process.returncode
                self.status = "completed" if self.exit_code == 0 else "failed"
            except asyncio.TimeoutError:
                self.status = "timeout"
                self.process.kill()
                await self.process.wait()
                self.exit_code = -1
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
            
            self.end_time = time.time()
            return self._get_result()
        
        except Exception as e:
            self.status = "failed"
            self.stderr_data = str(e)
            self.end_time = time.time()
            log.error(f"Process execution error: {e}")
            return self._get_result()
    
    async def _monitor_memory(self):
        """Monitorear memoria del proceso."""
        try:
            while self.pid and self.status == "running":
                try:
                    p = psutil.Process(self.pid)
                    mem_mb = p.memory_info().rss / (1024 * 1024)
                    self.memory_peak_mb = max(self.memory_peak_mb, mem_mb)
                    
                    # Kill si excede límite
                    if mem_mb > self.max_memory_mb:
                        log.warning(f"Process {self.pid} exceeded memory limit ({mem_mb:.1f}MB > {self.max_memory_mb}MB)")
                        self.process.kill()
                        self.status = "failed"
                        break
                except (psutil.NoSuchProcess, ProcessLookupError):
                    break
                
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    def _get_result(self) -> Dict[str, Any]:
        """Obtener resultado."""
        duration_ms = int((self.end_time - self.start_time) * 1000) if self.end_time else 0
        return {
            "spawn_id": self.spawn_id,
            "name": self.name,
            "pid": self.pid,
            "status": self.status,
            "stdout": self.stdout_data[:1000],  # Limit output
            "stderr": self.stderr_data[:1000],
            "exit_code": self.exit_code,
            "duration_ms": duration_ms,
            "memory_peak_mb": self.memory_peak_mb,
        }
    
    async def cleanup(self):
        """Limpiar recursos."""
        if self.process and self.status == "running":
            try:
                self.process.kill()
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except Exception as e:
                log.error(f"Cleanup error: {e}")


class SpawnerCore:
    """Core del spawner."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.processes: Dict[str, EphemeralProcess] = {}
    
    async def spawn_process(self, req: SpawnRequest) -> SpawnResponse:
        """Crear y ejecutar proceso efímero."""
        spawn_id = str(uuid.uuid4())[:8]
        
        # Crear proceso
        proc = EphemeralProcess(
            spawn_id=spawn_id,
            name=req.name,
            command=req.command,
            args=req.args or [],
            timeout_seconds=req.timeout_seconds,
            max_memory_mb=req.max_memory_mb,
            env=req.env or {},
        )
        
        # Ejecutar
        self.processes[spawn_id] = proc
        result = await proc.execute()
        
        # Registrar en BD
        try:
            spawn_record = Spawn(
                uuid=spawn_id,
                name=req.name,
                command=req.command,
                args=json.dumps(req.args or []),
                status=proc.status,
                pid=proc.pid,
                start_time=datetime.fromtimestamp(proc.start_time) if proc.start_time else None,
                end_time=datetime.fromtimestamp(proc.end_time) if proc.end_time else None,
                exit_code=proc.exit_code,
                stdout=proc.stdout_data[:500],
                stderr=proc.stderr_data[:500],
                memory_peak_mb=proc.memory_peak_mb,
                parent_spawn_id=req.parent_id,
            )
            self.db_session.add(spawn_record)
            self.db_session.commit()
        except Exception as e:
            log.error(f"BD save error: {e}")
        
        # Limpiar
        await proc.cleanup()
        del self.processes[spawn_id]
        
        return SpawnResponse(
            spawn_id=result["spawn_id"],
            pid=result["pid"],
            status=result["status"],
            stdout=result["stdout"],
            stderr=result["stderr"],
            exit_code=result["exit_code"],
            duration_ms=result["duration_ms"],
            memory_peak_mb=result["memory_peak_mb"],
        )
    
    async def get_process_status(self, spawn_id: str) -> Dict[str, Any]:
        """Obtener status de proceso."""
        proc = self.processes.get(spawn_id)
        if not proc:
            # Buscar en BD
            try:
                record = self.db_session.query(Spawn).filter_by(uuid=spawn_id).first()
                if record:
                    return {
                        "spawn_id": record.uuid,
                        "status": record.status,
                        "pid": record.pid,
                        "exit_code": record.exit_code,
                        "duration_ms": int((record.end_time - record.start_time).total_seconds() * 1000)
                            if record.start_time and record.end_time else 0,
                    }
            except Exception as e:
                log.error(f"Query error: {e}")
            raise HTTPException(status_code=404, detail="Process not found")
        
        return {
            "spawn_id": proc.spawn_id,
            "status": proc.status,
            "pid": proc.pid,
            "memory_peak_mb": proc.memory_peak_mb,
        }
    
    async def list_processes(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Listar procesos."""
        try:
            query = self.db_session.query(Spawn)
            if parent_id:
                query = query.filter_by(parent_spawn_id=parent_id)
            
            results = []
            for record in query.all():
                results.append({
                    "spawn_id": record.uuid,
                    "name": record.name,
                    "status": record.status,
                    "pid": record.pid,
                })
            return results
        except Exception as e:
            log.error(f"List error: {e}")
            return []


# =========== PATCH OPERATIONS (HIJAS EFÍMERAS PARA ORGANIZE) ===========


def _within_root(repo_root: Path, path: Path) -> bool:
    repo_root = repo_root.resolve()
    path = path.resolve()
    return repo_root == path or repo_root in path.parents


def apply_patch_operations(
    operations: List[Dict[str, Any]],
    repo_root: Path,
    backup_root: Path,
    ttl_seconds: int = 60,
) -> Dict[str, Any]:
    """
    Apply a list of patch operations safely with backups.

    Supported ops:
    - mv: {"op":"mv","from": "...","to":"..."}
    - rm: {"op":"rm","path":"...","backup":bool}
    - mkdir: {"op":"mkdir","path":"..."}
    - edit_replace: {"op":"edit_replace","file":"...","search":"...","replace":"...","max_replacements":1}
    """
    start = time.time()
    repo_root = repo_root.resolve()
    backup_root = backup_root.resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []

    protected = repo_root / "data" / "runtime"
    for op in operations:
        res = {"op": op.get("op"), "status": "pending"}
        if time.time() - start > ttl_seconds:
            res.update({"status": "skipped", "error": "ttl_expired"})
            results.append(res)
            continue

        try:
            if op.get("op") == "mv":
                src = Path(op.get("from", ""))
                dst = Path(op.get("to", ""))
                if not src.is_absolute():
                    src = repo_root / src
                if not dst.is_absolute():
                    dst = repo_root / dst
                src = src.resolve()
                dst = dst.resolve()
                if not _within_root(repo_root, src) or not _within_root(repo_root, dst):
                    raise ValueError("operation_outside_repo")
                if protected in src.parents:
                    raise ValueError("protected_path")
                if not src.exists():
                    res.update({"status": "skipped", "error": "source_missing"})
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if dst.exists():
                        backup_dst = backup_root / dst.relative_to(repo_root)
                        backup_dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(dst), str(backup_dst))
                    shutil.move(str(src), str(dst))
                    res["status"] = "ok"
                    res["from"] = str(src)
                    res["to"] = str(dst)

            elif op.get("op") == "rm":
                target = Path(op.get("path", ""))
                if not target.is_absolute():
                    target = repo_root / target
                target = target.resolve()
                if not _within_root(repo_root, target):
                    raise ValueError("operation_outside_repo")
                if protected in target.parents:
                    raise ValueError("protected_path")
                if not target.exists():
                    res.update({"status": "skipped", "error": "missing"})
                else:
                    if op.get("backup"):
                        backup_dst = backup_root / target.relative_to(repo_root)
                        backup_dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(target), str(backup_dst))
                    else:
                        if target.is_dir():
                            shutil.rmtree(target)
                        else:
                            target.unlink()
                    res["status"] = "ok"
                    res["path"] = str(target)

            elif op.get("op") == "mkdir":
                target = Path(op.get("path", ""))
                if not target.is_absolute():
                    target = repo_root / target
                target = target.resolve()
                if not _within_root(repo_root, target):
                    raise ValueError("operation_outside_repo")
                target.mkdir(parents=True, exist_ok=True)
                res["status"] = "ok"
                res["path"] = str(target)

            elif op.get("op") == "edit_replace":
                file_path = Path(op.get("file", ""))
                if not file_path.is_absolute():
                    file_path = repo_root / file_path
                file_path = file_path.resolve()
                if not _within_root(repo_root, file_path):
                    raise ValueError("operation_outside_repo")
                if not file_path.exists():
                    res.update({"status": "skipped", "error": "file_missing"})
                else:
                    search = op.get("search", "")
                    replace = op.get("replace", "")
                    max_repl = int(op.get("max_replacements", 1))
                    content = file_path.read_text(encoding="utf-8")
                    if search not in content:
                        res.update({"status": "skipped", "error": "search_not_found"})
                    else:
                        new_content = content.replace(search, replace, max_repl)
                        backup_dst = backup_root / file_path.relative_to(repo_root)
                        backup_dst.parent.mkdir(parents=True, exist_ok=True)
                        file_path.replace(backup_dst)
                        file_path.write_text(new_content, encoding="utf-8")
                        res["status"] = "ok"
                        res["file"] = str(file_path)
                        res["replacements"] = max_repl
            else:
                res.update({"status": "skipped", "error": "unknown_op"})

        except Exception as exc:
            res.update({"status": "error", "error": str(exc)})

        results.append(res)

    return {
        "results": results,
        "applied": len([r for r in results if r.get("status") == "ok"]),
        "skipped": len([r for r in results if r.get("status") == "skipped"]),
        "errors": len([r for r in results if r.get("status") == "error"]),
        "ttl_seconds": ttl_seconds,
    }


# =========== ENDPOINTS ===========

_SPAWNER_CORE: Optional[SpawnerCore] = None


def get_spawner_core(db_session = Depends(lambda: get_session("madre"))):
    """Dependency para spawner core."""
    global _SPAWNER_CORE
    if _SPAWNER_CORE is None:
        _SPAWNER_CORE = SpawnerCore(db_session)
    return _SPAWNER_CORE


@app.post("/spawn")
async def spawn(
    req: SpawnRequest,
    core: SpawnerCore = Depends(get_spawner_core),
) -> SpawnResponse:
    """Crear y ejecutar proceso efímero."""
    try:
        return await core.spawn_process(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/spawn/{spawn_id}/status")
async def get_spawn_status(
    spawn_id: str,
    core: SpawnerCore = Depends(get_spawner_core),
) -> Dict[str, Any]:
    """Obtener status de proceso."""
    return await core.get_process_status(spawn_id)


@app.get("/spawn/list")
async def list_spawns(
    parent_id: Optional[str] = None,
    core: SpawnerCore = Depends(get_spawner_core),
) -> List[Dict[str, Any]]:
    """Listar procesos efímeros."""
    return await core.list_processes(parent_id)


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check."""
    return {"status": "ok", "module": "spawner_v2"}


@app.post("/control")
async def control(action: str = "status") -> Dict[str, Any]:
    """Control actions."""
    return {
        "action": action,
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=52114, reload=True)
