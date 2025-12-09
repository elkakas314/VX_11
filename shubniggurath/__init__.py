"""Shubniggurath initialization module"""

__version__ = "1.0.0"
__author__ = "VX11 Core"

# Lazy imports para evitar conflictos de inicialización
try:
    from .database import Base, init_db
except Exception as e:
    print(f"Warning: Failed to import database: {e}")
    Base = None
    init_db = None

__all__ = [
    "Base",
    "init_db",
]
