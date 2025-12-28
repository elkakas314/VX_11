"""Bridge package so `operator.backend` resolves to `operator_backend.backend`.

This module re-exports the repository implementation under the dotted
name expected by tests (operator.backend.browser). Using a small bridge
file on disk is the most reliable way for Python's import machinery and
`unittest.mock.patch` to find the target.
"""

import importlib

try:
    _browser = importlib.import_module("operator_backend.backend.browser")
    # expose the browser module as attribute `browser` on this package
    browser = _browser
    __all__ = ["browser"]
except Exception:
    # Fallback minimal placeholder to avoid import errors during startup
    browser = None
    __all__ = ["browser"]
# operator.backend shim package
from . import main  # re-export main for `operator.backend.main`
from . import browser
