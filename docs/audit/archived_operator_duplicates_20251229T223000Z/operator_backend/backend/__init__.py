"""Backend submodule: FastAPI app + core contracts."""

from .main_v7 import app, VX11_TOKEN, health_check

__all__ = ["app", "VX11_TOKEN", "health_check"]
