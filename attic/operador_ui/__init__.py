"""Package shim adjustments.

NOTE: This repository includes a top-level `operator/` folder (frontend assets).
Creating an `__init__.py` here can accidentally shadow the stdlib `operator` module
which many libraries (numpy, etc.) import. This file exposes the stdlib `operator`
symbols and also provides a small `backend` alias to the real `operator_backend`
package so tests that expect `operator.backend` continue to work.
"""

import sys
import importlib
import importlib.util
from importlib.machinery import BuiltinImporter
import types

# Try to load the built-in stdlib 'operator' module and re-export safe symbols.
# Use BuiltinImporter to avoid reading filesystem paths and to be robust across
# Python builds. If this fails, do not attempt fragile filesystem loads.
try:
    spec = BuiltinImporter.find_spec("operator")
    if spec is not None and spec.loader is not None:
        _stdlib = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_stdlib)
        for _n in dir(_stdlib):
            if not _n.startswith("_"):
                globals()[_n] = getattr(_stdlib, _n)
except Exception:
    # fall back to minimal safe definitions if builtin import fails
    def itemgetter(i):
        def f(obj):
            return obj[i]
        return f

# Provide an `operator.backend` alias that forwards to operator_backend.backend
try:
    real_backend = importlib.import_module("operator_backend.backend")
    backend_mod = types.ModuleType("operator.backend")
    for _n in dir(real_backend):
        if not _n.startswith("_"):
            setattr(backend_mod, _n, getattr(real_backend, _n))
    sys.modules["operator.backend"] = backend_mod
    backend = backend_mod
except Exception:
    backend = types.ModuleType("operator.backend")
    sys.modules["operator.backend"] = backend

__all__ = [k for k in globals().keys() if not k.startswith("_")]
