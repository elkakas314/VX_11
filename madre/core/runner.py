"""Runner: executes plan steps."""

import logging
import httpx
from typing import Optional, Dict, Any
from .models import PlanV2, StatusEnum, StepType
from .db import MadreDB
from config.settings import settings
from config.db_schema import get_session, DaughterTask

log = logging.getLogger("madre.runner")


class Runner:
    """Executes plan steps safely."""

    def __init__(self, timeout_sec: float = 5.0):
        self.timeout_sec = timeout_sec

    async def execute_plan(self, plan: PlanV2, plan_id: str) -> PlanV2:
        """Execute all steps in plan. Returns updated plan."""
        plan.status = StatusEnum.RUNNING

        for i, step in enumerate(plan.steps):
            log.info(f"Executing step {i}: {step.type}")

            # Skip if already done/error
            if step.status in [StatusEnum.DONE, StatusEnum.ERROR]:
                continue

            # If blocking and waiting, stop execution
            if step.blocking and step.status == StatusEnum.WAITING:
                log.info(f"Step {i} is blocking and waiting. Pausing plan.")
                plan.status = StatusEnum.WAITING
                MadreDB.update_task(plan_id, status="WAITING")
                return plan

            try:
                result = await self._execute_step(step)
                step.result = result
                step.status = StatusEnum.DONE
                MadreDB.record_action(
                    module="madre",
                    action=f"step_executed:{step.type}",
                    reason=f"step_{i}",
                )
            except Exception as e:
                log.error(f"Step {i} failed: {e}")
                step.error = str(e)
                step.status = StatusEnum.ERROR
                # Don't stop plan; continue with other steps
                MadreDB.record_action(
                    module="madre",
                    action=f"step_failed:{step.type}",
                    reason=str(e),
                )

        # All steps completed (or had errors)
        plan.status = StatusEnum.DONE
        MadreDB.update_task(plan_id, status="DONE", result=plan.json())
        return plan

    async def _execute_step(self, step) -> Dict[str, Any]:
        """Execute single step."""
        if step.type == StepType.SYSTEM_HEALTHCHECK:
            return await self._healthcheck(step.payload.get("targets", []))
        elif step.type == StepType.CALL_SWITCH:
            return await self._call_switch(step.payload)
        elif step.type == StepType.CALL_HORMIGUERO_TASK:
            return await self._call_hormiguero(step.payload)
        elif step.type == StepType.CALL_MANIFESTATOR:
            return await self._call_manifestator(step.payload)
        elif step.type == StepType.CALL_SHUB:
            return await self._call_shub(step.payload)
        elif step.type == StepType.SPAWNER_REQUEST:
            # Call Spawner API to trigger background task
            try:
                async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                    resp = await client.post(
                        f"{settings.spawner_url}/spawner/spawn",
                        json={
                            "intent": "spawn",
                            "description": step.payload.get(
                                "description", "Spawner request from Madre"
                            ),
                            "task_type": "long",
                            "source": "madre",
                            "cmd": "echo 'Hija efimera ejecutando accion...'; sleep 2; echo 'Accion completada.'",
                            "metadata": step.payload,
                        },
                        headers={"X-VX11-Token": settings.api_token},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        log.info(
                            f"Spawner request successful: {data.get('spawn_uuid')}"
                        )
                        MadreDB.record_action(
                            module="madre",
                            action="spawner_request_sent",
                            reason="plan_execution",
                        )
                        return {
                            "status": "daughter_spawned",
                            "spawn_uuid": data.get("spawn_uuid"),
                            "daughter_id": data.get("daughter_id"),
                        }
                    else:
                        log.error(
                            f"Spawner call failed: {resp.status_code} - {resp.text}"
                        )
                        return {"status": "error", "detail": "spawner_call_failed"}
            except Exception as e:
                log.error(f"Spawner call exception: {e}")
                return {"status": "error", "detail": str(e)}
        elif step.type == StepType.NOOP:
            return {"status": "noop"}
        else:
            raise ValueError(f"Unknown step type: {step.type}")

    async def _healthcheck(self, targets: list) -> Dict[str, Any]:
        """System health check."""
        result = {}
        for target in targets:
            if target == "all":
                targets_list = ["tentaculo_link", "madre", "switch", "hermes"]
            else:
                targets_list = [target]

            for t in targets_list:
                # Resolve URL from settings
                url = getattr(settings, f"{t}_url", None)
                if not url:
                    # Fallback to PORTS dict if no _url attribute
                    port = settings.PORTS.get(t, 8000)
                    url = f"http://{t}:{port}"

                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        resp = await client.get(f"{url}/health")
                        result[t] = "up" if resp.status_code == 200 else "down"
                except:
                    result[t] = "down"

        return result

    async def _call_switch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Switch module."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{settings.switch_url}/switch/route-v5",
                    json=payload,
                    headers={"X-VX11-Token": settings.api_token},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            log.error(f"Switch call failed: {e}")
            raise

    async def _call_hormiguero(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Hormiguero module."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{settings.hormiguero_url}/hormiguero/task",
                    json=payload,
                    headers={"X-VX11-Token": settings.api_token},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            log.error(f"Hormiguero call failed: {e}")
            raise

    async def _call_manifestator(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Manifestator module."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{settings.manifestator_url}/drift",
                    json=payload,
                    headers={"X-VX11-Token": settings.api_token},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            log.error(f"Manifestator call failed: {e}")
            raise

    async def _call_shub(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Shub module."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                resp = await client.post(
                    f"{settings.shub_url}/shub/process",
                    json=payload,
                    headers={"X-VX11-Token": settings.api_token},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            log.error(f"Shub call failed: {e}")
            raise
