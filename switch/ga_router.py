"""
GA Router para Switch v7.1

Integra Genetic Algorithm en decisiones de routing en tiempo real.

Después de cada solicitud:
1. Registra métricas (latencia, éxito, coste)
2. Actualiza fitness de individuos GA
3. Periódicamente: evoluciona población
4. Usa mejores pesos para scoring

Es un "feedback loop" donde el sistema se optimiza a sí mismo.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from config.forensics import write_log
from switch.ga_optimizer import GeneticAlgorithmOptimizer, GAIndividual
from switch.hermes import get_metrics_collector

logger = logging.getLogger("vx11.switch.ga_router")


class GARouter:
    """Router que usa GA para optimizar decisiones."""

    def __init__(self, ga_optimizer: GeneticAlgorithmOptimizer):
        self.ga = ga_optimizer
        self.metrics = get_metrics_collector()
        self.evolution_interval = 100  # Evolucionar cada 100 requests
        self.request_count = 0
        self.last_evolution = datetime.now()

    def select_engine_with_ga(self, task_type: str) -> str:
        """
        Seleccionar engine usando pesos GA.

        El elite individual contiene pesos que indican qué engine es mejor para cada situación.
        Usamos esos pesos para hacer scoring.

        Args:
            task_type: Tipo de tarea (audio, code, reasoning, etc.)

        Returns:
            Nombre del engine elegido (local, cli, shub, etc.)
        """

        if not self.ga.elite:
            logger.warning("No elite individual in GA, using fallback")
            return "local"  # Fallback

        # Obtener pesos del elite individual
        weights = self.ga.elite.weights

        logger.debug(f"GA weights for {task_type}: {weights}")

        # Seleccionar engine basado en pesos
        best_engine = max(weights.items(), key=lambda x: x[1])[0]

        logger.info(f"GA selected engine: {best_engine} for task_type={task_type}")

        return best_engine

    def record_execution_result(
        self,
        engine_name: str,
        task_type: str,
        latency_ms: float,
        success: bool,
        cost: float = 0.0,
        tokens: int = 0,
        tokens_used: int = None,
    ) -> None:
        """
        Registrar resultado de ejecución y actualizar fitness GA.

        Esto es el feedback loop que hace que el GA se optimice.

        Args:
            engine_name: Engine usado
            task_type: Tipo de tarea
            latency_ms: Latencia en ms
            success: Si fue exitoso
            cost: Costo en $
            tokens: Tokens usados
        """

        try:
            # Registrar en métricas generales
            # Compatibilidad: aceptar `tokens_used` o `tokens`
            if tokens_used is not None:
                tokens = int(tokens_used)

            self.metrics.record_execution(
                engine_name=engine_name,
                task_type=task_type,
                latency_ms=int(latency_ms),
                tokens_used=tokens,
                cost=cost,
                success=success,
            )

            # Actualizar fitness del GA basado en métrica
            # Fitness = éxito * (1 / latencia) * (1 / coste)
            fitness_contribution = 0.0
            if success:
                # Success: beneficio positivo
                fitness_contribution += 1.0
            else:
                # Failure: penalidad
                fitness_contribution -= 1.0

            # Penalizar latencia alta
            if latency_ms > 0:
                fitness_contribution *= max(0.1, 1.0 / (1.0 + latency_ms / 1000.0))

            # Penalizar coste alto
            if cost > 0:
                fitness_contribution *= max(0.1, 1.0 / (1.0 + cost))

            logger.debug(
                f"Fitness contribution: {fitness_contribution} for {engine_name}"
            )

            # Incrementar request counter y chequear si evolucionar
            self.request_count += 1
            self._check_evolution()

        except Exception as e:
            logger.error(f"Error recording execution result: {e}")
            write_log("switch.ga_router", f"record_error:{e}", level="ERROR")

    def _check_evolution(self) -> None:
        """
        Chequear si es hora de evolucionar la población.

        Se ejecuta cada N requests o cada T tiempo.
        """

        # Condición 1: Cada N requests
        if self.request_count >= self.evolution_interval:
            self._evolve()
            return

        # Condición 2: Cada T tiempo (e.g., 1 hora)
        elapsed = (datetime.now() - self.last_evolution).total_seconds()
        if elapsed > 3600:  # 1 hora
            self._evolve()
            return

    def _evolve(self) -> None:
        """Disparar evolución de la población GA."""
        try:
            logger.info(
                f"GA Evolution triggered: generation={self.ga.generation}, requests={self.request_count}"
            )

            # Evolucionar
            self.ga.evolve()

            # Loguear
            write_log(
                "switch.ga_router",
                f"evolution:generation={self.ga.generation}:elite_fitness={self.ga.elite.fitness if self.ga.elite else 'none'}",
            )

            # Reset counters
            self.request_count = 0
            self.last_evolution = datetime.now()

            logger.info(
                f"GA Evolution complete: new elite fitness={self.ga.elite.fitness if self.ga.elite else 'none'}"
            )

        except Exception as e:
            logger.error(f"Error during evolution: {e}")
            write_log("switch.ga_router", f"evolution_error:{e}", level="ERROR")

    def get_ga_status(self) -> Dict[str, Any]:
        """Obtener estado actual del GA."""
        return {
            "enabled": True,
            "generation": self.ga.generation,
            "request_count": self.request_count,
            "evolution_interval": self.evolution_interval,
            "last_evolution": (
                self.last_evolution.isoformat() if self.last_evolution else None
            ),
            "elite_fitness": self.ga.elite.fitness if self.ga.elite else None,
            "population_summary": self.ga.get_population_summary(),
        }


# Instancia global
_ga_router: Optional[GARouter] = None


def get_ga_router(ga_optimizer: GeneticAlgorithmOptimizer) -> GARouter:
    """Obtener o crear instancia global de GA Router."""
    global _ga_router
    if not _ga_router:
        _ga_router = GARouter(ga_optimizer)
    return _ga_router
