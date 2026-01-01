"""
Core MVP Contracts: Canonical Intent / Result models.

INVARIANT: All external API contracts define via Pydantic models.
Single responsibility: define request/response shapes for /vx11/* endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from enum import Enum
from datetime import datetime
import uuid


class IntentTypeEnum(str, Enum):
    """Intent type classification."""

    CHAT = "chat"
    PLAN = "plan"
    EXEC = "exec"
    SPAWN = "spawn"


class StatusEnum(str, Enum):
    """Result status."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    DONE = "DONE"
    ERROR = "ERROR"


class ModeEnum(str, Enum):
    """Execution mode."""

    MADRE = "MADRE"
    SWITCH = "SWITCH"
    FALLBACK = "FALLBACK"
    SPAWNER = "SPAWNER"


class CoreIntent(BaseModel):
    """
    Canonical INTENT request (external API, :8000 entrypoint).

    INVARIANT: Minimal required fields, normalized before routing.
    """

    intent_type: IntentTypeEnum = IntentTypeEnum.CHAT
    text: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    require: Dict[str, bool] = Field(
        default_factory=lambda: {"switch": False, "spawner": False}
    )
    priority: Literal["P0", "P1", "P2"] = "P1"
    correlation_id: Optional[str] = None
    user_id: Optional[str] = "local"
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "intent_type": "chat",
                "text": "analizar el estado del sistema",
                "require": {"switch": False, "spawner": False},
                "priority": "P1",
            }
        }


class CoreIntentResponse(BaseModel):
    """
    Response from POST /vx11/intent (synchronous execution).

    INVARIANT: Must include correlation_id, status, mode for tracing.
    """

    correlation_id: str
    status: StatusEnum
    mode: ModeEnum
    provider: Optional[str] = None  # "switch" | "fallback_local" | "spawner"
    response: Optional[Dict[str, Any] | str] = None
    error: Optional[str] = None
    degraded: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "correlation_id": "uuid-123",
                "status": "DONE",
                "mode": "MADRE",
                "provider": "fallback_local",
                "response": {"plan": "executed", "result": "ok"},
                "degraded": False,
            }
        }


class CoreResultQuery(BaseModel):
    """
    Response from GET /vx11/result/{correlation_id}.

    INVARIANT: Unified result retrieval, no matter execution path.
    """

    correlation_id: str
    status: StatusEnum
    result: Optional[Dict[str, Any] | str] = None
    error: Optional[str] = None
    mode: Optional[ModeEnum] = None
    provider: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "correlation_id": "uuid-123",
                "status": "DONE",
                "result": {"output": "analysis complete"},
                "error": None,
                "mode": "MADRE",
                "provider": "fallback_local",
            }
        }


class CoreStatus(BaseModel):
    """
    Response from GET /vx11/status.

    INVARIANT: Best-effort health check without blocking.
    """

    mode: Literal["solo_madre", "windowed", "full"] = "solo_madre"
    policy: str = "SOLO_MADRE"
    madre_available: bool = True
    switch_available: Optional[bool] = None
    spawner_available: Optional[bool] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "mode": "solo_madre",
                "policy": "SOLO_MADRE",
                "madre_available": True,
                "switch_available": False,
                "spawner_available": False,
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response (401/403/423/502).

    INVARIANT: Uniform error format across all endpoints.
    """

    error: (
        str  # "auth_required" | "forbidden" | "off_by_policy" | "upstream_unavailable"
    )
    status_code: int
    detail: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "error": "off_by_policy",
                "status_code": 423,
                "detail": "switch required but solo_madre policy active",
                "correlation_id": "uuid-123",
            }
        }


class WindowTarget(str, Enum):
    """Service targets for window gating."""

    SWITCH = "switch"
    SPAWNER = "spawner"


class WindowOpen(BaseModel):
    """
    Request to open a time-gated window for switch/spawner.

    INVARIANT: Windows expire after TTL. Madre manages state + cleanup.
    """

    target: WindowTarget
    ttl_seconds: int = Field(ge=1, le=3600)  # 1 sec to 1 hour
    reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "target": "switch",
                "ttl_seconds": 300,
                "reason": "user-requested switch execution",
            }
        }


class WindowStatus(BaseModel):
    """
    Response: window state (open/closed, TTL remaining).

    INVARIANT: Shows actual state from Madre.
    """

    target: WindowTarget
    is_open: bool
    ttl_remaining_seconds: Optional[int] = None
    opened_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "target": "switch",
                "is_open": True,
                "ttl_remaining_seconds": 245,
                "opened_at": "2026-01-01T00:00:00Z",
                "expires_at": "2026-01-01T00:05:00Z",
            }
        }


class WindowClose(BaseModel):
    """
    Request to close a window (explicit closing).

    INVARIANT: Can close anytime. TTL-based auto-close also exists.
    """

    target: WindowTarget
    reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {"target": "switch", "reason": "task completed"}
        }


class WindowCloseResponse(BaseModel):
    """Response from closing a window."""

    target: WindowTarget
    closed: bool
    was_open: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {"target": "switch", "closed": True, "was_open": True}
        }
