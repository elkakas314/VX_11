"""
FASE 4: Pheromone Engine v6.2
Motor de feromonas para optimización adaptativa de engines
"""

import json
import os
from typing import Dict, Any
from datetime import datetime
from pathlib import Path


class PheromoneEngine:
    """Motor de feromonas con decay y rewards"""
    
    # Rewards canónicos
    REWARDS = {
        "success": 0.2,
        "partial_success": 0.05,
        "timeout": -0.1,
        "failure": -0.3,
        "error": -0.25,
    }
    
    # Decay factor (aplicado cada actualización)
    DECAY_FACTOR = 0.95
    
    # Límites de feromona
    MIN_PHEROMONE = -1.0
    MAX_PHEROMONE = 1.0
    
    def __init__(self, file_path: str = "switch/pheromones.json"):
        self.file_path = file_path
        self.pheromones = self._load()
    
    def _load(self) -> Dict[str, Dict[str, Any]]:
        """Carga feromonas desde JSON"""
        if os.path.isfile(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    # Validar estructura
                    if isinstance(data, dict) and all(
                        isinstance(v, dict) and "value" in v 
                        for v in data.values()
                    ):
                        return data
            except:
                pass
        
        # Retornar estructura vacía
        return {}
    
    def _save(self):
        """Persiste feromonas a JSON"""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w') as f:
                json.dump(self.pheromones, f, indent=2)
        except Exception as e:
            print(f"Error saving pheromones: {e}")
    
    def get(self, engine_id: str, default: float = 0.0) -> float:
        """Obtiene valor actual de feromona para engine"""
        if engine_id not in self.pheromones:
            return default
        return self.pheromones[engine_id].get("value", default)
    
    def update(self, engine_id: str, outcome: str) -> Dict[str, Any]:
        """
        Actualiza feromona basado en outcome.
        
        Retorna: {"engine_id": ..., "old_value": ..., "new_value": ..., "reward": ..., "timestamp": ...}
        """
        if engine_id not in self.pheromones:
            self.pheromones[engine_id] = {
                "value": 0.0,
                "decay": self.DECAY_FACTOR,
                "last_update": None,
                "successes": 0,
                "failures": 0,
            }
        
        phero = self.pheromones[engine_id]
        old_value = phero["value"]
        
        # 1. Aplicar decay
        phero["value"] = phero["value"] * self.DECAY_FACTOR
        
        # 2. Obtener reward
        reward = self.REWARDS.get(outcome, 0.0)
        
        # 3. Aplicar reward
        phero["value"] = max(
            self.MIN_PHEROMONE,
            min(self.MAX_PHEROMONE, phero["value"] + reward)
        )
        
        # 4. Actualizar metadata
        phero["last_update"] = datetime.utcnow().isoformat()
        if outcome == "success":
            phero["successes"] = phero.get("successes", 0) + 1
        elif outcome in ["failure", "error", "timeout"]:
            phero["failures"] = phero.get("failures", 0) + 1
        
        # 5. Persistir
        self._save()
        
        return {
            "engine_id": engine_id,
            "old_value": old_value,
            "new_value": phero["value"],
            "reward": reward,
            "decay_factor": self.DECAY_FACTOR,
            "outcome": outcome,
            "timestamp": phero["last_update"],
            "successes": phero.get("successes", 0),
            "failures": phero.get("failures", 0),
        }
    
    def decay_all(self) -> Dict[str, float]:
        """
        Aplica decay a TODAS las feromonas.
        Retorna: {"engine_id": new_value, ...}
        """
        result = {}
        for engine_id in self.pheromones.keys():
            phero = self.pheromones[engine_id]
            old_value = phero["value"]
            phero["value"] = phero["value"] * self.DECAY_FACTOR
            phero["last_update"] = datetime.utcnow().isoformat()
            result[engine_id] = phero["value"]
        
        self._save()
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumen de estado de feromonas"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "engines": {
                engine_id: {
                    "value": phero.get("value", 0.0),
                    "successes": phero.get("successes", 0),
                    "failures": phero.get("failures", 0),
                    "last_update": phero.get("last_update"),
                }
                for engine_id, phero in self.pheromones.items()
            },
            "total_successes": sum(p.get("successes", 0) for p in self.pheromones.values()),
            "total_failures": sum(p.get("failures", 0) for p in self.pheromones.values()),
        }


# Instancia global
_pheromone_engine = None


def get_pheromone_engine() -> PheromoneEngine:
    """Retorna instancia singleton del pheromone engine"""
    global _pheromone_engine
    if _pheromone_engine is None:
        _pheromone_engine = PheromoneEngine()
    return _pheromone_engine
