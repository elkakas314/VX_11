"""
Hermes v6.3 - Gestor de modelos locales y CLI externos.
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.settings import settings
from config.tokens import load_tokens, get_token
from config.forensics import write_log
from config.db_schema import get_session, ModelsLocal, ModelsRemoteCLI, ModelRegistry, CLIRegistry

# FASE 6: Hermes Shub Registration (Wiring)
from switch.hermes_shub_registration import get_hermes_shub_registrar

REPO_ROOT = Path(__file__).resolve().parents[2]
models_base = Path(settings.MODELS_PATH)
if not models_base.exists() or not os.access(models_base, os.W_OK):
    models_base = REPO_ROOT / "models"
if not models_base.exists() or not os.access(models_base, os.W_OK):
    models_base = REPO_ROOT / "build" / "artifacts" / "models"
models_base.mkdir(parents=True, exist_ok=True)
MODELS_DIR = (models_base / "hermes").resolve()
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_TTL_SECONDS = 24 * 3600  # limpiar modelos antiguos (TTL básico)
CLI_TOKENS: Dict[str, Dict[str, Any]] = {
    "cli-remote": {"limit_daily": 1000, "used": 0, "status": "enabled"},
}
CLI_STATUS: Dict[str, Dict[str, Any]] = {
    "cli-remote": {"latency_ms": 0, "last_used": None, "healthy": True},
}
_ALLOWED_BASE = MODELS_DIR
MAX_MODEL_BYTES = 2 * 1024 * 1024 * 1024  # 2GB límite canónico

load_tokens()
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


def check_token(x_vx11_token: str = Header(None), request: Request = None):
    if request and (request.url.path == "/health" or request.url.path.startswith("/metrics")):
        return True
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=401, detail="auth_required")
    return True


app = FastAPI(title="VX11 Hermes v6.3", dependencies=[Depends(check_token)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar categorías de audio para Shub
AUDIO_CATEGORIES = {
    "audio_analysis": "Análisis de audio (LUFS, espectro, dinámicas)",
    "mix": "Mezcla automática de pistas",
    "master": "Masterización profesional",
    "dsp": "Procesamiento DSP",
    "spectral": "Análisis espectral avanzado",
    "repair": "Reparación de audio",
    "fx_chain": "Generación de cadenas de efectos"
}


@app.get("/metrics{suffix:path}")
async def metrics_stub(suffix: str = ""):
    """Lightweight stub to satisfy metrics probes without noisy 404s."""
    return {"status": "ok", "module": "hermes", "metrics": "stub", "path": suffix or "/metrics"}


class ModelRegister(BaseModel):
    name: str
    category: str = "general"
    url: str = ""
    size_mb: int = 0
    compatibility: str = "cpu"
    task_type: Optional[str] = None
    source: str = "local"


class SearchQuery(BaseModel):
    category: str = "general"
    max_size_mb: int = 2000


class SearchResult(BaseModel):
    name: str
    source: str
    size_bytes: int
    tags: List[str] = []
    model_type: str = "llm"
    score: float = 0.0
    task_type: Optional[str] = None


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _upsert_model_registry(session: Session, name: str, path: str, category: str, size_bytes: int):
    """Sincroniza tabla model_registry con models_local."""
    try:
        rec = session.query(ModelRegistry).filter(ModelRegistry.name == name).first()
        if not rec:
            rec = ModelRegistry(name=name, provider="hermes_local", type=category, size_bytes=size_bytes)
        rec.path = path
        rec.provider = rec.provider or "hermes_local"
        rec.type = category or "general"
        rec.size_bytes = size_bytes
        rec.available = True
        rec.updated_at = datetime.utcnow()
        session.add(rec)
    except Exception as exc:
        write_log("hermes", f"registry_sync_error:{name}:{exc}", level="WARNING")


async def _search_hf_models(query: str, max_size: int) -> List[SearchResult]:
    """Crawler simple contra HuggingFace API (<2GB)."""
    token = get_token("HF_TOKEN") or os.environ.get("HF_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"search": query, "limit": 20, "full": "true"}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get("https://huggingface.co/api/models", params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            results = []
            for model in data:
                size_bytes = 0
                for sibling in model.get("siblings", []):
                    size = sibling.get("size") or "0"
                    if isinstance(size, str) and size.lower().endswith("gb"):
                        size_bytes += int(float(size.replace("GB", "").strip()) * 1024 * 1024 * 1024)
                if size_bytes and size_bytes > max_size:
                    continue
                results.append(
                    SearchResult(
                        name=model.get("modelId", "").split("/")[-1],
                        source="huggingface",
                        size_bytes=size_bytes or max_size,
                        tags=model.get("tags", []),
                        model_type=model.get("pipeline_tag") or "llm",
                        score=model.get("likes", 0) / 100 if model.get("likes") else 0.0,
                    ).model_dump()
                )
            return results
    except Exception as exc:
        write_log("hermes", f"hf_search_fallback:{exc}", level="WARNING")
        return [
            SearchResult(name=f"{query}-lite", source="huggingface", size_bytes=max_size // 2, tags=["fallback"]).model_dump(),
        ]


async def _search_openrouter_models(query: str, max_size: int) -> List[SearchResult]:
    """Placeholder para OpenRouter: retorna catálogo reducido sin exceder 2GB."""
    token = get_token("OPENROUTER_TOKEN") or os.environ.get("OPENROUTER_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            r = await client.get("https://openrouter.ai/api/v1/models", headers=headers)
            if r.status_code == 200:
                models = r.json().get("data", [])
                results = []
                for m in models:
                    name = m.get("id", "")
                    if query.lower() in name.lower():
                        results.append(
                            SearchResult(
                                name=name,
                                source="openrouter",
                                size_bytes=min(max_size, MAX_MODEL_BYTES),
                                tags=m.get("tags", []),
                                model_type=m.get("type", "llm"),
                                score=float(m.get("pricing", {}).get("prompt", 0)),
                            ).model_dump()
                        )
                return results[:5]
    except Exception as exc:
        write_log("hermes", f"openrouter_search_warn:{exc}", level="WARNING")
    return [
        SearchResult(name=f"{query}-remote", source="openrouter", size_bytes=max_size // 2, tags=["remote"]).model_dump(),
    ]


def _prune_models(session: Session, limit: int = 30):
    """
    Enforce max models and TTL simple using timestamps.
    """
    cutoff = datetime.utcnow().timestamp() - MODEL_TTL_SECONDS
    rows = session.query(ModelsLocal).order_by(ModelsLocal.updated_at or ModelsLocal.id).all()
    for r in rows:
        ts = getattr(r, "updated_at", None) or getattr(r, "created_at", None)
        if ts and ts.timestamp() < cutoff:
            session.delete(r)
    session.flush()
    rows = session.query(ModelsLocal).order_by(ModelsLocal.updated_at or ModelsLocal.id).all()
    if len(rows) > limit:
        for r in rows[:-limit]:
            session.delete(r)
    session.flush()


async def _discover_cli_with_playwright(cli_name: str) -> Dict[str, Any]:
    """
    Stub de descubrimiento CLI (Playwright opcional).
    En entorno ultra-low-memory devolvemos metadata mínima.
    """
    return {
        "name": cli_name,
        "install_command": f"pip install {cli_name}",
        "documentation": f"https://pypi.org/project/{cli_name}/",
        "discovered_at": datetime.utcnow().isoformat(),
    }


def local_models() -> List[Dict[str, Any]]:
    """Retorna modelos locales sin metadatos internos de SQLAlchemy."""
    session: Session = get_session("vx11")
    out: List[Dict[str, Any]] = []
    try:
        rows = session.query(ModelsLocal).all()
        for r in rows:
            data = {k: v for k, v in r.__dict__.items() if not k.startswith("_")}
            out.append(data)
    finally:
        session.close()
    return out


def _best_models_for(task_type: str, max_size_mb: int = 2048) -> List[Dict[str, Any]]:
    """Filtra modelos por task_type/categoría y límite de tamaño (<2GB)."""
    session: Session = get_session("vx11")
    try:
        rows = (
            session.query(ModelsLocal)
            .filter(ModelsLocal.size_mb <= max_size_mb)
            .filter(ModelsLocal.status != "deprecated")
            .filter((ModelsLocal.category == task_type) | (ModelsLocal.category == "general"))
            .filter(ModelsLocal.size_mb <= max_size_mb)
            .order_by(ModelsLocal.size_mb.asc())
            .limit(5)
            .all()
        )
        return [
            {
                "name": r.name,
                "category": r.category,
                "size_mb": r.size_mb,
                "path": r.path,
                "compatibility": r.compatibility,
                "task_type": task_type,
            }
            for r in rows
        ]
    finally:
        session.close()


@app.get("/health")
async def health():
    return {"status": "ok", "module": "hermes"}


@app.post("/hermes/execute")
async def hermes_execute(body: Dict[str, Any]):
    """
    Ejecutor ligero: registra uso de modelos/CLI.
    Rutea por provider si está disponible; mantiene stub seguro si no hay backends reales.
    """
    session: Session = get_session("vx11")
    try:
        # Registrar uso en registry si hay selección sugerida
        selection = body.get("selection", {}) or {}
        model_name = selection.get("model") or selection.get("engine_selected")
        provider = selection.get("provider") or model_name
        if model_name:
            rec = session.query(ModelRegistry).filter_by(name=model_name).first()
            if rec:
                rec.usage = (rec.usage or 0) + 1
                rec.updated_at = datetime.utcnow()
                session.add(rec)
                session.commit()
        # Ruteo mínimo: si provider es shub/shub-audio, delegar
        if provider in {"shub", "shub-audio"}:
            try:
                async with httpx.AsyncClient(timeout=10.0, headers={settings.token_header: get_token("VX11_GATEWAY_TOKEN") or settings.api_token}) as client:
                    resp = await client.post(
                        f"{settings.shub_url.rstrip('/')}/shub/execute",
                        json={
                            "task_id": selection.get("task_id"),
                            "task_type": body.get("task_type") or "audio",
                            "payload": body,
                        },
                    )
                    return resp.json()
            except Exception as exc:
                write_log("hermes", f"shub_route_error:{exc}", level="WARNING")
                return {"status": "stub", "engine": "shub", "details": f"shub route failed: {exc}"}

        # Fallback stub (no IA pesada en build ligero)
        return {
            "status": "stub",
            "engine": provider or "hermes_local",
            "echo": body.get("command") or body.get("prompt"),
            "model": model_name or "general-7b",
            "metadata": body.get("metadata", {}),
        }
    except Exception as exc:
        write_log("hermes", f"execute_error:{exc}", level="ERROR")
        return {"status": "error", "error": str(exc)}
    finally:
        session.close()


@app.get("/hermes/list")
async def list_models():
    session: Session = get_session("vx11")
    try:
        rows = session.query(ModelsLocal).all()
        cleaned = [{k: v for k, v in row.__dict__.items() if not k.startswith("_")} for row in rows]
        return {"models": cleaned, "cli_tokens": CLI_TOKENS, "cli_status": CLI_STATUS}
    finally:
        session.close()


@app.get("/hermes/cli/status")
async def cli_status():
    return {"cli_tokens": CLI_TOKENS, "cli_status": CLI_STATUS}


@app.get("/hermes/models/best")
async def models_best(task_type: str = "general", max_size_mb: int = 2048):
    """Devuelve candidatos de modelo <2GB para un task_type (registry lite)."""
    return {"models": _best_models_for(task_type, max_size_mb)}


# VX11 v6.7 – catalog summary (lightweight, backward-compatible)
@app.get("/hermes/catalog/summary")
async def catalog_summary(max_mb: int = 2048):
    session: Session = get_session("vx11")
    try:
        models = (
            session.query(ModelsLocal)
            .filter(ModelsLocal.size_mb <= max_mb)
            .filter(ModelsLocal.status != "deprecated")
            .all()
        )
        local = [
            {
                "name": m.name,
                "size_mb": m.size_mb,
                "category": m.category,
                "status": m.status,
                "cost_per_token": 0.0,
                "latency_ms": 0,
                "usage": getattr(m, "usage", 0),
            }
            for m in models
        ]
        return {
            "local": local,
            "cli": [],
            "remote": [],
            "limits": {"max_models": 30, "max_mb": max_mb},
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        session.close()


@app.post("/hermes/register_model")
async def register_model(body: ModelRegister):
    # Simulación de descarga mínima
    target_path = MODELS_DIR / f"{body.name}.bin"
    target_path.write_bytes(b"")  # placeholder
    size_mb = body.size_mb or int(target_path.stat().st_size / (1024 * 1024) + 1)
    if size_mb > 2048:
        raise HTTPException(status_code=400, detail="model_too_large")
    file_hash = _hash_file(target_path)

    session: Session = get_session("vx11")
    try:
        _prune_models(session, limit=30)
        model = session.query(ModelsLocal).filter_by(name=body.name).first()
        if not model:
            model = ModelsLocal(name=body.name)
        model.path = str(target_path)
        model.size_mb = size_mb
        model.hash = file_hash
        model.category = body.category
        model.status = "available"
        model.compatibility = body.compatibility
        model.task_type = body.task_type or body.category
        session.add(model)
        _upsert_model_registry(
            session,
            name=body.name,
            path=str(target_path),
            category=body.category,
            size_bytes=size_mb * 1024 * 1024,
        )
        session.commit()
        write_log("hermes", f"registered_model:{body.name}")
        return {"status": "ok", "name": body.name, "path": str(target_path)}
    finally:
        session.close()


@app.post("/hermes/search_models")
async def search_models(body: SearchQuery):
    session: Session = get_session("vx11")
    try:
        rows = (
            session.query(ModelsLocal)
            .filter(ModelsLocal.category == body.category)
            .filter(ModelsLocal.size_mb <= body.max_size_mb)
            .filter(ModelsLocal.status != "deprecated")
            .all()
        )
        local = [r.__dict__ for r in rows]
    finally:
        session.close()

    remote_hf = await _search_hf_models(body.category, min(body.max_size_mb * 1024 * 1024, MAX_MODEL_BYTES))
    remote_or = await _search_openrouter_models(body.category, min(body.max_size_mb * 1024 * 1024, MAX_MODEL_BYTES))

    return {"local": local, "remote": remote_hf + remote_or}


@app.post("/hermes/sync")
async def sync_models():
    """
    Sincroniza registros locales con BD unificada, limita a 30 modelos y busca reemplazos <2GB.
    """
    session: Session = get_session("vx11")
    removed = []
    try:
        rows = session.query(ModelsLocal).order_by(ModelsLocal.downloaded_at.asc()).all()
        # Deprecate extras
        if len(rows) > 30:
            deprecated = rows[:-30]
            for m in deprecated:
                m.status = "deprecated"
                removed.append(m.name)
                # Intento de eliminar archivo físico para liberar memoria
                try:
                    if m.path and Path(m.path).exists():
                        Path(m.path).unlink()
                except Exception:
                    pass
        # Refrescar registry
        for m in rows:
            _upsert_model_registry(
                session,
                name=m.name,
                path=m.path,
                category=m.category,
                size_bytes=m.size_mb * 1024 * 1024,
            )
        session.commit()
    finally:
        session.close()

    # Buscar mejoras rápidas (async) para categorías presentes
    categories = list({m.get("category", "general") for m in local_models()})
    improvements = {}
    for cat in categories:
        remote = await _search_hf_models(cat, MAX_MODEL_BYTES)
        if remote:
            improvements[cat] = remote[:3]

    return {"status": "ok", "removed": removed, "improvements": improvements}


@app.post("/hermes/reindex")
async def reindex():
    """Recompute size/hash for all entries."""
    session: Session = get_session("vx11")
    try:
        rows = session.query(ModelsLocal).all()
        count = 0
        for r in rows:
            p = Path(r.path)
            if p.exists():
                r.size_mb = int(p.stat().st_size / (1024 * 1024) + 1)
                count += 1
                _upsert_model_registry(
                    session,
                    name=r.name,
                    path=r.path,
                    category=r.category,
                    size_bytes=r.size_mb * 1024 * 1024,
                )
        session.commit()
        return {"status": "ok", "reindexed": count}
    finally:
        session.close()


@app.get("/hermes/cli/list")
async def cli_list():
    session: Session = get_session("vx11")
    try:
        rows = session.query(ModelsRemoteCLI).all()
        cleaned = [{k: v for k, v in r.__dict__.items() if not k.startswith("_")} for r in rows]
        return {"cli": cleaned}
    finally:
        session.close()


@app.get("/hermes/cli/candidates")
async def cli_candidates(task_type: Optional[str] = None):
    """CLIs registradas en CLIRegistry filtradas opcionalmente por task_type."""
    session: Session = get_session("vx11")
    try:
        q = session.query(CLIRegistry)
        if task_type:
            q = q.filter(CLIRegistry.cli_type == task_type)
        rows = q.all()
        cleaned = [{k: v for k, v in row.__dict__.items() if not k.startswith("_")} for row in rows]
        return {"cli": cleaned}
    finally:
        session.close()


@app.get("/hermes/cli/available")
async def cli_available():
    return await cli_list()


@app.post("/hermes/cli/renew")
async def cli_renew():
    # Placeholder for automated renewal via Playwright
    return {"status": "ok", "message": "renewal scheduled"}


@app.post("/hermes/cli/register")
async def cli_register(
    token: Optional[str] = None,
    limit_daily: int = 1000,
    limit_weekly: int = 5000,
    task_type: str = "general",
    provider: str = "external",
    cli_name: Optional[str] = None,
):
    """
    Registra CLI remoto y lo sincroniza con CLIRegistry para Switch/Hermes.
    """
    session: Session = get_session("vx11")
    try:
        if token:
            cli_remote = session.query(ModelsRemoteCLI).filter_by(token=token).first()
            if not cli_remote:
                cli_remote = ModelsRemoteCLI(token=token)
            cli_remote.limit_daily = limit_daily
            cli_remote.limit_weekly = limit_weekly
            cli_remote.task_type = task_type
            cli_remote.provider = provider
            session.add(cli_remote)

        if cli_name:
            meta = await _discover_cli_with_playwright(cli_name)
            cli_entry = session.query(CLIRegistry).filter(CLIRegistry.name == cli_name).first()
            if not cli_entry:
                cli_entry = CLIRegistry(name=cli_name, cli_type="external", token_config_key="GITHUB_TOKEN")
            cli_entry.bin_path = meta.get("install_command")
            cli_entry.available = True
            cli_entry.notes = json.dumps(meta)
            cli_entry.rate_limit_daily = limit_daily
            cli_entry.updated_at = datetime.utcnow()
            session.add(cli_entry)

        session.commit()
        return {"status": "ok", "token": token, "cli": cli_name}
    finally:
        session.close()


# ========== VX11 v7.0 NUEVOS ENDPOINTS ==========

@app.get("/hermes/resources")
async def hermes_resources():
    """
    Retorna catálogo consolidado de recursos disponibles (CLI + modelos).
    """
    session: Session = get_session("vx11")
    try:
        # Modelos locales
        local_models_list = (
            session.query(ModelsLocal)
            .filter(ModelsLocal.size_mb <= 2048)
            .filter(ModelsLocal.status != "deprecated")
            .all()
        )
        
        # CLI providers (desde ModelsRemoteCLI)
        cli_list = session.query(ModelsRemoteCLI).filter(ModelsRemoteCLI.status == "active").all()
        
        # CLIRegistry entries
        cli_registry_list = session.query(CLIRegistry).filter(CLIRegistry.available == True).all()  # noqa: E712
        
        return {
            "status": "ok",
            "local_models": [
                {
                    "name": m.name,
                    "size_mb": m.size_mb,
                    "category": m.category,
                    "status": m.status,
                    "compatibility": m.compatibility,
                }
                for m in local_models_list
            ],
            "cli_providers": [
                {
                    "provider": c.provider,
                    "task_type": c.task_type,
                    "limit_daily": c.limit_daily,
                    "limit_weekly": c.limit_weekly,
                }
                for c in cli_list
            ],
            "cli_registry": [
                {
                    "name": c.name,
                    "cli_type": c.cli_type,
                    "available": c.available,
                }
                for c in cli_registry_list
            ],
        }
    finally:
        session.close()


@app.post("/hermes/register/cli")
async def register_cli_v2(body: Dict[str, Any]):
    """
    Registra un CLI provider mejorado (DeepSeek R1, OpenRouter, etc.).
    Esperado:
    {
        "name": "deepseek_r1",
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "task_types": "chat,audio-engineer",
        "daily_limit_tokens": 100000,
        "monthly_limit_tokens": 3000000,
    }
    """
    from config.db_schema import CLIProvider
    
    session: Session = get_session("vx11")
    try:
        name = body.get("name", "")
        if not name:
            raise ValueError("name required")
        
        # Buscar existente
        provider = session.query(CLIProvider).filter_by(name=name).first()
        if not provider:
            provider = CLIProvider(name=name)
        
        provider.base_url = body.get("base_url", "")
        provider.api_key_env = body.get("api_key_env", "")
        provider.task_types = body.get("task_types", "chat")
        provider.daily_limit_tokens = body.get("daily_limit_tokens", 100000)
        provider.monthly_limit_tokens = body.get("monthly_limit_tokens", 3000000)
        provider.reset_hour_utc = body.get("reset_hour_utc", 0)
        provider.enabled = body.get("enabled", True)
        
        session.add(provider)
        session.commit()
        
        write_log("hermes", f"cli_registered:{name}")
        return {
            "status": "ok",
            "message": f"CLI '{name}' registered",
            "provider": name,
        }
    except Exception as e:
        session.rollback()
        write_log("hermes", f"cli_register_error:{e}", level="ERROR")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


@app.post("/hermes/register/local_model")
async def register_local_model_v2(body: Dict[str, Any]):
    """
    Registra un modelo local mejorado.
    Esperado:
    {
        "name": "llama2-7b",
        "engine": "llama.cpp",
        "path": "/app/models/llama2-7b.gguf",
        "size_bytes": 3900000000,
        "task_type": "chat",
        "max_context": 4096,
        "compatibility": "cpu"
    }
    """
    from config.db_schema import LocalModelV2
    
    session: Session = get_session("vx11")
    try:
        name = body.get("name", "")
        if not name:
            raise ValueError("name required")
        
        # Buscar existente
        model = session.query(LocalModelV2).filter_by(name=name).first()
        if not model:
            model = LocalModelV2(
                name=name,
                engine=body.get("engine", "unknown"),
                path=body.get("path", ""),
                size_bytes=body.get("size_bytes", 0),
                task_type=body.get("task_type", "general"),
            )
        
        model.max_context = body.get("max_context", 2048)
        model.compatibility = body.get("compatibility", "cpu")
        model.enabled = body.get("enabled", True)
        
        session.add(model)
        session.commit()
        
        write_log("hermes", f"local_model_registered:{name}")
        
        return {"status": "ok", "model": name, "registered": True}
    finally:
        session.close()


@app.post("/hermes/register/shub")
async def register_shub_resource():
    """
    FASE 6: Registra Shub-Niggurath como recurso de DSP remoto en catálogo de Hermes.
    
    Response:
    {
        "status": "ok",
        "resource_id": "remote_audio_dsp",
        "registered": true,
        "metadata": {...}
    }
    """
    try:
        registrar = get_hermes_shub_registrar()
        result = await registrar.register_shub()
        
        write_log("hermes", f"shub_registration:{result.get('status')}")
        return result
        
    except Exception as exc:
        write_log("hermes", f"shub_registration_error:{exc}", level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/hermes/shub/health")
async def shub_health_check():
    """
    FASE 6: Health check de Shub desde Hermes.
    
    Response:
    {
        "status": "ok",
        "health": "ok|degraded|offline",
        "modules": {...}
    }
    """
    try:
        registrar = get_hermes_shub_registrar()
        health = await registrar.report_shub_health()
        
        return health
        
    except Exception as exc:
        write_log("hermes", f"shub_health_error:{exc}", level="ERROR")
        return {
            "status": "error",
            "health": "offline",
            "error": str(exc),
        }
        return {
            "status": "ok",
            "message": f"Model '{name}' registered",
            "model": name,
            "size_bytes": model.size_bytes,
        }
    except Exception as e:
        session.rollback()
        write_log("hermes", f"local_model_register_error:{e}", level="ERROR")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


@app.post("/hermes/discover")
async def discover():
    """
    Dispara descubrimiento de modelos/CLI (stub avanzado).
    Implementa búsqueda en HuggingFace y OpenRouter si hay tokens.
    """
    session: Session = get_session("vx11")
    try:
        results = {
            "discovered_models": [],
            "discovered_cli": [],
        }
        
        # Buscar en HF
        hf_results = await _search_hf_models("gguf-model", max_size=2 * 1024 * 1024 * 1024)
        results["discovered_models"].extend(hf_results[:3])
        
        # Buscar en OpenRouter
        or_results = await _search_openrouter_models("gpt", max_size=2 * 1024 * 1024 * 1024)
        results["discovered_models"].extend(or_results[:3])
        
        # Registrar descubrimientos
        for model in results["discovered_models"][:2]:
            try:
                name = model.get("name", "")
                if name:
                    existing = session.query(ModelRegistry).filter_by(name=name).first()
                    if not existing:
                        registry_entry = ModelRegistry(
                            name=name,
                            provider=model.get("source", "unknown"),
                            type=model.get("model_type", "general"),
                            size_bytes=model.get("size_bytes", 0),
                        )
                        session.add(registry_entry)
            except Exception as e:
                write_log("hermes", f"discovery_register_error:{e}", level="WARNING")
        
        session.commit()
        write_log("hermes", f"discover_completed:found {len(results['discovered_models'])} models")
        
        return {
            "status": "ok",
            "discovered_count": len(results["discovered_models"]),
            "results": results,
        }
    except Exception as e:
        session.rollback()
        write_log("hermes", f"discover_error:{e}", level="ERROR")
        return {
            "status": "error",
            "error": str(e),
            "discovered_count": 0,
        }
    finally:
        session.close()


# ========== BACKGROUND WORKERS ==========

async def _hermes_background_tasks():
    """
    Worker en background para reseteo de límites y salud de CLI.
    Se ejecuta cada 3600s (1 hora).
    """
    from config.db_schema import CLIProvider
    import time
    
    write_log("hermes", "background_worker_started")
    
    while True:
        try:
            await asyncio.sleep(3600)  # Ejecutar cada hora
            
            session: Session = get_session("vx11")
            try:
                now = datetime.utcnow()
                hour = now.hour
                
                # Resetear contadores diarios si es la hora indicada
                for provider in session.query(CLIProvider).all():
                    if provider.reset_hour_utc == hour and (now - provider.last_reset_at).seconds > 3600:
                        provider.tokens_used_today = 0
                        provider.last_reset_at = now
                        session.add(provider)
                
                session.commit()
                write_log("hermes", f"background_reset_completed:hour={hour}")
            finally:
                session.close()
        except Exception as e:
            write_log("hermes", f"background_worker_error:{e}", level="ERROR")
            await asyncio.sleep(60)  # Reintentar en 60s


@app.on_event("startup")
async def startup_event():
    """Iniciar workers en background al startup."""
    asyncio.create_task(_hermes_background_tasks())
