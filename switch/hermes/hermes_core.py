"""
Hermes Core — Rol de gestor de recursos en VX11.

Responsabilidades:
- Proveer inventario de engines disponibles (CLI, HF, locales)
- Mantener métricas de performance
- Sugerir engines (NO decide, solo sugiere)
- Gestionar caché y fallbacks

Hermes es agnóstico. Switch es el que decide.
Hermes proporciona información de calidad.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .cli_registry import get_cli_registry, EngineType
from .hf_scanner import get_hf_scanner
from .local_scanner import get_local_scanner

logger = logging.getLogger(__name__)


class HermesCore:
    """Núcleo del rol Hermes."""
    
    def __init__(self):
        self.cli_registry = get_cli_registry()
        self.hf_scanner = get_hf_scanner()
        self.local_scanner = get_local_scanner()
        
        self.initialized_at = datetime.now()
        self.request_count = 0
    
    async def initialize(self) -> None:
        """Inicializar Hermes (scan de modelos locales, etc.)."""
        logger.info("Initializing Hermes...")
        
        # Scan local models
        count = self.local_scanner.scan_directory()
        logger.info(f"✓ Scanned {count} local models")
        
        # Validate local models
        results = self.local_scanner.validate_all()
        valid_count = sum(1 for v in results.values() if v)
        logger.info(f"✓ Validated {valid_count}/{len(results)} models")
    
    def get_available_engines(self) -> Dict[str, Any]:
        """Obtener inventario completo de engines disponibles."""
        self.request_count += 1
        
        return {
            "cli_engines": [
                {
                    "name": e.name,
                    "type": e.engine_type.value,
                    "max_tokens": e.max_tokens,
                    "latency_ms": e.avg_latency_ms,
                    "cost_per_1k_input": e.cost_per_1k_input,
                    "available": e.available,
                }
                for e in self.cli_registry.list_available_engines()
            ],
            "local_models": self.local_scanner.to_dict(),
            "metadata": {
                "uptime_seconds": (datetime.now() - self.initialized_at).total_seconds(),
                "requests_served": self.request_count,
            }
        }
    
    def get_engine_by_type(self, engine_type: str) -> Optional[Dict[str, Any]]:
        """Obtener engine específico por tipo."""
        try:
            etype = EngineType(engine_type)
            engine = self.cli_registry.get_engine_by_type(etype)
            if engine:
                return {
                    "name": engine.name,
                    "type": engine.engine_type.value,
                    "endpoint": engine.endpoint,
                    "max_tokens": engine.max_tokens,
                    "latency_ms": engine.avg_latency_ms,
                }
            return None
        except ValueError:
            logger.warning(f"Unknown engine type: {engine_type}")
            return None
    
    async def search_hf_models(
        self,
        task: str,
        max_size_gb: float = 2.0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Buscar modelos en HuggingFace."""
        models = await self.hf_scanner.search_models(task, max_size_gb, limit)
        
        return [
            {
                "model_id": m.model_id,
                "task": m.task,
                "size_gb": round(m.size_gb, 2),
                "downloads": m.downloads,
                "score": m.score,
                "url": m.download_url(),
            }
            for m in models
        ]
    
    def get_local_models_by_task(self, task: str) -> List[Dict[str, Any]]:
        """Obtener modelos locales para una tarea."""
        models = self.local_scanner.list_models(task=task)
        
        return [
            {
                "model_id": model_id,
                "path": m.model_path,
                "format": m.format,
                "size_gb": round(m.size_gb(), 2),
            }
            for model_id, m in [(self.local_scanner.models.get(k), v) for k, v in 
                               [(model_id, m) for model_id, m in self.local_scanner.models.items()]]
            if m is not None
        ]
    
    def suggest_engine_for_task(
        self,
        task: str,
        prefer_local: bool = False,
        max_cost: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Sugerir engine para tarea (informativo, Switch decide)."""
        
        logger.info(f"Suggesting engine for task={task} (prefer_local={prefer_local})")
        
        # Si se prefiere local, buscar modelo local
        if prefer_local:
            local_model = self.local_scanner.get_model_by_task(task)
            if local_model:
                return {
                    "suggestion": "local",
                    "model_id": local_model.model_path,
                    "format": local_model.format,
                    "size_gb": round(local_model.size_gb(), 2),
                    "reason": "Locally available, no network latency",
                }
        
        # Si no, sugerir CLI engine
        cli_suggestion = self.cli_registry.suggest_engine_for_task(task, max_cost)
        if cli_suggestion:
            return {
                "suggestion": "cli",
                "engine_name": cli_suggestion.name,
                "type": cli_suggestion.engine_type.value,
                "max_tokens": cli_suggestion.max_tokens,
                "latency_ms": cli_suggestion.avg_latency_ms,
                "cost_per_1k_input": cli_suggestion.cost_per_1k_input,
                "reason": f"Recommended for {task}",
            }
        
        return None
    
    def get_fallback_chain(self, primary_engine: str) -> List[Dict[str, Any]]:
        """Obtener cadena de fallback para engine."""
        chain = self.cli_registry.get_fallback_chain(primary_engine)
        
        return [
            {
                "name": engine.name,
                "type": engine.engine_type.value,
                "available": engine.available,
            }
            for engine in chain
        ]
    
    def report_engine_performance(
        self,
        engine_name: str,
        latency_ms: float,
        success: bool,
        error_msg: Optional[str] = None
    ) -> None:
        """Reportar performance de engine (feedback loop)."""
        self.cli_registry.update_metrics(engine_name, latency_ms, success, error_msg)
        logger.info(f"Updated metrics for {engine_name}: latency={latency_ms}ms, success={success}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado completo de Hermes."""
        local_stats = self.local_scanner.get_stats()
        
        return {
            "status": "operational",
            "uptime_seconds": (datetime.now() - self.initialized_at).total_seconds(),
            "requests_served": self.request_count,
            "engines": {
                "cli_count": len(self.cli_registry.list_engines()),
                "available_cli": len(self.cli_registry.list_available_engines()),
            },
            "local_models": local_stats,
            "timestamp": datetime.now().isoformat(),
        }


# Instancia global de Hermes
_hermes_core: Optional[HermesCore] = None


def get_hermes_core() -> HermesCore:
    """Obtener instancia global de Hermes."""
    global _hermes_core
    if _hermes_core is None:
        _hermes_core = HermesCore()
    return _hermes_core


async def initialize_hermes() -> HermesCore:
    """Inicializar Hermes y retornar instancia."""
    hermes = get_hermes_core()
    await hermes.initialize()
    return hermes
