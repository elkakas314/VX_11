from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
import asyncio
import os
import sys

PACKAGE_ROOT = os.path.join(os.path.dirname(__file__), "hormiguero")
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from hormiguero.config import settings
from hormiguero.core.db.sqlite import ensure_schema
from hormiguero.core.db import repo
from hormiguero.core.queen import Queen
from hormiguero.core.actions import executor

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class ActionItem(BaseModel):
    action: str
    target: str


class ActionsRequest(BaseModel):
    actions: List[ActionItem]
    approval_id: Optional[str] = None
    correlation_id: Optional[str] = None


class ScanResponse(BaseModel):
    status: str
    results: Dict[str, Any]


queen = Queen(root_path=ROOT_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    task = asyncio.create_task(queen.run_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="VX11 Hormiguero", lifespan=lifespan)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "hormiguero",
        "version": "v7",
    }


@app.get("/hormiguero/status")
async def hormiguero_status():
    return {
        "actions_enabled": settings.actions_enabled,
        "last_scan": queen.last_scan,
    }


@app.post("/hormiguero/scan/once", response_model=ScanResponse)
async def scan_once():
    result = queen.scan_once(all_checks=True)
    return {"status": "ok", "results": result}


@app.get("/hormiguero/incidents")
async def list_incidents(status: Optional[str] = None, limit: int = 100):
    return repo.list_incidents(status=status, limit=limit)


@app.get("/hormiguero/pheromones")
async def list_pheromones(limit: int = 100):
    return repo.list_pheromones(limit=limit)


@app.post("/hormiguero/actions/preview")
async def preview_actions(req: ActionsRequest):
    preview = executor.preview_actions([item.model_dump() for item in req.actions])
    return {"status": "ok", "preview": preview}


@app.post("/hormiguero/actions/apply")
async def apply_actions(req: ActionsRequest):
    result = executor.apply_actions(
        [item.model_dump() for item in req.actions],
        correlation_id=req.correlation_id or req.approval_id,
    )
    if result.get("status") == "denied":
        raise HTTPException(status_code=403, detail=result)
    return result
