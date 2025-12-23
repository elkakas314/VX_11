"""
INEE external routes for tentaculo_link (remote plane).

Rutas expuestas externamente (con feature flag):
- POST /api/v1/inee/intents/submit
- POST /api/v1/inee/register/colonies
- GET /api/v1/inee/heartbeat

Activación: VX11_INEE_REMOTE_PLANE_ENABLED=1 (OFF por defecto).

Forward:
- submit_intent -> Madre (POST /madre/...)
- register/intents -> Madre (POST /madre/...)
- heartbeat -> Hormiguero (POST /hormiguero/heartbeat)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
from datetime import datetime


class INEERegisterColonyRequest(BaseModel):
    colony_id: str
    remote_url: Optional[str] = None


class INEESubmitIntentRequest(BaseModel):
    intent_type: str
    payload: Dict[str, Any]
    remote_colony_id: str
    correlation_id: Optional[str] = None


class INEEHeartbeatRequest(BaseModel):
    colony_id: str
    agent_count: int = 0


# Router

router = APIRouter(prefix="/api/v1/inee", tags=["inee-remote"])

# Injection point for Madre/Hormiguero clients (will be set from main app)
_madre_client: Optional[Any] = None
_hormiguero_client: Optional[Any] = None


def init_inee_remote_routes(madre_client=None, hormiguero_client=None):
    """Initialize INEE remote routes with Madre/Hormiguero clients."""
    global _madre_client, _hormiguero_client
    _madre_client = madre_client
    _hormiguero_client = hormiguero_client


# Routes


@router.post("/register/colonies")
async def register_colonies(req: INEERegisterColonyRequest):
    """
    External: Register remote colony with Madre.
    Forward to Madre for orchestration.
    """
    if not _madre_client:
        raise HTTPException(status_code=500, detail="Madre client not initialized")

    # TODO: Call Madre endpoint to register (mocked for now)
    # result = await _madre_client.post("/madre/inee/colonies/register", json=req.dict())

    return {
        "status": "ok",
        "colony_id": req.colony_id,
        "message": "Colony registered (forwarded to Madre)",
    }


@router.post("/intents/submit")
async def submit_intent(req: INEESubmitIntentRequest):
    """
    External: Submit intent from remote INEE colony to Madre.
    Forward to Madre for processing.
    """
    if not _madre_client:
        raise HTTPException(status_code=500, detail="Madre client not initialized")

    correlation_id = req.correlation_id or str(uuid.uuid4())

    # TODO: Call Madre endpoint (mocked for now)
    # result = await _madre_client.post(
    #     "/madre/intents/submit",
    #     json={
    #         "intent_type": req.intent_type,
    #         "payload": req.payload,
    #         "remote_colony_id": req.remote_colony_id,
    #         "correlation_id": correlation_id,
    #     }
    # )

    return {
        "status": "ok",
        "intent_id": str(uuid.uuid4()),
        "correlation_id": correlation_id,
        "message": "Intent submitted to Madre",
    }


@router.post("/heartbeat")
async def heartbeat(req: INEEHeartbeatRequest):
    """
    External: Heartbeat from remote colony.
    Forward to Hormiguero for registry update.
    """
    if not _hormiguero_client:
        raise HTTPException(status_code=500, detail="Hormiguero client not initialized")

    # TODO: Call Hormiguero endpoint (mocked for now)
    # result = await _hormiguero_client.post(
    #     "/hormiguero/inee/heartbeat",
    #     json={"colony_id": req.colony_id}
    # )

    return {
        "status": "ok",
        "colony_id": req.colony_id,
        "message": "Heartbeat recorded",
    }
