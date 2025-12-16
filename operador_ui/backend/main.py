"""Compatibility shim that re-exports the real operator backend implementation.

Tests import `operator.backend.main`. The real implementation lives under
`operator_backend.backend.main_v7` in this workspace — re-export symbols here
so monkeypatch and imports succeed.
"""

from importlib import import_module
_real = import_module("operator_backend.backend.main_v7")

# Re-export commonly used names
for _name, _obj in vars(_real).items():
    if _name.startswith("__"):
        continue
    globals()[_name] = _obj

__all__ = [n for n in globals().keys() if not n.startswith("_")]
