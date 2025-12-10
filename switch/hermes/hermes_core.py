"""
Hermes Core — Gestor de recursos tentacular.

Responsabilidades canónicas:
- Inventario único de engines (CLI, HF, locales)
- Health/metrics y ranking métrico
- Selección canónica: decide_best_engine(intent) + especializaciones
- Fallback chain token-aware
- Proveedor universal para Switch (Switch consulta solo a HermesCore)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .cli_metrics import get_metrics_collector
from .cli_registry import EngineType, get_cli_registry
from .cli_selector import CLISelector
from .hf_scanner import get_hf_scanner
from .local_scanner import get_local_scanner

logger = logging.getLogger(__name__)


class HermesCore:
    """Núcleo del rol Hermes."""

    def __init__(self) -> None:
        self.cli_registry = get_cli_registry()
        self.hf_scanner = get_hf_scanner()
        self.local_scanner = get_local_scanner()
        self.selector = CLISelector()
        self.metrics = get_metrics_collector()

        self.initialized_at = datetime.now()
        self.request_count = 0

    async def initialize(self) -> None:
        """Inicializar Hermes (scan de modelos locales, health de engines)."""
        logger.info("Initializing Hermes...")

        count = self.local_scanner.scan_directory()
        logger.info(f"✓ Scanned {count} local models")

        results = self.local_scanner.validate_all()
        valid_count = sum(1 for v in results.values() if v)
        logger.info(f"✓ Validated {valid_count}/{len(results)} models")

        # Health check ligero
        try:
            await self.cli_registry.health_check()
        except Exception as exc:  # pragma: no cover - health is best-effort
            logger.warning(f"Hermes health check warning: {exc}")

    def inventory(self) -> Dict[str, Any]:
        """Inventario consolidado (CLI + local + HF)."""
        self.request_count += 1
        return {
            "cli": self.cli_registry.inventory(),
            "local": self.local_scanner.to_dict(),
            "hf_cached_tasks": list(self.hf_scanner.models_cache.keys()),
            "meta": {
                "uptime_seconds": (datetime.now() - self.initialized_at).total_seconds(),
                "requests_served": self.request_count,
            },
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
                    "available": engine.available,
                    "healthy": engine.healthy,
                }
            return None
        except ValueError:
            logger.warning(f"Unknown engine type: {engine_type}")
            return None

    async def search_hf_models(
        self, task: str, max_size_gb: float = 2.0, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Buscar modelos en HuggingFace (<2GB)."""
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

    def decide_best_engine(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        API única: decide el mejor engine para un intent.
        intent esperado incluye task_type, prompt y restricciones.
        """
        self.request_count += 1
        self.cli_registry.refresh_availability()
        decision_payload = self.selector.build_decision_payload(intent)
        decision_payload["metadata"] = {
            "uptime_seconds": (datetime.now() - self.initialized_at).total_seconds(),
            "requests_served": self.request_count,
        }
        return decision_payload

    def decide_for_audio(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Atajo: decisión orientada a audio/DSP."""
        intent = {**intent, "task_type": intent.get("task_type", "audio"), "allow_shub": True}
        return self.decide_best_engine(intent)

    def decide_for_task(self, task_type: str, prompt: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Atajo por tipo de tarea."""
        intent = {"task_type": task_type, "prompt": prompt, **kwargs}
        return self.decide_best_engine(intent)

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

    def metrics_snapshot(self) -> Dict[str, Any]:
        """Obtener métricas agregadas."""
        return self.metrics.get_all_stats()

    # Alias requerido por canon
    def metrics_report(self) -> Dict[str, Any]:
        return self.metrics_snapshot()


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
