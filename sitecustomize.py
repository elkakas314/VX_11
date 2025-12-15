# sitecustomize.py
# Bootstrap para manejar colisiones de `operator` package vs stdlib module
# Se ejecuta AUTOMÁTICAMENTE por pytest/Python cuando el repo está en PYTHONPATH

import sys
import asyncio
import threading


# 1. Ensure event loop in main thread
def _ensure_event_loop():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


_ensure_event_loop()

# 2. Pre-populate operator module with ALL stdlib symbols BEFORE importing operator/ package
try:
    import operator as _stdlib_operator

    # Keep reference to stdlib operator
    _STDLIB_OPERATOR = _stdlib_operator

    # Create operator namespace dict with ALL stdlib symbols
    _operator_symbols = {}
    for _attr in dir(_stdlib_operator):
        if not _attr.startswith("_"):
            _operator_symbols[_attr] = getattr(_stdlib_operator, _attr)

    # Inject these into the operator module itself
    # This ensures stdlib functions are available EVEN IF a local operator package exists
    _stdlib_operator.__dict__.update(_operator_symbols)

except Exception as e:
    pass  # Silence warnings; fallback will be in operator/__init__.py


_ensure_repo_on_path()
import types
import importlib as _importlib

# Create a safe `operator` module wrapper that preserves stdlib `operator`
# functions while allowing the repo `operator` package to provide submodules.
try:
    # Import the real stdlib operator (sys.path has repo appended, so stdlib wins)
    std_operator = _importlib.import_module("operator")
    mod = types.ModuleType("operator")
    # copy stdlib operator attributes (itemgetter, methodcaller, etc.)
    for k, v in vars(std_operator).items():
        setattr(mod, k, v)
    # let Python find repo subpackages like operator.backend under this path
    repo_op_path = str(REPO_ROOT / "operator")
    mod.__path__ = [repo_op_path]
    sys.modules["operator"] = mod
except Exception:
    # If anything fails, don't break imports — leave sys.modules unchanged
    pass


_ensure_repo_on_path()
import types
import importlib as _importlib

# Create a safe `operator` module wrapper that preserves stdlib `operator`
# functions while allowing a local `operator/backend` package under the repo.
try:
    std_operator = _importlib.import_module("operator")
    mod = types.ModuleType("operator")
    # copy stdlib operator attributes
    for k, v in vars(std_operator).items():
        setattr(mod, k, v)
    # allow importing `operator.backend` from repo/operator/
    mod.__path__ = [str(REPO_ROOT / "operator")]
    sys.modules["operator"] = mod
except Exception:
    # fallback: leave sys.modules alone
    pass

_patch_operator_package()

# Ensure an event loop exists in the main thread (some tests expect to run
# `asyncio.get_event_loop().run_until_complete(...)`). Create one if missing.
try:
    asyncio.get_event_loop()
except RuntimeError:
    if threading.current_thread() is threading.main_thread():
        asyncio.set_event_loop(asyncio.new_event_loop())
