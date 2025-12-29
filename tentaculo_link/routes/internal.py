"""Internal operator support routes for Tentáculo Link."""

from typing import Optional, Dict, Any
import os
from fastapi import APIRouter, Depends, Header, HTTPException

from tentaculo_link.clients import get_clients

router = APIRouter(prefix="/api/internal", tags=["internal"])


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


@router.get("/core-health")
async def core_health(auth: bool = Depends(check_auth)) -> Dict[str, Any]:
    clients = get_clients()
    results = await clients.health_check_all()
    services: Dict[str, Any] = {}

    for name, info in results.items():
        services[name] = {
            "status": "healthy" if info.get("status") == "healthy" else "unhealthy",
            "reason": info.get("reason"),
            "latency_ms": info.get("latency_ms"),
        }

    return {"status": "ok", "services": services}
