"""API v1 Gateway router (lightweight stubs).

This module provides a small APIRouter that delegates to the existing
`main_v7` implementations. It's a low-power surface for future migration.
"""

from fastapi import APIRouter
from tentaculo_link import main_v7

router = APIRouter()


@router.get("/v1/status")
async def v1_status():
    """Return the same aggregated status as the v7 app."""
    return await main_v7.vx11_status()


@router.get("/v1/health")
async def v1_health():
    return await main_v7.health()
