"""Operator backend routers module (minimal canonical API).

Provides canonical API definitions that tests can reference.
"""

from typing import Any, Dict

# Canonical API endpoints (contract definition)
canonical_api = {
    "endpoints": [
        {
            "path": "/operator/api/status",
            "method": "GET",
            "description": "System health + dormant services",
            "auth": "token_guard",
        },
        {
            "path": "/operator/api/config",
            "method": "GET",
            "description": "Operator configuration",
            "auth": "token_guard",
        },
        {
            "path": "/operator/api/metrics",
            "method": "GET",
            "description": "Performance metrics",
            "auth": "token_guard",
        },
        {
            "path": "/operator/api/events",
            "method": "GET",
            "description": "Event log",
            "auth": "token_guard",
        },
        {
            "path": "/operator/api/chat",
            "method": "POST",
            "description": "Chat interface",
            "auth": "token_guard",
        },
        {
            "path": "/operator/capabilities",
            "method": "POST",
            "description": "Feature discovery + dormant services",
            "auth": "token_guard",
        },
    ],
    "version": "7.0",
    "operational_mode": "solo_madre",
    "dormant_services": ["hormiguero", "shubniggurath", "mcp"],
}
