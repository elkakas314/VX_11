"""
Metrics Endpoints Mixin — Añadir a todos los módulos
"""

from fastapi import APIRouter
import psutil
from datetime import datetime
import logging

log = logging.getLogger(__name__)


def create_metrics_router() -> APIRouter:
    """Crea router con endpoints de métricas estándar."""
    router = APIRouter(prefix="/metrics", tags=["metrics"])
    
    # Almacenamiento simple de métricas
    _metrics_state = {
        "requests_count": 0,
        "queue_size": 0,
        "last_request": None
    }
    
    @router.get("/cpu")
    async def get_cpu_metrics():
        """Retorna métrica de CPU."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            return {
                "metric": "cpu",
                "value": cpu_percent,
                "unit": "percent",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except:
            return {"metric": "cpu", "value": 0, "unit": "percent"}
    
    @router.get("/memory")
    async def get_memory_metrics():
        """Retorna métrica de memoria."""
        try:
            memory = psutil.virtual_memory()
            return {
                "metric": "memory",
                "value": memory.percent,
                "unit": "percent",
                "available_mb": memory.available / (1024 * 1024),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except:
            return {"metric": "memory", "value": 0, "unit": "percent"}
    
    @router.get("/queue")
    async def get_queue_metrics():
        """Retorna tamaño de cola (placeholder)."""
        return {
            "metric": "queue",
            "value": _metrics_state["queue_size"],
            "unit": "items",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @router.get("/throughput")
    async def get_throughput_metrics():
        """Retorna throughput de requests."""
        return {
            "metric": "throughput",
            "value": _metrics_state["requests_count"],
            "unit": "requests",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def increment_request_count():
        _metrics_state["requests_count"] += 1
    
    return router
