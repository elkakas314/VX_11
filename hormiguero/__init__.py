"""Namespace shim to expose hormiguero.hormiguero as hormiguero.* imports."""

from pathlib import Path
import pkgutil

__path__ = pkgutil.extend_path(__path__, __name__)

_nested = Path(__file__).resolve().parent / "hormiguero"
if _nested.exists():
    __path__.append(str(_nested))
