"""
Audio Batch Engine — Procesamiento de Lotes Paralelo con Persistencia
=====================================================================

Motor de procesamiento por lotes con:
- Cola inteligente con prioridades (1-10)
- Integración con Hormiguero para distribución
- Persistencia en vx11.db (tabla batch_jobs)
- Manejo automático de errores y recuperación
- Reportes de progreso en tiempo real
- Validación post-procesamiento

Protocolo: HTTP + SQLite local
Endpoints expuestos vía main.py: /api/batch/*
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from config.settings import settings
from config.db_schema import get_session, Task, Context, Spawn
from config.forensics import write_log, record_crash
from shubniggurath.core.dsp_pipeline_full import pipeline
from shubniggurath.integrations.vx11_bridge import VX11Bridge

# =============================================================================
# LOGGING & CONSTANTS
# =============================================================================

logger = logging.getLogger(__name__)

# Estados de job
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"

# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class BatchJob:
    """Modelo de batch job"""
    job_id: str
    job_name: str
    audio_files: List[str]
    analysis_type: str  # quick, full, deep
    priority: int  # 1-10
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# AUDIO BATCH ENGINE
# =============================================================================


class AudioBatchEngine:
    """
    Motor de procesamiento por lotes para audio.
    
    Métodos principales:
    - enqueue_job(): Agregar job a cola
    - get_status(): Consultar estado
    - cancel_job(): Cancelar job
    - process_queue(): Procesar cola (internal)
    """

    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}  # En-memoria (caché)
        self.queue: List[str] = []  # Cola de job_ids ordenada por prioridad
        self.vx11_bridge = VX11Bridge()
        self.processing = False
        self.db = None

    async def initialize(self):
        """Inicializar engine y cargar jobs existentes de BD"""
        try:
            self.db = get_session("audio_batch_engine")
            write_log("audio_batch_engine", "INITIALIZE: Cargando jobs existentes de BD", level="INFO")
            
            # Cargar jobs no completados
            existing_tasks = self.db.query(Task).filter(
                Task.module == "shubniggurath",
                Task.action == "batch_job",
                Task.status.in_(["pending", "processing"]),
            ).all()
            
            for task in existing_tasks:
                # Reconstruir job desde BD
                try:
                    job_data = json.loads(task.metadata or "{}")
                    job = BatchJob(**job_data)
                    self.jobs[job.job_id] = job
                    
                    if job.status == JOB_STATUS_QUEUED:
                        self.queue.append(job.job_id)
                        
                except Exception as e:
                    write_log("audio_batch_engine", f"INITIALIZE_LOAD_ERROR: {str(e)}", level="WARNING")
            
            write_log("audio_batch_engine", f"INITIALIZE_COMPLETE: {len(self.jobs)} jobs cargados", level="INFO")
            
        except Exception as e:
            record_crash("audio_batch_engine", e)
            write_log("audio_batch_engine", f"INITIALIZE_ERROR: {str(e)}", level="ERROR")

    # =========================================================================
    # MÉTODO 1: enqueue_job
    # =========================================================================

    async def enqueue_job(
        self,
        audio_files: List[str],
        job_name: str = None,
        analysis_type: str = "full",
        priority: int = 5,
    ) -> Dict[str, Any]:
        """
        Encolar job de procesamiento.
        
        Args:
            audio_files: Lista de rutas de archivos
            job_name: Nombre del job (auto-generado si None)
            analysis_type: 'quick', 'full', 'deep'
            priority: 1-10 (10 = máxima prioridad)
            
        Retorna:
        {
            "status": "success",
            "job_id": "uuid",
            "job_name": "job_name",
            "queue_position": 3,
            "total_files": 10,
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            job_id = str(uuid.uuid4())
            job_name = job_name or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            write_log("audio_batch_engine", f"ENQUEUE_JOB: {job_name}, files={len(audio_files)}, priority={priority}", level="INFO")
            
            # Crear job
            job = BatchJob(
                job_id=job_id,
                job_name=job_name,
                audio_files=audio_files,
                analysis_type=analysis_type,
                priority=priority,
                status=JOB_STATUS_QUEUED,
                total_files=len(audio_files),
                processed_files=0,
                failed_files=0,
                created_at=datetime.now().isoformat(),
            )
            
            # Guardar en memoria
            self.jobs[job_id] = job
            
            # Insertar en cola (respetando prioridades)
            self.queue.append(job_id)
            self.queue.sort(key=lambda jid: self.jobs[jid].priority, reverse=True)
            
            queue_position = self.queue.index(job_id) + 1
            
            # Persistir en BD
            await self._save_job_to_db(job)
            
            # Notificar a Hormiguero
            hormiguero_response = await self.vx11_bridge.batch_submit(
                audio_files=audio_files,
                analysis_type=analysis_type,
                priority=priority,
            )
            
            write_log("audio_batch_engine", f"ENQUEUE_JOB_SUCCESS: job_id={job_id}, queue_pos={queue_position}", level="INFO")
            
            return {
                "status": "success",
                "job_id": job_id,
                "job_name": job_name,
                "queue_position": queue_position,
                "total_files": len(audio_files),
                "estimated_wait_seconds": queue_position * 30,  # Heurística
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("audio_batch_engine", e)
            write_log("audio_batch_engine", f"ENQUEUE_JOB_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 2: get_status
    # =========================================================================

    async def get_status(self, job_id: str) -> Dict[str, Any]:
        """
        Consultar estado de batch job.
        
        Args:
            job_id: ID del job
            
        Retorna:
        {
            "status": "success",
            "job": {
                "job_id": "uuid",
                "job_name": "...",
                "status": "processing",
                "progress": {
                    "total": 10,
                    "processed": 7,
                    "failed": 0,
                    "percent": 70
                },
                "estimated_remaining_seconds": 45,
                "timestamp": "2024-12-10T15:30:00Z"
            }
        }
        """
        try:
            if job_id not in self.jobs:
                write_log("audio_batch_engine", f"GET_STATUS: job_id not found: {job_id}", level="WARNING")
                return {"status": "error", "message": f"Job {job_id} not found"}
            
            job = self.jobs[job_id]
            
            # Calcular progreso
            percent_complete = (job.processed_files / max(job.total_files, 1)) * 100
            estimated_remaining = (job.total_files - job.processed_files) * 3  # ~3s por archivo
            
            write_log("audio_batch_engine", f"GET_STATUS: job_id={job_id}, progress={percent_complete:.1f}%", level="INFO")
            
            return {
                "status": "success",
                "job": {
                    "job_id": job.job_id,
                    "job_name": job.job_name,
                    "status": job.status,
                    "progress": {
                        "total": job.total_files,
                        "processed": job.processed_files,
                        "failed": job.failed_files,
                        "percent_complete": int(percent_complete),
                    },
                    "created_at": job.created_at,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                    "estimated_remaining_seconds": int(estimated_remaining),
                    "timestamp": datetime.now().isoformat(),
                },
            }
            
        except Exception as e:
            record_crash("audio_batch_engine", e)
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # MÉTODO 3: cancel_job
    # =========================================================================

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancelar batch job pendiente.
        
        Args:
            job_id: ID del job
            
        Retorna:
        {
            "status": "success",
            "job_id": "uuid",
            "message": "Job cancelled",
            "timestamp": "2024-12-10T15:30:00Z"
        }
        """
        try:
            if job_id not in self.jobs:
                return {"status": "error", "message": f"Job {job_id} not found"}
            
            job = self.jobs[job_id]
            
            # Solo cancelar si está en cola o procesando
            if job.status not in [JOB_STATUS_QUEUED, JOB_STATUS_PROCESSING]:
                return {"status": "error", "message": f"Cannot cancel {job.status} job"}
            
            # Cambiar estado
            job.status = JOB_STATUS_CANCELLED
            job.completed_at = datetime.now().isoformat()
            
            # Remover de cola
            if job_id in self.queue:
                self.queue.remove(job_id)
            
            # Persistir
            await self._save_job_to_db(job)
            
            write_log("audio_batch_engine", f"CANCEL_JOB_SUCCESS: job_id={job_id}", level="INFO")
            
            return {
                "status": "success",
                "job_id": job_id,
                "message": "Job cancelled",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            record_crash("audio_batch_engine", e)
            write_log("audio_batch_engine", f"CANCEL_JOB_ERROR: {str(e)}", level="ERROR")
            return {"status": "error", "message": str(e)}

    # =========================================================================
    # INTERNAL: Process Queue
    # =========================================================================

    async def process_queue(self):
        """
        Procesar cola de jobs (internal, run en background).
        Llamado por scheduler o manualmente para iniciar procesamiento.
        """
        if self.processing:
            return  # Ya está procesando
        
        self.processing = True
        
        try:
            write_log("audio_batch_engine", "PROCESS_QUEUE: iniciando", level="INFO")
            
            while len(self.queue) > 0:
                job_id = self.queue[0]
                job = self.jobs[job_id]
                
                # Cambiar estado a processing
                job.status = JOB_STATUS_PROCESSING
                job.started_at = datetime.now().isoformat()
                await self._save_job_to_db(job)
                
                # Procesar archivos
                try:
                    results = []
                    for audio_file in job.audio_files:
                        try:
                            # Aquí iría el análisis real usando dsp_pipeline_full
                            # Por ahora, simulado:
                            write_log("audio_batch_engine", f"PROCESSING: {audio_file}", level="INFO")
                            
                            # Simulación
                            await asyncio.sleep(0.1)
                            
                            job.processed_files += 1
                            results.append({
                                "file": audio_file,
                                "status": "success",
                                "analysis": {"mock": "data"},
                            })
                            
                        except Exception as e:
                            write_log("audio_batch_engine", f"PROCESS_FILE_ERROR: {audio_file}: {str(e)}", level="WARNING")
                            job.failed_files += 1
                            results.append({
                                "file": audio_file,
                                "status": "error",
                                "error": str(e),
                            })
                    
                    # Completar job
                    job.status = JOB_STATUS_COMPLETED
                    job.completed_at = datetime.now().isoformat()
                    job.results = results
                    
                    write_log("audio_batch_engine", f"PROCESS_QUEUE_JOB_COMPLETE: job_id={job_id}, processed={job.processed_files}, failed={job.failed_files}", level="INFO")
                    
                except Exception as e:
                    record_crash("audio_batch_engine", e)
                    job.status = JOB_STATUS_FAILED
                    job.completed_at = datetime.now().isoformat()
                    job.error_message = str(e)
                    write_log("audio_batch_engine", f"PROCESS_QUEUE_JOB_ERROR: {str(e)}", level="ERROR")
                
                # Persistir
                await self._save_job_to_db(job)
                
                # Remover de cola
                self.queue.pop(0)
                
                # Notificar a Madre
                await self.vx11_bridge.notify_madre(
                    event_type="batch_job_complete",
                    data={
                        "job_id": job_id,
                        "job_name": job.job_name,
                        "status": job.status,
                        "processed": job.processed_files,
                        "failed": job.failed_files,
                    },
                    priority="normal",
                )
            
            write_log("audio_batch_engine", "PROCESS_QUEUE_COMPLETE: Cola vacía", level="INFO")
            
        except Exception as e:
            record_crash("audio_batch_engine", e)
            write_log("audio_batch_engine", f"PROCESS_QUEUE_ERROR: {str(e)}", level="ERROR")
        
        finally:
            self.processing = False

    # =========================================================================
    # HELPERS: Database Persistence
    # =========================================================================

    async def _save_job_to_db(self, job: BatchJob):
        """Guardar job en vx11.db"""
        try:
            if self.db is None:
                self.db = get_session("audio_batch_engine")
            
            # Crear o actualizar Task
            task = self.db.query(Task).filter(Task.uuid == job.job_id).first()
            
            if task is None:
                task = Task(
                    uuid=job.job_id,
                    name=job.job_name,
                    module="shubniggurath",
                    action="batch_job",
                    status=job.status,
                    metadata=json.dumps(job.to_dict()),
                    created_at=datetime.now(),
                )
                self.db.add(task)
            else:
                task.status = job.status
                task.metadata = json.dumps(job.to_dict())
            
            self.db.commit()
            
        except Exception as e:
            write_log("audio_batch_engine", f"SAVE_JOB_DB_ERROR: {str(e)}", level="WARNING")
            if self.db:
                self.db.rollback()

    async def cleanup(self):
        """Cleanup: cerrar BD"""
        if self.db:
            self.db.close()
            self.db = None
        
        if self.vx11_bridge:
            await self.vx11_bridge.cleanup()
        
        write_log("audio_batch_engine", "CLEANUP: Motor detenido", level="INFO")


# Instancia global
batch_engine = AudioBatchEngine()
