"""Compatibility shim: re-export `app` from `main_v7.py` so tests
that import `operator_backend.backend.main` continue to work.
"""

from operator_backend.backend.main_v7 import app

__all__ = ["app"]
