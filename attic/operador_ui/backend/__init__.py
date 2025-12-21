"""Shim subpackage to expose `main` module expected by tests.

This file intentionally left minimal; main.py will re-export the real module.
"""

__all__ = ["main"]
