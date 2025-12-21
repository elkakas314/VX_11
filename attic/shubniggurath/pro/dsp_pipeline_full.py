"""
Orquestador completo del pipeline DSP
Coordina: ingestión → análisis → FX → mezcla → export → BD
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import uuid

from shubniggurath.pro.dsp_engine import DSPEngine, AudioAnalysisResult
from shubniggurath.pro.dsp_fx import FXChain, EffectConfig, EffectType
from shubniggurath.pro.audio_io import load_audio, save_wav
from shubniggurath.pro.shub_db import (
    get_shub_session,
    ShubSession,
    AdvancedAnalysis,
    ShubJob,
    ShubSandbox,
)


class JobStatus(Enum):
    """Estados del job"""
    QUEUED = "queued"
    RUNNING = "running"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineConfig:
    """Configuración del pipeline"""
    job_id: str
    session_id: str
    input_path: str
    output_path: Optional[str] = None
    
    # Análisis
    enable_analysis: bool = True
    
    # Procesamiento
    fx_chain_config: Optional[List[Dict[str, Any]]] = None
    
    # Export
    export_format: str = "wav"
    export_quality: int = 24  # bits
    
    # Metadata
    project_name: str = "Untitled"
    metadata: Optional[Dict[str, Any]] = None


class PipelineProgress:
    """Tracking de progreso"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = JobStatus.QUEUED
        self.current_stage = "init"
        self.progress_percent = 0
        self.estimated_time_remaining_s = 0
        self.timestamp_start = datetime.now()
        self.messages = []
    
    def update(self, stage: str, percent: float, message: str = ""):
        self.current_stage = stage
        self.progress_percent = min(100, max(0, percent))
        if message:
            self.messages.append(f"[{stage}] {message}")
        self._update_eta()
    
    def _update_eta(self):
        """Estimar tiempo restante"""
        elapsed = (datetime.now() - self.timestamp_start).total_seconds()
        if self.progress_percent > 0:
            total_estimated = elapsed * 100 / self.progress_percent
            self.estimated_time_remaining_s = max(0, total_estimated - elapsed)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "current_stage": self.current_stage,
            "progress_percent": self.progress_percent,
            "estimated_time_remaining_s": self.estimated_time_remaining_s,
            "elapsed_s": (datetime.now() - self.timestamp_start).total_seconds(),
            "messages": self.messages[-10:],  # Últimos 10 mensajes
        }


class DSPPipeline:
    """Orquestador principal del pipeline"""
    
    def __init__(self):
        self.dsp_engine = DSPEngine()
        self.jobs: Dict[str, ShubJob] = {}
        self.progress: Dict[str, PipelineProgress] = {}
    
    async def run_pipeline(self, config: PipelineConfig) -> Dict[str, Any]:
        """Ejecutar pipeline completo"""
        
        # Inicializar
        job_id = config.job_id or str(uuid.uuid4())
        progress = PipelineProgress(job_id)
        self.progress[job_id] = progress
        
        session = get_shub_session()
        
        try:
            # 1. Crear Job en BD
            progress.update("db_init", 5, "Inicializando job...")
            job = ShubJob(
                uuid=job_id,
                name=config.project_name,
                status=JobStatus.RUNNING.value,
                config_json=json.dumps(asdict(config)),
                input_path=config.input_path,
                output_path=config.output_path,
                session_id=config.session_id,
            )
            session.add(job)
            session.commit()
            self.jobs[job_id] = job
            
            # 2. Cargar audio
            progress.update("loading", 10, f"Cargando {config.input_path}...")
            audio, sr = load_audio(config.input_path)
            if audio is None:
                raise ValueError(f"No se pudo cargar audio: {config.input_path}")
            progress.update("loading", 15, f"Audio cargado: {len(audio)} muestras, {sr} Hz")
            
            # 3. Análisis DSP
            analysis_result = None
            if config.enable_analysis:
                progress.update("analyzing", 20, "Analizando audio...")
                analysis_result = await self.dsp_engine.analyze_audio(audio, sr)
                progress.update("analyzing", 50, f"Análisis completado: {len(analysis_result.issues)} issues detectados")
                
                # Guardar análisis en BD
                advanced_analysis = AdvancedAnalysis(
                    shub_job_id=job_id,
                    analysis_json=json.dumps(asdict(analysis_result)),
                    peak_db=analysis_result.peak_db,
                    rms_db=analysis_result.rms_db,
                    lufs=analysis_result.lufs,
                    spectral_centroid_hz=analysis_result.spectral_centroid_hz,
                    dynamic_range_db=analysis_result.dynamic_range_db,
                    detected_issues_json=json.dumps(analysis_result.issues),
                    recommendations_json=json.dumps(analysis_result.recommendations),
                )
                session.add(advanced_analysis)
                session.commit()
            
            # 4. Procesamiento (FX)
            processed_audio = audio
            if config.fx_chain_config:
                progress.update("processing", 51, "Construyendo cadena de efectos...")
                fx_chain = FXChain(sample_rate=sr)
                
                for fx_config_dict in config.fx_chain_config:
                    fx_type = EffectType(fx_config_dict.get("type"))
                    fx_config = EffectConfig(
                        type=fx_type,
                        enabled=fx_config_dict.get("enabled", True),
                        params=fx_config_dict.get("params", {}),
                    )
                    fx_chain.add_effect_config(fx_config)
                
                progress.update("processing", 60, f"Procesando {len(config.fx_chain_config)} efectos...")
                processed_audio = await fx_chain.process_async(audio)
                progress.update("processing", 80, "Procesamiento completado")
            
            # 5. Export
            output_path = config.output_path or f"output_{job_id}.wav"
            progress.update("exporting", 85, f"Exportando a {output_path}...")
            
            success = save_wav(
                processed_audio,
                output_path,
                sample_rate=sr,
                bit_depth=config.export_quality,
            )
            
            if not success:
                raise ValueError("Error exportando audio")
            
            progress.update("exporting", 95, "Finalizando...")
            
            # 6. Actualizar Job
            job.status = JobStatus.COMPLETED.value
            job.output_path = output_path
            job.result_json = json.dumps({
                "success": True,
                "output_path": output_path,
                "duration_s": len(processed_audio) / sr,
                "analysis": asdict(analysis_result) if analysis_result else None,
            })
            session.commit()
            
            progress.status = JobStatus.COMPLETED
            progress.update("complete", 100, "Pipeline completado exitosamente")
            
            return {
                "success": True,
                "job_id": job_id,
                "output_path": output_path,
                "analysis": asdict(analysis_result) if analysis_result else None,
                "progress": progress.to_dict(),
            }
        
        except Exception as e:
            progress.status = JobStatus.FAILED
            progress.update("error", 0, f"Error: {str(e)}")
            
            job.status = JobStatus.FAILED.value
            job.result_json = json.dumps({
                "success": False,
                "error": str(e),
            })
            session.commit()
            
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e),
                "progress": progress.to_dict(),
            }
    
    async def batch_process(
        self,
        configs: List[PipelineConfig],
        parallel_jobs: int = 2,
    ) -> List[Dict[str, Any]]:
        """Procesar múltiples jobs en paralelo"""
        
        results = []
        semaphore = asyncio.Semaphore(parallel_jobs)
        
        async def limited_pipeline(config):
            async with semaphore:
                return await self.run_pipeline(config)
        
        tasks = [limited_pipeline(config) for config in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r if isinstance(r, dict) else {"success": False, "error": str(r)}
            for r in results
        ]
    
    def get_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtener progreso de job"""
        progress = self.progress.get(job_id)
        if progress:
            return progress.to_dict()
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancelar job (nota: no es verdaderamente cancelable en ejecución)"""
        if job_id in self.progress:
            self.progress[job_id].status = JobStatus.CANCELLED
            
            session = get_shub_session()
            job = session.query(ShubJob).filter_by(uuid=job_id).first()
            if job:
                job.status = JobStatus.CANCELLED.value
                session.commit()
            
            return True
        return False
    
    def list_jobs(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Listar jobs"""
        session = get_shub_session()
        query = session.query(ShubJob)
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        jobs = query.all()
        return [
            {
                "uuid": job.uuid,
                "name": job.name,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "progress": self.get_progress(job.uuid),
            }
            for job in jobs
        ]


# Singleton global
_pipeline_instance = None


def get_pipeline() -> DSPPipeline:
    """Obtener instancia global del pipeline"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DSPPipeline()
    return _pipeline_instance
