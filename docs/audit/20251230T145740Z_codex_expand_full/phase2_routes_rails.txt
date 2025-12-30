"""
VX11 Operator Routes: Rails (Manifestator Integration)
tentaculo_link/routes/rails.py

Endpoints:
- GET /api/rails/lanes: List drift detection lanes + validation stages
- GET /api/rails: List all manifestator constraints/rules
- GET /api/rails/{lane_id}/status: Detailed lane status + audit findings
"""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Path as PathParam
import os
import json
import sqlite3
from pathlib import Path

try:
    from hormiguero.manifestator.controller import RailsController
except ImportError:
    RailsController = None

router = APIRouter(prefix="/api", tags=["rails"])
controller = None


def get_controller() -> Optional[RailsController]:
    """Get or initialize RailsController if available"""
    global controller
    if controller is None and RailsController is not None:
        repo_root = os.environ.get("VX11_REPO_ROOT", "/home/elkakas314/vx11")
        controller = RailsController(repo_root)
    return controller


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
        }

    if RailsController is None:
        raise HTTPException(
            status_code=501, detail="Hormiguero module not available in this deployment"
        )

    try:
        ctrl = get_controller()
        lanes = ctrl.get_all_lanes()
        return {
            "lanes": lanes,
            "count": len(lanes),
        }
    except Exception as e:
        return {
            "error": str(e),
            "lanes": [],
            "count": 0,
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
          "description": "..."
        }
      ],
      "count": 42
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
            "count": 0,
        }

    try:
        ctrl = get_controller()
        rails = ctrl.get_all_rails()
        return {
            "rails": rails,
            "count": len(rails),
        }
    except Exception as e:
        return {
            "error": str(e),
            "rails": [],
            "count": 0,
        }


@router.get("/rails/{lane_id}/status")
async def get_lane_status(
    lane_id: str = PathParam(..., description="Lane ID"),
    auth: bool = Depends(check_auth),
):
    """
    GET /api/rails/{lane_id}/status - Detailed lane status + audit findings

    Response:
    {
      "lane_id": "lane_structure_fs_drift",
      "name": "Filesystem Drift Detection",
      "description": "Detect filesystem drift against canonical manifest",
      "stage": "detect|plan|validate|apply",
      "checks": [...],
      "audit_findings": [
        {
          "event_id": "uuid",
          "finding_type": "drift|validation|risk",
          "severity": "critical|error|warn|info",
          "summary": "summary",
          "details": {...},
          "created_at": "timestamp"
        }
      ],
      "status": "ok",
      "created_at": "timestamp"
    }
    """

    if not os.environ.get("VX11_MANIFESTATOR_ENABLED", "false").lower() in (
        "true",
        "1",
    ):
        return {
            "error": "feature_disabled",
            "flag": "VX11_MANIFESTATOR_ENABLED",
            "lane_id": lane_id,
            "status": "disabled",
        }

    try:
        ctrl = get_controller()
        result = ctrl.get_lane_status(lane_id)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "lane_id": lane_id,
            "status": "error",
        }
