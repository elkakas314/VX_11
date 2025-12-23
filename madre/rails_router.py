"""Madre Rails routing helpers (DB-first, cache with TTL)."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("vx11.madre.rails_router")

_CACHE: Dict[str, Any] = {
    "version": None,
    "expires_at": 0.0,
    "lanes": {},
    "db_path": None,
}


def _db_path() -> Path:
    return Path(os.getenv("VX11_DB_PATH", "./data/runtime/vx11.db"))


def _cache_ttl_seconds() -> int:
    raw = os.getenv("VX11_RAILS_ROUTING_CACHE_TTL_SECONDS", "3600")
    try:
        return int(raw)
    except ValueError:
        return 3600


def get_db() -> sqlite3.Connection:
    """Get SQLite connection for rails tables."""
    conn = sqlite3.connect(str(_db_path()))
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = sqlite3.Row
    return conn


def get_latest_map_version() -> Optional[str]:
    """Return latest rails map version (by created_at)."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT version
            FROM rails_map_versions
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        return row["version"] if row else None
    except Exception as exc:
        logger.error(f"get_latest_map_version failed: {exc}")
        return None
    finally:
        conn.close()


def _load_lanes(map_version: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT lane_id, domain, intent_type, owner_module, escalation_rule,
                   constraints_json, invariants_json
            FROM rails_lanes
            WHERE map_version = ?
            """,
            (map_version,),
        )
        lanes: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for row in cursor.fetchall():
            constraints = json.loads(row["constraints_json"]) if row["constraints_json"] else None
            invariants = json.loads(row["invariants_json"]) if row["invariants_json"] else None
            lanes[(row["domain"], row["intent_type"])] = {
                "lane_id": row["lane_id"],
                "domain": row["domain"],
                "intent_type": row["intent_type"],
                "owner_module": row["owner_module"],
                "escalation_rule": row["escalation_rule"],
                "constraints": constraints,
                "invariants": invariants,
                "map_version": map_version,
            }
        return lanes
    finally:
        conn.close()


def _refresh_cache(map_version: str, db_path: str) -> None:
    _CACHE["lanes"] = _load_lanes(map_version)
    _CACHE["version"] = map_version
    _CACHE["expires_at"] = time.time() + _cache_ttl_seconds()
    _CACHE["db_path"] = db_path


def find_lane(domain: str, intent_type: str) -> Optional[Dict[str, Any]]:
    """Find lane for (domain, intent_type) using cached rails map."""
    db_path = str(_db_path())
    if _CACHE["db_path"] != db_path:
        _CACHE["version"] = None
        _CACHE["expires_at"] = 0.0
        _CACHE["lanes"] = {}
        _CACHE["db_path"] = db_path

    map_version = get_latest_map_version()
    if not map_version:
        return None

    if _CACHE["version"] != map_version or time.time() >= _CACHE["expires_at"]:
        _refresh_cache(map_version, db_path)

    return _CACHE["lanes"].get((domain, intent_type))


def record_event(
    who: str,
    what: str,
    why: str,
    result_json: Optional[Dict[str, Any]],
    correlation_id: Optional[str],
) -> None:
    """Insert a rails_events row (audit trail)."""
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO rails_events (who, what, why, result_json, correlation_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                who,
                what,
                why,
                json.dumps(result_json) if result_json is not None else None,
                correlation_id,
            ),
        )
        conn.commit()
    except Exception as exc:
        logger.error(f"record_event failed: {exc}")
        conn.rollback()
    finally:
        conn.close()


def resolve_lane(
    domain: str,
    intent_type: str,
    correlation_id: Optional[str],
    details: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Resolve lane; on miss, emit lane_missing event."""
    lane = find_lane(domain, intent_type)
    if lane:
        return lane

    payload = {
        "domain": domain,
        "intent_type": intent_type,
        "details": details or {},
    }
    record_event(
        who="madre",
        what="lane_missing",
        why=f"{domain}:{intent_type}",
        result_json=payload,
        correlation_id=correlation_id,
    )
    return None
