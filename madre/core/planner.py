"""Planner: Intent → Plan (sequence of steps)."""

import logging
from typing import List, Optional, Dict, Any
from .models import IntentV2, PlanV2, StepV2, StepType, StatusEnum, ModeEnum

log = logging.getLogger("madre.planner")


class Planner:
    """Generates execution plans from intents."""

    def __init__(self, enabled_targets: Optional[Dict[str, bool]] = None):
        """
        Args:
            enabled_targets: dict like {"switch": True, "shub": False, "manifestator": False}
        """
        self.enabled_targets = enabled_targets or {
            "switch": True,
            "hormiguero": True,
            "manifestator": False,
            "shub": False,
            "spawner": False,
        }

    def plan(self, intent: IntentV2) -> PlanV2:
        """Generate plan from intent."""
        plan = PlanV2(
            intent_id=intent.intent_id,
            session_id=intent.session_id,
            mode=intent.mode,
        )

        # Step 1: Health check (system is always available)
        plan.steps.append(
            StepV2(
                type=StepType.SYSTEM_HEALTHCHECK,
                payload={"targets": ["tentaculo_link", "madre"]},
            )
        )

        # Step 2: Route based on domain/mode
        if intent.mode == ModeEnum.AUDIO_ENGINEER:
            plan.steps.extend(self._plan_audio(intent))
        else:
            plan.steps.extend(self._plan_madre(intent))

        # Step 3: Gather results (NOOP placeholder)
        plan.steps.append(
            StepV2(
                type=StepType.NOOP,
                payload={"reason": "plan_complete"},
            )
        )

        plan.status = StatusEnum.RUNNING
        return plan

    def _plan_madre(self, intent: IntentV2) -> List[StepV2]:
        """Plan for MADRE mode (general queries, monitoring)."""
        steps = []

        # If requires confirmation, add a blocking NOOP step
        if intent.requires_confirmation:
            steps.append(
                StepV2(
                    type=StepType.NOOP,
                    payload={"reason": "awaiting_confirmation"},
                    blocking=True,
                    status=StatusEnum.WAITING,
                )
            )

        # Route to Switch if available (for intent understanding)
        if self.enabled_targets.get("switch", True):
            steps.append(
                StepV2(
                    type=StepType.CALL_SWITCH,
                    payload={
                        "prompt": intent.dsl.original_text,
                        "metadata": {},
                        "source": "madre",
                    },
                    blocking=False,
                )
            )

        # If action mentions health/status, add healthcheck
        if any(w in intent.dsl.action for w in ["status", "health", "check"]):
            steps.append(
                StepV2(
                    type=StepType.SYSTEM_HEALTHCHECK,
                    payload={"targets": intent.targets or ["all"]},
                )
            )

        # If requires spawner (e.g., long-running task) -> WAITING
        if self.enabled_targets.get("spawner", False):
            if any(w in intent.dsl.action for w in ["run", "execute", "start"]):
                steps.append(
                    StepV2(
                        type=StepType.SPAWNER_REQUEST,
                        payload={
                            "task": intent.dsl.action,
                            "params": intent.dsl.parameters,
                        },
                    )
                )

        return steps

    def _plan_audio(self, intent: IntentV2) -> List[StepV2]:
        """Plan for AUDIO_ENGINEER mode (delegated to Shub/HUZ)."""
        steps = []

        # If requires confirmation, add blocking step
        if intent.requires_confirmation:
            steps.append(
                StepV2(
                    type=StepType.NOOP,
                    payload={"reason": "awaiting_confirmation"},
                    blocking=True,
                    status=StatusEnum.WAITING,
                )
            )

        # Audio tasks go to Shub (if enabled)
        if self.enabled_targets.get("shub", False):
            steps.append(
                StepV2(
                    type=StepType.CALL_SHUB,
                    payload={
                        "task": intent.dsl.action,
                        "params": intent.dsl.parameters,
                    },
                )
            )
        else:
            # Shub disabled: warning + NOOP
            steps.append(
                StepV2(
                    type=StepType.NOOP,
                    payload={
                        "reason": "shub_disabled",
                        "warning": "audio_tasks_unavailable",
                    },
                )
            )

        return steps
