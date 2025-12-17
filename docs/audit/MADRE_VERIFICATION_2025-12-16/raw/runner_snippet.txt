"""Runner: executes plan steps."""

import logging
import httpx
from typing import Optional, Dict, Any
from .models import PlanV2, StatusEnum, StepType
from .db import MadreDB
from config.settings import settings

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
            # Insert into daughter_tasks and mark task WAITING (no hijas launched here)
            from config.db_schema import DaughterTask
            import json
            import uuid
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy import create_engine

            daughter_task = DaughterTask(
                source="madre",
                priority=3,
                status="pending",
                task_type="long",
                description=step.payload.get(
                    "description", "Spawner request from Madre"
                ),
                metadata_json=json.dumps(step.payload),
            )
            engine = create_engine(
                "sqlite:////home/elkakas314/vx11/data/runtime/vx11.db"
            )
            Session = sessionmaker(bind=engine)
            db = Session()
            try:
                db.add(daughter_task)
                db.commit()
                log.info(f"DaughterTask inserted: {daughter_task.id}")
                MadreDB.record_action(
                    module="madre",
                    action="daughter_task_created",
                    reason="spawner_request",
                )
                return {
                    "status": "daughter_task_queued",
                    "daughter_task_id": daughter_task.id,
                }
            finally:
                db.close()
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
                port = settings.PORTS.get(t, 8000)
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        resp = await client.get(f"http://127.0.0.1:{port}/health")
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
