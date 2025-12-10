"""
VX11 DSL Compiler — Convertir VX11Intents a Workflows ejecutables.

PASO 3.0: Compilador DSL que transforma intents a workflows.

FLUJO:
  1. VX11DSLParser.parse(text) → VX11Intent
  2. VX11DSLCompiler.compile(intent) → WorkflowPlan
  3. Madre.execute_workflow(plan) → resultado

EJEMPLO:
  Input:  "VX11::AUDIO analyze file=/audio.wav preset=default"
  Output: WorkflowPlan(
            steps=[
              {"executor": "shub", "action": "analyze", "params": {...}},
              {"executor": "switch", "action": "score", "params": {...}}
            ]
          )
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger("vx11.madre.dsl_compiler")


class ExecutorType(Enum):
    """Ejecutores disponibles para pasos de workflow"""
    HERMES = "hermes"
    SHUB = "shub"
    SPAWNER = "spawner"
    SWITCH = "switch"
    MADRE = "madre"
    MANIFESTATOR = "manifestator"
    HORMIGUERO = "hormiguero"
    LOCAL = "local"


@dataclass
class WorkflowStep:
    """Un paso en el workflow ejecutable"""
    executor: ExecutorType
    action: str
    parameters: Dict[str, Any]
    timeout_ms: int = 30000
    retry_count: int = 1
    fallback_executor: Optional[ExecutorType] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "executor": self.executor.value,
            "action": self.action,
            "parameters": self.parameters,
            "timeout_ms": self.timeout_ms,
            "retry_count": self.retry_count,
            "fallback_executor": self.fallback_executor.value if self.fallback_executor else None,
        }


@dataclass
class WorkflowPlan:
    """Plan de ejecución compilado desde DSL"""
    workflow_id: str
    domain: str
    intent_action: str
    steps: List[WorkflowStep]
    priority: int = 2
    timeout_ms: int = 60000
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "domain": self.domain,
            "intent_action": self.intent_action,
            "steps": [step.to_dict() for step in self.steps],
            "priority": self.priority,
            "timeout_ms": self.timeout_ms,
            "created_at": self.created_at,
        }


class VX11DSLCompiler:
    """
    Compilador DSL que transforma VX11Intents a WorkflowPlans.
    
    Soporta 8 dominios principales:
    - TASK: Crear/gestionar tareas
    - AUDIO: Procesamiento de audio (Shub)
    - PATCH: Generación/aplicación de parches
    - SCAN: Escaneo del sistema
    - HERMES: Ejecución de comandos CLI
    - SHUB: Orquestación directa de Shub
    - HORMIGUERO: Control de colonia
    - OPERATOR: Comandos del operador
    """
    
    def __init__(self):
        self.workflow_counter = 0
        logger.info("DSL Compiler VX11 inicializado (PASO 3.0)")
    
    def compile(self, intent: Dict[str, Any]) -> WorkflowPlan:
        """
        Compila un intent a un plan de workflow ejecutable.
        
        Args:
            intent: Dict con estructura de VX11Intent.to_dict()
            
        Returns:
            WorkflowPlan con steps ejecutables
        """
        self.workflow_counter += 1
        workflow_id = f"wf_{self.workflow_counter}_{int(datetime.utcnow().timestamp() * 1000)}"
        
        domain = intent.get("domain", "UNKNOWN")
        action = intent.get("action", "unknown")
        parameters = intent.get("parameters", {})
        
        logger.info(f"Compilando workflow {workflow_id}: {domain}::{action}")
        
        # Compilar según dominio
        if domain == "TASK":
            steps = self._compile_task(action, parameters)
        elif domain == "AUDIO":
            steps = self._compile_audio(action, parameters)
        elif domain == "PATCH":
            steps = self._compile_patch(action, parameters)
        elif domain == "SCAN":
            steps = self._compile_scan(action, parameters)
        elif domain == "HERMES":
            steps = self._compile_hermes(action, parameters)
        elif domain == "SHUB":
            steps = self._compile_shub(action, parameters)
        elif domain == "HORMIGUERO":
            steps = self._compile_hormiguero(action, parameters)
        elif domain == "OPERATOR":
            steps = self._compile_operator(action, parameters)
        else:
            steps = [WorkflowStep(
                executor=ExecutorType.LOCAL,
                action="fallback",
                parameters=parameters,
            )]
        
        return WorkflowPlan(
            workflow_id=workflow_id,
            domain=domain,
            intent_action=action,
            steps=steps,
            priority=intent.get("priority", 2),
        )
    
    def _compile_task(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio TASK"""
        steps = []
        
        if action in ("create", "nueva"):
            # Crear tarea: registrar en BD + encolador
            steps.extend([
                WorkflowStep(
                    executor=ExecutorType.MADRE,
                    action="register_task",
                    parameters={"name": params.get("name", "tarea_sin_nombre"), "type": params.get("type", "general")},
                    timeout_ms=5000,
                ),
                WorkflowStep(
                    executor=ExecutorType.SWITCH,
                    action="enqueue",
                    parameters={"task_id": "${steps[0].task_id}", "priority": params.get("priority", 2)},
                    timeout_ms=5000,
                    fallback_executor=ExecutorType.MADRE,
                ),
            ])
        elif action in ("execute", "run"):
            # Ejecutar tarea
            steps.append(WorkflowStep(
                executor=ExecutorType.SPAWNER,
                action="spawn",
                parameters={"task_id": params.get("task_id"), "command": params.get("command", "")},
                timeout_ms=30000,
                retry_count=2,
            ))
        elif action in ("status", "show"):
            # Mostrar estado
            steps.append(WorkflowStep(
                executor=ExecutorType.MADRE,
                action="get_task_status",
                parameters={"task_id": params.get("task_id")},
                timeout_ms=5000,
            ))
        
        return steps
    
    def _compile_audio(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio AUDIO → Shub"""
        steps = []
        
        if action in ("restore", "denoise"):
            # Audio restoration: Shub restore
            steps.append(WorkflowStep(
                executor=ExecutorType.SHUB,
                action="restore",
                parameters={
                    "file": params.get("file"),
                    "preset": params.get("preset", "default"),
                    "force_gpu": params.get("force_gpu", False),
                },
                timeout_ms=120000,
                retry_count=2,
            ))
        elif action in ("arrange", "mix"):
            # Audio arrangement/mixing
            steps.append(WorkflowStep(
                executor=ExecutorType.SHUB,
                action="arrange",
                parameters={
                    "files": params.get("files", []),
                    "preset": params.get("preset", "default"),
                },
                timeout_ms=120000,
                retry_count=1,
            ))
        elif action in ("master",):
            # Mastering
            steps.append(WorkflowStep(
                executor=ExecutorType.SHUB,
                action="master",
                parameters={
                    "file": params.get("file"),
                    "target_lufs": params.get("target_lufs", -14),
                },
                timeout_ms=60000,
                retry_count=1,
            ))
        
        return steps
    
    def _compile_patch(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio PATCH → Manifestator"""
        steps = []
        
        if action in ("generate", "scan"):
            # Detectar drift y generar patch
            steps.extend([
                WorkflowStep(
                    executor=ExecutorType.MANIFESTATOR,
                    action="detect_drift",
                    parameters={"scope": params.get("scope", "sistema")},
                    timeout_ms=30000,
                ),
                WorkflowStep(
                    executor=ExecutorType.MANIFESTATOR,
                    action="generate_patch",
                    parameters={
                        "drift_report": "${steps[0].drift_report}",
                        "target": params.get("target", "madre"),
                    },
                    timeout_ms=10000,
                    retry_count=1,
                ),
            ])
        elif action in ("apply",):
            # Aplicar patch
            steps.extend([
                WorkflowStep(
                    executor=ExecutorType.MANIFESTATOR,
                    action="validate_patch",
                    parameters={"patch_file": params.get("patch_file")},
                    timeout_ms=5000,
                ),
                WorkflowStep(
                    executor=ExecutorType.MANIFESTATOR,
                    action="apply_patch",
                    parameters={"patch_file": params.get("patch_file")},
                    timeout_ms=10000,
                    retry_count=1,
                ),
            ])
        
        return steps
    
    def _compile_scan(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio SCAN"""
        steps = []
        
        if action in ("drift", "analyze"):
            steps.append(WorkflowStep(
                executor=ExecutorType.MANIFESTATOR,
                action="scan_drift",
                parameters={"scope": params.get("scope", "sistema")},
                timeout_ms=60000,
            ))
        elif action in ("system", "status", "health"):
            steps.append(WorkflowStep(
                executor=ExecutorType.MADRE,
                action="system_health",
                parameters={"detailed": params.get("detailed", False)},
                timeout_ms=10000,
            ))
        
        return steps
    
    def _compile_hermes(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio HERMES → CLI execution"""
        steps = []
        
        if action in ("execute", "run"):
            steps.append(WorkflowStep(
                executor=ExecutorType.HERMES,
                action="execute",
                parameters={
                    "command": params.get("command", ""),
                    "engine": params.get("engine", "auto"),
                    "max_tokens": params.get("max_tokens", 8192),
                },
                timeout_ms=30000,
                retry_count=2,
            ))
        elif action in ("list", "enumerate"):
            steps.append(WorkflowStep(
                executor=ExecutorType.HERMES,
                action="list_tools",
                parameters={"category": params.get("category", "all")},
                timeout_ms=5000,
            ))
        
        return steps
    
    def _compile_shub(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio SHUB directo"""
        steps = []
        
        # Directamente a Shub
        steps.append(WorkflowStep(
            executor=ExecutorType.SHUB,
            action=action,
            parameters=params,
            timeout_ms=params.get("timeout_ms", 120000),
            retry_count=1,
        ))
        
        return steps
    
    def _compile_hormiguero(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio HORMIGUERO"""
        steps = []
        
        if action in ("create", "spawn"):
            steps.append(WorkflowStep(
                executor=ExecutorType.HORMIGUERO,
                action="spawn_colony",
                parameters={
                    "size": params.get("size", 10),
                    "pheromone": params.get("pheromone", "default"),
                },
                timeout_ms=10000,
            ))
        elif action in ("report", "status"):
            steps.append(WorkflowStep(
                executor=ExecutorType.HORMIGUERO,
                action="get_report",
                parameters={"colony_id": params.get("colony_id")},
                timeout_ms=5000,
            ))
        
        return steps
    
    def _compile_operator(self, action: str, params: Dict) -> List[WorkflowStep]:
        """Compilar dominio OPERATOR"""
        steps = []
        
        if action in ("chat",):
            # Enviar a Switch para procesamiento conversacional
            steps.append(WorkflowStep(
                executor=ExecutorType.SWITCH,
                action="chat",
                parameters={
                    "messages": params.get("messages", []),
                    "context": params.get("context", {}),
                },
                timeout_ms=30000,
                retry_count=1,
            ))
        
        return steps
    
    def compile_and_validate(self, intent: Dict[str, Any]) -> Tuple[Optional[WorkflowPlan], List[str]]:
        """
        Compila y valida un intent.
        
        Returns:
            (WorkflowPlan, validation_errors)
        """
        errors = []
        
        # Validar estructura de intent
        if not isinstance(intent, dict):
            errors.append("Intent debe ser diccionario")
            return None, errors
        
        if "domain" not in intent:
            errors.append("Intent requiere 'domain'")
            return None, errors
        
        if "action" not in intent:
            errors.append("Intent requiere 'action'")
            return None, errors
        
        try:
            plan = self.compile(intent)
            logger.info(f"✓ Workflow compilado exitosamente: {plan.workflow_id}")
            return plan, []
        except Exception as e:
            errors.append(f"Error compilación: {str(e)}")
            logger.error(f"✗ Error compilando workflow: {e}")
            return None, errors


def compile_dsl_to_workflow(dsl_text: str) -> Tuple[Optional[WorkflowPlan], List[str]]:
    """
    Helper function: Parsea DSL text → Compila a Workflow.
    
    Args:
        dsl_text: Texto DSL como "VX11::AUDIO analyze file=/audio.wav"
        
    Returns:
        (WorkflowPlan, errors)
    """
    from madre.dsl_parser import VX11DSLParser
    
    parser = VX11DSLParser()
    intent = parser.parse(dsl_text)
    
    if not intent:
        return None, ["No se pudo parsear DSL text"]
    
    compiler = VX11DSLCompiler()
    return compiler.compile_and_validate(intent.to_dict())
