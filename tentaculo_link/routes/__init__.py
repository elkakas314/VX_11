"""
VX11 Operator API Routes Package
tentaculo_link/routes/__init__.py

Exposes all route modules for integration into tentaculo_link main app.
"""

from . import events
from . import settings
from . import audit
from . import metrics
from . import rails
from . import window
from . import internal
from . import hormiguero
from . import spawner

__all__ = [
    "events",
    "settings",
    "audit",
    "metrics",
    "rails",
    "window",
    "internal",
    "hormiguero",
    "spawner",
]
