"""
Top-level router wiring for Shub-Niggurath.
"""

from fastapi import APIRouter, Depends, HTTPException

from shubniggurath.core.registry import get_engine
from shubniggurath.routes.schemas import AnalyzeRequest, MixRequest, EventReadyRequest


def create_router() -> APIRouter:
    router = APIRouter(prefix="/shub", tags=["shub"])

    @router.get("/health")
    async def health():
        engine = get_engine()
        return await engine.health()

    @router.post("/analyze")
    async def analyze(req: AnalyzeRequest, engine=Depends(get_engine)):
        if not req.audio:
            raise HTTPException(status_code=400, detail="audio_required")
        return await engine.analyze(req.audio, req.sample_rate, req.metadata or {})

    @router.post("/mix")
    async def mix(req: MixRequest, engine=Depends(get_engine)):
        if not req.stems:
            raise HTTPException(status_code=400, detail="stems_required")
        return await engine.mix(req.stems, req.metadata or {})

    @router.post("/event-ready")
    async def event_ready(req: EventReadyRequest, engine=Depends(get_engine)):
        return await engine.event_ready(req.payload or {})

    return router
