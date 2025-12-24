"""
Shub Canonical Routes — VX11 v1.7.1

Endpoints explícitos según CANONICAL_SHUB_VX11.json.

Estos endpoints son públicos (sin window guard):
- GET /health
- GET /ready
- GET /engines
- GET /metrics
- GET /pipelines
- GET /reaper/search
- GET /jobs/{job_id}
- GET /jobs/{job_id}/events (SSE)
- GET /jobs/{job_id}/artifacts
- GET /api/jobs (legacy alias)
- GET /api/analyze (legacy alias)

Estos endpoints REQUIEREN window guard (mutators):
- POST /jobs (window guard)
- POST /pipelines/run (window guard)
- POST /jobs/{job_id}/actions (window guard)
- POST /reaper/index/rebuild (window guard)
- POST /api/process (legacy, window guard)
- POST /api/reaper/{subpath} (legacy, window guard)

NO hay catch-all routes. Rutas no explícitas devuelven 404.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, Field

from shubniggurath.security.windowguard import require_window_token

router = APIRouter(
    prefix="/shub",
    tags=["shub-canonical"],
)

# =============================================================================
# MODELS
# =============================================================================


class JobRequest(BaseModel):
    """Job submission request"""

    pipeline_id: str = Field(..., description="Pipeline identifier")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Pipeline parameters"
    )
    idempotency_key: Optional[str] = Field(
        None, description="Idempotency key (for deduplication)"
    )


class JobResponse(BaseModel):
    """Job response"""

    job_id: str
    status: str  # queued|running|completed|failed|canceled
    pipeline_id: str
    created_at: str


class JobEvent(BaseModel):
    """Job event (for SSE)"""

    event_type: str  # job_started|job_progress|job_completed|job_failed
    job_id: str
    data: Dict[str, Any]
    timestamp: str


class PipelineResponse(BaseModel):
    """Pipeline response"""

    pipeline_id: str
    name: str
    description: str
    params_schema: Dict[str, Any]


class EngineResponse(BaseModel):
    """Engine response"""

    engine_id: str
    status: str  # operational|degraded|offline
    capabilities: List[str]


# =============================================================================
# PUBLIC ENDPOINTS (no window guard required)
# =============================================================================


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint (always available)"""
    return {
        "status": "ok",
        "module": "shubniggurath",
        "version": "1.7.1-canon",
    }


@router.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check (operational status)"""
    return {
        "ready": True,
        "disabled_by_policy": False,  # Unless VX11_RUNTIME_DEFAULT=solo_madre
        "details": {
            "dsp_engine": "ok",
            "job_system": "ok",
            "reaper_bridge": "ok",
        },
    }


@router.get("/pipelines", tags=["Pipelines"])
async def list_pipelines() -> List[PipelineResponse]:
    """List available pipelines"""
    return [
        {
            "pipeline_id": "plugin_inventory_scan",
            "name": "Plugin Inventory Scan",
            "description": "Scan system plugins and update catalog",
            "params_schema": {"force_rescan": {"type": "boolean", "default": False}},
        },
        {
            "pipeline_id": "parse_colloquial_intent",
            "name": "Colloquial Intent Parser",
            "description": "Parse Spanish colloquial request into technical intent",
            "params_schema": {},
        },
    ]


@router.get("/engines", tags=["Engines"])
async def list_engines() -> List[EngineResponse]:
    """List available engines"""
    return [
        {
            "engine_id": "plugin_inventory_engine",
            "status": "operational",
            "capabilities": ["scan", "index", "persist"],
        },
        {
            "engine_id": "colloquial_nlu_intent_engine",
            "status": "operational",
            "capabilities": ["parse", "normalize", "extract_intent"],
        },
        {
            "engine_id": "reaper_project_mapper_engine",
            "status": "operational",
            "capabilities": ["map_projects", "extract_structure"],
        },
        {
            "engine_id": "track_freeze_manager_engine",
            "status": "degraded",
            "capabilities": ["freeze", "unfreeze"],
        },
    ]


@router.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Prometheus metrics endpoint"""
    # TODO: Implement metrics collection
    return {
        "shub_jobs_total": 0,
        "shub_jobs_completed": 0,
        "shub_jobs_failed": 0,
        "shub_job_latency_ms": 0,
    }


@router.get("/jobs/{job_id}", tags=["Jobs"])
async def get_job_status(job_id: str):
    """Get job status"""
    return {
        "job_id": job_id,
        "status": "completed",
        "pipeline_id": "plugin_inventory_scan",
        "created_at": "2025-12-25T00:00:00Z",
        "completed_at": "2025-12-25T00:05:00Z",
    }


@router.get("/jobs/{job_id}/events", tags=["Jobs"])
async def get_job_events(job_id: str):
    """
    Stream job events (SSE - Server-Sent Events).

    Content-Type: text/event-stream
    """
    return {
        "events": [
            {
                "event": "job_started",
                "data": {"job_id": job_id},
                "timestamp": "2025-12-25T00:00:00Z",
            }
        ]
    }


@router.get("/jobs/{job_id}/artifacts", tags=["Jobs"])
async def get_job_artifacts(job_id: str):
    """Get job artifacts"""
    return {
        "job_id": job_id,
        "artifacts": [
            {"name": "report.json", "url": "/shub/artifacts/uuid1", "size_bytes": 1024},
        ],
    }


@router.get("/reaper/search", tags=["REAPER"])
async def reaper_search(q: str = "", type: str = "plugin", limit: int = 10):
    """Search REAPER resources"""
    return {
        "query": q,
        "type": type,
        "results": [],
    }


# =============================================================================
# MUTATOR ENDPOINTS (require window guard)
# =============================================================================


@router.post("/jobs", tags=["Jobs"])
async def submit_job(
    request: JobRequest,
    window: dict = Depends(require_window_token),
) -> JobResponse:
    """
    Submit a new job (mutator).

    Requires:
    - Authorization: Bearer <window_token>
    - Scope: shub:jobs:submit
    """
    return {
        "job_id": "job-123",
        "status": "queued",
        "pipeline_id": request.pipeline_id,
        "created_at": "2025-12-25T00:00:00Z",
    }


@router.post("/pipelines/run", tags=["Pipelines"])
async def run_pipeline(
    request: Dict[str, Any],
    window: dict = Depends(require_window_token),
):
    """
    Run a pipeline (mutator).

    Requires:
    - Authorization: Bearer <window_token>
    - Scope: shub:mutate
    """
    return {
        "status": "ok",
        "job_id": "job-456",
        "message": "Pipeline queued for execution",
    }


@router.post("/jobs/{job_id}/actions", tags=["Jobs"])
async def job_action(
    job_id: str,
    action: str,
    window: dict = Depends(require_window_token),
):
    """
    Perform action on job (cancel, pause, resume).

    Requires:
    - Authorization: Bearer <window_token>
    - Scope: shub:jobs:mutate
    """
    return {
        "job_id": job_id,
        "action": action,
        "result": "ok",
    }


@router.post("/reaper/index/rebuild", tags=["REAPER"])
async def rebuild_reaper_index(
    window: dict = Depends(require_window_token),
):
    """
    Rebuild REAPER resource index (mutator).

    Requires:
    - Authorization: Bearer <window_token>
    - Scope: shub:reaper:index:rebuild
    """
    return {
        "status": "rebuilding",
        "job_id": "reaper-index-1",
    }


# =============================================================================
# LEGACY ALIASES (deprecated, but compatible)
# =============================================================================


@router.get("/api/jobs", tags=["Legacy"])
async def api_legacy_jobs():
    """
    Legacy /api/jobs endpoint.

    Deprecated: Use /jobs instead.
    """
    return {
        "_deprecated": "true",
        "_new_endpoint": "/jobs",
        "jobs": [],
    }


@router.post("/api/analyze", tags=["Legacy"])
async def api_legacy_analyze(request: Dict[str, Any]):
    """
    Legacy /api/analyze endpoint.

    Deprecated: Use /pipelines/run instead.
    """
    return {
        "_deprecated": "true",
        "_new_endpoint": "/pipelines/run",
        "status": "ok",
    }


@router.post("/api/process", tags=["Legacy"])
async def api_legacy_process(
    request: Dict[str, Any],
    window: dict = Depends(require_window_token),
):
    """
    Legacy /api/process endpoint (mutator).

    Deprecated: Use /jobs instead.
    """
    return {
        "_deprecated": "true",
        "_new_endpoint": "/jobs",
        "job_id": "legacy-job-1",
    }


@router.get("/api/reaper/{subpath:path}", tags=["Legacy"])
async def api_legacy_reaper_get(subpath: str):
    """Legacy REAPER GET endpoint"""
    return {"_deprecated": "true", "subpath": subpath}


@router.post("/api/reaper/{subpath:path}", tags=["Legacy"])
async def api_legacy_reaper_post(
    subpath: str,
    request: Dict[str, Any],
    window: dict = Depends(require_window_token),
):
    """Legacy REAPER POST endpoint (mutator)"""
    return {"_deprecated": "true", "subpath": subpath, "status": "ok"}
