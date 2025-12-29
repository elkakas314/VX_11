"""
VX11 Operator Routes: Settings
tentaculo_link/routes/settings.py

Endpoints: GET /api/settings, POST /api/settings
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Header, HTTPException
import os
import json
import sqlite3
from pathlib import Path

router = APIRouter(prefix="/api", tags=["settings"])


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


def check_admin(x_vx11_token: Optional[str] = Header(None)) -> bool:
    """Admin check (stricter than regular auth)"""
    if not check_auth(x_vx11_token):
        return False
    # Optional: check role from token (implement if needed)
    return True


def get_db() -> sqlite3.Connection:
    repo_root = Path(os.environ.get("VX11_REPO_ROOT", "/home/elkakas314/vx11"))
    db_path = repo_root / "data" / "runtime" / "vx11.db"
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/settings")
async def get_settings(auth: bool = Depends(check_auth)):
    """
    GET /api/settings - Get all operator settings

    Response:
    {
      "settings": {
        "key1": "value1",
        "key2": {...},
        ...
      }
    }
    """

    if not os.environ.get("VX11_SETTINGS_ENABLED", "false").lower() in ("true", "1"):
        return {
            "error": "feature_disabled",
            "flag": "VX11_SETTINGS_ENABLED",
            "settings": {},
        }

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value_json FROM operator_settings")
        rows = cursor.fetchall()
        conn.close()

        settings = {}
        for row in rows:
            try:
                settings[row["key"]] = json.loads(row["value_json"])
            except:
                settings[row["key"]] = row["value_json"]

        return {"settings": settings}
    except Exception as e:
        return {
            "error": str(e),
            "settings": {},
        }


@router.post("/settings")
async def update_settings(
    data: Dict[str, Any],
    auth: bool = Depends(check_admin),
):
    """
    POST /api/settings - Update operator settings

    Request:
    {
      "setting_key": setting_value,
      ...
    }

    Response:
    {
      "ok": true,
      "updated_keys": ["key1", "key2"]
    }
    """

    if not os.environ.get("VX11_SETTINGS_ENABLED", "false").lower() in ("true", "1"):
        raise HTTPException(status_code=503, detail="feature_disabled")

    try:
        conn = get_db()
        cursor = conn.cursor()

        updated_keys = []
        for key, value in data.items():
            # Validate key (prevent injection)
            if not key.replace("_", "").isalnum():
                return {"ok": False, "error": f"Invalid setting key: {key}"}

            value_json = json.dumps(value) if not isinstance(value, str) else value

            cursor.execute(
                """
                INSERT OR REPLACE INTO operator_settings (key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (key, value_json),
            )
            updated_keys.append(key)

        conn.commit()
        conn.close()

        return {
            "ok": True,
            "updated_keys": updated_keys,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
        }
