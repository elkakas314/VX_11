"""
CLI Registry — Registro exhaustivo de engines de IA disponibles.

Rol canónico (Hermes):
- Registro token-aware de engines externos/locales
- Health-check ligero para marcar availability real
- Fallback chains y ranking métrico
- Inventario expuesto a HermesCore (Switch consume solo vía HermesCore)
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

import httpx

from config.tokens import get_token

logger = logging.getLogger(__name__)


class EngineType(Enum):
    """Tipos de engines soportados."""

    LOCAL = "local"  # ollama, vLLM, local models
    DEEPSEEK_R1 = "deepseek_r1"
    GEMINI = "gemini"
    GPT4 = "gpt4"
    CODEX = "codex"
    ANTHROPIC = "anthropic"
    SHUB = "shub"


@dataclass
class EngineMetadata:
    """Metadata de un engine."""

    name: str
    engine_type: EngineType
    endpoint: str  # URL o local path
    model_name: str  # Model identifier

    # Capacidades
    max_tokens: int
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = False

    # Costos y límites
    cost_per_1k_input: float = 0.0  # $ per 1000 input tokens
    cost_per_1k_output: float = 0.0  # $ per 1000 output tokens
    rate_limit_rpm: int = 0  # Requests per minute (0 = unlimited)
    concurrent_limit: int = 0  # Max concurrent requests (0 = unlimited)

    # Performance
    avg_latency_ms: float = 0.0  # Average response time
    success_rate: float = 1.0  # Success rate (0-1)

    # Fallbacks
    fallback_engines: List[str] = field(default_factory=list)  # Engine names to fallback to

    # Status
    available: bool = True
    last_health_check: Optional[float] = None
    error_count: int = 0
    token_name: Optional[str] = None  # nombre de token en tokens.env
    pricing_model: str = "per_1k"  # per_1k | flat | local
    notes: str = ""  # metadata opcional
    healthy: bool = True


class CLIRegistry:
    """Registro global de engines de IA disponibles."""

    def __init__(self):
        self.engines: Dict[str, EngineMetadata] = {}
        self._initialize_builtin_engines()

    def _token_allows(self, token_name: Optional[str]) -> bool:
        """Verificar disponibilidad basada en token requerido."""
        if not token_name:
            return True
        token_value = get_token(token_name)
        return bool(token_value)

    def _initialize_builtin_engines(self) -> None:
        """Registrar engines built-in y conocidos, token-aware."""

        # 1. DeepSeek R1 (recomendado para razonamiento pesado)
        self.register_engine(
            EngineMetadata(
                name="deepseek_r1",
                engine_type=EngineType.DEEPSEEK_R1,
                endpoint="${DEEPSEEK_API_ENDPOINT}",  # from env
                model_name="deepseek-r1",
                max_tokens=8192,
                supports_function_calling=True,
                supports_streaming=True,
                cost_per_1k_input=0.50,  # $ placeholder
                cost_per_1k_output=1.50,
                rate_limit_rpm=100,
                avg_latency_ms=800,
                fallback_engines=["gpt4", "gemini"],
                token_name="DEEPSEEK_API_KEY",
                pricing_model="per_1k",
            )
        )

        # 2. OpenAI GPT-4 (propósito general)
        self.register_engine(
            EngineMetadata(
                name="gpt4",
                engine_type=EngineType.GPT4,
                endpoint="https://api.openai.com/v1/chat/completions",
                model_name="gpt-4",
                max_tokens=8192,
                supports_vision=True,
                supports_function_calling=True,
                supports_streaming=True,
                cost_per_1k_input=0.03,
                cost_per_1k_output=0.06,
                rate_limit_rpm=200,
                avg_latency_ms=600,
                fallback_engines=["gemini"],
                token_name="OPENAI_API_KEY",
                pricing_model="per_1k",
            )
        )

        # 3. Google Gemini (multimodal)
        self.register_engine(
            EngineMetadata(
                name="gemini",
                engine_type=EngineType.GEMINI,
                endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
                model_name="gemini-pro",
                max_tokens=32768,
                supports_vision=True,
                supports_function_calling=True,
                cost_per_1k_input=0.0005,
                cost_per_1k_output=0.0015,
                rate_limit_rpm=100,
                avg_latency_ms=700,
                fallback_engines=["gpt4"],
                token_name="GEMINI_API_KEY",
                pricing_model="per_1k",
            )
        )

        # 4. GitHub Copilot / Codex (código + texto)
        self.register_engine(
            EngineMetadata(
                name="codex",
                engine_type=EngineType.CODEX,
                endpoint="https://api.openai.com/v1/engines/code-davinci-003/completions",
                model_name="code-davinci-003",
                max_tokens=4000,
                supports_function_calling=False,
                cost_per_1k_input=0.02,
                cost_per_1k_output=0.04,
                rate_limit_rpm=100,
                avg_latency_ms=400,
                fallback_engines=["gpt4"],
                token_name="CODEX_API_KEY",
                pricing_model="per_1k",
            )
        )

        # 5. Ollama local (sin costo, latencia variable)
        self.register_engine(
            EngineMetadata(
                name="ollama_local",
                engine_type=EngineType.LOCAL,
                endpoint="http://localhost:11434/api/generate",
                model_name="mistral",  # default
                max_tokens=4096,
                supports_streaming=True,
                cost_per_1k_input=0.0,  # Local = free
                rate_limit_rpm=0,  # Unlimited
                avg_latency_ms=1500,  # CPU-dependent
                success_rate=0.95,
                fallback_engines=["gpt4"],
                pricing_model="local",
                notes="Local Ollama; requiere modelo predescargado",
            )
        )

        # 6. vLLM local (alta throughput)
        self.register_engine(
            EngineMetadata(
                name="vllm_local",
                engine_type=EngineType.LOCAL,
                endpoint="http://localhost:8000/v1/completions",
                model_name="llama-2-7b",
                max_tokens=4096,
                supports_streaming=True,
                cost_per_1k_input=0.0,
                rate_limit_rpm=0,
                avg_latency_ms=800,
                success_rate=0.98,
                fallback_engines=["ollama_local", "gpt4"],
                pricing_model="local",
                notes="vLLM servidor local",
            )
        )

        logger.info("✓ Registered 6 built-in engines")

    def register_engine(self, metadata: EngineMetadata) -> None:
        """Registrar nuevo engine, respetando tokens y health inicial."""
        metadata.available = self._token_allows(metadata.token_name)
        if not metadata.available:
            metadata.notes = (metadata.notes or "") + " (token missing)"
        self.engines[metadata.name] = metadata
        logger.info(
            f"Registered engine: {metadata.name} ({metadata.engine_type.value}) available={metadata.available}"
        )

    def get_engine(self, name: str) -> Optional[EngineMetadata]:
        """Obtener metadata de engine por nombre."""
        return self.engines.get(name)

    def list_engines(self, engine_type: Optional[EngineType] = None) -> List[EngineMetadata]:
        """Listar engines, opcionalmente filtrados por tipo."""
        engines = list(self.engines.values())
        if engine_type:
            engines = [e for e in engines if e.engine_type == engine_type]
        return engines

    def list_available_engines(self) -> List[EngineMetadata]:
        """Listar solo engines disponibles."""
        return [e for e in self.engines.values() if e.available]

    def refresh_availability(self) -> None:
        """Re-evaluar availability según tokens presentes."""
        for engine in self.engines.values():
            engine.available = self._token_allows(engine.token_name) and engine.healthy

    def get_engine_by_type(self, engine_type: EngineType) -> Optional[EngineMetadata]:
        """Obtener primer engine disponible de un tipo."""
        for engine in self.engines.values():
            if engine.engine_type == engine_type and engine.available:
                return engine
        return None

    def get_fallback_chain(self, engine_name: str) -> List[EngineMetadata]:
        """Obtener cadena de fallback para un engine."""
        engine = self.get_engine(engine_name)
        if not engine:
            return []

        chain = [engine]
        for fallback_name in engine.fallback_engines:
            fallback = self.get_engine(fallback_name)
            if fallback:
                chain.append(fallback)

        return chain

    async def health_check(self, names: Optional[Iterable[str]] = None, timeout: float = 3.0) -> Dict[str, Any]:
        """
        Health-check ligero (GET) para marcar availability real.
        No descarga modelos ni ejecuta prompts; solo verificación rápida.
        """
        targets = names or self.engines.keys()
        results: Dict[str, Any] = {}
        async with httpx.AsyncClient(timeout=timeout) as client:
            for name in targets:
                engine = self.engines.get(name)
                if not engine:
                    continue
                url = engine.endpoint
                ok = True
                if url.startswith("http"):
                    try:
                        resp = await client.get(url, timeout=timeout)
                        ok = resp.status_code < 500
                    except Exception as exc:  # pragma: no cover - network failures
                        ok = False
                        engine.notes = (engine.notes or "") + f" health_error:{exc}"
                engine.healthy = ok
                engine.health_checked_at = time.time()
                engine.available = engine.available and ok
                results[name] = {"healthy": ok, "checked_at": engine.health_checked_at}
        return results

    def update_metrics(
        self,
        engine_name: str,
        latency_ms: float,
        success: bool,
        error_msg: Optional[str] = None,
    ) -> None:
        """Actualizar métricas de performance de un engine."""
        engine = self.get_engine(engine_name)
        if not engine:
            return

        # Update latency (exponential moving average)
        alpha = 0.3
        engine.avg_latency_ms = alpha * latency_ms + (1 - alpha) * engine.avg_latency_ms

        # Update success rate
        total_requests = 100  # Simplified: assume rolling window
        engine.success_rate = (
            engine.success_rate * (total_requests - 1) + (1 if success else 0)
        ) / total_requests

        # Track errors
        if not success:
            engine.error_count += 1
            logger.warning(f"Engine {engine_name} error: {error_msg}")

    def suggest_engine_for_task(
        self, task_type: str, max_cost: Optional[float] = None, require_streaming: bool = False
    ) -> Optional[EngineMetadata]:
        """Sugerir mejor engine para una tarea (no toma decisión, solo sugiere)."""

        candidates = self.list_available_engines()

        if require_streaming:
            candidates = [e for e in candidates if e.supports_streaming]

        if max_cost is not None:
            candidates = [e for e in candidates if e.cost_per_1k_input <= max_cost]

        # Sugerir basado en task_type
        if task_type == "reasoning":
            for e in candidates:
                if e.engine_type == EngineType.DEEPSEEK_R1:
                    return e

        elif task_type == "code":
            for e in candidates:
                if e.engine_type == EngineType.CODEX:
                    return e

        elif task_type == "vision":
            for e in candidates:
                if e.supports_vision and e.avg_latency_ms < 1000:
                    return e

        elif task_type == "local":
            for e in candidates:
                if e.engine_type == EngineType.LOCAL:
                    return e

        # Default: pick lowest latency available
        if candidates:
            return min(candidates, key=lambda e: e.avg_latency_ms)

        return None

    def rank_engines(self) -> List[Dict[str, Any]]:
        """Ranking simple por éxito/costo/latencia."""
        ranking = []
        for e in self.list_available_engines():
            success = e.success_rate or 0.0
            latency_penalty = (e.avg_latency_ms or 1000) / 2000.0
            cost_penalty = (e.cost_per_1k_input or 0.0) / 1.0
            score = round(success - latency_penalty - cost_penalty, 3)
            ranking.append(
                {
                    "name": e.name,
                    "type": e.engine_type.value,
                    "score": score,
                    "latency_ms": e.avg_latency_ms,
                    "cost_per_1k": e.cost_per_1k_input,
                    "available": e.available,
                    "healthy": e.healthy,
                }
            )
        ranking.sort(key=lambda x: x["score"], reverse=True)
        return ranking

    def to_dict(self) -> Dict[str, Any]:
        """Serializar registry a diccionario."""
        return {
            name: {
                "type": engine.engine_type.value,
                "endpoint": engine.endpoint,
                "max_tokens": engine.max_tokens,
                "latency_ms": engine.avg_latency_ms,
                "success_rate": engine.success_rate,
                "available": engine.available,
                "healthy": engine.healthy,
                "last_health_check": engine.health_checked_at,
            }
            for name, engine in self.engines.items()
        }

    def inventory(self) -> Dict[str, Any]:
        """Inventario consolidado para HermesCore."""
        return {
            "engines": self.to_dict(),
            "ranking": self.rank_engines(),
        }


# Instancia global (singleton)
_cli_registry: Optional[CLIRegistry] = None


def get_cli_registry() -> CLIRegistry:
    """Obtener instancia global de CLI registry."""
    global _cli_registry
    if _cli_registry is None:
        _cli_registry = CLIRegistry()
    return _cli_registry
