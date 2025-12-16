"""
Pydantic schemas for CLI Concentrator contract.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ProviderConfig(BaseModel):
    """Configuration for a CLI provider."""

    provider_id: str
    kind: str  # "copilot_cli" | "generic_shell" | "copilot" | "codex" | "gemini" | etc.
    priority: int  # 1 (highest) to 100 (lowest)
    enabled: bool = True
    command: str  # e.g., "copilot-cli chat" or "curl https://api.example.com"
    args_template: Optional[str] = None
    auth_state: str = "ok"  # "ok" | "needs_login" | "blocked"
    quota_daily: int = -1  # -1 = unlimited
    quota_reset_at: Optional[datetime] = None
    last_ok_at: Optional[datetime] = None
    last_fail_at: Optional[datetime] = None
    breaker_state: str = "closed"  # "closed" | "open" | "half_open"
    tags: List[str] = Field(default_factory=list)  # ["language", "coding", "reasoning"]


class CLIRequest(BaseModel):
    """Request to CLI Concentrator."""

    prompt: str
    intent: str  # "chat" | "code" | "reasoning" | "general"
    task_type: str  # "short" | "long"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    force_cli: bool = False  # Force CLI selection
    provider_preference: Optional[str] = None  # Preferred provider (can be overridden)
    trace_id: Optional[str] = None  # Correlation ID


class CLIResponse(BaseModel):
    """Response from CLI Concentrator."""

    reply: str
    provider_id: str
    model_hint: Optional[str] = None
    latency_ms: int = 0
    tokens_estimated: int = 0
    cost_estimated: float = 0.0
    success: bool = True
    error_class: Optional[str] = None
    trace_id: str
    scoring_debug: Optional[Dict[str, Any]] = None  # Debug scoring info


class CLIUsageStat(BaseModel):
    """Usage statistics for a CLI call."""

    provider_id: str
    timestamp: datetime
    success: bool
    latency_ms: int
    cost_estimated: float
    tokens_estimated: int
    error_class: Optional[str] = None


class RoutingEvent(BaseModel):
    """Routing decision event."""

    timestamp: datetime
    trace_id: str
    route_type: str  # "cli" | "local_model"
    provider_id: str
    score: float
    reasoning_short: str
