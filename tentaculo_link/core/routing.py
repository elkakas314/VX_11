"""Core routing helpers for Tentáculo Link.

Thin helpers that reuse `routes.py` static table, kept lightweight.
"""

from typing import Optional, Dict
from tentaculo_link.routes import get_route, list_routes


def lookup_route(intent_type: str) -> Optional[Dict]:
    cfg = get_route(intent_type)
    return cfg.to_dict() if cfg else None


def routes_map() -> Dict[str, Dict]:
    return list_routes()
