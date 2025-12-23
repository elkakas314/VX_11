"""SQLite helpers for Hormiguero."""

import sqlite3
from contextlib import contextmanager
from typing import Dict, List

try:
    from hormiguero.config import settings
except ModuleNotFoundError:
    from config import settings


def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_connection():
    conn = sqlite3.connect(settings.db_path, timeout=5, check_same_thread=False)
    conn.row_factory = _dict_factory
    try:
        yield conn
    finally:
        conn.close()


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (table,),
    )
    return cur.fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cur = conn.execute(f"PRAGMA table_info({table});")
    return [row["name"] for row in cur.fetchall()]


def _ensure_columns(
    conn: sqlite3.Connection, table: str, columns: Dict[str, str]
) -> None:
    existing = set(_columns(conn, table))
    for name, col_type in columns.items():
        if name in existing:
            continue
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {col_type};")


def ensure_schema() -> None:
    schema = {
        "hormiga_state": {
            "hormiga_id": "TEXT",
            "ant_id": "TEXT",
            "name": "TEXT",
            "role": "TEXT",
            "enabled": "INTEGER",
            "aggression_level": "INTEGER",
            "scan_interval_sec": "INTEGER",
            "last_scan_at": "DATETIME",
            "last_ok_at": "DATETIME",
            "last_error_at": "DATETIME",
            "last_error": "TEXT",
            "stats_json": "TEXT",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "incidents": {
            "incident_id": "TEXT",
            "kind": "TEXT",
            "severity": "TEXT",
            "status": "TEXT",
            "title": "TEXT",
            "description": "TEXT",
            "evidence_json": "TEXT",
            "source": "TEXT",
            "detected_at": "DATETIME",
            "first_seen_at": "DATETIME",
            "last_seen_at": "DATETIME",
            "resolved_at": "DATETIME",
            "correlation_id": "TEXT",
            "tags": "TEXT",
            "suggested_actions_json": "TEXT",
            "execution_plan_json": "TEXT",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
        },
        "pheromone_log": {
            "pheromone_id": "TEXT",
            "incident_id": "TEXT",
            "action_kind": "TEXT",
            "action_payload_json": "TEXT",
            "requested_by": "TEXT",
            "approved_by": "TEXT",
            "status": "TEXT",
            "result_json": "TEXT",
            "created_at": "DATETIME",
            "updated_at": "DATETIME",
            "executed_at": "DATETIME",
        },
        "feromona_events": {
            "kind": "TEXT",
            "scope": "TEXT",
            "payload_json": "TEXT",
            "source": "TEXT",
            "created_at": "DATETIME",
        },
    }

    with get_connection() as conn:
        for table, columns in schema.items():
            if not _table_exists(conn, table):
                column_defs = ["id INTEGER PRIMARY KEY"]
                for name, col_type in columns.items():
                    column_defs.append(f"{name} {col_type}")
                conn.execute(f"CREATE TABLE {table} ({', '.join(column_defs)});")
            _ensure_columns(conn, table, columns)

        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_hormiga_state_hormiga_id "
            "ON hormiga_state(hormiga_id);"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_incidents_incident_id "
            "ON incidents(incident_id);"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_pheromone_log_pheromone_id "
            "ON pheromone_log(pheromone_id);"
        )
        conn.commit()
