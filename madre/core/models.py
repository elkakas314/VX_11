"""Madre V2 Pydantic Models: canonical contracts."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class ModeEnum(str, Enum):
    """Modo de operación de Madre."""

    MADRE = "MADRE"
    AUDIO_ENGINEER = "AUDIO_ENGINEER"


class RiskLevel(str, Enum):
    """Niveles de riesgo para acciones."""

    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"


class StatusEnum(str, Enum):
    """Estados de planes/tareas."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    DONE = "DONE"
    ERROR = "ERROR"


class StepType(str, Enum):
    """Tipos de pasos permitidos."""

    CALL_SWITCH = "CALL_SWITCH"
    CALL_HORMIGUERO_TASK = "CALL_HORMIGUERO_TASK"
    CALL_MANIFESTATOR = "CALL_MANIFESTATOR"
    CALL_SHUB = "CALL_SHUB"
    SPAWNER_REQUEST = "SPAWNER_REQUEST"
    SYSTEM_HEALTHCHECK = "SYSTEM_HEALTHCHECK"
    NOOP = "NOOP"


class DSL(BaseModel):
    """Domain-Specific Language: intent structure."""

    domain: str
    action: str
    parameters: Dict[str, Any] = {}
    confidence: float = 0.5
    original_text: str = ""
    warnings: List[str] = []


class IntentV2(BaseModel):
    """Canonical intent representation (v2)."""

    intent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    mode: ModeEnum
    dsl: DSL
    risk: RiskLevel
    requires_confirmation: bool = False
    targets: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StepV2(BaseModel):
    """Plan step: atomic action."""

    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: StepType
    payload: Dict[str, Any] = {}
    blocking: bool = False
    status: StatusEnum = StatusEnum.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PlanV2(BaseModel):
    """Canonical plan: sequence of steps."""

    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent_id: str
    session_id: str
    status: StatusEnum = StatusEnum.PENDING
    steps: List[StepV2] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    mode: ModeEnum = ModeEnum.MADRE


class ChatRequest(BaseModel):
    """POST /madre/chat request."""

    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """POST /madre/chat response: guaranteed fields."""

    response: str
    session_id: str
    intent_id: str
    plan_id: str
    status: StatusEnum
    mode: ModeEnum
    warnings: List[str] = []
    targets: List[str] = []
    actions: List[Dict[str, Any]] = []


class ControlRequest(BaseModel):
    """POST /madre/control request."""

    target: str
    action: str
    params: Optional[Dict[str, Any]] = None
    confirm_token: Optional[str] = None


class ControlResponse(BaseModel):
    """POST /madre/control response."""

    status: str  # "accepted" | "pending_confirmation" | "denied"
    action_id: Optional[int] = None
    confirm_token: Optional[str] = None
    reason: Optional[str] = None
    plan_id: Optional[str] = None


class HealthResponse(BaseModel):
    """GET /health response."""

    module: str = "madre"
    status: str
    version: str
    time: datetime = Field(default_factory=datetime.utcnow)
    deps: Dict[str, str] = {}
