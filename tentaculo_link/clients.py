"""
Tentáculo Link - Async HTTP clients for VX11 modules
Pattern: single-client per module, lazy initialization, circuit breaker, centralized URL config
"""

import asyncio
import httpx
import time
from enum import Enum
from typing import Dict, Any, Optional, Literal
from config.settings import settings
from config.tokens import get_token
from config.forensics import write_log

# Token resolution (same as main.py pattern)
VX11_TOKEN = (
    get_token("VX11_TENTACULO_LINK_TOKEN")
    or get_token("VX11_GATEWAY_TOKEN")
    or settings.api_token
)
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple circuit breaker for module clients."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED

    def record_success(self) -> None:
        """Record successful request; reset failure count."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record failed request; increment failure count."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def should_attempt_request(self) -> bool:
        """Determine if request should be attempted."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.HALF_OPEN:
            return True
        if self.state == CircuitState.OPEN:
            if (
                self.last_failure_time
                and (time.time() - self.last_failure_time) > self.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time,
        }


class ModuleClient:
    """Base async HTTP client for a single module with circuit breaker."""

    def __init__(self, module_name: str, base_url: str, timeout: float = 15.0):
        self.module_name = module_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60.0
        )

    async def startup(self):
        """Initialize HTTP client."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout, headers=AUTH_HEADERS)

    async def shutdown(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get(
        self,
        path: str,
        timeout: Optional[float] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """GET request with circuit breaker."""
        if not self.circuit_breaker.should_attempt_request():
            write_log("tentaculo_link", f"cb_open:{self.module_name}:{path}")
            return {
                "status": "service_offline",
                "module": self.module_name,
                "reason": "circuit_open",
            }

        try:
            if not self.client:
                await self.startup()
            url = f"{self.base_url}{path}"
            # Merge extra_headers with client default headers
            headers = dict(self.client.headers)
            if extra_headers:
                headers.update(extra_headers)
            resp = await self.client.get(
                url, timeout=timeout or self.timeout, headers=headers
            )
            if resp.status_code < 300:
                self.circuit_breaker.record_success()
                return resp.json()
            else:
                self.circuit_breaker.record_failure()
                return {"status": "error", "code": resp.status_code}
        except Exception as exc:
            self.circuit_breaker.record_failure()
            write_log(
                "tentaculo_link",
                f"client_get_error:{self.module_name}:{exc}",
                level="WARNING",
            )
            return {
                "status": "service_offline",
                "module": self.module_name,
                "error": str(exc),
            }

    async def post(
        self,
        path: str,
        payload: Dict[str, Any],
        timeout: Optional[float] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """POST request with circuit breaker."""
        if not self.circuit_breaker.should_attempt_request():
            write_log("tentaculo_link", f"cb_open:{self.module_name}:{path}")
            return {
                "status": "service_offline",
                "module": self.module_name,
                "reason": "circuit_open",
            }

        try:
            if not self.client:
                await self.startup()
            url = f"{self.base_url}{path}"
            # Merge extra_headers with client default headers
            headers = dict(self.client.headers)
            if extra_headers:
                headers.update(extra_headers)
            resp = await self.client.post(
                url, json=payload, timeout=timeout or self.timeout, headers=headers
            )
            if resp.status_code < 300:
                self.circuit_breaker.record_success()
                return resp.json()
            else:
                self.circuit_breaker.record_failure()
                return {"status": "error", "code": resp.status_code}
        except Exception as exc:
            self.circuit_breaker.record_failure()
            write_log(
                "tentaculo_link",
                f"client_post_error:{self.module_name}:{exc}",
                level="WARNING",
            )
            return {
                "status": "service_offline",
                "module": self.module_name,
                "error": str(exc),
            }


class VX11Clients:
    """Centralized module clients for Tentáculo Link."""

    def __init__(self):
        self.clients: Dict[str, ModuleClient] = {}
        self._init_clients()

    def _init_clients(self):
        """Initialize clients for all modules (lazy startup)."""
        modules = {
            "madre": settings.madre_url or f"http://madre:{settings.madre_port}",
            "switch": settings.switch_url or f"http://switch:{settings.switch_port}",
            "hermes": settings.hermes_url or f"http://hermes:{settings.hermes_port}",
            "hormiguero": settings.hormiguero_url
            or f"http://hormiguero:{settings.hormiguero_port}",
            "spawner": settings.spawner_url
            or f"http://spawner:{settings.spawner_port}",
            "mcp": settings.mcp_url or f"http://mcp:{settings.mcp_port}",
            "shub": settings.shub_url or f"http://shubniggurath:{settings.shub_port}",
            "operator-backend": settings.operator_url
            or f"http://operator-backend:{settings.operator_port}",
        }
        for name, url in modules.items():
            self.clients[name] = ModuleClient(name, url)

    async def startup(self):
        """Initialize all clients on startup."""
        for client in self.clients.values():
            await client.startup()
        write_log("tentaculo_link", "clients_initialized")

    async def shutdown(self):
        """Close all clients on shutdown."""
        for client in self.clients.values():
            await client.shutdown()
        write_log("tentaculo_link", "clients_closed")

    def get_client(self, module_name: str) -> Optional[ModuleClient]:
        """Get a specific module client."""
        return self.clients.get(module_name)

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Parallel health checks for all modules."""
        tasks = {name: client.get("/health") for name, client in self.clients.items()}
        results = {}
        try:
            responses = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for name, response in zip(tasks.keys(), responses):
                if isinstance(response, Exception):
                    results[name] = {"status": "error", "error": str(response)}
                else:
                    results[name] = response
        except Exception as exc:
            write_log("tentaculo_link", f"health_check_all_error:{exc}", level="ERROR")
            results["error"] = str(exc)
        return results

    async def route_to_switch(
        self,
        prompt: str,
        session_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route chat/task to Switch."""
        client = self.get_client("switch")
        if not client:
            return {"error": "switch_client_unavailable"}
        payload = {
            "prompt": prompt,
            "session_id": session_id,
            "metadata": metadata or {},
        }
        write_log("tentaculo_link", "route_switch")
        return await client.post("/switch/route-v5", payload)

    async def route_to_switch_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        provider_hint: Optional[str] = None,
        source: str = "operator",
    ) -> Dict[str, Any]:
        """Route TASK/ANALYSIS to Switch (canonical /switch/task)."""
        client = self.get_client("switch")
        if not client:
            return {"error": "switch_client_unavailable"}
        merged_payload = dict(payload or {})
        if metadata:
            merged_payload.setdefault("metadata", metadata)
        body = {
            "task_type": task_type,
            "payload": merged_payload,
            "source": source,
        }
        if provider_hint:
            body["provider_hint"] = provider_hint
        write_log("tentaculo_link", "route_switch_task")
        return await client.post("/switch/task", body)

    async def route_to_madre_chat(
        self,
        message: str,
        session_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Route chat to Madre (P1 fallback when switch is offline)."""
        client = self.get_client("madre")
        if not client:
            return {"error": "madre_client_unavailable"}
        payload = {
            "message": message,
            "session_id": session_id,
            "context": metadata or {},
        }
        write_log("tentaculo_link", "route_madre_chat")
        return await client.post("/madre/chat", payload)

    async def route_to_operator(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route to Operator backend."""
        client = self.get_client("operator-backend")
        if not client:
            return {"error": "operator_backend_unavailable"}
        write_log("tentaculo_link", f"route_operator:{endpoint}")
        return await client.post(endpoint, payload)

    async def route_to_shub(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route to Shubniggurath."""
        client = self.get_client("shub")
        if not client:
            return {"error": "shub_unavailable"}
        write_log("tentaculo_link", f"route_shub:{endpoint}")
        return await client.post(endpoint, payload)

    async def route_to_madre(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route to Madre."""
        client = self.get_client("madre")
        if not client:
            return {"error": "madre_unavailable"}
        write_log("tentaculo_link", f"route_madre:{endpoint}")
        return await client.post(endpoint, payload)

    async def route_to_spawner(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route to Spawner."""
        client = self.get_client("spawner")
        if not client:
            return {"error": "spawner_unavailable"}
        write_log("tentaculo_link", f"route_spawner:{endpoint}")
        return await client.post(endpoint, payload)

    async def route_to_hormiguero(
        self, endpoint: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Route to Hormiguero."""
        client = self.get_client("hormiguero")
        if not client:
            return {"error": "hormiguero_unavailable"}
        write_log("tentaculo_link", f"route_hormiguero:{endpoint}")
        if payload:
            return await client.post(endpoint, payload)
        else:
            return await client.get(endpoint)


# Global singleton
_clients: Optional[VX11Clients] = None


def get_clients() -> VX11Clients:
    """Get or create global clients instance."""
    global _clients
    if _clients is None:
        _clients = VX11Clients()
    return _clients
