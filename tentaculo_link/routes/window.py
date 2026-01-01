"""
VX11 Operator Routes: Window Status
tentaculo_link/routes/window.py

Endpoint: GET /api/window/status - Alias for /madre/power/state
"""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
import os
import httpx
import asyncio

router = APIRouter(prefix="/api", tags=["window"])


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


async def get_madre_window_status() -> dict:
    """
    Llamar a madre:8001 para obtener estado de ventana temporal.
    Fallback a default si madre no responde.
    """
    try:
        token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
        headers = {"X-VX11-Token": token} if token else {}
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                "http://madre:8001/madre/power/state", headers=headers
            )
            if response.status_code == 200:
                payload = response.json()
                policy = payload.get("policy", "solo_madre")
                return {
                    "mode": "window_active" if policy == "windowed" else "solo_madre",
                    "ttl_seconds": payload.get("ttl_remaining_sec"),
                    "window_id": payload.get("window_id"),
                    "services": payload.get("active_services", ["madre", "redis"]),
                    "degraded": False,
                    "reason": None,
                }
    except Exception:
        pass

    # Fallback: assume solo_madre mode
    return {
        "mode": "solo_madre",
        "ttl_seconds": None,
        "window_id": None,
        "services": ["madre", "redis"],
    }


@router.get("/window/status")
async def get_window_status(auth: bool = Depends(check_auth)):
    """
    GET /api/window/status - Get current window/power state

    Aliases to madre:8001/power/state if available.
    Falls back to solo_madre if madre is unavailable.

    Response:
    {
      "mode": "solo_madre|window_active",
      "ttl_seconds": null | number,    // Remaining TTL if window open
      "window_id": null | string,      // ID of active window
      "services": ["madre", "redis", ...],  // Services currently running
      "degraded": boolean,  // true if window detection incomplete
      "reason": string|null // Why degraded
    }
    """

    status = await get_madre_window_status()

    # Normalize response
    return {
        "mode": status.get("mode", "solo_madre"),
        "ttl_seconds": status.get("ttl_seconds"),
        "window_id": status.get("window_id"),
        "services": status.get("services", ["madre", "redis"]),
        "degraded": status.get("degraded", False),
        "reason": status.get("reason"),
    }


@router.post("/window/open")
async def open_window(request: dict, auth: bool = Depends(check_auth)):
    """
    POST /api/window/open - Open a power window via Madre.
    """
    token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    headers = {"X-VX11-Token": token}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "http://madre:8001/madre/power/window/open",
            json=request,
            headers=headers,
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/window/close")
async def close_window(auth: bool = Depends(check_auth)):
    """
    POST /api/window/close - Close active window via Madre.
    """
    token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    headers = {"X-VX11-Token": token}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "http://madre:8001/madre/power/window/close",
            json={},
            headers=headers,
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
