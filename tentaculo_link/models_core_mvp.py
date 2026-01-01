"""
Core MVP Contracts: Canonical Intent / Result models.

INVARIANT: All external API contracts define via Pydantic models.
Single responsibility: define request/response shapes for /vx11/* endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, List
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


# ============ SPAWN CALLBACK MODELS (PHASE 3) ============


class SpawnCallbackRequest(BaseModel):
    """
    Spawn task completion callback (sent by Spawner → Madre).

    INVARIANT: Madre receives this to update result store and DB.
    """

    spawn_id: str  # Task ID from spawner
    correlation_id: Optional[str] = None
    status: Literal["success", "failed", "timeout", "error"] = "success"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None  # Execution time
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "spawn_id": "spawn-123-abc",
                "correlation_id": "corr-456-def",
                "status": "success",
                "result": {"output": "task completed", "return_code": 0},
                "duration_ms": 1234,
            }
        }


class SpawnCallbackResponse(BaseModel):
    """Response from spawn callback handler."""

    spawn_id: str
    correlation_id: Optional[str] = None
    status: str = "received"  # "received", "stored", "error"
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "spawn_id": "spawn-123-abc",
                "correlation_id": "corr-456-def",
                "status": "stored",
                "message": "Spawn result persisted",
            }
        }


# ============ SPAWN REQUEST/RESPONSE MODELS (PHASE 5) ============


class SpawnRequest(BaseModel):
    """
    Request to spawn a new async task (daughter execution).

    INVARIANT: Requires spawner window to be open.
    """

    task_type: str  # "python" | "shell" | "system"
    code: str  # Task code to execute
    max_retries: int = Field(default=0, ge=0, le=10)
    ttl_seconds: int = Field(default=3600, ge=1, le=86400)  # 1 sec to 1 day
    user_id: Optional[str] = "local"
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "python",
                "code": "print('hello world')",
                "max_retries": 2,
                "ttl_seconds": 300,
                "user_id": "local",
            }
        }


class SpawnResponse(BaseModel):
    """Response from spawn request submission."""

    spawn_id: str  # Task ID (UUID)
    spawn_uuid: Optional[str] = None  # Full UUID (for result retrieval)
    correlation_id: Optional[str] = None
    status: Literal["QUEUED", "RUNNING", "DONE", "ERROR"] = "QUEUED"
    task_type: str
    error: Optional[str] = None  # Semantic error (e.g., "off_by_policy")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "spawn_id": "spawn-789-xyz",
                "spawn_uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "correlation_id": "corr-456-def",
                "status": "QUEUED",
                "task_type": "python",
                "created_at": "2026-01-01T00:00:00Z",
            }
        }


class SpawnResult(BaseModel):
    """Result of a spawn task (retrieved via spawn_uuid)."""

    spawn_uuid: str
    spawn_id: str
    status: str  # "queued", "running", "completed", "failed", "timeout"
    task_type: Optional[str] = None
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    ttl_seconds: int = 300

    class Config:
        json_schema_extra = {
            "example": {
                "spawn_uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "spawn_id": "spawn-789-xyz",
                "status": "completed",
                "task_type": "python",
                "exit_code": 0,
                "stdout": "MVP works",
                "stderr": None,
                "created_at": "2026-01-01T00:00:00Z",
                "finished_at": "2026-01-01T00:00:05Z",
            }
        }


class DBSummary(BaseModel):
    """Summary of database audit records."""

    counts: Dict[str, int]  # Table name → count
    last_spawns: List[Dict[str, Any]] = []  # Last 5 spawns
    last_routing_events: List[Dict[str, Any]] = []  # Last 5 routing events

    class Config:
        json_schema_extra = {
            "example": {
                "counts": {
                    "spawns": 42,
                    "tasks": 150,
                    "routing_events": 87,
                    "cli_providers": 12,
                },
                "last_spawns": [
                    {
                        "uuid": "uuid-1",
                        "status": "completed",
                        "created_at": "2026-01-01T00:00:00Z",
                    }
                ],
            }
        }
