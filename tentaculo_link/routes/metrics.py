"""
VX11 Operator Routes: Metrics
tentaculo_link/routes/metrics.py

Endpoint: GET /api/metrics
"""

from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
import os
import json
import sqlite3
from pathlib import Path

from tentaculo_link.db.events_metrics import get_metrics

router = APIRouter(prefix="/api", tags=["metrics"])


def check_auth(x_vx11_token: Optional[str] = Header(None)) -> bool:
    if not os.environ.get("ENABLE_AUTH", "true").lower() in ("true", "1"):
        return True
    required_token = os.environ.get("VX11_TENTACULO_LINK_TOKEN", "")
    if not x_vx11_token:
        raise HTTPException(status_code=401, detail="auth_required")
    if x_vx11_token != required_token:
        raise HTTPException(status_code=403, detail="forbidden")
    return True


@router.get("/metrics")
async def get_metrics_endpoint(
    name: Optional[str] = None,
    window_seconds: int = 3600,
    module: Optional[str] = None,
    limit: int = 1000,
    auth: bool = Depends(check_auth),
):
    """
    GET /api/metrics - Get metrics timeseries

    Query Parameters:
    - name: Filter by metric name (cpu_percent, ram_gib, latency_ms, etc.)
    - window_seconds: Include metrics from last N seconds (default 3600)
    - module: Filter by module
    - limit: Max results (default 1000)

    Response:
    {
      "metrics": [
        {
          "metric_id": "met_...",
          "ts": "2025-12-29T...",
          "metric_name": "cpu_percent|ram_gib|latency_ms|chat_throughput|window_ttl|event_backlog",
          "value": 42.5,
          "module": "string",
          "dimensions": {...}
        }
      ],
      "count": 123
    }
    """

    if not os.environ.get("VX11_METRICS_ENABLED", "false").lower() in ("true", "1"):
        return {
            "error": "feature_disabled",
            "flag": "VX11_METRICS_ENABLED",
            "metrics": [],
            "count": 0,
        }

    result = get_metrics(
        metric_name=name,
        window_seconds=window_seconds,
        module=module,
        limit=min(limit, 10000),  # Cap at 10k
    )

    return result
