"""DB helpers for Tentáculo Link (use unified vx11.db session).

This module provides a tiny wrapper around `config.db_schema.get_session`
so the gateway can write minimal audit/events without migrations.
"""

from config.db_schema import get_session


def get_db_session():
    """Return a DB session connected to the unified vx11.db."""
    return get_session("vx11")
