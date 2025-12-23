"""Repository helpers for Hormiguero data."""

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from hormiguero.core.db.sqlite import get_connection
except ModuleNotFoundError:
    from core.db.sqlite import get_connection


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _stable_id(seed: str) -> str:
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()


def upsert_hormiga_state(
    hormiga_id: str,
    name: str,
    role: str,
    enabled: bool,
    aggression_level: int,
    scan_interval_sec: int,
    ant_id: Optional[str] = None,
    last_scan_at: Optional[str] = None,
    last_ok_at: Optional[str] = None,
    last_error_at: Optional[str] = None,
    last_error: Optional[str] = None,
    stats_json: Optional[Dict[str, Any]] = None,
) -> None:
    payload = json.dumps(stats_json or {})
    now = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO hormiga_state (
                hormiga_id, ant_id, name, role, enabled, aggression_level, scan_interval_sec,
                last_scan_at, last_ok_at, last_error_at, last_error, stats_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hormiga_id) DO UPDATE SET
                ant_id=excluded.ant_id,
                name=excluded.name,
                role=excluded.role,
                enabled=excluded.enabled,
                aggression_level=excluded.aggression_level,
                scan_interval_sec=excluded.scan_interval_sec,
                last_scan_at=excluded.last_scan_at,
                last_ok_at=excluded.last_ok_at,
                last_error_at=excluded.last_error_at,
                last_error=excluded.last_error,
                stats_json=excluded.stats_json,
                updated_at=excluded.updated_at;
            """,
            (
                hormiga_id,
                ant_id or hormiga_id,
                name,
                role,
                int(enabled),
                aggression_level,
                scan_interval_sec,
                last_scan_at,
                last_ok_at,
                last_error_at,
                last_error,
                payload,
                now,
                now,
            ),
        )
        conn.commit()


def upsert_incident(
    kind: str,
    severity: str,
    status: str,
    title: str,
    description: str,
    source: str,
    evidence: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    correlation_id: Optional[str] = None,
    incident_id: Optional[str] = None,
) -> str:
    now = _now()
    if not incident_id:
        seed = f"{kind}:{title}:{source}:{correlation_id or ''}"
        incident_id = correlation_id or _stable_id(seed)
    evidence_json = json.dumps(evidence or {})
    tags_json = json.dumps(tags or [])
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT incident_id, first_seen_at FROM incidents WHERE incident_id=?;",
            (incident_id,),
        )
        row = cur.fetchone()
        if row:
            conn.execute(
                """
                UPDATE incidents
                SET severity=?, status=?, title=?, description=?, evidence_json=?, source=?,
                    last_seen_at=?, updated_at=?
                WHERE incident_id=?;
                """,
                (
                    severity,
                    status,
                    title,
                    description,
                    evidence_json,
                    source,
                    now,
                    now,
                    incident_id,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO incidents (
                    incident_id, kind, severity, status, title, description,
                    evidence_json, source, detected_at, first_seen_at, last_seen_at,
                    correlation_id, tags, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    incident_id,
                    kind,
                    severity,
                    status,
                    title,
                    description,
                    evidence_json,
                    source,
                    now,
                    now,
                    now,
                    correlation_id,
                    tags_json,
                    now,
                    now,
                ),
            )
        conn.commit()
    return incident_id


def set_incident_suggestions(
    incident_id: str, suggested_actions: Dict[str, Any]
) -> None:
    now = _now()
    with get_connection() as conn:
        conn.execute(
            "UPDATE incidents SET suggested_actions_json=?, updated_at=? WHERE incident_id=?;",
            (json.dumps(suggested_actions), now, incident_id),
        )
        conn.commit()


def list_incidents(status: Optional[str], limit: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if status:
            cur = conn.execute(
                "SELECT * FROM incidents WHERE status=? ORDER BY last_seen_at DESC LIMIT ?;",
                (status, limit),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM incidents ORDER BY last_seen_at DESC LIMIT ?;",
                (limit,),
            )
        return cur.fetchall()


def create_pheromone_log(
    pheromone_id: str,
    incident_id: str,
    action_kind: str,
    action_payload: Dict[str, Any],
    requested_by: str,
    status: str = "pending",
) -> None:
    now = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO pheromone_log (
                pheromone_id, incident_id, action_kind, action_payload_json,
                requested_by, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                pheromone_id,
                incident_id,
                action_kind,
                json.dumps(action_payload),
                requested_by,
                status,
                now,
                now,
            ),
        )
        conn.commit()


def list_pheromones(limit: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM pheromone_log ORDER BY created_at DESC LIMIT ?;",
            (limit,),
        )
        return cur.fetchall()


def approval_status(correlation_id: str) -> Optional[str]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT status FROM pheromone_log
            WHERE pheromone_id=? OR incident_id=?
            ORDER BY created_at DESC LIMIT 1;
            """,
            (correlation_id, correlation_id),
        )
        row = cur.fetchone()
    return row["status"] if row else None


def record_feromona_event(
    kind: str, scope: str, payload: Dict[str, Any], source: str
) -> None:
    now = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO feromona_events (kind, scope, payload_json, source, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            (kind, scope, json.dumps(payload), source, now),
        )
        conn.commit()


def recent_hijas_errors(limit: int = 20) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT * FROM hijas_runtime
            WHERE state IN ('error', 'failed', 'timeout')
            ORDER BY last_heartbeat DESC
            LIMIT ?;
            """,
            (limit,),
        )
        return cur.fetchall()
