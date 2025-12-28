"""
INEE Extended Endpoints for Hormiguero.
All dormant (flag-gated), no side effects when flags OFF.
"""

import os
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Dict, Any, List
from datetime import datetime

from hormiguero.inee.models import (
    BuilderCreatePatchsetRequest,
    BuilderPatchset,
    BuilderPromptPack,
    ColonyRegisterRequest,
    ColonyHeartbeat,
    RewardStatusResponse,
    INEEStatusResponse,
    INEEIntentRequest,
    INEEIntentResponse,
)
from hormiguero.inee.builder import (
    BuilderService,
    ColonyLifecycleManager,
    ColonyEnvelopeManager,
    RewardsEngine,
    ManifestatorExtension,
)

# Services (singletons, created on module init)
builder_service = None
colony_manager = None
colony_envelope_mgr = None
rewards_engine = None
manifestator_ext = None


def init_inee_extended_services():
    """Initialize extended INEE services (called by hormiguero/main.py)."""
    global builder_service, colony_manager, colony_envelope_mgr, rewards_engine, manifestator_ext

    builder_service = BuilderService()
    colony_manager = ColonyLifecycleManager()
    colony_envelope_mgr = ColonyEnvelopeManager()
    rewards_engine = RewardsEngine()
    manifestator_ext = ManifestatorExtension()


# Router for extended INEE endpoints
router = APIRouter(prefix="/hormiguero/inee/extended", tags=["inee-extended"])


# ============ BUILDER ENDPOINTS ============


@router.post("/builder/patchset", response_model=Dict[str, Any])
async def create_patchset(
    req: BuilderCreatePatchsetRequest, x_vx11_token: Optional[str] = Header(None)
):
    """
    Create patchset (Builder: generates, does NOT execute).
    Dormant if HORMIGUERO_BUILDER_ENABLED != 1.
    """
    if not builder_service.enabled:
        raise HTTPException(
            status_code=503, detail="Builder not enabled (HORMIGUERO_BUILDER_ENABLED=0)"
        )

    result = await builder_service.create_patchset(
        req.spec_id, req.description or "", req.parameters or {}
    )

    return result


@router.post("/builder/prompt-pack", response_model=Dict[str, Any])
async def create_prompt_pack(
    patchset_id: str, x_vx11_token: Optional[str] = Header(None)
):
    """Generate prompt pack from patchset."""
    if not builder_service.enabled:
        raise HTTPException(status_code=503, detail="Builder not enabled")

    result = await builder_service.create_prompt_pack(patchset_id)
    return result


# ============ COLONY ENDPOINTS ============


@router.post("/colony/register", response_model=Dict[str, Any])
async def register_colony(
    req: ColonyRegisterRequest, x_vx11_token: Optional[str] = Header(None)
):
    """Register remote colony (state: egg)."""
    result = await colony_manager.register_colony(req.colony_id, req.remote_url)
    return result


@router.post("/colony/lifecycle/advance", response_model=Dict[str, Any])
async def advance_lifecycle(
    colony_id: str, new_state: str, x_vx11_token: Optional[str] = Header(None)
):
    """Advance colony state (egg -> larva -> adult)."""
    result = await colony_manager.advance_lifecycle(colony_id, new_state)
    return result


@router.post("/colony/heartbeat", response_model=Dict[str, Any])
async def colony_heartbeat(colony_id: str, x_vx11_token: Optional[str] = Header(None)):
    """Record colony heartbeat."""
    result = await colony_manager.heartbeat(colony_id)
    return result


@router.post("/colony/envelope", response_model=Dict[str, Any])
async def create_envelope(
    colony_id: str, payload: Dict[str, Any], x_vx11_token: Optional[str] = Header(None)
):
    """
    Create HMAC-signed envelope (remote colony communication).
    Only active if VX11_INEE_REMOTE_PLANE_ENABLED=1.
    """
    if not os.getenv("VX11_INEE_REMOTE_PLANE_ENABLED", "0") == "1":
        raise HTTPException(
            status_code=503,
            detail="Remote plane not enabled (VX11_INEE_REMOTE_PLANE_ENABLED=0)",
        )

    envelope = colony_envelope_mgr.create_envelope(colony_id, payload)
    return envelope


# ============ REWARD ENDPOINTS ============


@router.get("/rewards/status", response_model=RewardStatusResponse)
async def rewards_status(x_vx11_token: Optional[str] = Header(None)):
    """Get rewards engine status."""
    if not rewards_engine.enabled:
        return RewardStatusResponse(
            status="disabled", top_accounts=[], total_points_in_circulation=0
        )

    # Stub: would query DB for top accounts
    return RewardStatusResponse(
        status="ok", top_accounts=[], total_points_in_circulation=0
    )


@router.post("/rewards/account/{account_id}", response_model=Dict[str, Any])
async def get_reward_account(
    account_id: str, x_vx11_token: Optional[str] = Header(None)
):
    """Get reward account."""
    if not rewards_engine.enabled:
        return {"status": "disabled"}

    result = await rewards_engine.get_account(account_id)
    return result


@router.post("/rewards/transaction", response_model=Dict[str, Any])
async def record_transaction(
    account_id: str,
    amount: int,
    reason: str,
    x_vx11_token: Optional[str] = Header(None),
):
    """Record reward transaction."""
    if not rewards_engine.enabled:
        return {"status": "disabled"}

    result = await rewards_engine.add_transaction(account_id, amount, reason)
    return result


# ============ MANIFESTATOR EXTENDED ENDPOINTS ============


@router.post("/manifestator/patch-plan", response_model=Dict[str, Any])
async def generate_patch_plan(
    modules: List[str], patch_type: str, x_vx11_token: Optional[str] = Header(None)
):
    """Generate patch plan (code/config/schema)."""
    if not manifestator_ext.enabled:
        return {"status": "disabled"}

    result = await manifestator_ext.generate_patch_plan(modules, patch_type)
    return result


@router.post("/manifestator/prompt-pack", response_model=Dict[str, Any])
async def generate_manifestator_prompts(
    context: Dict[str, Any], x_vx11_token: Optional[str] = Header(None)
):
    """Generate prompt pack."""
    if not manifestator_ext.enabled:
        return {"status": "disabled"}

    result = await manifestator_ext.generate_prompt_pack(context)
    return result


# ============ STATUS ENDPOINT ============


@router.get("/status", response_model=INEEStatusResponse)
async def inee_extended_status(x_vx11_token: Optional[str] = Header(None)):
    """Get INEE extended status."""
    return INEEStatusResponse(
        status="ok",
        enabled=os.getenv("VX11_INEE_ENABLED", "0") == "1",
        remote_plane_enabled=os.getenv("VX11_INEE_REMOTE_PLANE_ENABLED", "0") == "1",
        execution_enabled=os.getenv("VX11_INEE_EXECUTION_ENABLED", "0") == "1",
        colonies_count=0,  # Would query DB
        pending_intents=0,
        builder_available=builder_service is not None and builder_service.enabled,
        rewards_available=rewards_engine is not None and rewards_engine.enabled,
    )
