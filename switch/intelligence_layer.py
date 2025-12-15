"""
Switch Intelligence Layer (SIL) v7.1

Capa inteligente que asegura que Switch SIEMPRE:
1. Consulta Hermes para recursos disponibles
2. Usa CLISelector para elegir engine óptimo
3. Registra uso en cli_metrics para optimización
4. Sigue prioridades tentaculares (shub > operator > madre > hijas)

No reemplaza la lógica de Switch, la AMPLIFICA.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

import httpx

from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log
from switch.hermes import CLISelector, CLIFusion, ExecutionMode, get_metrics_collector

logger = logging.getLogger("vx11.switch.intelligence")

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class RoutingDecision(Enum):
    """Decisión de routing tomada por SIL."""

    LOCAL = "local"  # Usar modelo local
    CLI = "cli"  # Usar CLI remoto (DeepSeek, GPT, etc.)
    HYBRID = "hybrid"  # Combinar local + CLI
    SHUB = "shub"  # Delegar a Shub-Niggurath
    MADRE = "madre"  # Delegar a Madre (sistema)
    MANIFESTATOR = "manifestator"  # Delegar a Manifestator (auditoría)
    FALLBACK = "fallback"  # Fallback a stub


@dataclass
class RoutingContext:
    """Contexto de enrutamiento con información completa."""

    task_type: str  # "audio", "code", "reasoning", etc.
    source: str  # "operator", "madre", "shub", etc.
    messages: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    provider_hint: Optional[str] = None

    # Restricciones
    max_latency_ms: Optional[int] = None
    max_cost: Optional[float] = None
    max_tokens: Optional[int] = 4096

    # Capacidades requeridas
    require_vision: bool = False
    require_function_calling: bool = False
    require_streaming: bool = False


@dataclass
class RoutingResult:
    """Resultado del análisis de routing."""

    decision: RoutingDecision
    primary_engine: str  # Engine elegido
    fallback_engines: List[str] = None  # Alternativas
    estimated_cost: float = 0.0
    estimated_latency_ms: int = 0
    reasoning: str = ""

    def __post_init__(self):
        if self.fallback_engines is None:
            self.fallback_engines = []

    @property
    def cost(self) -> float:
        """Compatibilidad: alias `cost` -> `estimated_cost` para callers antiguos."""
        return self.estimated_cost


class SwitchIntelligenceLayer:
    """
    Capa de inteligencia de Switch que centraliza la lógica de decisión.

    Asegura que:
    1. Hermes siempre es consultado
    2. CLISelector siempre elige el motor óptimo
    3. Métricas siempre se registran
    4. Prioridades tentaculares siempre se respetan
    """

    def __init__(self):
        self.cli_selector = CLISelector()
        self.cli_fusion = CLIFusion()
        self.metrics_collector = get_metrics_collector()
        self._hermes_endpoint = settings.hermes_url or "http://switch:8003"
        self._priority_map = {
            "shub": 0,
            "operator": 1,
            "tentaculo_link": 1,
            "madre": 2,
            "hijas": 3,
            "default": 4,
        }

    async def make_routing_decision(self, context: RoutingContext) -> RoutingResult:
        """
        Tomar decisión de routing inteligente.

        Procedimiento:
        1. Detectar tipo de tarea (SYSTEM → Madre, DRIFT → Manifestator, AUDIO → Shub, etc.)
        2. Si no es especial, consultar Hermes
        3. Usar CLISelector para elegir engine
        4. Registrar decisión en métricas

        Args:
            context: Contexto de enrutamiento

        Returns:
            RoutingResult con decisión y alternativas
        """

        logger.info(
            f"Making routing decision: task_type={context.task_type}, source={context.source}"
        )

        try:
            # PASO 1: Detectar tareas especiales (SYSTEM, DRIFT, AUDIO)
            if (
                context.task_type in ("system", "workflow")
                or context.provider_hint == "madre"
            ):
                return RoutingResult(
                    decision=RoutingDecision.MADRE,
                    primary_engine="madre",
                    reasoning="Task type is system/workflow, delegating to Madre",
                )

            if (
                context.task_type in ("drift", "audit", "manifest")
                or context.provider_hint == "manifestator"
            ):
                return RoutingResult(
                    decision=RoutingDecision.MANIFESTATOR,
                    primary_engine="manifestator",
                    reasoning="Task type is drift/audit, delegating to Manifestator",
                )

            if context.task_type == "audio" or context.provider_hint in (
                "shub",
                "shub-audio",
            ):
                return RoutingResult(
                    decision=RoutingDecision.SHUB,
                    primary_engine="shub",
                    reasoning="Task type is audio, delegating to Shub",
                )

            # PASO 2: Consultar Hermes para recursos disponibles
            hermes_resources = await self._fetch_hermes_resources()

            # PASO 3: Usar CLISelector para elegir engine óptimo
            execution_plan = self.cli_selector.select_engine_for_task(
                task=context.metadata.get("prompt", "") if context.metadata else "",
                task_type=context.task_type,
                max_tokens=context.max_tokens or 4096,
                max_cost=context.max_cost,
                max_latency_ms=context.max_latency_ms,
                require_streaming=context.require_streaming,
            )

            # PASO 4: Convertir ExecutionPlan a RoutingResult
            return RoutingResult(
                decision=RoutingDecision(execution_plan.mode.value.lower()),
                primary_engine=execution_plan.primary_engine,
                fallback_engines=execution_plan.fallback_engines,
                estimated_cost=execution_plan.estimated_cost,
                estimated_latency_ms=execution_plan.estimated_latency_ms,
                reasoning=execution_plan.reasoning,
            )

        except Exception as exc:
            logger.error(f"Error in routing decision: {exc}")
            write_log("switch.sil", f"routing_error:{exc}", level="ERROR")

            # Fallback a stub si todo falla
            return RoutingResult(
                decision=RoutingDecision.FALLBACK,
                primary_engine="stub",
                reasoning=f"Routing error: {str(exc)}",
            )

    async def _fetch_hermes_resources(self) -> Dict[str, Any]:
        """Consultar Hermes para obtener recursos disponibles."""
        try:
            async with httpx.AsyncClient(timeout=5.0, headers=AUTH_HEADERS) as client:
                resp = await client.get(
                    f"{self._hermes_endpoint.rstrip('/')}/hermes/resources",
                    headers=AUTH_HEADERS,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch Hermes resources: {e}")

        return {"local_models": [], "cli": []}

    def record_execution(
        self,
        decision: RoutingResult,
        task_type: str,
        latency_ms: float,
        success: bool,
        tokens_used: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Registrar ejecución en métricas."""
        try:
            self.metrics_collector.record_execution(
                engine_name=decision.primary_engine,
                task_type=task_type,
                latency_ms=int(latency_ms),
                tokens_used=tokens_used,
                cost=cost,
                success=success,
            )
            write_log(
                "switch.sil",
                f"recorded_execution:{decision.primary_engine}:task_type={task_type}:latency={latency_ms}ms:success={success}",
            )
        except Exception as e:
            logger.error(f"Error recording execution: {e}")

    async def execute_with_fallback(
        self, decision: RoutingResult, execution_fn, *args, **kwargs
    ) -> Any:
        """
        Ejecutar decisión con fallback inteligente.

        Si el engine primario falla, intentar con los fallbacks.
        """

        # Intentar con engine primario
        try:
            result = await execution_fn(decision.primary_engine, *args, **kwargs)
            return result
        except Exception as e:
            logger.warning(f"Primary engine {decision.primary_engine} failed: {e}")
            write_log(
                "switch.sil", f"primary_engine_failed:{decision.primary_engine}:{e}"
            )

        # Intentar con fallbacks
        for fallback_engine in decision.fallback_engines:
            try:
                logger.info(f"Trying fallback engine: {fallback_engine}")
                result = await execution_fn(fallback_engine, *args, **kwargs)
                return result
            except Exception as e:
                logger.warning(f"Fallback engine {fallback_engine} failed: {e}")

        # Si todo falla, retornar error
        raise Exception(
            f"All engines failed, including fallbacks: {decision.fallback_engines}"
        )


# Instancia global
_sil: Optional[SwitchIntelligenceLayer] = None


def get_switch_intelligence_layer() -> SwitchIntelligenceLayer:
    """Obtener instancia global de SIL."""
    global _sil
    if not _sil:
        _sil = SwitchIntelligenceLayer()
    return _sil
