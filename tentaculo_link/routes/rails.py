"""
VX11 Operator Routes: Rails (Manifestator Integration)
tentaculo_link/routes/rails.py

Endpoints:
- GET /api/rails/lanes: List drift detection lanes + validation stages
- GET /api/rails: List all manifestator constraints/rules
- GET /api/rails/{lane_id}/status: Detailed lane status + audit findings
"""

from typing import Optional, TYPE_CHECKING, Union
from fastapi import APIRouter, Depends, Header, HTTPException, Path as PathParam
from fastapi.responses import JSONResponse
import os
import json
import sqlite3
from pathlib import Path
import httpx

if TYPE_CHECKING:
    from hormiguero.manifestator.controller import RailsController

router = APIRouter(prefix="/api", tags=["rails"])
controller = None


def _resolve_controller_class():
    try:
        from hormiguero.manifestator.controller import RailsController

        return RailsController
    except ImportError:
        return None


async def _get_power_policy() -> str:
    token = (
        os.environ.get("VX11_TENTACULO_LINK_TOKEN")
        or os.environ.get("VX11_GATEWAY_TOKEN")
        or os.environ.get("VX11_TOKEN")
        or ""
    )
    headers = {"X-VX11-Token": token} if token else {}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "http://madre:8001/madre/power/state", headers=headers
            )
        if response.status_code == 200:
            payload = response.json()
            return payload.get("policy", "solo_madre")
    except Exception:
        pass
    return "solo_madre"


async def _dependency_unavailable_response() -> JSONResponse:
    policy = await _get_power_policy()
    if policy != "windowed":
        return JSONResponse(
            status_code=403,
            content={
                "status": "OFF_BY_POLICY",
                "service": "manifestator",
                "message": "Disabled by SOLO_MADRE policy",
                "recommended_action": "Ask Madre to open manifestator window",
            },
        )
    return JSONResponse(
        status_code=503,
        content={
            "status": "DEPENDENCY_UNAVAILABLE",
            "dependency": "hormiguero.manifestator",
            "message": "Manifestator dependency not available in this image.",
        },
    )


async def get_controller() -> Union["RailsController", JSONResponse]:
    """Get or initialize RailsController"""
    global controller
    controller_class = _resolve_controller_class()
    if controller_class is None:
        return await _dependency_unavailable_response()
    if controller is None:
        repo_root = os.environ.get("VX11_REPO_ROOT", "/home/elkakas314/vx11")
        controller = controller_class(repo_root)
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

    try:
        ctrl = await get_controller()
        if isinstance(ctrl, JSONResponse):
            return ctrl
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
        ctrl = await get_controller()
        if isinstance(ctrl, JSONResponse):
            return ctrl
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
        ctrl = await get_controller()
        if isinstance(ctrl, JSONResponse):
            return ctrl
        result = ctrl.get_lane_status(lane_id)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "lane_id": lane_id,
            "status": "error",
        }
