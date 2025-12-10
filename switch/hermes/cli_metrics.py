"""
CLI Metrics — Rastreo de performance, costo, confiabilidad de engines.

Mantiene histórico de:
- Latencias
- Costos
- Tasas de éxito
- Fallos

Usado para optimización de routing y feedback loop.
"""

import logging
from typing import Dict, List, Optional, Any
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExecutionMetric:
    """Métrica individual de una ejecución."""
    
    def __init__(
        self,
        engine_name: str,
        task_type: str,
        latency_ms: int,
        tokens_used: int,
        cost: float,
        success: bool,
        error_msg: Optional[str] = None,
    ):
        self.engine_name = engine_name
        self.task_type = task_type
        self.latency_ms = latency_ms
        self.tokens_used = tokens_used
        self.cost = cost
        self.success = success
        self.error_msg = error_msg
        self.timestamp = datetime.now()


class EngineMetricsTracker:
    """Rastreo de métricas por engine."""
    
    def __init__(self, max_history: int = 1000):
        self.engine_name: str = ""
        self.metrics: deque = deque(maxlen=max_history)
        self.total_cost: float = 0.0
        self.total_tokens: int = 0
        self.total_requests: int = 0
        self.failures: int = 0
    
    def record_metric(self, metric: ExecutionMetric) -> None:
        """Registrar métrica de ejecución."""
        self.metrics.append(metric)
        self.total_cost += metric.cost
        self.total_tokens += metric.tokens_used
        self.total_requests += 1
        if not metric.success:
            self.failures += 1
    
    def get_success_rate(self) -> float:
        """Obtener tasa de éxito (0-1)."""
        if not self.metrics:
            return 1.0
        successes = sum(1 for m in self.metrics if m.success)
        return successes / len(self.metrics)
    
    def get_avg_latency_ms(self) -> float:
        """Latencia promedio."""
        if not self.metrics:
            return 0.0
        return sum(m.latency_ms for m in self.metrics) / len(self.metrics)
    
    def get_avg_cost_per_request(self) -> float:
        """Costo promedio por solicitud."""
        if not self.total_requests:
            return 0.0
        return self.total_cost / self.total_requests
    
    def get_avg_tokens_per_request(self) -> float:
        """Tokens promedio por solicitud."""
        if not self.total_requests:
            return 0.0
        return self.total_tokens / self.total_requests
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas resumidas."""
        recent_metrics = list(self.metrics)[-100:] if self.metrics else []  # Últimas 100
        
        return {
            "total_requests": self.total_requests,
            "failures": self.failures,
            "success_rate": round(self.get_success_rate() * 100, 2),
            "avg_latency_ms": round(self.get_avg_latency_ms(), 1),
            "avg_cost_per_request": round(self.get_avg_cost_per_request(), 4),
            "total_cost": round(self.total_cost, 2),
            "avg_tokens_per_request": round(self.get_avg_tokens_per_request(), 0),
        }
    
    def get_recent_metrics(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Obtener últimas N métricas."""
        recent = list(self.metrics)[-last_n:]
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "task_type": m.task_type,
                "latency_ms": m.latency_ms,
                "cost": m.cost,
                "success": m.success,
                "error": m.error_msg,
            }
            for m in recent
        ]


class GlobalMetricsCollector:
    """Colector global de métricas de todos los engines."""
    
    def __init__(self):
        self.engines: Dict[str, EngineMetricsTracker] = {}
    
    def register_engine(self, engine_name: str) -> None:
        """Registrar engine para rastreo."""
        if engine_name not in self.engines:
            tracker = EngineMetricsTracker()
            tracker.engine_name = engine_name
            self.engines[engine_name] = tracker
            logger.info(f"Registered metrics tracker for {engine_name}")
    
    def record_execution(
        self,
        engine_name: str,
        task_type: str,
        latency_ms: int,
        tokens_used: int,
        cost: float,
        success: bool,
        error_msg: Optional[str] = None,
    ) -> None:
        """Registrar ejecución."""
        self.register_engine(engine_name)
        
        metric = ExecutionMetric(
            engine_name=engine_name,
            task_type=task_type,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            cost=cost,
            success=success,
            error_msg=error_msg,
        )
        
        self.engines[engine_name].record_metric(metric)
    
    def get_engine_stats(self, engine_name: str) -> Optional[Dict[str, Any]]:
        """Obtener estadísticas de un engine."""
        if engine_name not in self.engines:
            return None
        return self.engines[engine_name].get_stats()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Obtener estadísticas de todos los engines."""
        return {
            name: tracker.get_stats()
            for name, tracker in self.engines.items()
        }
    
    def get_best_engine_for_task(self, task_type: str) -> Optional[str]:
        """Obtener engine con mejor rendimiento para tarea."""
        best_engine = None
        best_score = float('-inf')
        
        for name, tracker in self.engines.items():
            # Score: éxito - (latencia / 1000) - (costo / 0.01)
            success_rate = tracker.get_success_rate()
            latency_factor = tracker.get_avg_latency_ms() / 1000.0
            cost_factor = tracker.get_avg_cost_per_request() / 0.01
            
            score = success_rate - latency_factor - cost_factor
            
            if score > best_score:
                best_score = score
                best_engine = name
        
        return best_engine
    
    def get_ranking(self) -> List[tuple]:
        """Obtener engines ordenados por performance."""
        rankings = []
        
        for name, tracker in self.engines.items():
            success_rate = tracker.get_success_rate()
            avg_latency = tracker.get_avg_latency_ms()
            avg_cost = tracker.get_avg_cost_per_request()
            
            rankings.append((
                name,
                {
                    "success_rate": round(success_rate * 100, 2),
                    "latency_ms": round(avg_latency, 1),
                    "cost": round(avg_cost, 4),
                    "requests": tracker.total_requests,
                }
            ))
        
        # Sort by success rate descending, then by latency ascending
        rankings.sort(key=lambda x: (x[1]["success_rate"], -x[1]["latency_ms"]), reverse=True)
        return rankings
    
    def generate_report(self) -> Dict[str, Any]:
        """Generar reporte de performance."""
        all_stats = self.get_all_stats()
        total_cost = sum(s["total_cost"] for s in all_stats.values())
        total_requests = sum(s["total_requests"] for s in all_stats.values())
        
        return {
            "summary": {
                "total_requests": total_requests,
                "total_cost": round(total_cost, 2),
                "avg_cost_per_request": round(total_cost / total_requests if total_requests > 0 else 0, 4),
            },
            "engines": all_stats,
            "ranking": [{"engine": name, "stats": stats} for name, stats in self.get_ranking()],
        }


# Instancia global
_metrics_collector: Optional[GlobalMetricsCollector] = None


def get_metrics_collector() -> GlobalMetricsCollector:
    """Obtener instancia global de colector de métricas."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = GlobalMetricsCollector()
    return _metrics_collector
