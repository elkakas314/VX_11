"""
Bridge Handler for MADRE: Converts conversational requests into orchestrated actions.
Implements HIJAS (ephemeral daughters) that execute specific tasks and report back.
"""

import uuid
import logging
import asyncio
import httpx
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

from manifestator.auto_patcher import PatchBuilder

# NOTE: spawner.ephemeral_v2 not available; using manifestator.auto_patcher as fallback
# from spawner.ephemeral_v2 import apply_patch_operations

log = logging.getLogger("vx11.madre.bridge")


@dataclass
class HIJA:
    """Ephemeral daughter process: lightweight task executor."""

    hija_id: str
    name: str
    task_type: str  # "audit", "scan", "drift", "route", "spawn"
    status: str  # "pending", "running", "completed", "failed"
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BridgeHandler:
    """
    Converts user messages → orchestrated actions via HIJAS.

    Supported HIJA types:
    - audit_full: Check manifestator drift + hermes registry
    - scan_hive: Check hormiguero queen + ant states
    - route_query: Send query to switch/route-v5
    - spawn_cmd: Execute command via hermes CLI
    - manifestator_apply: Trigger configuration deployment
    """

    def __init__(self, madre_ports: Dict[str, int]):
        """
        Args:
            madre_ports: {"hermes": 8003, "switch": 8002, "manifestator": 8005, "hormiguero": 8004}
        """
        self.madre_ports = madre_ports
        self.hijas: Dict[str, HIJA] = {}
        self.client = None
        self.repo_root = Path(__file__).resolve().parents[1]
        self.patch_builder = PatchBuilder(self.repo_root)

    async def _get_client(self):
        """Lazy-init httpx AsyncClient."""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client

    async def close(self):
        """Cleanup HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    def _create_hija(self, name: str, task_type: str) -> HIJA:
        """Create and register new HIJA."""
        hija = HIJA(
            hija_id=f"hija-{uuid.uuid4().hex[:8]}",
            name=name,
            task_type=task_type,
            status="pending",
            started_at=datetime.utcnow(),
        )
        self.hijas[hija.hija_id] = hija
        log.info(f"hija_created:{hija.hija_id}:type={task_type}")
        return hija

    async def _update_hija(
        self,
        hija_id: str,
        status: str,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        """Update HIJA status and result."""
        if hija_id not in self.hijas:
            return

        hija = self.hijas[hija_id]
        hija.status = status
        if result:
            hija.result = result
        if error:
            hija.error = error
        if status in ["completed", "failed"]:
            hija.completed_at = datetime.utcnow()

        log.info(f"hija_updated:{hija_id}:status={status}")

    async def audit_full(
        self, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        HIJA: audit_full - Check manifestator drift + hermes registry + switch status.
        """
        hija = self._create_hija("audit_full", "audit")
        await self._update_hija(hija.hija_id, "running")

        result = {
            "hija_id": hija.hija_id,
            "components": {},
        }

        try:
            client = await self._get_client()

            # 1. Check Manifestator drift
            try:
                manifestator_url = (
                    settings.manifestator_url
                    or f"http://manifestator:{settings.manifestator_port}"
                )
                resp = await client.get(
                    f"{manifestator_url}/drift",
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    result["components"]["manifestator_drift"] = resp.json()
            except Exception as e:
                result["components"]["manifestator_drift"] = {"error": str(e)}

            # 2. Check Hermes registry
            try:
                hermes_url = (
                    settings.hermes_url or f"http://hermes:{settings.hermes_port}"
                )
                resp = await client.get(
                    f"{hermes_url}/hermes/list-engines",
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    result["components"]["hermes_engines"] = resp.json()
            except Exception as e:
                result["components"]["hermes_engines"] = {"error": str(e)}

            # 3. Check Switch health
            try:
                switch_url = (
                    settings.switch_url or f"http://switch:{settings.switch_port}"
                )
                resp = await client.get(
                    f"{switch_url}/health",
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    result["components"]["switch_health"] = resp.json()
            except Exception as e:
                result["components"]["switch_health"] = {"error": str(e)}

            # 4. Check Hormiguero hive
            try:
                hormiguero_url = (
                    settings.hormiguero_url
                    or f"http://hormiguero:{settings.hormiguero_port}"
                )
                resp = await client.get(
                    f"{hormiguero_url}/hormiguero/hive",
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    result["components"]["hormiguero_hive"] = resp.json()
            except Exception as e:
                result["components"]["hormiguero_hive"] = {"error": str(e)}

            await self._update_hija(hija.hija_id, "completed", result=result)

        except Exception as e:
            log.error(f"audit_full_error:{e}")
            await self._update_hija(hija.hija_id, "failed", error=str(e))

        return result

    async def organize(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        HIJA: organize - Build patch via Manifestator and apply with ephemeral executor.
        """
        hija = self._create_hija("organize", "organize")
        await self._update_hija(hija.hija_id, "running")

        try:
            patch_plan = self.patch_builder.build_patch(intent)
            if not patch_plan.get("operations"):
                await self._update_hija(
                    hija.hija_id,
                    "completed",
                    result={"patch": patch_plan, "applied": False},
                )
                return {"hija_id": hija.hija_id, "patch": patch_plan, "applied": False}

            backup_root = Path(
                patch_plan.get(
                    "backup_root", self.repo_root / "build" / "artifacts" / "backups"
                )
            )
            # NOTE: apply_patch_operations not available; using PatchBuilder fallback
            try:
                patcher = PatchBuilder(str(self.repo_root))
                apply_result = {
                    "status": "planned",
                    "operations_count": len(patch_plan.get("operations", [])),
                    "note": "Patch builder initialized; actual apply pending implementation",
                }
            except Exception as e:
                apply_result = {"status": "error", "error": str(e)}

            result = {"patch": patch_plan, "apply_result": apply_result}
            await self._update_hija(hija.hija_id, "completed", result=result)
            return {"hija_id": hija.hija_id, **result}
        except Exception as e:
            log.error(f"organize_error:{e}")
            await self._update_hija(hija.hija_id, "failed", error=str(e))
            return {"hija_id": hija.hija_id, "error": str(e)}

    async def scan_hive(
        self, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        HIJA: scan_hive - Check hormiguero queen + ants status.
        """
        hija = self._create_hija("scan_hive", "scan")
        await self._update_hija(hija.hija_id, "running")

        result = {
            "hija_id": hija.hija_id,
            "queen": {},
            "ants": [],
        }

        try:
            client = await self._get_client()

            hormiguero_url = (
                settings.hormiguero_url
                or f"http://hormiguero:{settings.hormiguero_port}"
            )
            resp = await client.get(
                f"{hormiguero_url}/hormiguero/queen",
                timeout=5.0,
            )
            if resp.status_code == 200:
                result["queen"] = resp.json()

            # Scan ants (if endpoint exists)
            resp = await client.get(
                f"{hormiguero_url}/hormiguero/ants",
                timeout=5.0,
            )
            if resp.status_code == 200:
                result["ants"] = resp.json().get("ants", [])

            await self._update_hija(hija.hija_id, "completed", result=result)

        except Exception as e:
            log.error(f"scan_hive_error:{e}")
            await self._update_hija(hija.hija_id, "failed", error=str(e))

        return result

    async def route_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        HIJA: route_query - Send query to SmartRouter (switch/route-v5).
        """
        hija = self._create_hija(f"route_query", "route")
        await self._update_hija(hija.hija_id, "running")

        result = {
            "hija_id": hija.hija_id,
            "query": query,
            "router_response": {},
        }

        try:
            client = await self._get_client()

            switch_url = settings.switch_url or f"http://switch:{settings.switch_port}"
            resp = await client.post(
                f"{switch_url}/switch/route-v5",
                json={"query": query, "context": context or {}},
                timeout=30.0,
            )
            if resp.status_code == 200:
                result["router_response"] = resp.json()
            else:
                result["router_response"] = {"error": f"status={resp.status_code}"}

            await self._update_hija(hija.hija_id, "completed", result=result)

        except Exception as e:
            log.error(f"route_query_error:{e}")
            await self._update_hija(hija.hija_id, "failed", error=str(e))

        return result

    async def spawn_cmd(
        self, cmd: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        HIJA: spawn_cmd - Execute CLI command via hermes.
        """
        hija = self._create_hija(f"spawn_cmd", "spawn")
        await self._update_hija(hija.hija_id, "running")

        result = {
            "hija_id": hija.hija_id,
            "cmd": cmd,
            "exec_response": {},
        }

        try:
            client = await self._get_client()

            resp = await client.post(
                f"http://127.0.0.1:{self.madre_ports.get('hermes', 8003)}/hermes/exec",
                json={"cmd": cmd},
                timeout=30.0,
            )
            if resp.status_code == 200:
                result["exec_response"] = resp.json()
            else:
                result["exec_response"] = {"error": f"status={resp.status_code}"}

            await self._update_hija(hija.hija_id, "completed", result=result)

        except Exception as e:
            log.error(f"spawn_cmd_error:{e}")
            await self._update_hija(hija.hija_id, "failed", error=str(e))

        return result

    async def get_hija(self, hija_id: str) -> Optional[HIJA]:
        """Retrieve HIJA by ID."""
        return self.hijas.get(hija_id)

    async def list_hijas(self, status: Optional[str] = None) -> List[HIJA]:
        """List all HIJAS, optionally filtered by status."""
        hijas = list(self.hijas.values())
        if status:
            hijas = [h for h in hijas if h.status == status]
        return hijas

    async def cleanup_completed(self):
        """Remove completed/failed HIJAS older than 5 minutes."""
        cutoff = datetime.utcnow()
        cutoff_ts = cutoff.timestamp() - 300  # 5 minutes ago

        to_remove = []
        for hija_id, hija in self.hijas.items():
            if hija.status in ["completed", "failed"] and hija.completed_at:
                if hija.completed_at.timestamp() < cutoff_ts:
                    to_remove.append(hija_id)

        for hija_id in to_remove:
            del self.hijas[hija_id]
            log.info(f"hija_cleaned:{hija_id}")
