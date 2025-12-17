"""Shub-Niggurath core package.

Exports key classes used by tests to avoid import errors when the full
implementation is split across multiple modules.
"""

from .initializer import ShubCoreInitializer  # re-export
from .dsp_engine import DSPEngine  # re-export

__all__ = ["ShubCoreInitializer", "DSPEngine"]
