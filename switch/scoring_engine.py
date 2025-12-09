"""
SWITCH Scoring Engine v6.2
Implementa fórmula canónica de scoring con soporte para modos y feromonas
"""

import json
import os
from typing import Dict, Any, Tuple
from pathlib import Path


class SwitchScoringEngine:
    """Motor de scoring canónico para VX11"""
    
    # Modos y sus pesos asociados
    MODES = {
        "eco": {"w_q": 0.3, "w_l": 0.3, "w_c": 0.4, "w_f": 0.0},
        "balanced": {"w_q": 0.4, "w_l": 0.3, "w_c": 0.3, "w_f": 0.0},
        "high-perf": {"w_q": 0.6, "w_l": 0.2, "w_c": 0.2, "w_f": 0.0},
        "critical": {"w_q": 0.7, "w_l": 0.2, "w_c": 0.1, "w_f": 0.0},
    }
    
    # Engines canónicos
    ENGINES = {
        "local_gguf_small": {
            "type": "local",
            "tags": ["fast", "cheap"],
            "max_ctx": 4096,
            "latency_ms": 150,
            "quality": 0.6,
            "cost": 0.0
        },
        "deepseek_auto": {
            "type": "remote",
            "tags": ["reasoning", "heavy"],
            "max_ctx": 16000,
            "latency_ms": 1200,
            "quality": 0.9,
            "cost": 2.0
        },
        "gpt5_mini": {
            "type": "remote",
            "tags": ["balanced"],
            "max_ctx": 16000,
            "latency_ms": 800,
            "quality": 0.8,
            "cost": 1.2
        },
        "hermes_cli": {
            "type": "tool",
            "tags": ["cli", "commands"],
            "latency_ms": 200,
            "quality": 1.0,
            "cost": 0.0
        },
        "hermes_playwright": {
            "type": "tool",
            "tags": ["browser", "scraping"],
            "latency_ms": 5000,
            "quality": 1.0,
            "cost": 0.0
        }
    }
    
    def __init__(self, pheromone_file: str = "switch/pheromones.json"):
        self.pheromone_file = pheromone_file
        self.pheromones = self._load_pheromones()
    
    def _load_pheromones(self) -> Dict[str, Dict[str, float]]:
        """Carga feromonas desde JSON"""
        if os.path.isfile(self.pheromone_file):
            try:
                with open(self.pheromone_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Inicializar feromonas en 0 (neutral)
        pheros = {}
        for engine_id in self.ENGINES.keys():
            pheros[engine_id] = {
                "value": 0.0,
                "decay": 0.95,
                "last_update": None,
                "successes": 0,
                "failures": 0,
            }
        
        return pheros
    
    def _save_pheromones(self):
        """Persiste feromonas a JSON"""
        try:
            os.makedirs(os.path.dirname(self.pheromone_file), exist_ok=True)
            with open(self.pheromone_file, 'w') as f:
                json.dump(self.pheromones, f, indent=2)
        except Exception as e:
            print(f"Error saving pheromones: {e}")
    
    def score(self, engine_id: str, context7: Dict[str, Any] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Calcula score para engine usando fórmula canónica:
        score = w_q*quality + w_l*(1-latency) + w_c*(1-cost) + w_f*pheromone
        
        Returns: (score, debug_info)
        """
        if engine_id not in self.ENGINES:
            return (0.0, {"error": f"Engine {engine_id} not found"})
        
        engine = self.ENGINES[engine_id]
        mode = "balanced"
        
        # Extraer modo desde context-7
        if context7 and "layer7_meta" in context7:
            mode = context7["layer7_meta"].get("mode", "balanced")
        
        if mode not in self.MODES:
            mode = "balanced"
        
        weights = self.MODES[mode]
        
        # Normalización
        max_quality = 1.0
        max_latency = 5000.0  # ms
        max_cost = 10.0
        
        quality_norm = engine["quality"] / max_quality
        latency_norm = min(engine["latency_ms"] / max_latency, 1.0)
        cost_norm = min(engine["cost"] / max_cost, 1.0)
        pheromone_val = self.pheromones.get(engine_id, {}).get("value", 0.0)
        
        # Fórmula
        score = (
            weights["w_q"] * quality_norm +
            weights["w_l"] * (1 - latency_norm) +
            weights["w_c"] * (1 - cost_norm) +
            weights["w_f"] * pheromone_val
        )
        
        debug_info = {
            "engine_id": engine_id,
            "mode": mode,
            "weights": weights,
            "quality_norm": quality_norm,
            "latency_norm": latency_norm,
            "cost_norm": cost_norm,
            "pheromone": pheromone_val,
            "final_score": score
        }
        
        return (score, debug_info)
    
    def choose_best(self, context7: Dict[str, Any] = None) -> Tuple[str, float, Dict[str, Any]]:
        """
        Elige el mejor engine según scoring completo.
        Returns: (engine_id, score, debug_info)
        """
        best_engine = None
        best_score = -1.0
        best_debug = {}
        
        for engine_id in self.ENGINES.keys():
            score, debug = self.score(engine_id, context7)
            
            if score > best_score:
                best_score = score
                best_engine = engine_id
                best_debug = debug
        
        return (best_engine, best_score, best_debug)
    
    def update_pheromone(self, engine_id: str, outcome: str):
        """
        Actualiza feromona basado en outcome.
        outcome: "success"|"failure"|"timeout"|"partial"
        """
        if engine_id not in self.pheromones:
            return
        
        phero = self.pheromones[engine_id]
        
        # Aplicar decay
        phero["value"] = phero["value"] * phero["decay"]
        
        # Aplicar reward
        if outcome == "success":
            reward = 0.2
            phero["successes"] = phero.get("successes", 0) + 1
        elif outcome == "failure":
            reward = -0.3
            phero["failures"] = phero.get("failures", 0) + 1
        elif outcome == "timeout":
            reward = -0.1
        elif outcome == "partial":
            reward = 0.05
        else:
            reward = 0.0
        
        phero["value"] = max(-1.0, min(1.0, phero["value"] + reward))
        phero["last_update"] = __import__("datetime").datetime.utcnow().isoformat()
        
        self._save_pheromones()


# Instancia global
_scoring_engine = None


def get_scoring_engine() -> SwitchScoringEngine:
    """Retorna instancia singleton del scoring engine"""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = SwitchScoringEngine()
    return _scoring_engine
