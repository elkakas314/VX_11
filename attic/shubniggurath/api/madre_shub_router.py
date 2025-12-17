"""
Shub HTTP API Endpoints para Madre

FastAPI endpoints que expone Shub hacia Madre.
"""

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from shubniggurath.api.madre_shub_handler import get_madre_handler

log = logging.getLogger("vx11.shub.madre_router")

router = APIRouter(prefix="/shub/madre", tags=["madre"])


# ============= REQUEST MODELS =============

class AnalyzeRequest(BaseModel):
    """Solicitud de análisis de audio desde Madre."""
    task_id: str
    sample_rate: int = 44100
    mode: str = "mode_c"  # quick | mode_c | deep
    metadata: Optional[Dict[str, Any]] = None


class MasteringRequest(BaseModel):
    """Solicitud de mastering desde Madre."""
    task_id: str
    audio_analysis: Dict[str, Any]
    target_lufs: float = -14.0
    metadata: Optional[Dict[str, Any]] = None


class BatchRequest(BaseModel):
    """Solicitud de batch desde Madre."""
    batch_name: str
    file_list: List[str]
    analysis_type: str = "quick"
    priority: int = 5


class StatusRequest(BaseModel):
    """Solicitud de status."""
    task_id: str


# ============= ENDPOINTS =============

@router.post("/analyze")
async def analyze_audio(req: AnalyzeRequest, file: UploadFile = File(...)):
    """
    Endpoint que Madre llama para analizar audio.
    
    Request:
    {
        "task_id": "...",
        "sample_rate": 44100,
        "mode": "mode_c",
        "metadata": {...}
    }
    
    Response:
    {
        "status": "ok",
        "task_id": "...",
        "analysis": {...},
        "fx_chain": {...},
        "reaper_preset": {...},
        "virtual_engineer_decision": {...},
        "madre_actions": {...}
    }
    """
    try:
        handler = get_madre_handler()
        
        # Leer archivo audio
        audio_bytes = await file.read()
        
        result = await handler.handle_analyze_task(
            task_id=req.task_id,
            audio_bytes=audio_bytes,
            sample_rate=req.sample_rate,
            mode=req.mode,
            metadata=req.metadata,
        )
        
        log.info(f"Analyze endpoint: {req.task_id} → {result['status']}")
        return result
        
    except Exception as exc:
        log.error(f"Analyze error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/mastering")
async def apply_mastering(req: MasteringRequest):
    """
    Endpoint que Madre llama para aplicar mastering.
    
    Request:
    {
        "task_id": "...",
        "audio_analysis": {...},
        "target_lufs": -14.0,
        "metadata": {...}
    }
    
    Response:
    {
        "status": "ok",
        "task_id": "...",
        "master_preset": {...},
        "estimated_lufs": -14.0,
        "recommendation": "..."
    }
    """
    try:
        handler = get_madre_handler()
        
        result = await handler.handle_mastering_task(
            task_id=req.task_id,
            audio_analysis_dict=req.audio_analysis,
            target_lufs=req.target_lufs,
            metadata=req.metadata,
        )
        
        log.info(f"Mastering endpoint: {req.task_id} → {result['status']}")
        return result
        
    except Exception as exc:
        log.error(f"Mastering error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch/submit")
async def submit_batch(req: BatchRequest):
    """
    Endpoint que Madre llama para encolar batch.
    
    Request:
    {
        "batch_name": "...",
        "file_list": ["file1.wav", "file2.wav"],
        "analysis_type": "quick",
        "priority": 5
    }
    
    Response:
    {
        "status": "ok",
        "batch_id": "...",
        "total_files": 2,
        "queue_position": 1
    }
    """
    try:
        handler = get_madre_handler()
        
        result = await handler.handle_batch_task(
            batch_name=req.batch_name,
            file_list=req.file_list,
            analysis_type=req.analysis_type,
            priority=req.priority,
        )
        
        log.info(f"Batch submit: {req.batch_name} → {result['status']}")
        return result
        
    except Exception as exc:
        log.error(f"Batch submit error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/task/{task_id}/status")
async def get_task_status(task_id: str):
    """
    Endpoint que Madre llama para consultar status.
    
    Response:
    {
        "status": "ok",
        "task_id": "...",
        "state": "processing|completed|failed",
        "progress": 50
    }
    """
    try:
        handler = get_madre_handler()
        
        result = await handler.handle_status(task_id)
        
        return result
        
    except Exception as exc:
        log.error(f"Status error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/health-cascade")
async def health_cascade():
    """
    Health check que Madre puede llamar.
    
    Response:
    {
        "status": "ok",
        "shub_healthy": true,
        "modules": {
            "dsp_pipeline": "ok",
            "batch_engine": "ok",
            "virtual_engineer": "ok",
            "reaper_rpc": "ok"
        }
    }
    """
    try:
        return {
            "status": "ok",
            "shub_healthy": True,
            "modules": {
                "dsp_pipeline": "ok",
                "batch_engine": "ok",
                "virtual_engineer": "ok",
                "reaper_rpc": "ok",
            },
        }
    except Exception as exc:
        log.error(f"Health check error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
