"""
Madre FLUZO Integration (Phase 4)
Safe, non-decisional integration that consults Switch FLUZO endpoint
for resource-limiting hints when enabled.
"""

import logging
import httpx
from typing import Dict, Optional, Any
from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log

log = logging.getLogger("vx11.madre.fluzo")


async def get_fluzo_hints() -> Dict[str, Any]:
    """
    Safely fetch FLUZO hints from Switch (non-blocking, defensive).

    Returns:
        {
            "status": "ok" | "error",
            "profile": "balanced" | "low_power" | "performance",
            "signals": {...},
            "error": "reason if status=error"
        }
    """
    if not settings.enable_madre_fluzo:
        return {"status": "disabled", "reason": "VX11_ENABLE_MADRE_FLUZO=False"}

    try:
        VX11_TOKEN = get_token("VX11_TENTACULO_LINK_TOKEN") or settings.api_token
        AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.switch_url.rstrip('/')}/switch/fluzo",
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                result = resp.json()
                write_log(
                    "madre", f"fluzo_hints_received:{result.get('profile', 'unknown')}"
                )
                # Ensure 'status' key is present
                if "status" not in result:
                    result["status"] = "ok"
                return result
            else:
                write_log("madre", f"fluzo_hints_error:status={resp.status_code}")
                return {
                    "status": "error",
                    "reason": f"switch_status_{resp.status_code}",
                }
    except Exception as e:
        write_log("madre", f"fluzo_hints_exception:{e}", level="WARNING")
        return {"status": "error", "reason": str(e)}


async def apply_fluzo_resource_limits(hints: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply resource-limiting hints from FLUZO to Madre's task planning.

    This is a *non-decisional* application: FLUZO only suggests resource
    constraints and CPU/memory strategies, not which task to execute.

    Returns:
        {
            "profile": current profile (e.g., "balanced"),
            "cpu_limit": float (0.0-1.0),
            "max_concurrent_hijas": int,
            "task_timeout_ms": int,
            "reason": str
        }
    """
    profile = hints.get("profile", "balanced")

    resource_config = {
        "low_power": {
            "cpu_limit": 0.2,
            "max_concurrent_hijas": 2,
            "task_timeout_ms": 3000,
        },
        "balanced": {
            "cpu_limit": 0.5,
            "max_concurrent_hijas": 5,
            "task_timeout_ms": 5000,
        },
        "performance": {
            "cpu_limit": 0.9,
            "max_concurrent_hijas": 10,
            "task_timeout_ms": 2000,
        },
    }

    config = resource_config.get(profile, resource_config["balanced"])
    config["profile"] = profile
    config["reason"] = f"Applied from FLUZO profile: {profile}"

    write_log("madre", f"fluzo_resource_limits_applied:{profile}")
    return config


async def get_madre_fluzo_context() -> Dict[str, Any]:
    """
    Convenience: fetch FLUZO hints and apply resource limits in one call.

    Returns:
        {
            "status": "ok" | "disabled" | "error",
            "fluzo_hints": {...},
            "resource_config": {...} if status="ok" else None
        }
    """
    hints = await get_fluzo_hints()

    if hints.get("status") in ("disabled", "error"):
        return {
            "status": hints.get("status", "unknown"),
            "fluzo_hints": hints,
            "resource_config": None,
        }

    config = await apply_fluzo_resource_limits(hints)
    return {
        "status": "ok",
        "fluzo_hints": hints,
        "resource_config": config,
    }
