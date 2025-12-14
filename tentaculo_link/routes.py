"""
Tentáculo Link - Route Table for Intent Routing
Maps intent_type → {module_url, endpoint, method, timeout}
"""

from typing import Dict, Optional, Literal
from enum import Enum


class IntentType(str, Enum):
    """Supported intent types for routing."""
    CHAT = "chat"
    CODE = "code"
    AUDIO = "audio"
    ANALYSIS = "analysis"
    TASK = "task"
    SPAWN = "spawn"
    STREAM = "stream"


class RouteConfig:
    """Route configuration for a specific intent type."""
    
    def __init__(
        self,
        module: str,
        endpoint: str,
        method: Literal["GET", "POST"] = "POST",
        timeout: float = 15.0,
        description: str = "",
        auth_required: bool = True,
    ):
        self.module = module
        self.endpoint = endpoint
        self.method = method
        self.timeout = timeout
        self.description = description
        self.auth_required = auth_required
    
    def to_dict(self) -> Dict:
        return {
            "module": self.module,
            "endpoint": self.endpoint,
            "method": self.method,
            "timeout": self.timeout,
            "description": self.description,
            "auth_required": self.auth_required,
        }


# Route Table: Intent Type → Route Config
ROUTE_TABLE: Dict[IntentType, RouteConfig] = {
    IntentType.CHAT: RouteConfig(
        module="switch",
        endpoint="/switch/route-v5",
        method="POST",
        timeout=15.0,
        description="Route chat to Switch (IA model selection)",
        auth_required=True,
    ),
    IntentType.CODE: RouteConfig(
        module="switch",
        endpoint="/switch/route-v5",
        method="POST",
        timeout=20.0,
        description="Route code analysis to Switch",
        auth_required=True,
    ),
    IntentType.AUDIO: RouteConfig(
        module="hermes",
        endpoint="/hermes/analyze-audio",
        method="POST",
        timeout=30.0,
        description="Route audio processing to Hermes",
        auth_required=True,
    ),
    IntentType.ANALYSIS: RouteConfig(
        module="madre",
        endpoint="/madre/task",
        method="POST",
        timeout=60.0,
        description="Route deep analysis to Madre (spawner)",
        auth_required=True,
    ),
    IntentType.TASK: RouteConfig(
        module="madre",
        endpoint="/madre/task",
        method="POST",
        timeout=60.0,
        description="Create task via Madre",
        auth_required=True,
    ),
    IntentType.SPAWN: RouteConfig(
        module="spawner",
        endpoint="/spawner/spawn",
        method="POST",
        timeout=120.0,
        description="Spawn ephemeral hija",
        auth_required=True,
    ),
    IntentType.STREAM: RouteConfig(
        module="shub",
        endpoint="/shub/stream",
        method="POST",
        timeout=300.0,
        description="Route to Shubniggurath (audio pipeline)",
        auth_required=True,
    ),
}


def get_route(intent_type: str) -> Optional[RouteConfig]:
    """
    Lookup route for a given intent_type.
    
    Args:
        intent_type: Intent type (str or IntentType enum)
    
    Returns:
        RouteConfig if found, None otherwise
    """
    try:
        intent = IntentType(intent_type)
        return ROUTE_TABLE.get(intent)
    except (ValueError, KeyError):
        return None


def list_routes() -> Dict[str, Dict]:
    """List all available routes."""
    return {
        intent.value: config.to_dict()
        for intent, config in ROUTE_TABLE.items()
    }


def register_route(intent_type: str, config: RouteConfig) -> None:
    """
    Register a new route (runtime modification).
    Use with caution; prefer static routes in ROUTE_TABLE.
    """
    try:
        intent = IntentType(intent_type)
        ROUTE_TABLE[intent] = config
    except ValueError:
        raise ValueError(f"Invalid intent_type: {intent_type}")
