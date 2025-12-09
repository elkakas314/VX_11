"""
Bootstrap shim para el paquete `operator` evitando colisiones con la librería estándar.
Se ejecuta automáticamente cuando el repo está en PYTHONPATH (pytest, uvicorn, etc.).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
OPERATOR_INIT = REPO_ROOT / "operator" / "__init__.py"


def _ensure_repo_on_path():
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _patch_operator_package():
    """Extiende el módulo stdlib `operator` para que actúe como paquete shim."""
    if not OPERATOR_INIT.exists():
        return
    mod = sys.modules.get("operator")
    if mod:
        # Convertir módulo stdlib en paquete apuntando al shim local.
        mod.__path__ = [str(OPERATOR_INIT.parent)]
        if getattr(mod, "__spec__", None):
            mod.__spec__.submodule_search_locations = mod.__path__
        try:
            code = OPERATOR_INIT.read_text()
            exec(compile(code, str(OPERATOR_INIT), "exec"), mod.__dict__)
            return
        except Exception:
            # fallback a carga limpia
            sys.modules.pop("operator", None)

    spec = importlib.util.spec_from_file_location("operator", OPERATOR_INIT)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules["operator"] = module
        spec.loader.exec_module(module)


_ensure_repo_on_path()
_patch_operator_package()
