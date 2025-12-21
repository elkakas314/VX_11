"""
Pheromone Engine — Sistema de comunicación química entre hormigas (workers).

Feromonas representan métricas: latencia, carga, calidad.
Las hormigas distribuyen trabajo según "olor" de feromonas.

STATUS: Stub para FASE 3 - Coordinación distribuida
"""

import logging
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Pheromone:
    """Marcador químico distribuido entre hormigas."""
    
    trail_id: str  # ID de ruta/tarea
    intensity: float  # 0-1, mayor = más atractivo
    deposited_by: str  # ID de hormiga que depositó
    timestamp: float = field(default_factory=time.time)
    decay_rate: float = 0.95  # Decaimiento por iteración
    
    def intensity_now(self) -> float:
        """Calcular intensidad actual con decaimiento exponencial."""
        elapsed = time.time() - self.timestamp
        return self.intensity * (self.decay_rate ** (elapsed / 60))  # Decae cada 60s


class PheromoneEngine:
    """Motor de feromonas para coordinación de hormigas."""
    
    def __init__(self):
        self.pheromones: Dict[str, List[Pheromone]] = defaultdict(list)
        self.trail_metrics: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    def deposit_pheromone(
        self,
        trail_id: str,
        intensity: float,
        ant_id: str,
        decay_rate: float = 0.95
    ) -> None:
        """Depositar feromona en ruta.
        
        Args:
            trail_id: Identificador de la ruta/tarea
            intensity: Intensidad inicial (0-1)
            ant_id: ID de hormiga que deposita
            decay_rate: Tasa de decaimiento exponencial
        """
        pheromone = Pheromone(
            trail_id=trail_id,
            intensity=min(1.0, max(0.0, intensity)),  # Clamp [0,1]
            deposited_by=ant_id,
            decay_rate=decay_rate,
        )
        self.pheromones[trail_id].append(pheromone)
        logger.debug(f"Ant {ant_id} deposited pheromone on trail {trail_id} (intensity={intensity})")
    
    def get_trail_attractiveness(self, trail_id: str) -> float:
        """Calcular atracción total de una ruta (suma de feromonas activas)."""
        if trail_id not in self.pheromones:
            return 0.0
        
        total = 0.0
        active_pheros = []
        for phero in self.pheromones[trail_id]:
            intensity = phero.intensity_now()
            if intensity > 0.01:  # Ignorar feromonas muy débiles
                total += intensity
                active_pheros.append(intensity)
        
        # Mantener solo feromonas activas
        self.pheromones[trail_id] = [
            p for p in self.pheromones[trail_id]
            if p.intensity_now() > 0.01
        ]
        
        return min(total, 10.0)  # Cap en 10 para evitar overflow
    
    def select_best_trail(self, available_trails: List[str]) -> Optional[str]:
        """Seleccionar mejor ruta según atracción de feromonas (ACO-inspired).
        
        Args:
            available_trails: Lista de rutas disponibles
            
        Returns:
            ID de ruta seleccionada o None si no hay opciones
        """
        if not available_trails:
            return None
        
        scores = {trail: self.get_trail_attractiveness(trail) for trail in available_trails}
        
        # Si todas tienen intensidad 0, seleccionar aleatoriamente
        if all(v == 0 for v in scores.values()):
            return available_trails[0]
        
        # Seleccionar ruta con máxima atracción
        return max(scores, key=scores.get)
    
    def record_trail_metrics(
        self,
        trail_id: str,
        latency_ms: float,
        success: bool,
        load: float
    ) -> None:
        """Registrar métricas de ejecución en ruta para feedback.
        
        Args:
            trail_id: ID de ruta
            latency_ms: Latencia en milisegundos
            success: Si la ejecución fue exitosa
            load: Carga de CPU/memoria (0-1)
        """
        self.trail_metrics[trail_id] = {
            "latency_ms": latency_ms,
            "success": success,
            "load": load,
            "timestamp": time.time(),
        }
        
        # Depositar feromona basada en éxito y baja latencia
        if success:
            # Fórmula: mayor intensidad si bajo latency y baja carga
            intensity = 1.0 - min(1.0, (latency_ms / 1000.0) + (load / 2.0))
            self.deposit_pheromone(trail_id, intensity, "metrics")
    
    def get_ant_decision(
        self,
        ant_id: str,
        available_trails: List[str],
        explore_rate: float = 0.1
    ) -> str:
        """Decidir qué ruta seguir (exploitation vs exploration).
        
        Args:
            ant_id: ID de hormiga
            available_trails: Rutas disponibles
            explore_rate: Probabilidad de exploración (vs explotación)
            
        Returns:
            ID de ruta seleccionada
        """
        import random
        
        if random.random() < explore_rate:
            # Exploración: seleccionar aleatoriamente
            selected = random.choice(available_trails)
        else:
            # Explotación: seguir feromona más fuerte
            selected = self.select_best_trail(available_trails)
        
        logger.debug(f"Ant {ant_id} selected trail {selected}")
        return selected
    
    def evaporate_all(self) -> None:
        """Hacer evaporar todas las feromonas (limpieza periódica)."""
        for trail_id in list(self.pheromones.keys()):
            self.pheromones[trail_id] = [
                p for p in self.pheromones[trail_id]
                if p.intensity_now() > 0.01
            ]
            if not self.pheromones[trail_id]:
                del self.pheromones[trail_id]
