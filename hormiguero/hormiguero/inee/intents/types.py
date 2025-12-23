"""INEE types and data structures for VX11 intent mapping."""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class INEEIntent:
    """Intent proveniente de remote INEE (before translation to VX11)."""

    intent_id: str
    remote_colony_id: str
    intent_type: str  # e.g., "diagnose", "propose", "apply"
    payload: Dict[str, Any]
    timestamp: str  # ISO8601
    correlation_id: Optional[str] = None


@dataclass
class VX11Intent:
    """Intent traslated to VX11 internal format."""

    intent_id: str
    source: str  # "inee"
    operation: str  # "scan", "notify_incident", "propose_action"
    context: Dict[str, Any]
    created_at: str  # ISO8601
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class INEEColony:
    """Remote INEE colony registration."""

    colony_id: str
    remote_url: Optional[str] = None
    status: str = "pending"  # pending, active, failed, disabled
    last_heartbeat: Optional[str] = None
    agent_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class INEEAgent:
    """Agent within an INEE colony."""

    agent_id: str
    colony_id: str
    agent_type: str  # e.g., "scanner", "planner", "executor"
    status: str = "idle"  # idle, working, failed
    last_seen: Optional[str] = None
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class INEEPheromone:
    """Pheromone-like signal in INEE (async message)."""

    pheromone_id: str
    colony_id: str
    signal_type: str  # e.g., "pressure", "alert", "coordination"
    payload: Dict[str, Any]
    ttl_seconds: int = 300
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
