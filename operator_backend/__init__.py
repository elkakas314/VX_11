"""Operator Backend package.

Real FastAPI application for operator API endpoints.
Used by tentaculo_link as proxy target and standalone for testing.
"""

from .backend.main_v7 import app, VX11_TOKEN

__all__ = ["app", "VX11_TOKEN"]
