from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def load_operator_backend() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    backend_path = repo_root / "operator" / "backend" / "main.py"
    spec = importlib.util.spec_from_file_location("vx11_operator_backend", backend_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load operator backend module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
