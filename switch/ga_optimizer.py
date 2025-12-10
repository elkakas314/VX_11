"""
Genetic Algorithm (GA) Optimizer para Switch

Optimiza pesos de routing basándose en historial de ejecuciones.
Población = conjunto de configuraciones de pesos
Fitness = éxito + latencia + coste (métricas)
Generación = mutación + crossover de pesos
"""

import random
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from pathlib import Path

log = logging.getLogger("vx11.switch.ga_optimizer")


@dataclass
class GAIndividual:
    """Individuo de la población GA (configuración de pesos)"""
    
    id: str = ""
    weights: Dict[str, float] = field(default_factory=dict)  # {engine_id: weight}
    fitness: float = 0.0
    generation: int = 0
    age: int = 0
    success_rate: float = 0.0
    avg_latency: float = 0.0
    avg_cost: float = 0.0
    executions: int = 0
    created_at: str = ""
    
    def normalize_weights(self):
        """Normaliza pesos a suma = 1.0"""
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def mutate(self, mutation_rate: float = 0.1, intensity: float = 0.2):
        """Mutación: cambiar pesos aleatoriamente"""
        for engine_id in self.weights.keys():
            if random.random() < mutation_rate:
                delta = random.uniform(-intensity, intensity)
                self.weights[engine_id] = max(0.0, self.weights[engine_id] + delta)
        self.normalize_weights()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializar para BD"""
        return {
            "id": self.id,
            "weights": self.weights,
            "fitness": self.fitness,
            "generation": self.generation,
            "age": self.age,
            "success_rate": self.success_rate,
            "avg_latency": self.avg_latency,
            "avg_cost": self.avg_cost,
            "executions": self.executions,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GAIndividual":
        """Deserializar desde BD"""
        ind = cls(
            id=data.get("id", ""),
            weights=data.get("weights", {}),
            fitness=data.get("fitness", 0.0),
            generation=data.get("generation", 0),
            age=data.get("age", 0),
            success_rate=data.get("success_rate", 0.0),
            avg_latency=data.get("avg_latency", 0.0),
            avg_cost=data.get("avg_cost", 0.0),
            executions=data.get("executions", 0),
            created_at=data.get("created_at", ""),
        )
        return ind


class GeneticAlgorithmOptimizer:
    """
    Optimizador GA para los pesos de routing del Switch.
    
    Mantiene población de configuraciones, evalúa fitness,
    y evoluciona hacia configuraciones de mayor rendimiento.
    """
    
    def __init__(self, 
                 population_size: int = 10,
                 engine_ids: List[str] = None,
                 persistence_path: str = "switch/ga_population.json"):
        self.population_size = population_size
        self.engine_ids = engine_ids or ["local_gguf", "deepseek_r1", "cli", "shub"]
        self.persistence_path = persistence_path
        self.generation = 0
        self.population: List[GAIndividual] = []
        self.elite: GAIndividual = None
        self.history: List[Dict[str, Any]] = []
        
        self._load_or_initialize()
    
    def _load_or_initialize(self):
        """Carga población desde disco o inicializa aleatoria"""
        path = Path(self.persistence_path)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.generation = data.get("generation", 0)
                    self.population = [
                        GAIndividual.from_dict(ind_data)
                        for ind_data in data.get("population", [])
                    ]
                    if self.population:
                        self.elite = max(self.population, key=lambda x: x.fitness)
                    log.info(f"GA: Población cargada desde {path} (gen {self.generation})")
            except Exception as e:
                log.warning(f"GA: Error cargando población: {e}, inicializando nueva")
                self._initialize_random()
        else:
            self._initialize_random()
    
    def _initialize_random(self):
        """Inicializa población aleatoria"""
        for i in range(self.population_size):
            weights = {
                engine_id: random.uniform(0.1, 1.0)
                for engine_id in self.engine_ids
            }
            ind = GAIndividual(
                id=f"individual_{i:03d}_{self.generation}",
                weights=weights,
                generation=self.generation,
                created_at=datetime.utcnow().isoformat(),
            )
            ind.normalize_weights()
            self.population.append(ind)
        
        self.elite = self.population[0]
        log.info(f"GA: Población aleatoria inicializada ({self.population_size} individuos)")
    
    def _persist(self):
        """Guarda población a disco"""
        try:
            Path(self.persistence_path).parent.mkdir(parents=True, exist_ok=True)
            data = {
                "generation": self.generation,
                "elite": self.elite.to_dict() if self.elite else None,
                "population": [ind.to_dict() for ind in self.population],
                "history": self.history[-100:],  # Últimas 100 generaciones
            }
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error(f"GA: Error persistiendo población: {e}")
    
    def evaluate_fitness(self, individual: GAIndividual, 
                        metrics: Dict[str, float] = None) -> float:
        """
        Evalúa fitness de un individuo.
        
        Fitness = éxito * (1 - latencia_norm) * (1 - coste_norm)
        
        Args:
            individual: Individuo a evaluar
            metrics: Métricas de ejecución {success_rate, avg_latency, avg_cost}
        
        Returns:
            Fitness score (0-1)
        """
        if not metrics:
            # Sin métricas aún: fitness aleatorio
            return random.uniform(0.3, 0.7)
        
        success_rate = metrics.get("success_rate", 0.5)
        latency_norm = min(metrics.get("avg_latency", 0) / 5000.0, 1.0)  # Normalizar a 5s
        cost_norm = min(metrics.get("avg_cost", 0) / 10.0, 1.0)  # Normalizar a $10
        
        fitness = success_rate * (1 - latency_norm * 0.3) * (1 - cost_norm * 0.2)
        return min(max(fitness, 0.0), 1.0)
    
    def record_execution(self, individual: GAIndividual, 
                        success: bool, latency_ms: float, cost: float):
        """Registra ejecución para actualizar fitness"""
        individual.executions += 1
        
        # Actualizar métricas con promedio móvil
        if individual.success_rate == 0:
            individual.success_rate = 1.0 if success else 0.0
            individual.avg_latency = latency_ms
            individual.avg_cost = cost
        else:
            alpha = 0.1  # Factor de suavizado
            individual.success_rate = (
                individual.success_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
            )
            individual.avg_latency = individual.avg_latency * (1 - alpha) + latency_ms * alpha
            individual.avg_cost = individual.avg_cost * (1 - alpha) + cost * alpha
        
        metrics = {
            "success_rate": individual.success_rate,
            "avg_latency": individual.avg_latency,
            "avg_cost": individual.avg_cost,
        }
        individual.fitness = self.evaluate_fitness(individual, metrics)
    
    def evolve(self) -> List[GAIndividual]:
        """
        Evoluciona población: selección + crossover + mutación.
        
        Returns:
            Nueva población
        """
        self.generation += 1
        
        # Selección: top 50% por fitness
        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        elite_count = max(1, self.population_size // 2)
        elite_pool = sorted_pop[:elite_count]
        
        # Actualizar elite global
        if elite_pool[0].fitness > (self.elite.fitness if self.elite else 0):
            self.elite = elite_pool[0]
            log.info(f"GA: Nuevo elite encontrado (gen {self.generation}, fitness={self.elite.fitness:.4f})")
        
        # Nueva población: élite + mutantes + crossovers
        new_population = []
        
        # Copiar élite
        for parent in elite_pool:
            child = GAIndividual(
                id=f"individual_{len(new_population):03d}_{self.generation}",
                weights=dict(parent.weights),
                generation=self.generation,
                created_at=datetime.utcnow().isoformat(),
            )
            child.age = parent.age + 1
            new_population.append(child)
        
        # Mutantes
        while len(new_population) < self.population_size:
            parent = random.choice(elite_pool)
            child = GAIndividual(
                id=f"individual_{len(new_population):03d}_{self.generation}",
                weights=dict(parent.weights),
                generation=self.generation,
                created_at=datetime.utcnow().isoformat(),
            )
            child.mutate(mutation_rate=0.15, intensity=0.3)
            new_population.append(child)
        
        self.population = new_population
        
        # Guardar historial
        self.history.append({
            "generation": self.generation,
            "best_fitness": self.elite.fitness,
            "avg_fitness": sum(ind.fitness for ind in self.population) / len(self.population),
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        self._persist()
        
        log.info(f"GA: Evolución completada (gen {self.generation})")
        return self.population
    
    def get_best_weights(self) -> Dict[str, float]:
        """Retorna los pesos del mejor individuo"""
        if not self.elite:
            return {engine_id: 1.0 / len(self.engine_ids) for engine_id in self.engine_ids}
        return dict(self.elite.weights)
    
    def get_population_summary(self) -> Dict[str, Any]:
        """Retorna resumen de la población"""
        if not self.population:
            return {}
        
        fitness_values = [ind.fitness for ind in self.population]
        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "best_fitness": max(fitness_values),
            "avg_fitness": sum(fitness_values) / len(fitness_values),
            "worst_fitness": min(fitness_values),
            "elite_id": self.elite.id if self.elite else None,
            "elite_fitness": self.elite.fitness if self.elite else 0.0,
            "history_length": len(self.history),
        }
