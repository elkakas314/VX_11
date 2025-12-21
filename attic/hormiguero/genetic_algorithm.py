"""
FASE 5: Hormiguero Genetic Algorithm v6.2
Algoritmo evolutivo para optimización de parámetros de engines
"""

import random
import json
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class Individual:
    """Un individuo en la población GA"""
    genome: Dict[str, float]  # {param: value}
    fitness: float = 0.0
    age: int = 0
    evaluations: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class GeneticAlgorithm:
    """
    Algoritmo genético para optimización de engines VX11
    
    Parámetros: temperature (0-2), top_k (1-50), frequency_penalty (0-1)
    """
    
    PARAMETER_BOUNDS = {
        "temperature": (0.0, 2.0),
        "top_k": (1.0, 50.0),
        "frequency_penalty": (0.0, 1.0),
        "presence_penalty": (0.0, 1.0),
    }
    
    def __init__(self, population_size: int = 20, generations: int = 100, 
                 mutation_rate: float = 0.1, crossover_rate: float = 0.7):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # Estado evolutivo
        self.population: List[Individual] = []
        self.best_individual: Individual = None
        self.generation: int = 0
        self.history: List[Dict] = []
    
    def _create_random_individual(self) -> Individual:
        """Crea un individuo con parámetros aleatorios"""
        genome = {}
        for param, (lower, upper) in self.PARAMETER_BOUNDS.items():
            genome[param] = random.uniform(lower, upper)
        return Individual(genome=genome)
    
    def initialize_population(self):
        """Inicializa población aleatoria"""
        self.population = [self._create_random_individual() for _ in range(self.population_size)]
        self.best_individual = self.population[0]
    
    def _mutate(self, individual: Individual) -> Individual:
        """Mutación: cambio aleatorio de parámetros"""
        mutant = Individual(
            genome=individual.genome.copy(),
            age=individual.age + 1
        )
        
        for param in mutant.genome.keys():
            if random.random() < self.mutation_rate:
                lower, upper = self.PARAMETER_BOUNDS[param]
                # Gaussian mutation con sigma = 10% del rango
                sigma = (upper - lower) * 0.1
                new_val = mutant.genome[param] + random.gauss(0, sigma)
                # Clip a límites
                mutant.genome[param] = max(lower, min(upper, new_val))
        
        return mutant
    
    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Crossover: combina dos padres"""
        child1 = Individual(genome={}, age=0)
        child2 = Individual(genome={}, age=0)
        
        for param in self.PARAMETER_BOUNDS.keys():
            if random.random() < 0.5:
                child1.genome[param] = parent1.genome[param]
                child2.genome[param] = parent2.genome[param]
            else:
                child1.genome[param] = parent2.genome[param]
                child2.genome[param] = parent1.genome[param]
        
        return child1, child2
    
    def evaluate_individual(self, individual: Individual, fitness_func) -> float:
        """
        Evalúa fitness de un individuo.
        fitness_func: callable(genome) -> float (0-1)
        """
        fitness = fitness_func(individual.genome)
        individual.fitness = fitness
        individual.evaluations += 1
        
        # Actualizar best
        if fitness > self.best_individual.fitness:
            self.best_individual = Individual(
                genome=individual.genome.copy(),
                fitness=fitness,
                age=0
            )
        
        return fitness
    
    def step(self, fitness_func) -> Dict[str, Any]:
        """
        Ejecuta una generación del GA.
        Retorna: {"generation": ..., "best_fitness": ..., "avg_fitness": ..., ...}
        """
        self.generation += 1
        
        # Selección (tournament selection)
        selected = []
        for _ in range(self.population_size):
            tournament = random.sample(self.population, k=min(3, self.population_size))
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(winner)
        
        # Reproducción (crossover + mutación)
        new_population = []
        for i in range(0, len(selected), 2):
            parent1 = selected[i]
            parent2 = selected[(i + 1) % len(selected)]
            
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1, parent2
            
            # Mutación
            if random.random() < 0.5:
                child1 = self._mutate(child1)
            if random.random() < 0.5:
                child2 = self._mutate(child2)
            
            new_population.extend([child1, child2])
        
        # Limitar población
        new_population = new_population[:self.population_size]
        
        # Evaluar nuevos individuos
        for ind in new_population:
            if ind.evaluations == 0:
                self.evaluate_individual(ind, fitness_func)
        
        # Elitismo: mantener mejor
        new_population.sort(key=lambda x: x.fitness, reverse=True)
        new_population[0] = self.best_individual
        
        self.population = new_population
        
        # Estadísticas
        fitness_vals = [ind.fitness for ind in self.population]
        avg_fitness = sum(fitness_vals) / len(fitness_vals) if fitness_vals else 0.0
        
        step_info = {
            "generation": self.generation,
            "best_fitness": self.best_individual.fitness,
            "avg_fitness": avg_fitness,
            "best_params": self.best_individual.genome.copy(),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.history.append(step_info)
        
        return step_info
    
    def get_best_params(self) -> Dict[str, float]:
        """Retorna los mejores parámetros encontrados"""
        return self.best_individual.genome.copy() if self.best_individual else {}
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Retorna resumen del historial evolutivo"""
        if not self.history:
            return {}
        
        best_fitnesses = [h["best_fitness"] for h in self.history]
        avg_fitnesses = [h["avg_fitness"] for h in self.history]
        
        return {
            "generations_completed": len(self.history),
            "best_fitness_overall": max(best_fitnesses) if best_fitnesses else 0.0,
            "avg_fitness_final": avg_fitnesses[-1] if avg_fitnesses else 0.0,
            "improvement": best_fitnesses[-1] - best_fitnesses[0] if len(best_fitnesses) > 1 else 0.0,
            "best_params": self.best_individual.genome.copy() if self.best_individual else {},
        }


class HormigueroPheromoneGA:
    """GA integrado con sistema de feromonas para Hormiguero"""
    
    def __init__(self, storage_dir: str = "data/ga_state"):
        self.storage_dir = storage_dir
        self.ga_per_engine: Dict[str, GeneticAlgorithm] = {}
        self.load_state()
    
    def _get_engine_file(self, engine_id: str) -> str:
        """Ruta para estado de GA de un engine"""
        return os.path.join(self.storage_dir, f"ga_{engine_id}.json")
    
    def load_state(self):
        """Carga estado de GA desde archivos"""
        os.makedirs(self.storage_dir, exist_ok=True)
        # Cargar archivos si existen
        # Por ahora inicializar vacío
    
    def save_state(self):
        """Persiste estado de GA"""
        os.makedirs(self.storage_dir, exist_ok=True)
        for engine_id, ga in self.ga_per_engine.items():
            filepath = self._get_engine_file(engine_id)
            try:
                with open(filepath, 'w') as f:
                    json.dump({
                        "engine_id": engine_id,
                        "generation": ga.generation,
                        "best_individual": ga.best_individual.to_dict() if ga.best_individual else None,
                        "history": ga.history[-10:],  # Últimas 10 generaciones
                    }, f, indent=2)
            except Exception as e:
                print(f"Error saving GA state for {engine_id}: {e}")
    
    def get_or_create_ga(self, engine_id: str) -> GeneticAlgorithm:
        """Obtiene o crea GA para un engine"""
        if engine_id not in self.ga_per_engine:
            ga = GeneticAlgorithm(population_size=20, generations=100)
            ga.initialize_population()
            self.ga_per_engine[engine_id] = ga
        return self.ga_per_engine[engine_id]
    
    def optimize_engine(self, engine_id: str, fitness_func, steps: int = 1) -> List[Dict]:
        """Ejecuta `steps` generaciones de GA para un engine"""
        ga = self.get_or_create_ga(engine_id)
        results = []
        
        for _ in range(steps):
            result = ga.step(fitness_func)
            results.append(result)
        
        self.save_state()
        return results
    
    def get_summary_all(self) -> Dict[str, Dict]:
        """Retorna resumen de todos los GA por engine"""
        return {
            engine_id: ga.get_history_summary()
            for engine_id, ga in self.ga_per_engine.items()
        }


# Instancia global
_hormiguero_ga = None


def get_hormiguero_ga() -> HormigueroPheromoneGA:
    """Retorna instancia singleton"""
    global _hormiguero_ga
    if _hormiguero_ga is None:
        _hormiguero_ga = HormigueroPheromoneGA()
    return _hormiguero_ga
