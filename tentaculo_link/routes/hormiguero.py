"""VX11 Operator Routes: Hormiguero"""

from typing import Optional, Dict, Any
import os
from fastapi import APIRouter, Depends, Header, HTTPException

from tentaculo_link.clients import get_clients
from tentaculo_link.routes.window import get_madre_window_status

router = APIRouter(prefix="/api/hormiguero", tags=["hormiguero"])


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


@router.post("/scan/once")
async def scan_once(auth: bool = Depends(check_auth)) -> Dict[str, Any]:
    window = await get_madre_window_status()
    if window.get("mode") != "window_active" or "hormiguero" not in window.get(
        "services", []
    ):
        return {
            "status": "off_by_policy",
            "policy": window.get("mode", "solo_madre"),
            "message": "Hormiguero disabled by solo_madre policy",
            "window": window,
        }
    clients = get_clients()
    result = await clients.route_to_hormiguero("/hormiguero/scan/once")
    return result


@router.get("/status")
async def hormiguero_status(auth: bool = Depends(check_auth)) -> Dict[str, Any]:
    window = await get_madre_window_status()
    if window.get("mode") != "window_active" or "hormiguero" not in window.get(
        "services", []
    ):
        return {
            "status": "off_by_policy",
            "policy": window.get("mode", "solo_madre"),
            "message": "Hormiguero disabled by solo_madre policy",
            "window": window,
        }
    clients = get_clients()
    result = await clients.route_to_hormiguero("/hormiguero/queen/status")
    return result


@router.get("/incidents")
async def hormiguero_incidents(
    limit: int = 10,
    auth: bool = Depends(check_auth),
) -> Dict[str, Any]:
    window = await get_madre_window_status()
    if window.get("mode") != "window_active" or "hormiguero" not in window.get(
        "services", []
    ):
        return {
            "status": "off_by_policy",
            "policy": window.get("mode", "solo_madre"),
            "message": "Hormiguero disabled by solo_madre policy",
            "window": window,
            "incidents": [],
            "total": 0,
        }
    clients = get_clients()
    result = await clients.route_to_hormiguero(
        "/hormiguero/incidents", params={"limit": limit}
    )
    return result
