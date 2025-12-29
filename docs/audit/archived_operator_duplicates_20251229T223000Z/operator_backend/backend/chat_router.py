import asyncio
import httpx
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

log = logging.getLogger("vx11.operator.chat")

SWITCH_BASE_URL = "http://switch:8002"
MADRE_BASE_URL = "http://madre:8001"
REQUEST_TIMEOUT = 30.0
FALLBACK_TIMEOUT = 5.0


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    model_used: str
    latency_ms: float
    correlation_id: str
    session_id: str
    provider: str
    status: str = "ok"
    degraded: bool = False


class ChatRouter:

    def __init__(self):
        self.switch_healthy = True
        self.last_switch_check = 0
        self.switch_check_interval = 30

    async def _check_switch_health(self) -> bool:
        """Quick health check for switch service."""
        current_time = time.time()
        if current_time - self.last_switch_check < self.switch_check_interval:
            return self.switch_healthy

        self.last_switch_check = current_time
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{SWITCH_BASE_URL}/health")
                self.switch_healthy = resp.status_code == 200
                return self.switch_healthy
        except Exception as e:
            log.debug(f"Switch health check failed: {e}")
            self.switch_healthy = False
            return False

    async def route_chat(self, req: ChatRequest) -> ChatResponse:
        """
        Route chat request to switch (primary) or madre (fallback).

        Returns ChatResponse with:
        - response: The actual chat response text
        - model_used: Model name (e.g., "deepseek-r1", "general-7b")
        - latency_ms: Total request latency
        - correlation_id: Maintained throughout request chain
        - provider: "switch" or "madre"
        - degraded: True if using fallback
        """
        correlation_id = req.correlation_id or str(uuid.uuid4())
        session_id = req.session_id or str(uuid.uuid4())
        start_time = time.monotonic()

        switch_available = await self._check_switch_health()

        if switch_available:
            try:
                log.info(
                    f"[{correlation_id}] Routing to switch",
                    extra={"correlation_id": correlation_id},
                )
                return await self._call_switch(
                    req, correlation_id, session_id, start_time
                )
            except Exception as e:
                log.warning(
                    f"[{correlation_id}] Switch failed, fallback to madre: {e}",
                    extra={"correlation_id": correlation_id},
                )
                return await self._call_madre(
                    req, correlation_id, session_id, start_time, degraded=True
                )
        else:
            log.info(
                f"[{correlation_id}] Switch unavailable, using madre fallback",
                extra={"correlation_id": correlation_id},
            )
            return await self._call_madre(
                req, correlation_id, session_id, start_time, degraded=True
            )

    async def _call_switch(
        self,
        req: ChatRequest,
        correlation_id: str,
        session_id: str,
        start_time: float,
    ) -> ChatResponse:
        """Call switch service with full timeout."""
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            payload = {
                "messages": [{"role": "user", "content": req.message}],
                "session_id": session_id,
                "correlation_id": correlation_id,
                "metadata": req.metadata or {},
            }

            resp = await client.post(
                f"{SWITCH_BASE_URL}/switch/chat",
                json=payload,
                headers={"x-correlation-id": correlation_id},
            )
            resp.raise_for_status()

            data = resp.json()
            latency_ms = int((time.monotonic() - start_time) * 1000)

            response_text = data.get("reply") or data.get("content") or str(data)
            model_used = data.get("engine_used") or data.get("provider", "switch")

            return ChatResponse(
                response=response_text,
                model_used=model_used,
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                session_id=session_id,
                provider="switch",
                status="ok",
                degraded=False,
            )

    async def _call_madre(
        self,
        req: ChatRequest,
        correlation_id: str,
        session_id: str,
        start_time: float,
        degraded: bool = False,
    ) -> ChatResponse:
        """Call madre service with shorter timeout."""
        async with httpx.AsyncClient(timeout=FALLBACK_TIMEOUT) as client:
            payload = {
                "message": req.message,
                "session_id": session_id,
                "correlation_id": correlation_id,
                "context": req.context or {},
            }

            resp = await client.post(
                f"{MADRE_BASE_URL}/madre/chat",
                json=payload,
                headers={"x-correlation-id": correlation_id},
            )
            resp.raise_for_status()

            data = resp.json()
            latency_ms = int((time.monotonic() - start_time) * 1000)

            response_text = data.get("response") or str(data)
            model_used = data.get("model", "madre-local")
            provider_name = data.get("provider", "madre")

            return ChatResponse(
                response=response_text,
                model_used=model_used,
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                session_id=session_id,
                provider=provider_name,
                status="ok",
                degraded=degraded,
            )


_router = ChatRouter()


def get_chat_router() -> ChatRouter:
    """Get singleton chat router instance."""
    return _router


async def route_chat_request(req: ChatRequest) -> ChatResponse:
    """Convenience function to route a chat request."""
    router = get_chat_router()
    return await router.route_chat(req)
