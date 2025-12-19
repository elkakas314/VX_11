"""
Operator package shim.

Objetivo:
- Permitir `import operator.backend.*` sin romper la librería estándar.
- Reexportar los helpers de `_operator` para mantener compatibilidad con terceros.
"""

from __future__ import annotations

import sys
from types import ModuleType

try:
    import _operator as _stdlib_operator  # C-extension, no dependencias
except Exception:  # pragma: no cover - entorno incompleto
    _stdlib_operator = None


def _expose_stdlib() -> list[str]:
    """Copia segura de funciones stdlib para que el shim actúe como operator."""
    exposed: list[str] = []
    if not _stdlib_operator:
        return exposed
    for name in (
        "abs",
        "add",
        "and_",
        "attrgetter",
        "concat",
        "contains",
        "countOf",
        "delitem",
        "eq",
        "floordiv",
        "ge",
        "getitem",
        "ge",
        "gt",
        "index",
        "iadd",
        "iand",
        "iconcat",
        "ifloordiv",
        "ilshift",
        "imatmul",
        "imod",
        "imul",
        "invert",
        "ior",
        "inv",
        "invert",
        "is_",
        "is_not",
        "itemgetter",
        "itruediv",
        "ixor",
        "le",
        "length_hint",
        "lshift",
        "lt",
        "matmul",
        "methodcaller",
        "mod",
        "mul",
        "ne",
        "neg",
        "not_",
        "or_",
        "pos",
        "pow",
        "rshift",
        "setitem",
        "sub",
        "truediv",
        "truth",
        "xor",
    ):
        if hasattr(_stdlib_operator, name):
            globals()[name] = getattr(_stdlib_operator, name)
            exposed.append(name)
    return exposed


_EXPOSED = _expose_stdlib()

# Garantizar que, si el operador stdlib se cargó antes, el módulo actual añade backend.
existing = sys.modules.get(__name__)
if isinstance(existing, ModuleType) and existing is not globals():
    existing.__dict__.update(globals())
    sys.modules[__name__] = existing

__all__ = sorted(set(_EXPOSED + [name for name in globals() if not name.startswith("_")]))
