"""VX11 Operator Routes: Switch status and provider context."""

from typing import Optional, Dict, Any
import os
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from tentaculo_link.clients import get_clients

router = APIRouter(prefix="/api/switch", tags=["switch"])


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


@router.get("/provider")
async def switch_provider(auth: bool = Depends(check_auth)) -> Dict[str, Any]:
    clients = get_clients()
    switch_client = clients.get_client("switch")
    if not switch_client:
        return JSONResponse(
            status_code=503,
            content={
                "status": "DEPENDENCY_UNAVAILABLE",
                "service": "switch",
                "message": "Switch unavailable (profile not active)",
            },
        )

    context = await switch_client.get("/switch/context", timeout=4.0)
    providers = await switch_client.get("/switch/providers", timeout=4.0)

    if context.get("status") == "service_offline" or context.get("error"):
        return JSONResponse(
            status_code=503,
            content={
                "status": "DEPENDENCY_UNAVAILABLE",
                "service": "switch",
                "message": "Switch unavailable (profile not active)",
            },
        )

    selected_provider = context.get("active_model") or context.get("mode")

    return {
        "status": "ok",
        "selected_provider": selected_provider,
        "explainability": {
            "source": "/switch/context",
            "note": "active_model from Switch context",
        },
        "context": context,
        "providers": providers.get("providers", []),
    }
