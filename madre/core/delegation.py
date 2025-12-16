"""Delegation: HTTP calls to other modules + daughter_tasks insertions."""

import logging
import httpx
from typing import Dict, Any
from .db import MadreDB
from config.settings import settings

log = logging.getLogger("madre.delegation")


class DelegationClient:
    """Handles HTTP calls and daughter_task insertions."""

    def __init__(self, timeout_sec: float = 5.0):
        self.timeout_sec = timeout_sec
        self.headers = {"X-VX11-Token": settings.api_token}

    async def check_dependencies(self) -> Dict[str, str]:
        """Check if critical dependencies are UP."""
        deps = {}

        for module, port in [
            ("switch", settings.switch_port),
            ("hormiguero", settings.hormiguero_port),
            ("spawner", settings.spawner_port),
        ]:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"http://127.0.0.1:{port}/health")
                    deps[module] = "up" if resp.status_code == 200 else "down"
            except:
                deps[module] = "down"

        return deps

    async def request_spawner_hija(
        self,
        intent_id: str,
        plan_id: str,
        step_id: str,
        task_description: str,
        params: Dict[str, Any],
    ) -> int:
        """Request a spawner hija. Returns daughter_task ID."""
        metadata = {
            "plan_id": plan_id,
            "step_id": step_id,
            "intent_id": intent_id,
        }
        plan_json = {
            "plan_id": plan_id,
            "step": {"id": step_id, "params": params},
        }

        daughter_task_id = MadreDB.request_spawner_task(
            intent_id=intent_id,
            task_type="command",
            description=task_description,
            metadata=metadata,
            plan_json=plan_json,
            priority=3,
        )

        log.info(f"Requested spawner hija: daughter_task_id={daughter_task_id}")
        return daughter_task_id

    async def call_module(
        self,
        module: str,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generic HTTP call to any module."""
        url_map = {
            "switch": settings.switch_url,
            "hormiguero": settings.hormiguero_url,
            "hermes": settings.hermes_url,
            "shub": settings.shub_url,
            "manifestator": settings.manifestator_url,
        }

        base_url = url_map.get(module)
        if not base_url:
            raise ValueError(f"Unknown module: {module}")

        url = f"{base_url}{endpoint}"
        log.info(f"Calling {module}: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(url, json=payload, headers=self.headers)
                resp.raise_for_status()
                return resp.json()
        except httpx.TimeoutException:
            log.warning(f"{module} timeout")
            raise
        except Exception as e:
            log.error(f"{module} call failed: {e}")
            raise
