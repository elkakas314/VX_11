"""Thin entrypoint for Tentáculo Link (production-ready launcher).

This module re-exports the FastAPI `app` defined in `main_v7.py` so that
deployments can import `tentaculo_link.main:app` as the ASGI app.
Low-power, no heavy imports here.
"""

from tentaculo_link.main_v7 import app  # re-export main app

__all__ = ["app"]
"""
Tentáculo Link - Main entry point (alias to main_v7)
"""

from .main_v7 import app  # noqa: F401
