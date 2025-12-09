"""Shub Database Module - PostgreSQL integration"""

from .models import Base, init_db

__all__ = ["Base", "init_db"]
