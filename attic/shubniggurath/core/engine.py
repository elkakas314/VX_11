"""
Shub-Niggurath core engine.
Lightweight orchestrator that wires DSP, ops, and VX11 services (switch/hermes/spawner).
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

try:
    from config.settings import settings
    from config.tokens import get_token
except Exception:  # pragma: no cover - fallback for isolated runs
    class _FallbackSettings:  # type: ignore
        PORTS = {}
        api_token = "vx11-local-token"
        token_header = "X-VX11-Token"
        switch_url = "http://switch:8002"
        hermes_url = "http://hermes:8003"
        spawner_url = "http://spawner:8008"
    settings = _FallbackSettings()  # type: ignore
    def get_token(key: str) -> Optional[str]:  # type: ignore
        return None

from shubniggurath.pipelines.audio_analyzer import AudioAnalyzerPipeline
from shubniggurath.pipelines.mix_pipeline import MixPipeline
from shubniggurath.pipelines.reaper_pipeline import ReaperPipeline

log = logging.getLogger("vx11.shub.core")


class ShubEngine:
    """Main orchestrator for Shub-Niggurath."""

    def __init__(
        self,
        analyzer_pipeline: AudioAnalyzerPipeline,
        mix_pipeline: MixPipeline,
        reaper_pipeline: ReaperPipeline,
    ):
        self.analyzer_pipeline = analyzer_pipeline
        self.mix_pipeline = mix_pipeline
        self.reaper_pipeline = reaper_pipeline
        self._http_client: Optional[httpx.AsyncClient] = None
        self._token = (
            get_token("VX11_GATEWAY_TOKEN")
            or get_token("VX11_TENTACULO_LINK_TOKEN")
            or getattr(settings, "api_token", None)
            or "vx11-local-token"
        )
        self._token_header = getattr(settings, "token_header", "X-VX11-Token")
        self._ports = getattr(settings, "PORTS", {}) or {}
        self._ensure_workspace()

    def _ensure_workspace(self) -> None:
        base = os.path.join(os.path.dirname(__file__), "..", "workspace")
        for folder in ("tmp", "cache"):
            os.makedirs(os.path.abspath(os.path.join(base, folder)), exist_ok=True)

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=6.0)
        return self._http_client

    async def health(self) -> Dict[str, Any]:
        """Return lightweight health state."""
        return {
            "status": "ok",
            "module": "shub",
            "pipelines": {
                "analyzer": self.analyzer_pipeline.name,
                "mix": self.mix_pipeline.name,
                "reaper": self.reaper_pipeline.name,
            },
            "switch_url": getattr(settings, "switch_url", None),
            "ports": self._ports,
        }

    async def analyze(self, audio_frames: List[float], sample_rate: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Run the audio analyzer pipeline and optionally enrich with Switch hints."""
        base_result = await self.analyzer_pipeline.run(audio_frames, sample_rate, metadata or {})
        switch_hint = await self._send_switch_hint(base_result.get("summary", {}), metadata or {})
        if switch_hint:
            base_result["switch_hint"] = switch_hint
        return base_result

    async def mix(self, stems: Dict[str, List[float]], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mix pipeline (stems merge + suggested gain staging)."""
        return await self.mix_pipeline.run(stems, metadata or {})

    async def event_ready(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle readiness notifications (non-blocking)."""
        tasks = [
            self._notify_hermes(payload),
            self._notify_spawner(payload),
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        return {"status": "ready", "received": payload}

    async def _post_json(self, url: str, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        headers = {self._token_header: self._token}
        try:
            resp = await self.http_client.post(url, json=body, headers=headers)
            if resp.status_code == 200:
                return resp.json()
        except Exception as exc:  # pragma: no cover - network failure tolerated
            log.debug("ShubEngine POST failed to %s: %s", url, exc)
        return None

    async def _send_switch_hint(self, summary: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        switch_url = getattr(settings, "switch_url", None) or f"http://127.0.0.1:{self._ports.get('switch', 8002)}"
        payload = {"prompt": summary.get("headline", ""), "metadata": {"task_type": "audio", **metadata}}
        return await self._post_json(f"{switch_url}/switch/route-v5", payload)

    async def _notify_hermes(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        hermes_url = getattr(settings, "hermes_url", None) or f"http://127.0.0.1:{self._ports.get('hermes', 8003)}"
        return await self._post_json(f"{hermes_url}/hermes/event-ready", {"module": "shub", **payload})

    async def _notify_spawner(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        spawner_url = getattr(settings, "spawner_url", None) or f"http://127.0.0.1:{self._ports.get('spawner', 8008)}"
        return await self._post_json(f"{spawner_url}/spawner/event-ready", {"module": "shub", **payload})

    async def close(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
