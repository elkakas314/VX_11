"""
VX11 Operator Routes: Events
tentaculo_link/routes/events.py

Endpoint: GET /api/events - Server-Sent Events stream o polling
"""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
import os

from tentaculo_link.db.events_metrics import get_events, log_event

router = APIRouter(prefix="/api", tags=["events"])


def check_auth(
    request: Request,
    x_vx11_token: Optional[str] = Header(None),
    token: Optional[str] = Query(None),
) -> bool:
    """Simple auth check - supports both header and query param tokens"""
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")

    # Try header first, then query param (for SSE/EventSource API)
    provided_token = x_vx11_token or token

    if not provided_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if provided_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


@router.get("/events")
async def get_events_endpoint(
    limit: int = 100,
    offset: int = 0,
    correlation_id: Optional[str] = None,
    severity: Optional[str] = None,
    module: Optional[str] = None,
    hours_back: int = 24,
    auth: bool = Depends(check_auth),
):
    """
    GET /api/events - Obtain event stream (polling)

    Query Parameters:
    - limit: Max events (default 100)
    - offset: Pagination offset (default 0)
    - correlation_id: Filter by correlation_id
    - severity: Filter by severity (info|warn|crit)
    - module: Filter by module name
    - hours_back: Include events from last N hours (default 24)

    Response:
    {
      "events": [
        {
          "id": "evt_...",
          "ts": "2025-12-29T...",
          "type": "status|module|window|intent|audit",
          "severity": "info|warn|crit",
          "module": "string",
          "correlation_id": "string|null",
          "summary": "Human readable summary",
          "payload": {...}
        }
      ],
      "total": 1234,
      "has_more": true
    }

    Errors:
    - 401: Missing or invalid token
    - 503: Feature disabled (VX11_EVENTS_ENABLED=false)
    """

    # Check feature flag
    if not os.environ.get("VX11_EVENTS_ENABLED", "false").lower() in ("true", "1"):
        return {
            "error": "feature_disabled",
            "flag": "VX11_EVENTS_ENABLED",
            "status_code": 503,
            "events": [],
            "total": 0,
            "has_more": False,
        }

    result = get_events(
        limit=min(limit, 1000),  # Cap at 1000
        offset=offset,
        correlation_id=correlation_id,
        severity=severity,
        module=module,
        hours_back=hours_back,
    )

    return result
