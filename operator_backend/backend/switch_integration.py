"""
Switch Integration Module (v7.0)
Routes chat requests to Switch without modifying Switch itself.
Abstraction layer for Switch communication.
"""

import httpx
import json
from typing import Optional, Dict, Any

from config.settings import settings
from config.tokens import get_token, load_tokens
from config.forensics import write_log

load_tokens()

VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class SwitchClient:
    """Client for Switch integration."""
    
    def __init__(self, switch_url: Optional[str] = None, timeout: float = 30.0):
        """Initialize."""
        self.switch_url = switch_url or settings.switch_url or f"http://switch:{settings.switch_port}"
        self.timeout = timeout
    
    async def query_chat(
        self,
        messages: list,
        task_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Query Switch for chat response."""
        try:
            payload = {
                "messages": messages,
                "task_type": task_type,
                "metadata": metadata or {},
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.switch_url}/switch/chat",
                    json=payload,
                    headers=AUTH_HEADERS,
                )
                resp.raise_for_status()
                result = resp.json()
                write_log("operator_backend", f"switch_chat:ok:{task_type}")
                return result
        
        except httpx.HTTPError as exc:
            write_log("operator_backend", f"switch_chat_error:{exc}", level="ERROR")
            return {"status": "service_offline", "error": str(exc), "response": None}
        except Exception as exc:
            write_log("operator_backend", f"switch_chat_unexpected:{exc}", level="ERROR")
            return {"status": "service_offline", "error": str(exc), "response": None}
    
    async def query_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Query Switch for task execution."""
        try:
            request_body = {
                "task_type": task_type,
                "payload": payload,
                "source": "operator",
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.switch_url}/switch/task",
                    json=request_body,
                    headers=AUTH_HEADERS,
                )
                resp.raise_for_status()
                result = resp.json()
                write_log("operator_backend", f"switch_task:ok:{task_type}")
                return result
        
        except httpx.HTTPError as exc:
            write_log("operator_backend", f"switch_task_error:{exc}", level="ERROR")
            return {"status": "service_offline", "error": str(exc), "result": None}
        except Exception as exc:
            write_log("operator_backend", f"switch_task_unexpected:{exc}", level="ERROR")
            return {"status": "service_offline", "error": str(exc), "result": None}
    
    async def submit_feedback(
        self,
        engine: str,
        success: bool,
        latency_ms: int,
        tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit feedback about engine performance."""
        try:
            payload = {
                "engine": engine,
                "success": success,
                "latency_ms": latency_ms,
                "tokens": tokens,
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.switch_url}/switch/hermes/record_result",
                    json=payload,
                    headers=AUTH_HEADERS,
                )
                resp.raise_for_status()
                result = resp.json()
                write_log("operator_backend", f"switch_feedback:recorded:{engine}")
                return result
        
        except httpx.HTTPError as exc:
            write_log("operator_backend", f"switch_feedback_error:{exc}", level="ERROR")
            return {"status": "service_offline", "error": str(exc)}
        except Exception as exc:
            write_log("operator_backend", f"switch_feedback_unexpected:{exc}", level="ERROR")
            return {"status": "service_offline", "error": str(exc)}
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get Switch queue status."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    f"{self.switch_url}/switch/queue/status",
                    headers=AUTH_HEADERS,
                )
                resp.raise_for_status()
                result = resp.json()
                write_log("operator_backend", "switch_queue_status:ok")
                return result
        
        except httpx.HTTPError as exc:
            write_log("operator_backend", f"switch_queue_status_error:{exc}", level="WARNING")
            return {"status": "service_offline", "error": str(exc), "queue_size": 0}
        except Exception as exc:
            write_log("operator_backend", f"switch_queue_status_unexpected:{exc}", level="ERROR")
            return {"status": "service_offline", "error": str(exc), "queue_size": 0}


async def get_switch_client(switch_url: Optional[str] = None) -> SwitchClient:
    """Factory for SwitchClient (can be mocked in tests)."""
    return SwitchClient(switch_url)
