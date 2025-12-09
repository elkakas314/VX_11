"""
Shub-Niggurath API Routers — Endpoints REST v1
Integración conversacional sin tocar VX11
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import deepseek
from config.settings import settings
from config.db_schema import (
    get_session,
    ShubProject,
    ShubTrack,
    ShubAnalysis,
    ShubFXChain,
    ShubPreset,
)
from shubniggurath.dsp_pipeline import analyze_audio
import uuid

# ============================================================================
# MODELOS REQUEST/RESPONSE
# ============================================================================

class CommandRequest(BaseModel):
    """Request para comandos del asistente"""
    command: str
    args: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class CommandResponse(BaseModel):
    """Response de comando"""
    status: str
    command: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str


class CopilotEntryRequest(BaseModel):
    """Entry point desde Copilot (VX11 compatible)"""
    user_message: str
    require_action: bool = False
    context: Optional[Dict[str, Any]] = None
    task_id: Optional[str] = None


class CopilotEntryResponse(BaseModel):
    """Response a Copilot"""
    session_id: str
    response: str
    actions_taken: List[Dict[str, Any]] = []
    reasoning: Optional[str] = None
    confidence: float = 0.0
    timestamp: str


# ============================================================================
# HELPERS BD
# ============================================================================


def _ensure_project(session, project_name: str) -> ShubProject:
    proj = session.query(ShubProject).filter_by(name=project_name).first()
    if proj:
        return proj
    proj = ShubProject(project_id=f"proj-{uuid.uuid4().hex[:8]}", name=project_name)
    session.add(proj)
    session.commit()
    return proj


def _ensure_track(session, project: ShubProject, track_name: str, path: Optional[str]) -> ShubTrack:
    track = session.query(ShubTrack).filter_by(project_id=project.project_id, name=track_name).first()
    if track:
        return track
    track = ShubTrack(project_id=project.project_id, name=track_name, file_path=path or "")
    session.add(track)
    session.commit()
    return track


def _store_analysis(session, track: ShubTrack, metrics: Dict[str, Any]) -> ShubAnalysis:
    analysis = ShubAnalysis(
        track_id=track.id,
        rms=metrics.get("rms", 0.0),
        peak=metrics.get("peak", 0.0),
        lufs=metrics.get("lufs", 0.0),
        noise_floor=metrics.get("noise_floor", 0.0),
        dynamic_range=metrics.get("dynamic_range", 0.0),
        clipping=metrics.get("clipping_events", 0),
        notes=";".join(metrics.get("issues", [])),
    )
    session.add(analysis)
    session.commit()
    return analysis


def _store_fx_chain(session, track: ShubTrack, metrics: Dict[str, Any]) -> ShubFXChain:
    chain = ShubFXChain(
        track_id=track.id,
        chain_name="auto_fx",
        steps_json=str(metrics.get("fx_suggestions", [])),
    )
    session.add(chain)
    session.commit()
    return chain


# ============================================================================
# ROUTER: ASSISTANT
# ============================================================================

def create_assistant_router() -> APIRouter:
    """Crear router de asistente"""
    router = APIRouter(prefix="/v1/assistant", tags=["assistant"])
    
    @router.post("/command", response_model=CommandResponse)
    async def post_command(req: CommandRequest) -> CommandResponse:
        """Ejecutar comando en el asistente"""
        return CommandResponse(
            status="processing",
            command=req.command,
            result={
                "queued": True,
                "command_args": req.args,
            },
            timestamp=datetime.utcnow().isoformat(),
        )
    
    @router.get("/status")
    async def get_status():
        """Obtener estado del asistente"""
        return {
            "status": "ok",
            "assistant": "Shub-Niggurath v3.0",
            "mode": "conversational",
            "uptime_seconds": 0,  # Llenar en runtime
        }
    
    @router.post("/copilot-entry", response_model=CopilotEntryResponse)
    async def copilot_entry(req: CopilotEntryRequest) -> CopilotEntryResponse:
        """
        Entry point de Copilot → Shub
        Compatible con VX11 v6.2 conversational flow
        """
        import uuid
        session_id = str(uuid.uuid4())
        
        return CopilotEntryResponse(
            session_id=session_id,
            response=f"Copilot command received: '{req.user_message}'",
            actions_taken=[
                {
                    "action": "queued_for_processing",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ],
            confidence=0.85,
            timestamp=datetime.utcnow().isoformat(),
        )
    
    return router


# ============================================================================
# ROUTER: ANALYSIS
# ============================================================================

def create_analysis_router() -> APIRouter:
    """Crear router de análisis de audio"""
    router = APIRouter(prefix="/v1/analysis", tags=["analysis"])
    
    @router.post("/analyze")
    async def post_analyze(
        project_id: str = Query(...),
        analysis_type: str = Query("full"),
    ):
        """Iniciar análisis de proyecto"""
        return {
            "status": "queued",
            "project_id": project_id,
            "analysis_type": analysis_type,
            "eta_seconds": 30,
        }

    @router.post("/recommend")
    async def post_recommend(audio_summary: str = Query(""), audio_path: Optional[str] = Query(None)):
        """
        Generar recomendaciones de FX combinando métricas DSP + DeepSeek si está disponible.
        """
        dsp_metrics = {}
        if audio_path:
            dsp_metrics = analyze_audio(audio_path)

        try:
            if getattr(settings, "deepseek_api_key", None) and audio_summary:
                result, latency_ms, confidence = await deepseek.call_deepseek_reasoner_async(
                    audio_summary, task_type="audio_analysis", max_reasoning_tokens=1200
                )
                return {
                    "status": "ok",
                    "provider": result.get("provider", "deepseek-r1"),
                    "latency_ms": latency_ms,
                    "confidence": confidence,
                    "recommendations": result,
                    "dsp": dsp_metrics,
                }
            return {"status": "ok", "provider": "local", "recommendations": {"notes": audio_summary[:200]}, "dsp": dsp_metrics}
        except Exception as e:
            return {"status": "error", "error": str(e), "dsp": dsp_metrics}
    
    @router.get("/results/{project_id}")
    async def get_analysis_results(project_id: str):
        """Obtener resultados de análisis"""
        return {
            "project_id": project_id,
            "status": "pending",
            "results": {},
        }

    @router.post("/detail")
    async def analysis_detail(project_name: str = Query("demo"), track_name: str = Query("track"), audio_path: str = Query(...)):
        """
        Devuelve métricas DSP y guarda en BD unificada.
        """
        session = get_session("madre")
        proj = _ensure_project(session, project_name)
        track = _ensure_track(session, proj, track_name, audio_path)
        metrics = analyze_audio(audio_path)
        if metrics.get("status") != "ok":
            raise HTTPException(status_code=400, detail=metrics.get("error", "analysis_failed"))
        _store_analysis(session, track, metrics)
        chain = _store_fx_chain(session, track, metrics)
        return {
            "status": "ok",
            "project_id": proj.project_id,
            "track_id": track.id,
            "metrics": metrics,
            "fx_chain_id": chain.id,
        }
    
    return router


# ============================================================================
# ROUTER: MIXING
# ============================================================================

def create_mixing_router() -> APIRouter:
    """Crear router de mezcla"""
    router = APIRouter(prefix="/v1/mixing", tags=["mixing"])
    
    @router.post("/mix")
    async def post_mix(
        project_id: str = Query(...),
        mode: str = Query("auto"),
    ):
        """Iniciar mezcla automática o manual"""
        return {
            "status": "queued",
            "project_id": project_id,
            "mode": mode,
            "mix_session_id": "mix_" + datetime.utcnow().isoformat(),
        }
    
    @router.get("/mix/{mix_session_id}")
    async def get_mix_status(mix_session_id: str):
        """Obtener estado de mezcla"""
        return {
            "mix_session_id": mix_session_id,
            "status": "processing",
            "progress": 45,
        }
    
    return router


# ============================================================================
# ROUTER: MASTERING
# ============================================================================

def create_mastering_router() -> APIRouter:
    """Crear router de mastering"""
    router = APIRouter(prefix="/v1/mastering", tags=["mastering"])
    
    @router.post("/master")
    async def post_master(
        mix_id: str = Query(...),
        target_loudness: float = Query(-14.0),
    ):
        """Iniciar masterización"""
        return {
            "status": "queued",
            "mix_id": mix_id,
            "target_loudness_lufs": target_loudness,
            "master_session_id": "master_" + datetime.utcnow().isoformat(),
        }
    
    return router


# ============================================================================
# ROUTER: MODE C PIPELINE
# ============================================================================


class ModeCPayload(BaseModel):
    project_name: str
    track_name: str
    audio_path: str
    metadata: Optional[Dict[str, Any]] = None


def create_mode_c_router() -> APIRouter:
    router = APIRouter(prefix="/v1/mode_c", tags=["mode_c"])

    @router.post("/run")
    async def run_mode_c(payload: ModeCPayload):
        """
        Pipeline RAW → DSP → issues → FX chain → JSON VX11.
        """
        session = get_session("madre")
        proj = _ensure_project(session, payload.project_name)
        track = _ensure_track(session, proj, payload.track_name, payload.audio_path)
        metrics = analyze_audio(payload.audio_path)
        if metrics.get("status") != "ok":
            raise HTTPException(status_code=400, detail=metrics.get("error", "analysis_failed"))
        analysis = _store_analysis(session, track, metrics)
        chain = _store_fx_chain(session, track, metrics)
        response = {
            "status": "ok",
            "project_id": proj.project_id,
            "track_id": track.id,
            "analysis_id": analysis.id,
            "metrics": metrics,
            "fx_chain_id": chain.id,
            "issues": metrics.get("issues", []),
        }
        return response

    return router


# ============================================================================
# ROUTER: PREVIEW
# ============================================================================

def create_preview_router() -> APIRouter:
    """Crear router de previsualizaciones"""
    router = APIRouter(prefix="/v1/preview", tags=["preview"])
    
    @router.get("/play/{track_id}")
    async def play_preview(track_id: str):
        """Iniciar reproducción de preview"""
        return {
            "status": "playing",
            "track_id": track_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @router.get("/stop")
    async def stop_preview():
        """Detener reproducción"""
        return {"status": "stopped"}
    
    return router


# ============================================================================
# ROUTER: MAINTENANCE
# ============================================================================

def create_maintenance_router() -> APIRouter:
    """Crear router de mantenimiento"""
    router = APIRouter(prefix="/v1/maintenance", tags=["maintenance"])
    
    @router.post("/cleanup")
    async def post_cleanup(
        cache: bool = Query(True),
        logs: bool = Query(False),
    ):
        """Ejecutar limpieza del sistema"""
        return {
            "status": "cleaning",
            "cache_cleared": cache,
            "logs_rotated": logs,
        }
    
    @router.get("/health")
    async def get_health():
        """Health check de Shub"""
        return {
            "status": "healthy",
            "service": "shub-niggurath",
            "version": "3.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    return router


# ============================================================================
# ROUTER: HEADPHONES
# ============================================================================

def create_headphones_router() -> APIRouter:
    """Crear router de control de auriculares"""
    router = APIRouter(prefix="/v1/headphones", tags=["headphones"])
    
    @router.post("/calibrate")
    async def calibrate_headphones():
        """Calibrar auriculares"""
        return {
            "status": "calibrating",
            "eta_seconds": 60,
        }
    
    @router.get("/profile")
    async def get_headphone_profile():
        """Obtener perfil de auriculares actual"""
        return {
            "profile": "default",
            "calibration_date": None,
        }
    
    return router


# ============================================================================
# AGGREGADOR DE ROUTERS
# ============================================================================

def create_all_routers() -> List[tuple]:
    """
    Crear y retornar lista de (router, prefijo) para montaje en main.py
    """
    return [
        (create_assistant_router(), ""),
        (create_analysis_router(), ""),
        (create_mixing_router(), ""),
        (create_mastering_router(), ""),
        (create_preview_router(), ""),
        (create_maintenance_router(), ""),
        (create_headphones_router(), ""),
    ]


__all__ = [
    "create_all_routers",
    "create_assistant_router",
    "create_analysis_router",
    "create_mixing_router",
    "create_mastering_router",
    "create_preview_router",
    "create_maintenance_router",
    "create_headphones_router",
]
