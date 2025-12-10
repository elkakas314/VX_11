"""
CLI Registry — Registro exhaustivo de engines de IA disponibles.

Mantiene:
- Engines externos (Gemini, DeepSeek R1, GPT, Codex)
- Engines locales (ollama, vLLM)
- Tokens, límites, precios, latencias
- Fallbacks inteligentes

No toma decisiones. Proporciona información a Switch.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class EngineType(Enum):
    """Tipos de engines soportados."""
    LOCAL = "local"              # ollama, vLLM, local models
    DEEPSEEK_R1 = "deepseek_r1"  # API DeepSeek R1
    GEMINI = "gemini"            # Google Gemini API
    GPT4 = "gpt4"                # OpenAI GPT-4
    CODEX = "codex"              # GitHub Copilot / OpenAI Codex
    ANTHROPIC = "anthropic"      # Claude API


@dataclass
class EngineMetadata:
    """Metadata de un engine."""
    
    name: str
    engine_type: EngineType
    endpoint: str              # URL o local path
    model_name: str            # Model identifier
    
    # Capacidades
    max_tokens: int            # Max tokens per request
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = False
    
    # Costos y límites
    cost_per_1k_input: float = 0.0     # $ per 1000 input tokens
    cost_per_1k_output: float = 0.0    # $ per 1000 output tokens
    rate_limit_rpm: int = 0             # Requests per minute (0 = unlimited)
    concurrent_limit: int = 0           # Max concurrent requests (0 = unlimited)
    
    # Performance
    avg_latency_ms: float = 0.0         # Average response time
    success_rate: float = 1.0           # Success rate (0-1)
    
    # Fallbacks
    fallback_engines: List[str] = field(default_factory=list)  # Engine names to fallback to
    
    # Status
    available: bool = True
    last_health_check: Optional[float] = None
    error_count: int = 0


class CLIRegistry:
    """Registro global de engines de IA disponibles."""
    
    def __init__(self):
        self.engines: Dict[str, EngineMetadata] = {}
        self._initialize_builtin_engines()
    
    def _initialize_builtin_engines(self):
        """Registrar engines built-in y conocidos."""
        
        # 1. DeepSeek R1 (recomendado para razonamiento pesado)
        self.register_engine(EngineMetadata(
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
        ))
        
        # 2. OpenAI GPT-4 (propósito general)
        self.register_engine(EngineMetadata(
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
            fallback_engines=["gpt3.5", "gemini"],
        ))
        
        # 3. Google Gemini (multimodal)
        self.register_engine(EngineMetadata(
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
        ))
        
        # 4. GitHub Copilot / Codex (código + texto)
        self.register_engine(EngineMetadata(
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
        ))
        
        # 5. Ollama local (sin costo, latencia variable)
        self.register_engine(EngineMetadata(
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
        ))
        
        # 6. vLLM local (alta throughput)
        self.register_engine(EngineMetadata(
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
        ))
        
        logger.info("✓ Registered 6 built-in engines")
    
    def register_engine(self, metadata: EngineMetadata) -> None:
        """Registrar nuevo engine."""
        self.engines[metadata.name] = metadata
        logger.info(f"Registered engine: {metadata.name} ({metadata.engine_type.value})")
    
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
    
    def update_metrics(
        self,
        engine_name: str,
        latency_ms: float,
        success: bool,
        error_msg: Optional[str] = None
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
        engine.success_rate = (engine.success_rate * (total_requests - 1) + (1 if success else 0)) / total_requests
        
        # Track errors
        if not success:
            engine.error_count += 1
            logger.warning(f"Engine {engine_name} error: {error_msg}")
        
        logger.debug(f"Updated {engine_name}: latency={engine.avg_latency_ms:.0f}ms, success_rate={engine.success_rate:.2%}")
    
    def suggest_engine_for_task(
        self,
        task_type: str,
        max_cost: Optional[float] = None,
        require_streaming: bool = False
    ) -> Optional[EngineMetadata]:
        """Sugerir mejor engine para una tarea (no toma decisión, solo sugiere)."""
        
        # Filtrar por capacidades requeridas
        candidates = self.list_available_engines()
        
        if require_streaming:
            candidates = [e for e in candidates if e.supports_streaming]
        
        if max_cost is not None:
            candidates = [e for e in candidates if e.cost_per_1k_input <= max_cost]
        
        # Sugerir basado en task_type
        if task_type == "reasoning":
            # Deep thinking → DeepSeek R1
            for e in candidates:
                if e.engine_type == EngineType.DEEPSEEK_R1:
                    return e
        
        elif task_type == "code":
            # Code generation → Codex o local
            for e in candidates:
                if e.engine_type == EngineType.CODEX:
                    return e
        
        elif task_type == "vision":
            # Vision tasks → Gemini o GPT-4
            for e in candidates:
                if e.supports_vision and e.avg_latency_ms < 1000:
                    return e
        
        elif task_type == "local":
            # Local execution → ollama, vLLM
            for e in candidates:
                if e.engine_type == EngineType.LOCAL:
                    return e
        
        # Default: pick lowest latency available
        if candidates:
            return min(candidates, key=lambda e: e.avg_latency_ms)
        
        return None
    
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
            }
            for name, engine in self.engines.items()
        }


# Instancia global (singleton)
_cli_registry: Optional[CLIRegistry] = None


def get_cli_registry() -> CLIRegistry:
    """Obtener instancia global de CLI registry."""
    global _cli_registry
    if _cli_registry is None:
        _cli_registry = CLIRegistry()
    return _cli_registry
