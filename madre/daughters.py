"""
Daughters Management (Hijas) — Procesos autónomos coordinados por Madre.

PASO 4: Integración real con Spawner.
Las hijas son procesos efímeros que:
1. Se crean vía POST /spawner/create
2. Reportan estado cada 10 segundos
3. Tienen TTL dinámico
4. Ejecutan subtareas en paralelo
5. Se terminan gracefully al expirar TTL

EJEMPLO:
  hija = await madre.spawn_daughter(
    task_type="audio_restore",
    file="/audio.wav",
    ttl_seconds=300
  )
  
  status = await madre.get_daughter_status(hija.id)
  # Output: {"status": "running", "progress": 0.45, ...}
"""

import logging
import asyncio
import uuid
import time
import httpx
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log
from config.db_schema import get_session, Daughter as DBDaughter

logger = logging.getLogger(__name__)
VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class Daughter:
    """Represenación de una hija (proceso autónomo coordinado)."""
    
    def __init__(self, 
                 task_name: str,
                 task_type: str,
                 parameters: Dict[str, Any],
                 ttl_seconds: int = 300,
                 priority: int = 2):
        self.id = str(uuid.uuid4())
        self.task_name = task_name
        self.task_type = task_type
        self.parameters = parameters
        self.ttl_seconds = ttl_seconds
        self.priority = priority
        self.status = "pending"  # pending, running, completed, failed, expired
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.spawner_pid: Optional[int] = None
        self.progress: float = 0.0
        self.last_heartbeat: Optional[datetime] = None
        self.mutation_level: int = 0
        self.retry_count: int = 0
    
    def is_expired(self) -> bool:
        """Verificar si hija ha expirado su TTL."""
        if not self.started_at:
            return False
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def is_stale(self, threshold_seconds: int = 30) -> bool:
        """Verificar si hija no ha reportado en threshold_seconds."""
        if not self.last_heartbeat:
            return False
        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed > threshold_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializar hija a diccionario."""
        return {
            "id": self.id,
            "task_name": self.task_name,
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "spawner_pid": self.spawner_pid,
            "ttl_seconds": self.ttl_seconds,
            "mutation_level": self.mutation_level,
            "retry_count": self.retry_count,
        }


class DaughterManager:
    """Gestor de hijas con soporte real a Spawner."""
    
    def __init__(self):
        self.daughters: Dict[str, Daughter] = {}
        self.max_concurrent = 8  # Máximo 8 hijas simultáneamente
        self.heartbeat_interval = 10  # Segundos entre heartbeats
    
    async def spawn_daughter(self,
                            task_name: str,
                            task_type: str,
                            parameters: Dict[str, Any],
                            ttl_seconds: int = 300) -> Optional[Daughter]:
        """
        Crear y lanzar hija real vía Spawner.
        
        Args:
            task_name: Nombre de la tarea
            task_type: Tipo de tarea (audio_restore, patch_gen, etc.)
            parameters: Parámetros de la tarea
            ttl_seconds: Tiempo de vida en segundos
            
        Returns:
            Objeto Daughter si exitoso, None si error
        """
        daughter = Daughter(task_name, task_type, parameters, ttl_seconds)
        
        try:
            # 1. Registrar en BD
            session = get_session("vx11")
            try:
                db_daughter = DBDaughter(
                    id=daughter.id,
                    task_id=str(uuid.uuid4()),
                    name=task_name,
                    purpose=task_type,
                    ttl_seconds=ttl_seconds,
                    status="spawning",
                )
                session.add(db_daughter)
                session.commit()
            finally:
                session.close()
            
            # 2. Invocar Spawner para crear proceso real
            spawner_url = settings.spawner_url or f"http://spawner:{settings.spawner_port}"
            
            payload = {
                "name": f"hija_{daughter.id[:8]}_{task_type}",
                "cmd": "python",
                "args": ["-c", f"print('Hija ejecutando: {task_name}'); import asyncio; asyncio.run(asyncio.sleep(10))"],
                "parent_task_id": daughter.id,
                "intent_type": task_type,
                "purpose": task_name,
                "ttl": ttl_seconds,
                "context": {
                    "daughter_id": daughter.id,
                    "parameters": parameters,
                },
                "env": {"VX11_DAUGHTER_ID": daughter.id},
            }
            
            async with httpx.AsyncClient(timeout=10.0, headers=AUTH_HEADERS) as client:
                resp = await client.post(
                    f"{spawner_url}/spawner/create",
                    json=payload,
                    headers=AUTH_HEADERS,
                )
            
            if resp.status_code != 200:
                daughter.status = "failed"
                daughter.error = f"Spawner returned {resp.status_code}"
                write_log("madre", f"daughter_spawn_failed:{daughter.id}:{resp.status_code}")
                return None
            
            result = resp.json()
            daughter.spawner_pid = result.get("pid")
            daughter.status = "running"
            daughter.started_at = datetime.utcnow()
            daughter.last_heartbeat = datetime.utcnow()
            
            # 3. Registrar en diccionario local
            self.daughters[daughter.id] = daughter
            
            write_log("madre", f"daughter_spawned:{daughter.id}:pid={daughter.spawner_pid}:ttl={ttl_seconds}")
            logger.info(f"✓ Daughter {daughter.id} spawned with PID {daughter.spawner_pid}")
            return daughter
        
        except Exception as e:
            daughter.status = "failed"
            daughter.error = str(e)
            write_log("madre", f"daughter_spawn_error:{daughter.id}:{e}", level="ERROR")
            logger.error(f"✗ Error spawning daughter {daughter.id}: {e}")
            return None
    
    async def heartbeat_daughter(self, daughter_id: str, progress: float = 0.0) -> bool:
        """
        Recibir heartbeat de hija (llamado por hija misma).
        
        Args:
            daughter_id: ID de hija reportando
            progress: Progreso 0.0-1.0
            
        Returns:
            True si heartbeat registrado
        """
        daughter = self.daughters.get(daughter_id)
        if not daughter:
            logger.warning(f"Heartbeat from unknown daughter: {daughter_id}")
            return False
        
        daughter.last_heartbeat = datetime.utcnow()
        daughter.progress = min(1.0, max(0.0, progress))
        
        # Verificar TTL
        if daughter.is_expired():
            daughter.status = "expired"
            write_log("madre", f"daughter_expired:{daughter_id}")
            return False
        
        return True
    
    async def complete_daughter(self, daughter_id: str, result: Dict[str, Any]) -> bool:
        """Marcar hija como completada."""
        daughter = self.daughters.get(daughter_id)
        if not daughter:
            return False
        
        daughter.status = "completed"
        daughter.completed_at = datetime.utcnow()
        daughter.result = result
        daughter.progress = 1.0
        
        write_log("madre", f"daughter_completed:{daughter_id}")
        logger.info(f"✓ Daughter {daughter_id} completed")
        return True
    
    async def fail_daughter(self, daughter_id: str, error: str) -> bool:
        """Marcar hija como fallida."""
        daughter = self.daughters.get(daughter_id)
        if not daughter:
            return False
        
        daughter.status = "failed"
        daughter.completed_at = datetime.utcnow()
        daughter.error = error
        
        write_log("madre", f"daughter_failed:{daughter_id}:{error}", level="ERROR")
        logger.error(f"✗ Daughter {daughter_id} failed: {error}")
        return True
    
    async def get_daughter_status(self, daughter_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de hija."""
        daughter = self.daughters.get(daughter_id)
        if not daughter:
            return None
        
        # Verificar si expiró
        if daughter.status == "running" and daughter.is_expired():
            daughter.status = "expired"
        
        # Verificar si está stale (sin heartbeat)
        if daughter.status == "running" and daughter.is_stale(threshold_seconds=60):
            logger.warning(f"Daughter {daughter_id} is stale (no heartbeat in 60s)")
        
        return daughter.to_dict()
    
    async def list_daughters(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Listar todas las hijas, opcionalmente filtradas."""
        daughters_list = []
        for daughter in self.daughters.values():
            # Actualizar estado si expiró
            if daughter.status == "running" and daughter.is_expired():
                daughter.status = "expired"
            
            if status_filter and daughter.status != status_filter:
                continue
            
            daughters_list.append(daughter.to_dict())
        
        return daughters_list
    
    async def wait_for_daughter(self, daughter_id: str, timeout: float = 300.0) -> Optional[Dict[str, Any]]:
        """Esperar a que hija se complete (blocking)."""
        start_time = time.time()
        poll_interval = 0.5  # Poll cada 500ms
        
        while True:
            daughter = self.daughters.get(daughter_id)
            if not daughter:
                logger.warning(f"Daughter {daughter_id} not found")
                return None
            
            # Check si completó o falló
            if daughter.status in ("completed", "failed", "expired"):
                return daughter.to_dict()
            
            # Check timeout
            if time.time() - start_time > timeout:
                logger.warning(f"Timeout waiting for daughter {daughter_id}")
                return None
            
            await asyncio.sleep(poll_interval)
    
    async def cleanup_expired_daughters(self):
        """Background task: Limpiar hijas expiradas."""
        while True:
            try:
                await asyncio.sleep(30)  # Check cada 30 segundos
                
                expired_ids = []
                for daughter_id, daughter in list(self.daughters.items()):
                    if daughter.status == "running" and daughter.is_expired():
                        daughter.status = "expired"
                        daughter.completed_at = datetime.utcnow()
                        write_log("madre", f"daughter_cleanup_expired:{daughter_id}")
                    
                    # Remover muy antiguas (> 1 hora)
                    if daughter.created_at:
                        age_seconds = (datetime.utcnow() - daughter.created_at).total_seconds()
                        if age_seconds > 3600:
                            expired_ids.append(daughter_id)
                
                for daughter_id in expired_ids:
                    del self.daughters[daughter_id]
                    logger.info(f"Removed old daughter from memory: {daughter_id}")
            
            except Exception as e:
                logger.error(f"Cleanup task error: {e}")


# Singleton instance
_daughter_manager: Optional[DaughterManager] = None


def get_daughter_manager() -> DaughterManager:
    """Get or create global daughter manager."""
    global _daughter_manager
    if _daughter_manager is None:
        _daughter_manager = DaughterManager()
    return _daughter_manager
