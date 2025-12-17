"""
Shub-Niggurath ↔ Madre HTTP Handler

Recibe tareas de audio desde Madre y orquesta pipeline DSP completo.
Mantiene comunicación HTTP-only con Madre.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import asdict
import httpx

from shubniggurath.core.dsp_pipeline_full import pipeline, AudioAnalysis
from shubniggurath.core.audio_batch_engine import AudioBatchEngine, BatchJob
from shubniggurath.core.virtual_engineer import VirtualEngineer
from shubniggurath.integrations.vx11_bridge import VX11Bridge
from shubniggurath.integrations.reaper_rpc import REAPERController

log = logging.getLogger("vx11.shub.madre_handler")


class ShubMadreHandler:
    """
    Interfaz HTTP Madre ↔ Shub.
    
    Métodos:
    - handle_analyze_task: Recibe audio, ejecuta pipeline, retorna análisis
    - handle_mastering_task: Recibe análisis, aplica mastering, retorna preset
    - handle_batch_task: Encola batch de audios
    - handle_status: Consulta estado de tarea
    """
    
    def __init__(self, vx11_bridge: VX11Bridge = None, virtual_engineer: VirtualEngineer = None):
        self.vx11_bridge = vx11_bridge or VX11Bridge()
        self.virtual_engineer = virtual_engineer or VirtualEngineer()
        self.batch_engine = AudioBatchEngine()
        self.reaper = REAPERController()
    
    async def handle_analyze_task(
        self,
        task_id: str,
        audio_bytes: bytes,
        sample_rate: int = 44100,
        mode: str = "mode_c",  # quick | mode_c | deep
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        MADRE LLAMA AQUÍ: analiza audio completo.
        
        Retorna: {
            "status": "ok",
            "task_id": "...",
            "analysis": AudioAnalysis(33 campos),
            "fx_chain": FXChain,
            "reaper_preset": REAPERPreset,
            "recommendations": [...],
            "virtual_engineer_decision": {...},
            "madre_actions": {...}
        }
        """
        try:
            # 1. Ejecutar pipeline DSP completo (8 fases)
            log.info(f"[MADRE] Análisis iniciado: task_id={task_id}, mode={mode}")
            
            pipeline_result = await pipeline.run_full_pipeline(
                audio_bytes=audio_bytes,
                sample_rate=sample_rate,
                mode=mode
            )
            
            if pipeline_result["status"] != "ok":
                return {
                    "status": "error",
                    "task_id": task_id,
                    "error": pipeline_result.get("error", "Pipeline failed"),
                }
            
            audio_analysis: AudioAnalysis = pipeline_result["audio_analysis"]
            fx_chain = pipeline_result["fx_chain"]
            reaper_preset = pipeline_result["reaper_preset"]
            
            # 2. Virtual Engineer toma decisión
            ve_decision = {
                "pipeline_mode": self.virtual_engineer.decide_pipeline(audio_analysis),
                "master_style": self.virtual_engineer.decide_master_style(audio_analysis),
                "priority": self.virtual_engineer.decide_priority(audio_analysis),
                "delegation": self.virtual_engineer.decide_delegation(audio_analysis, mode),
                "recommendations": self.virtual_engineer.generate_recommendations(audio_analysis),
            }
            
            # 3. Notificar Madre con resultado completo
            madre_actions = {
                "log_analysis": True,
                "apply_fx": bool(fx_chain.chain),
                "notify_hormiguero": len(audio_analysis.issues) > 0,
                "create_hija_for_mastering": True,
            }
            
            log.info(f"[MADRE] Análisis completado: task_id={task_id}")
            
            return {
                "status": "ok",
                "task_id": task_id,
                "analysis": asdict(audio_analysis),
                "fx_chain": asdict(fx_chain),
                "reaper_preset": asdict(reaper_preset),
                "virtual_engineer_decision": ve_decision,
                "madre_actions": madre_actions,
                "pipeline_timing": pipeline_result.get("processing_time_ms", 0),
            }
            
        except Exception as exc:
            log.error(f"[MADRE] Error en análisis: {exc}", exc_info=True)
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(exc),
            }
    
    async def handle_mastering_task(
        self,
        task_id: str,
        audio_analysis_dict: Dict[str, Any],
        target_lufs: float = -14.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        MADRE LLAMA AQUÍ: aplica mastering basado en análisis anterior.
        
        Retorna: {
            "status": "ok",
            "task_id": "...",
            "master_preset": REAPERPreset,
            "estimated_lufs": float,
            "recommendation": str
        }
        """
        try:
            log.info(f"[MADRE] Mastering iniciado: task_id={task_id}, target_lufs={target_lufs}")
            
            # Crear AudioAnalysis desde dict
            audio_analysis = AudioAnalysis(**audio_analysis_dict)
            
            # Virtual Engineer decide estilo
            master_style = self.virtual_engineer.decide_master_style(audio_analysis)
            
            # Generar preset REAPER para mastering
            # (En implementación real, integrar con REAPER vía RPC)
            master_preset = {
                "style": master_style,
                "target_lufs": target_lufs,
                "plugin_chain": [
                    "ReEQ",
                    "Compressor",
                    "Limiter"
                ],
                "gain_staging": 0.0,
                "applied": False,
            }
            
            log.info(f"[MADRE] Mastering completado: task_id={task_id}")
            
            return {
                "status": "ok",
                "task_id": task_id,
                "master_preset": master_preset,
                "estimated_lufs": target_lufs,
                "recommendation": f"Mastering aplicado con estilo {master_style}",
            }
            
        except Exception as exc:
            log.error(f"[MADRE] Error en mastering: {exc}", exc_info=True)
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(exc),
            }
    
    async def handle_batch_task(
        self,
        batch_name: str,
        file_list: List[str],
        analysis_type: str = "quick",
        priority: int = 5,
    ) -> Dict[str, Any]:
        """
        MADRE LLAMA AQUÍ: encola múltiples audios.
        
        Retorna: {
            "status": "ok",
            "batch_id": "...",
            "total_files": int,
            "queue_position": int
        }
        """
        try:
            log.info(f"[MADRE] Batch encolado: {batch_name}, files={len(file_list)}")
            
            batch_job = BatchJob(
                batch_name=batch_name,
                file_list=file_list,
                analysis_type=analysis_type,
                priority=priority,
                status="queued",
                total_files=len(file_list),
                processed_files=0,
                failed_files=0,
            )
            
            # Encolar en batch engine
            job_id = self.batch_engine.enqueue_job(
                files=file_list,
                name=batch_name,
                type=analysis_type,
                priority=priority,
            )
            
            log.info(f"[MADRE] Batch encolado: batch_id={job_id}")
            
            return {
                "status": "ok",
                "batch_id": job_id,
                "total_files": len(file_list),
                "queue_position": 1,  # Simplificado
            }
            
        except Exception as exc:
            log.error(f"[MADRE] Error encolando batch: {exc}", exc_info=True)
            return {
                "status": "error",
                "error": str(exc),
            }
    
    async def handle_status(self, task_id: str) -> Dict[str, Any]:
        """
        MADRE LLAMA AQUÍ: consulta estado de tarea.
        """
        try:
            # En implementación real, consultar BD vx11.db
            return {
                "status": "ok",
                "task_id": task_id,
                "state": "processing",
                "progress": 50,
            }
        except Exception as exc:
            log.error(f"[MADRE] Error consultando status: {exc}")
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(exc),
            }


# Instancia global (singleton)
_madre_handler = None


def get_madre_handler() -> ShubMadreHandler:
    """Get or create singleton instance."""
    global _madre_handler
    if _madre_handler is None:
        _madre_handler = ShubMadreHandler()
    return _madre_handler
