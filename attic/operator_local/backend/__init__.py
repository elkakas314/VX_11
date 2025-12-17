"""Operator package shim to satisfy tests importing `operator.backend`.

This package re-exports a minimal `main` module that provides a `switch_client`
object which tests monkeypatch. The real backend lives in `operator_backend`.
"""

from . import main  # re-export main for `operator.backend.main`
