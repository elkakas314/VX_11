"""
Manifestator Rails Orchestrator Module
planning-only endpoints for querying + refreshing RailsMap
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import hashlib
from datetime import datetime
import sqlite3
from pathlib import Path

# === MODELS ===


class RailsLane(BaseModel):
    lane_id: str
    domain: str
    intent_type: str
    owner_module: str
    escalation_rule: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    invariants: Optional[List[str]] = None


class RailsMapResponse(BaseModel):
    map_version: str
    content_hash: str
    lanes: List[RailsLane]
    flow_templates: List[Dict[str, Any]]
    container_blueprints: List[Dict[str, Any]]
    generated_at: str
    canonical_source_hash: Optional[str] = None


class RailsRefreshRequest(BaseModel):
    reason: str = "scheduled_maintenance"
    consult_switch: bool = False
    force: bool = False
    correlation_id: Optional[str] = None


class RailsRefreshResponse(BaseModel):
    old_version: str
    new_version: str
    old_hash: str
    new_hash: str
    changes: Dict[str, Any]
    duration_ms: int
    canonical_source_hash: Optional[str] = None


# === DB HELPERS ===

DB_PATH = Path("./data/runtime/vx11.db")


def get_db_connection():
    """Get SQLite connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def read_rails_map_from_db(version: str = "latest") -> Optional[Dict[str, Any]]:
    """Read RailsMap from DB (planning-only, no computation)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get version
        if version == "latest":
            cursor.execute(
                """
              SELECT version, content_hash, created_at, source_canon_hash
              FROM rails_map_versions
              ORDER BY created_at DESC
              LIMIT 1
            """
            )
        else:
            cursor.execute(
                """
              SELECT version, content_hash, created_at, source_canon_hash
              FROM rails_map_versions
              WHERE version = ?
            """,
                (version,),
            )

        version_row = cursor.fetchone()
        if not version_row:
            conn.close()
            return None

        current_version, content_hash, created_at, canon_hash = version_row

        # Get lanes
        cursor.execute(
            """
          SELECT lane_id, domain, intent_type, owner_module, escalation_rule, 
                 constraints_json, invariants_json
          FROM rails_lanes
          WHERE map_version = ?
        """,
            (current_version,),
        )

        lanes = []
        for row in cursor.fetchall():
            lanes.append(
                {
                    "lane_id": row[0],
                    "domain": row[1],
                    "intent_type": row[2],
                    "owner_module": row[3],
                    "escalation_rule": row[4],
                    "constraints": json.loads(row[5]) if row[5] else None,
                    "invariants": json.loads(row[6]) if row[6] else None,
                }
            )

        # Get flow templates
        cursor.execute(
            """
          SELECT flow_id, triggers_json, steps_json, invariants_json
          FROM rails_flow_templates
          WHERE map_version = ?
        """,
            (current_version,),
        )

        templates = []
        for row in cursor.fetchall():
            templates.append(
                {
                    "flow_id": row[0],
                    "triggers": json.loads(row[1]) if row[1] else None,
                    "steps": json.loads(row[2]) if row[2] else None,
                    "invariants": json.loads(row[3]) if row[3] else None,
                }
            )

        # Get container blueprints
        cursor.execute(
            """
          SELECT blueprint_id, purpose, sandbox_policy_json, mounts_json, network_config,
                 cpu_limit_millicores, mem_limit_mb, ttl_sec
          FROM rails_container_blueprints
          WHERE map_version = ?
        """,
            (current_version,),
        )

        blueprints = []
        for row in cursor.fetchall():
            blueprints.append(
                {
                    "blueprint_id": row[0],
                    "purpose": row[1],
                    "sandbox_policy": json.loads(row[2]) if row[2] else None,
                    "mounts": json.loads(row[3]) if row[3] else None,
                    "network_config": row[4],
                    "cpu_limit_millicores": row[5],
                    "mem_limit_mb": row[6],
                    "ttl_sec": row[7],
                }
            )

        conn.close()

        return {
            "map_version": current_version,
            "content_hash": content_hash,
            "lanes": lanes,
            "flow_templates": templates,
            "container_blueprints": blueprints,
            "generated_at": created_at,
            "canonical_source_hash": canon_hash,
        }

    except Exception as e:
        import logging

        logging.error(f"read_rails_map_from_db error: {e}")
        return None


# === ENDPOINTS ===

router = None  # Will be attached to main app


def create_rails_router():
    """Create FastAPI router for rails endpoints."""
    from fastapi import APIRouter

    router = APIRouter(prefix="/manifestator/rails", tags=["manifestator-rails"])

    @router.get("/map")
    async def get_rails_map(version: str = "latest") -> RailsMapResponse:
        """
        GET /manifestator/rails/map
        Read-only access to RailsMap from DB (no Manifestator computation).
        """
        data = read_rails_map_from_db(version)
        if not data:
            raise HTTPException(
                status_code=404, detail=f"RailsMap version not found: {version}"
            )

        return RailsMapResponse(**data)

    @router.post("/refresh")
    async def refresh_rails(
        request: RailsRefreshRequest, x_maintenance_token: str = Header(None)
    ) -> RailsRefreshResponse:
        """
        POST /manifestator/rails/refresh
        Recalculate RailsMap from canonical + errors (maintenance-only).
        Gated by maintenance token or role.
        """
        # ⚠️ Gate: Check maintenance token (placeholder; adjust to your auth system)
        if not x_maintenance_token or x_maintenance_token != "MAINTENANCE_SECRET":
            raise HTTPException(status_code=403, detail="Maintenance token required")

        import time

        start_ms = time.time() * 1000

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get current version
            cursor.execute(
                """
              SELECT version FROM rails_map_versions
              ORDER BY created_at DESC LIMIT 1
            """
            )
            old_version_row = cursor.fetchone()
            old_version = old_version_row[0] if old_version_row else "v0.0"

            # New version: increment
            parts = old_version.split(".")
            new_patch = int(parts[-1]) + 1 if len(parts) > 0 else 1
            new_version = f"v1.{new_patch}"

            # === PLACEHOLDER: R1 suggests recalculating from canon ===
            # For now, just copy lanes/templates/blueprints from old version
            # TODO: Consult docs/canon/* and recompute

            cursor.execute(
                """
              SELECT lane_id, domain, intent_type, owner_module, escalation_rule,
                     constraints_json, invariants_json
              FROM rails_lanes
              WHERE map_version = ?
            """,
                (old_version,),
            )

            old_lanes = cursor.fetchall()
            lanes_count = len(old_lanes)

            # Compute content hash for new version
            content_payload = json.dumps(
                {"version": new_version, "lanes": lanes_count}, sort_keys=True
            )
            content_hash = hashlib.sha256(content_payload.encode()).hexdigest()[:12]

            # Insert new version
            cursor.execute(
                """
              INSERT INTO rails_map_versions (version, content_hash, author, notes)
              VALUES (?, ?, ?, ?)
            """,
                (
                    new_version,
                    content_hash,
                    "manifestator",
                    f"Refresh: {request.reason}",
                ),
            )

            # Copy lanes to new version
            for lane_row in old_lanes:
                cursor.execute(
                    """
                  INSERT INTO rails_lanes 
                    (lane_id, domain, intent_type, owner_module, escalation_rule, 
                     constraints_json, invariants_json, map_version)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (*lane_row[:-1], new_version),
                )

            # Record event
            cursor.execute(
                """
              INSERT INTO rails_events (who, what, why, result_json, correlation_id)
              VALUES (?, ?, ?, ?, ?)
            """,
                (
                    "manifestator",
                    "rails_refresh",
                    request.reason,
                    json.dumps({"status": "ok", "lanes": lanes_count}),
                    request.correlation_id,
                ),
            )

            conn.commit()
            conn.close()

            duration_ms = int(time.time() * 1000 - start_ms)

            return RailsRefreshResponse(
                old_version=old_version,
                new_version=new_version,
                old_hash="sha256:...",  # Placeholder
                new_hash=content_hash,
                changes={"lanes_added": 0, "lanes_removed": 0, "lanes_updated": 0},
                duration_ms=duration_ms,
            )

        except Exception as e:
            import logging

            logging.error(f"refresh_rails error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
