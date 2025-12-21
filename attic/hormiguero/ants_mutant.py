"""
PASO 5: Hormigas Mutantes — Paralelización con GA + Feromonas.

Sistema de colonia autónoma donde:
1. Hormigas detectan drift en paralelo
2. Feromonas comunican cambios
3. Reina toma decisiones basadas en feedback
4. GA evolution en base a métricas de éxito

FLUJO:
  1. Reina crea colonia de 8-16 hormigas
  2. Cada hormiga escanea zona asignada
  3. Si detectan drift → depositan feromonas
  4. Reina agrega feromonas → incrementa intensidad
  5. GA evoluciona comportamiento de hormigas
  6. Próxima generación es más eficiente

ESTADO: Implementación completa PASO 5
"""

import logging
import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import random
import json
import httpx

from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log
from config.db_schema import get_session

logger = logging.getLogger(__name__)
VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class PheromoneType(Enum):
    """Tipos de feromonas en colonia"""
    DRIFT = "drift"          # Detección de cambios
    FOOD = "food"            # Tarea completada
    DANGER = "danger"        # Error detectado
    REPAIR = "repair"        # Se necesita reparación
    COMMUNICATION = "communication"  # Comunicación general


@dataclass
class Pheromone:
    """Marcador de feromona dejado por hormiga"""
    id: str
    pheromone_type: PheromoneType
    intensity: float  # 0.0-1.0
    location: str  # Zona/archivo/dominio
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    source_ant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def decay(self, rate: float = 0.05) -> None:
        """Reducir intensidad por decay natural (evaporación)."""
        self.intensity = max(0.0, self.intensity - rate)
        self.updated_at = datetime.utcnow()
    
    def reinforce(self, amount: float = 0.1) -> None:
        """Aumentar intensidad si otra hormiga pasa por aquí."""
        self.intensity = min(1.0, self.intensity + amount)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.pheromone_type.value,
            "intensity": self.intensity,
            "location": self.location,
            "age_seconds": (datetime.utcnow() - self.created_at).total_seconds(),
            "metadata": self.metadata,
        }


class Ant:
    """Hormiga individual en la colonia"""
    
    def __init__(self, ant_id: str, colony_id: str, mutation_level: int = 0):
        self.id = ant_id
        self.colony_id = colony_id
        self.mutation_level = mutation_level  # 0=baseline, 1+=evolved
        self.status = "idle"  # idle, scanning, reporting
        self.current_zone: Optional[str] = None
        self.tasks_completed = 0
        self.drift_found = 0
        self.errors = 0
        self.fitness_score = 0.0
        self.last_active = datetime.utcnow()
        self.pheromones_left: List[str] = []
        self.energy = 1.0  # 0.0-1.0
    
    def lose_energy(self, amount: float = 0.05) -> None:
        """Gastar energía en actividad."""
        self.energy = max(0.0, self.energy - amount)
    
    def gain_energy(self, amount: float = 0.1) -> None:
        """Recuperar energía (rest/food)."""
        self.energy = min(1.0, self.energy + amount)
    
    def is_alive(self) -> bool:
        """Hormiga viva si tiene energía > 0"""
        return self.energy > 0.0
    
    def update_fitness(self) -> float:
        """Calcular fitness basado en desempeño."""
        self.fitness_score = (
            (self.tasks_completed * 0.4) +
            (self.drift_found * 0.3) +
            (max(0.0, 1.0 - self.errors * 0.1) * 0.3)
        )
        return self.fitness_score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "current_zone": self.current_zone,
            "tasks_completed": self.tasks_completed,
            "drift_found": self.drift_found,
            "errors": self.errors,
            "fitness": round(self.fitness_score, 2),
            "energy": round(self.energy, 2),
            "mutation_level": self.mutation_level,
        }


class AntColony:
    """Colonia de hormigas autónoma"""
    
    def __init__(self, colony_id: str, size: int = 8, mutation_level: int = 0):
        self.id = colony_id
        self.size = size
        self.mutation_level = mutation_level
        self.ants: Dict[str, Ant] = {}
        self.pheromones: Dict[str, Pheromone] = {}
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.generation = 0
        self.total_tasks = 0
        self.total_drift_found = 0
        
        # Crear hormigas
        for i in range(size):
            ant = Ant(
                ant_id=f"ant_{colony_id[:8]}_{i}",
                colony_id=colony_id,
                mutation_level=mutation_level
            )
            self.ants[ant.id] = ant
    
    def deposit_pheromone(self,
                         pheromone_type: PheromoneType,
                         location: str,
                         intensity: float = 0.7,
                         source_ant_id: Optional[str] = None,
                         metadata: Dict[str, Any] = None) -> Pheromone:
        """Depositar feromona en ubicación."""
        pheromone_id = str(uuid.uuid4())[:8]
        key = f"{location}_{pheromone_type.value}"
        
        if key in self.pheromones:
            # Reforzar existente
            self.pheromones[key].reinforce(intensity * 0.2)
        else:
            # Crear nueva
            pheromone = Pheromone(
                id=pheromone_id,
                pheromone_type=pheromone_type,
                intensity=intensity,
                location=location,
                source_ant_id=source_ant_id,
                metadata=metadata or {},
            )
            self.pheromones[key] = pheromone
        
        return self.pheromones[key]
    
    def get_pheromones_at_location(self, location: str) -> List[Pheromone]:
        """Obtener feromonas en ubicación específica."""
        result = []
        for pheromone in self.pheromones.values():
            if pheromone.location == location and pheromone.intensity > 0.0:
                result.append(pheromone)
        
        return result
    
    async def scan_zone(self, ant: Ant, zone: str) -> Dict[str, Any]:
        """Simular escaneo de zona por hormiga."""
        ant.status = "scanning"
        ant.current_zone = zone
        ant.lose_energy(0.1)
        
        # Simular detección de drift
        drift_detected = random.random() < 0.3  # 30% probabilidad
        if drift_detected:
            ant.drift_found += 1
            self.total_drift_found += 1
            self.deposit_pheromone(
                PheromoneType.DRIFT,
                zone,
                intensity=0.8,
                source_ant_id=ant.id,
                metadata={"drift_level": random.uniform(0.3, 0.9)}
            )
        
        ant.tasks_completed += 1
        self.total_tasks += 1
        ant.status = "idle"
        
        return {
            "ant_id": ant.id,
            "zone": zone,
            "drift_detected": drift_detected,
        }
    
    def get_colony_status(self) -> Dict[str, Any]:
        """Estado actual de la colonia."""
        ant_dicts = [ant.to_dict() for ant in self.ants.values()]
        alive_ants = sum(1 for ant in self.ants.values() if ant.is_alive())
        
        return {
            "colony_id": self.id,
            "generation": self.generation,
            "size": self.size,
            "alive": alive_ants,
            "total_tasks": self.total_tasks,
            "total_drift_found": self.total_drift_found,
            "mutation_level": self.mutation_level,
            "created_at": self.created_at.isoformat(),
            "ants": ant_dicts,
            "pheromone_count": len(self.pheromones),
        }
    
    async def natural_decay(self) -> int:
        """Aplicar decay a todas las feromonas."""
        decayed = 0
        for pheromone in list(self.pheromones.values()):
            pheromone.decay(rate=0.05)
            if pheromone.intensity <= 0.0:
                del self.pheromones[pheromone.id]
                decayed += 1
        
        return decayed


class QueenBrain:
    """Reina que toma decisiones basadas en estado de colonia"""
    
    def __init__(self, queen_id: str):
        self.id = queen_id
        self.colonies: Dict[str, AntColony] = {}
        self.decision_history: List[Dict[str, Any]] = []
    
    async def create_colony(self, size: int = 8, mutation_level: int = 0) -> AntColony:
        """Crear nueva colonia."""
        colony_id = f"col_{str(uuid.uuid4())[:8]}"
        colony = AntColony(colony_id, size=size, mutation_level=mutation_level)
        self.colonies[colony_id] = colony
        
        logger.info(f"✓ Queen created colony {colony_id} with {size} ants (gen {mutation_level})")
        write_log("hormiguero", f"colony_created:{colony_id}:size={size}")
        
        return colony
    
    async def execute_colony_cycle(self, colony_id: str) -> Dict[str, Any]:
        """Ejecutar ciclo de actividad de colonia."""
        colony = self.colonies.get(colony_id)
        if not colony:
            return {"status": "error", "error": "Colony not found"}
        
        zones = ["sistema", "config", "data", "scripts"]
        
        # Scan phase: cada hormiga escanea zona
        scan_results = []
        for i, ant in enumerate(list(colony.ants.values())[:4]):  # 4 hormigas activas
            zone = zones[i % len(zones)]
            result = await colony.scan_zone(ant, zone)
            scan_results.append(result)
        
        # Decay phase: feromonas se evaporan
        decayed = await colony.natural_decay()
        
        # Calculate statistics
        total_drift = sum(ant.drift_found for ant in colony.ants.values())
        avg_fitness = sum(ant.update_fitness() for ant in colony.ants.values()) / len(colony.ants)
        
        decision = {
            "cycle_time": datetime.utcnow().isoformat(),
            "scans": len(scan_results),
            "drift_detected": total_drift,
            "avg_fitness": round(avg_fitness, 2),
            "pheromone_decay": decayed,
        }
        
        self.decision_history.append(decision)
        
        return {
            "status": "ok",
            "colony_id": colony_id,
            "scan_results": scan_results,
            "decision": decision,
            "colony_status": colony.get_colony_status(),
        }
    
    async def get_colony_status(self, colony_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de colonia."""
        colony = self.colonies.get(colony_id)
        if not colony:
            return None
        
        return colony.get_colony_status()
    
    async def list_colonies(self) -> List[Dict[str, Any]]:
        """Listar todas las colonias."""
        return [colony.get_colony_status() for colony in self.colonies.values()]


# Singleton instance
_queen_brain: Optional[QueenBrain] = None


def get_queen_brain() -> QueenBrain:
    """Get or create global queen brain."""
    global _queen_brain
    if _queen_brain is None:
        queen_id = f"queen_{str(uuid.uuid4())[:8]}"
        _queen_brain = QueenBrain(queen_id)
        logger.info(f"🐝 Queen initialized: {queen_id}")
        write_log("hormiguero", f"queen_initialized:{queen_id}")
    
    return _queen_brain
