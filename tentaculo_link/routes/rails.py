"""
VX11 Operator Routes: Rails (Manifestator Integration)
tentaculo_link/routes/rails.py

Endpoint: GET /api/rails/lanes
"""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
import os
import json
import sqlite3
from pathlib import Path

router = APIRouter(prefix="/api", tags=["rails"])


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


def get_db() -> sqlite3.Connection:
    repo_root = Path(os.environ.get("VX11_REPO_ROOT", "/home/elkakas314/vx11"))
    db_path = repo_root / "data" / "runtime" / "vx11.db"
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/rails/lanes")
async def get_rails_lanes(auth: bool = Depends(check_auth)):
    """
    GET /api/rails/lanes - Get manifestator drift detection lanes

    Response:
    {
      "lanes": [
        {
          "lane_id": "lane_001_detect",
          "name": "Drift Detection",
          "description": "Identify deviations from canonical state",
          "stage": "detect|plan|validate|apply",
          "checks": [
            {
              "check_id": "drift_001",
              "name": "File integrity check",
              "timeout_seconds": 30
            }
          ]
        }
      ],
      "rails": [
        {
          "rail_id": "rail_001_single_entrypoint",
          "name": "Single Entrypoint Validation",
          "rule_type": "constraint",
          "severity": "critical"
        }
      ]
    }
    """

    if not os.environ.get("VX11_MANIFESTATOR_ENABLED", "false").lower() in (
        "true",
        "1",
    ):
        return {
            "error": "feature_disabled",
            "flag": "VX11_MANIFESTATOR_ENABLED",
            "lanes": [],
            "rails": [],
        }

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get lanes
        cursor.execute(
            """
            SELECT lane_id, name, description, stage, checks_json
            FROM manifestator_lanes
            ORDER BY stage
            """
        )
        lane_rows = cursor.fetchall()

        # Get rails
        cursor.execute(
            """
            SELECT rail_id, name, description, rule_type, severity_on_violation, active
            FROM manifestator_rails
            WHERE active = TRUE
            ORDER BY severity_on_violation DESC
            """
        )
        rail_rows = cursor.fetchall()

        conn.close()

        lanes = []
        for row in lane_rows:
            try:
                checks = json.loads(row["checks_json"] or "[]")
            except:
                checks = []

            lanes.append(
                {
                    "lane_id": row["lane_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "stage": row["stage"],
                    "checks": checks,
                }
            )

        rails = []
        for row in rail_rows:
            rails.append(
                {
                    "rail_id": row["rail_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "rule_type": row["rule_type"],
                    "severity": row["severity_on_violation"],
                    "active": row["active"],
                }
            )

        return {
            "lanes": lanes,
            "rails": rails,
        }
    except Exception as e:
        return {
            "error": str(e),
            "lanes": [],
            "rails": [],
        }


@router.get("/rails")
async def get_rails(auth: bool = Depends(check_auth)):
    """
    GET /api/rails - Get all manifestator rails (constraints + rules)

    Response:
    {
      "rails": [
        {
          "rail_id": "rail_001",
          "name": "Name",
          "rule_type": "constraint|drift_threshold|naming_convention|schema_rule",
          "severity": "critical|error|warn",
          "active": true,
          "rule_definition": {...}
        }
      ]
    }
    """

    if not os.environ.get("VX11_MANIFESTATOR_ENABLED", "false").lower() in (
        "true",
        "1",
    ):
        return {
            "error": "feature_disabled",
            "flag": "VX11_MANIFESTATOR_ENABLED",
            "rails": [],
        }

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT rail_id, name, description, rule_type, rule_definition_json, 
                   severity_on_violation, active
            FROM manifestator_rails
            ORDER BY severity_on_violation DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        rails = []
        for row in rows:
            try:
                rule_def = json.loads(row["rule_definition_json"] or "{}")
            except:
                rule_def = {}

            rails.append(
                {
                    "rail_id": row["rail_id"],
                    "name": row["name"],
                    "description": row["description"],
                    "rule_type": row["rule_type"],
                    "severity": row["severity_on_violation"],
                    "active": row["active"],
                    "rule_definition": rule_def,
                }
            )

        return {
            "rails": rails,
        }
    except Exception as e:
        return {
            "error": str(e),
            "rails": [],
        }
