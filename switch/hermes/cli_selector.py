"""
CLI Selector — Lógica de selección y fusión de engines.

Decide cuál engine usar basándose en:
- Tipo de tarea
- Presupuesto (tokens, dinero)
- Latencia requerida
- Disponibilidad
- Performance histórica

Usado por Switch para enrutar solicitudes.
"""

import logging
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum

from .cli_registry import get_cli_registry, EngineType
from .local_scanner import get_local_scanner
from .hf_scanner import get_hf_scanner

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Modo de ejecución de una solicitud."""
    LOCAL = "local"            # Modelo local, sin latencia de red
    HYBRID = "hybrid"          # Local + CLI (ej: local analysis + DeepSeek reasoning)
    CLI = "cli"                # Engine CLI remoto
    FALLBACK = "fallback"      # Fallback de CLI primario
    SHUB = "shub"              # DSP/Audio via Shubniggurath


@dataclass
class ExecutionPlan:
    """Plan de ejecución decidido por selector."""
    
    mode: ExecutionMode
    primary_engine: str         # Nombre del engine principal
    fallback_engines: List[str] # Alternativas si falla primario
    estimated_cost: float       # Costo estimado ($)
    estimated_latency_ms: int   # Latencia estimada
    reasoning: str              # Por qué se eligió este plan


class CLISelector:
    """Selector de engines para el Switch."""
    
    def __init__(self):
        self.cli_registry = get_cli_registry()
        self.local_scanner = get_local_scanner()
        self.hf_scanner = get_hf_scanner()
    
    def select_engine_for_task(
        self,
        task: str,
        task_type: str,  # "reasoning", "code", "audio", "vision", etc.
        max_tokens: int = 4096,
        max_cost: Optional[float] = None,
        max_latency_ms: Optional[int] = None,
        require_streaming: bool = False,
    ) -> ExecutionPlan:
        """
        Seleccionar motor para tarea específica.
        
        Args:
            task: Descripción de la tarea
            task_type: Tipo categorizado (reasoning, code, etc.)
            max_tokens: Tokens necesarios
            max_cost: Presupuesto máximo ($)
            max_latency_ms: Latencia máxima aceptable
            require_streaming: Se requiere streaming
            
        Returns:
            ExecutionPlan con decisión y alternativas
        """
        
        logger.info(f"Selecting engine for task_type={task_type}, tokens={max_tokens}")
        
        # Paso 1: Intentar local primero si es posible
        local_plan = self._try_local_first(task_type)
        if local_plan:
            return local_plan
        
        # Paso 2: Si no local, seleccionar CLI
        cli_plan = self._select_cli_engine(
            task_type=task_type,
            max_tokens=max_tokens,
            max_cost=max_cost,
            max_latency_ms=max_latency_ms,
            require_streaming=require_streaming,
        )
        return cli_plan
    
    def _try_local_first(self, task_type: str) -> Optional[ExecutionPlan]:
        """Intentar usar modelo local."""
        local_model = self.local_scanner.get_model_by_task(task_type)
        
        if local_model and local_model.is_valid:
            fallbacks = ["gpt4", "deepseek_r1"]  # Default fallbacks si local falla
            
            plan = ExecutionPlan(
                mode=ExecutionMode.LOCAL,
                primary_engine=local_model.model_path,
                fallback_engines=fallbacks,
                estimated_cost=0.0,
                estimated_latency_ms=int(500 + local_model.size_mb),  # Rough estimate
                reasoning=f"Local model available: {local_model.model_name} ({local_model.size_gb():.1f}GB)"
            )
            logger.info(f"✓ Selected LOCAL: {plan.reasoning}")
            return plan
        
        return None
    
    def _select_cli_engine(
        self,
        task_type: str,
        max_tokens: int,
        max_cost: Optional[float],
        max_latency_ms: Optional[int],
        require_streaming: bool,
    ) -> ExecutionPlan:
        """Seleccionar motor CLI."""
        
        candidates = self.cli_registry.list_available_engines()
        
        # Filtrar por requisitos
        if require_streaming:
            candidates = [e for e in candidates if e.supports_streaming]
        
        if max_cost:
            candidates = [e for e in candidates if e.cost_per_1k_input <= max_cost]
        
        if max_latency_ms:
            candidates = [e for e in candidates if e.avg_latency_ms <= max_latency_ms]
        
        if max_tokens:
            candidates = [e for e in candidates if e.max_tokens >= max_tokens]
        
        # Scoring por task_type
        if task_type == "reasoning":
            # Deep thinking → DeepSeek R1 preferido
            for e in candidates:
                if e.engine_type == EngineType.DEEPSEEK_R1:
                    return self._create_plan(e, "Deep reasoning → DeepSeek R1")
        
        elif task_type == "code":
            # Code generation → Codex preferido
            for e in candidates:
                if e.engine_type == EngineType.CODEX:
                    return self._create_plan(e, "Code generation → GitHub Copilot/Codex")
        
        elif task_type == "vision":
            # Vision → Gemini preferido
            for e in candidates:
                if e.supports_vision:
                    return self._create_plan(e, "Vision task → Gemini")
        
        # Default: lowest cost
        cheapest = min(candidates, key=lambda e: e.cost_per_1k_input) if candidates else None
        if cheapest:
            return self._create_plan(cheapest, f"Selected {cheapest.name} (lowest cost)")
        
        # Fallback: GPT-4 always available
        gpt4 = self.cli_registry.get_engine("gpt4")
        if gpt4:
            return self._create_plan(gpt4, "Fallback to GPT-4")
        
        # Emergency fallback
        raise ValueError("No engines available!")
    
    def _create_plan(self, engine, reasoning: str) -> ExecutionPlan:
        """Crear ExecutionPlan desde engine."""
        fallbacks = engine.fallback_engines if engine.fallback_engines else []
        
        estimated_cost = (engine.cost_per_1k_input + engine.cost_per_1k_output) / 2
        
        return ExecutionPlan(
            mode=ExecutionMode.CLI,
            primary_engine=engine.name,
            fallback_engines=fallbacks,
            estimated_cost=round(estimated_cost, 4),
            estimated_latency_ms=int(engine.avg_latency_ms),
            reasoning=reasoning,
        )
    
    def should_use_hybrid(self, task_type: str) -> bool:
        """Decidir si usar ejecución híbrida (local + CLI)."""
        
        # Híbrida es útil para:
        # - Análisis local + razonamiento remoto
        # - Pre-procesamiento local + inference remoto
        
        return task_type in ("analysis", "preprocessing", "complex_reasoning")


class CLIFusion:
    """Fusión de IA local + CLI + Shub."""
    
    def __init__(self):
        self.selector = CLISelector()
        self.metrics_store: Dict[str, Dict] = {}
    
    def fusion_execute(
        self,
        task: str,
        task_type: str,
        inputs: Dict[str, Any],
        strategy: str = "auto",  # auto, local_first, hybrid, cli_only
    ) -> Dict[str, Any]:
        """
        Ejecutar tarea con lógica de fusión.
        
        Strategies:
        - auto: Dejar que selector elija
        - local_first: Preferir local, fallback a CLI
        - hybrid: Local analysis + CLI reasoning
        - cli_only: Usar solo CLI
        """
        
        logger.info(f"Fusion execute: task_type={task_type}, strategy={strategy}")
        
        if strategy == "auto":
            plan = self.selector.select_engine_for_task(task, task_type)
        elif strategy == "local_first":
            plan = self.selector._try_local_first(task_type) or self.selector._select_cli_engine(task_type, 4096, None, None, False)
        elif strategy == "hybrid":
            # Ejecutar análisis local primero
            local_result = self._execute_local_analysis(inputs)
            # Luego enviar a CLI para razonamiento
            plan = self.selector._select_cli_engine("reasoning", 2048, None, None, False)
            return {
                "execution_plan": plan,
                "local_analysis": local_result,
                "cli_reasoning_pending": True,
            }
        elif strategy == "cli_only":
            plan = self.selector._select_cli_engine(task_type, 4096, None, None, False)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        return {
            "execution_plan": {
                "mode": plan.mode.value,
                "primary_engine": plan.primary_engine,
                "fallback_engines": plan.fallback_engines,
                "estimated_cost": plan.estimated_cost,
                "estimated_latency_ms": plan.estimated_latency_ms,
                "reasoning": plan.reasoning,
            },
            "task": task,
            "task_type": task_type,
        }
    
    def _execute_local_analysis(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar análisis local (preprocessing)."""
        # Stub: análisis real depende del tipo
        return {
            "status": "analyzed",
            "input_size": len(str(inputs)),
            "detected_patterns": ["pattern1", "pattern2"],
        }
    
    def record_execution(
        self,
        execution_plan,
        actual_cost: float,
        actual_latency_ms: int,
        success: bool,
        error_msg: Optional[str] = None,
    ) -> None:
        """Registrar métrica de ejecución para feedback."""
        engine_name = execution_plan.primary_engine
        
        # Update engine metrics
        self.selector.cli_registry.update_metrics(
            engine_name,
            actual_latency_ms,
            success,
            error_msg,
        )
        
        # Store execution record
        if engine_name not in self.metrics_store:
            self.metrics_store[engine_name] = {
                "total_cost": 0,
                "total_latency": 0,
                "total_requests": 0,
                "failures": 0,
            }
        
        record = self.metrics_store[engine_name]
        record["total_cost"] += actual_cost
        record["total_latency"] += actual_latency_ms
        record["total_requests"] += 1
        if not success:
            record["failures"] += 1
        
        logger.info(f"Recorded execution: {engine_name} ({actual_latency_ms}ms, ${actual_cost})")
