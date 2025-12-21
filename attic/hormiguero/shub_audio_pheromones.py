"""
Hormiguero → Shub Audio Pheromones Integration

Define feromonas específicas para tareas de audio/DSP que Shub procesa.
Las hormigas usan estas feromonas para coordinar análisis y batch jobs.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

log = logging.getLogger("vx11.hormiguero.shub_pheromones")


@dataclass
class AudioPheromone:
    """Feromona específica para tareas de audio."""
    
    pheromone_id: str
    task_type: str  # "audio_scan" | "audio_batch_fix" | "audio_mastering"
    intensity: float  # 0-1
    source: str = "shub"
    
    def __repr__(self):
        return f"AudioPhero({self.task_type}:{self.intensity:.2f})"


class ShubAudioPheromones:
    """
    Sistema de feromonas para orquestación de tareas de audio en Shub.
    
    Feromonas disponibles:
    1. AUDIO_SCAN: Detecta archivos de audio para análisis
    2. AUDIO_BATCH_FIX: Coordina batch fixes (restauración, denoise)
    3. AUDIO_MASTERING: Señaliza oportunidad de mastering
    """
    
    # IDs canónicos de feromonas
    AUDIO_SCAN = "audio_scan"
    AUDIO_BATCH_FIX = "audio_batch_fix"
    AUDIO_MASTERING = "audio_mastering"
    
    # Intensidades por defecto
    DEFAULT_INTENSITIES = {
        AUDIO_SCAN: 0.7,
        AUDIO_BATCH_FIX: 0.8,
        AUDIO_MASTERING: 0.6,
    }
    
    def __init__(self):
        self.active_pheromones: Dict[str, AudioPheromone] = {}
        log.info("ShubAudioPheromones initialized")
    
    def deposit_audio_scan_pheromone(self, intensity: float = 0.7) -> AudioPheromone:
        """
        Deposita feromona de escaneo de audio.
        
        Indica: "Hay archivos de audio listos para analizar"
        Atrae a hormigas para ejecutar análisis DSP en paralelo.
        """
        phero = AudioPheromone(
            pheromone_id="audio_scan",
            task_type=self.AUDIO_SCAN,
            intensity=intensity,
        )
        self.active_pheromones[self.AUDIO_SCAN] = phero
        log.info(f"Deposited {phero}: hormigas comenzarán análisis")
        return phero
    
    def deposit_batch_fix_pheromone(self, intensity: float = 0.8) -> AudioPheromone:
        """
        Deposita feromona de batch fix de audio.
        
        Indica: "Hay lotes de audio con issues para restaurar"
        Atrae a hormigas para ejecutar denoise, declip, restauración en paralelo.
        """
        phero = AudioPheromone(
            pheromone_id="audio_batch_fix",
            task_type=self.AUDIO_BATCH_FIX,
            intensity=intensity,
        )
        self.active_pheromones[self.AUDIO_BATCH_FIX] = phero
        log.info(f"Deposited {phero}: hormigas comenzarán batch fixes")
        return phero
    
    def deposit_mastering_pheromone(self, intensity: float = 0.6) -> AudioPheromone:
        """
        Deposita feromona de mastering.
        
        Indica: "Audio está listo para masterizar"
        Atrae a hormigas para ejecutar mastering en paralelo.
        """
        phero = AudioPheromone(
            pheromone_id="audio_mastering",
            task_type=self.AUDIO_MASTERING,
            intensity=intensity,
        )
        self.active_pheromones[self.AUDIO_MASTERING] = phero
        log.info(f"Deposited {phero}: hormigas comenzarán mastering")
        return phero
    
    def get_pheromone(self, task_type: str) -> Optional[AudioPheromone]:
        """Obtener feromona activa de tipo dado."""
        return self.active_pheromones.get(task_type)
    
    def get_all_active(self) -> Dict[str, AudioPheromone]:
        """Obtener todas las feromonas activas."""
        return dict(self.active_pheromones)
    
    def clear_pheromone(self, task_type: str) -> None:
        """Limpiar feromona cuando tarea se complete."""
        if task_type in self.active_pheromones:
            del self.active_pheromones[task_type]
            log.info(f"Cleared pheromone: {task_type}")
    
    def decay_all(self, decay_factor: float = 0.95) -> None:
        """
        Aplicar decaimiento a todas las feromonas.
        
        Las feromonas se vuelven menos atractivas con el tiempo.
        Las hormigas seguirán rutas menos fuertes si no se refuerzan.
        """
        for task_type, phero in self.active_pheromones.items():
            old_intensity = phero.intensity
            phero.intensity *= decay_factor
            
            # Remover si intensidad < umbral
            if phero.intensity < 0.01:
                del self.active_pheromones[task_type]
                log.debug(f"Removed decayed pheromone: {task_type}")
            else:
                log.debug(f"Decayed {task_type}: {old_intensity:.2f} → {phero.intensity:.2f}")


# Instancia global
_audio_pheromones = None


def get_shub_audio_pheromones() -> ShubAudioPheromones:
    """Get or create singleton instance."""
    global _audio_pheromones
    if _audio_pheromones is None:
        _audio_pheromones = ShubAudioPheromones()
    return _audio_pheromones


class ShubAudioBatchReporter:
    """
    Reportador que batch_engine usa para notificar Hormiguero de issues.
    
    Cuando batch_engine detecta errores o issues en audios,
    reporta a Hormiguero para coordinar hormigas en fixes.
    """
    
    def __init__(self):
        self.pheromones = get_shub_audio_pheromones()
        log.info("ShubAudioBatchReporter initialized")
    
    async def report_batch_issues(self, batch_id: str, issues: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reporta issues encontrados en batch.
        
        Args:
            batch_id: ID del batch
            issues: {
                "total_issues": int,
                "denoise_required": bool,
                "declip_required": bool,
                "restoration_needed": bool,
                "files_affected": int
            }
        
        Retorna: {
            "status": "ok",
            "pheromones_deposited": [...],
            "hormigas_alerted": int
        }
        """
        try:
            pheromones_deposited = []
            
            # Determinar qué feromonas depositar basado en issues
            total_issues = issues.get("total_issues", 0)
            
            if total_issues > 0:
                # Depositar feromona de batch fix con intensidad proporcional
                intensity = min(1.0, 0.5 + (total_issues / 100.0))
                phero = self.pheromones.deposit_batch_fix_pheromone(intensity)
                pheromones_deposited.append(str(phero))
                log.info(f"Batch {batch_id}: Issues detected, pheromone deposited")
            
            if issues.get("denoise_required"):
                log.info(f"Batch {batch_id}: Denoise feromona activa")
            
            if issues.get("declip_required"):
                log.info(f"Batch {batch_id}: Declip feromona activa")
            
            return {
                "status": "ok",
                "batch_id": batch_id,
                "pheromones_deposited": pheromones_deposited,
                "hormigas_alerted": len(pheromones_deposited),
                "issues_summary": issues,
            }
            
        except Exception as exc:
            log.error(f"Report batch issues error: {exc}", exc_info=True)
            return {
                "status": "error",
                "batch_id": batch_id,
                "error": str(exc),
            }


def get_shub_audio_batch_reporter() -> ShubAudioBatchReporter:
    """Get or create singleton instance."""
    return ShubAudioBatchReporter()
