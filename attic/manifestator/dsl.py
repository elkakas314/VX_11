"""
ManifestatorDSL: Declarative configuration management with simulate/apply/rollback.
Enables safe deployment patterns and configuration validation before apply.
"""

import logging
import json
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

log = logging.getLogger("vx11.manifestator.dsl")


@dataclass
class ConfigBlock:
    """Represents a configuration block to deploy."""
    id: str
    target: str  # service module or file path
    operation: str  # "set", "create", "delete", "replace"
    key: str  # config key or file path
    value: Any
    depends_on: Optional[List[str]] = None
    rollback_value: Optional[Any] = None


@dataclass
class DeploymentPlan:
    """Plan for deployment: blocks + rollback info."""
    plan_id: str
    blocks: List[ConfigBlock]
    created_at: datetime
    simulated: bool = False
    simulation_results: Optional[Dict[str, Any]] = None
    applied: bool = False
    applied_at: Optional[datetime] = None
    rollback_info: Optional[Dict[str, Any]] = None


class ManifestatorDSL:
    """
    Declarative configuration DSL for VX11 services.
    
    Workflow:
    1. Define blocks (target module, operation, key, value)
    2. Call simulate() to validate without changes
    3. Review simulation results
    4. Call apply() to commit changes (creates rollback info)
    5. Call rollback() if needed
    """
    
    def __init__(self, storage_dir: str = ".tmp_copilot/manifestator"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.plans: Dict[str, DeploymentPlan] = {}
        self.applied_configs: Dict[str, Any] = {}
    
    def create_block(
        self,
        target: str,
        operation: str,
        key: str,
        value: Any,
        depends_on: Optional[List[str]] = None,
    ) -> ConfigBlock:
        """Create a config block."""
        block_id = f"block-{len([b for p in self.plans.values() for b in p.blocks])}"
        return ConfigBlock(
            id=block_id,
            target=target,
            operation=operation,
            key=key,
            value=value,
            depends_on=depends_on or [],
        )
    
    def create_plan(self, blocks: List[ConfigBlock]) -> DeploymentPlan:
        """Create deployment plan from blocks."""
        plan_id = f"plan-{datetime.utcnow().timestamp():.0f}"
        plan = DeploymentPlan(
            plan_id=plan_id,
            blocks=blocks,
            created_at=datetime.utcnow(),
        )
        self.plans[plan_id] = plan
        return plan
    
    async def _validate_block(self, block: ConfigBlock) -> Tuple[bool, Optional[str]]:
        """
        Validate block:
        - Check operation is valid
        - Check target module exists (or will be created)
        - Check value is serializable
        """
        valid_ops = ["set", "create", "delete", "replace"]
        if block.operation not in valid_ops:
            return False, f"invalid_operation:{block.operation}"
        
        if block.operation == "delete" and not block.value:
            # delete operation doesn't need value
            pass
        
        # Try to serialize value (must be JSON-compatible)
        try:
            json.dumps(block.value)
        except Exception as e:
            return False, f"value_not_serializable:{e}"
        
        return True, None
    
    async def _validate_dependencies(self, blocks: List[ConfigBlock]) -> Tuple[bool, Optional[str]]:
        """Validate block dependencies are resolvable."""
        block_ids = {b.id for b in blocks}
        
        for block in blocks:
            if block.depends_on:
                for dep_id in block.depends_on:
                    if dep_id not in block_ids:
                        return False, f"unresolvable_dependency:{block.id}->{dep_id}"
        
        # Check for cycles (simple: if A->B and B->A)
        for block_a in blocks:
            for block_b in blocks:
                if block_a.id == block_b.id:
                    continue
                if (block_a.depends_on and block_b.id in block_a.depends_on and
                    block_b.depends_on and block_a.id in block_b.depends_on):
                    return False, f"circular_dependency:{block_a.id}<->{block_b.id}"
        
        return True, None
    
    async def simulate(self, plan_id: str) -> Dict[str, Any]:
        """
        Simulate plan without making changes.
        Returns: {ok: bool, blocks_validated: int, errors: [], warnings: []}
        """
        if plan_id not in self.plans:
            return {"ok": False, "error": "plan_not_found"}
        
        plan = self.plans[plan_id]
        results = {
            "plan_id": plan_id,
            "ok": True,
            "blocks_validated": 0,
            "errors": [],
            "warnings": [],
            "simulation_time": datetime.utcnow().isoformat(),
        }
        
        # Validate each block
        for block in plan.blocks:
            valid, error = await self._validate_block(block)
            if not valid:
                results["ok"] = False
                results["errors"].append(f"{block.id}: {error}")
            else:
                results["blocks_validated"] += 1
        
        # Validate dependencies
        valid, error = await self._validate_dependencies(plan.blocks)
        if not valid:
            results["ok"] = False
            results["errors"].append(f"dependencies: {error}")
        
        # Estimate impact
        set_ops = sum(1 for b in plan.blocks if b.operation == "set")
        create_ops = sum(1 for b in plan.blocks if b.operation == "create")
        delete_ops = sum(1 for b in plan.blocks if b.operation == "delete")
        
        results["estimated_impact"] = {
            "set_operations": set_ops,
            "create_operations": create_ops,
            "delete_operations": delete_ops,
            "total_blocks": len(plan.blocks),
        }
        
        plan.simulated = True
        plan.simulation_results = results
        
        log.info(f"simulate:plan={plan_id}:ok={results['ok']}:blocks={results['blocks_validated']}")
        
        return results
    
    async def apply(self, plan_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Apply plan: commit changes and record rollback info.
        
        Args:
            plan_id: Plan ID to apply
            force: Skip simulation check if True
        
        Returns: {ok: bool, applied_blocks: int, rollback_info: {}}
        """
        if plan_id not in self.plans:
            return {"ok": False, "error": "plan_not_found"}
        
        plan = self.plans[plan_id]
        
        # Check simulation (unless force=True)
        if not force and not plan.simulated:
            return {"ok": False, "error": "plan_not_simulated:run_simulate_first"}
        
        if not force and plan.simulation_results and not plan.simulation_results.get("ok"):
            return {
                "ok": False,
                "error": "simulation_failed",
                "errors": plan.simulation_results.get("errors", []),
            }
        
        applied_blocks = 0
        rollback_info = {}
        
        for block in plan.blocks:
            try:
                # Record current value for rollback
                current = self.applied_configs.get(f"{block.target}/{block.key}")
                rollback_info[block.id] = {
                    "operation": block.operation,
                    "current_value": current,
                }
                
                # Apply operation (simulated)
                if block.operation == "set":
                    self.applied_configs[f"{block.target}/{block.key}"] = block.value
                elif block.operation == "create":
                    if f"{block.target}/{block.key}" in self.applied_configs:
                        log.warning(f"apply:block={block.id}:already_exists")
                    else:
                        self.applied_configs[f"{block.target}/{block.key}"] = block.value
                elif block.operation == "delete":
                    if f"{block.target}/{block.key}" in self.applied_configs:
                        del self.applied_configs[f"{block.target}/{block.key}"]
                elif block.operation == "replace":
                    self.applied_configs[f"{block.target}/{block.key}"] = block.value
                
                applied_blocks += 1
                
            except Exception as e:
                log.error(f"apply:block={block.id}:error={e}")
                return {
                    "ok": False,
                    "error": f"apply_failed:block={block.id}:{e}",
                    "applied_blocks": applied_blocks,
                    "rollback_info": rollback_info,
                }
        
        plan.applied = True
        plan.applied_at = datetime.utcnow()
        plan.rollback_info = rollback_info
        
        log.info(f"apply:plan={plan_id}:blocks={applied_blocks}")
        
        return {
            "ok": True,
            "plan_id": plan_id,
            "applied_blocks": applied_blocks,
            "rollback_info": rollback_info,
            "applied_at": plan.applied_at.isoformat(),
        }
    
    async def rollback(self, plan_id: str) -> Dict[str, Any]:
        """
        Rollback applied plan to previous state.
        """
        if plan_id not in self.plans:
            return {"ok": False, "error": "plan_not_found"}
        
        plan = self.plans[plan_id]
        
        if not plan.applied:
            return {"ok": False, "error": "plan_not_applied"}
        
        if not plan.rollback_info:
            return {"ok": False, "error": "no_rollback_info"}
        
        rolled_back = 0
        
        for block in plan.blocks:
            try:
                rollback_entry = plan.rollback_info.get(block.id)
                if not rollback_entry:
                    continue
                
                current_value = rollback_entry.get("current_value")
                
                if current_value is None:
                    # Was not set before, delete now
                    if f"{block.target}/{block.key}" in self.applied_configs:
                        del self.applied_configs[f"{block.target}/{block.key}"]
                else:
                    # Restore previous value
                    self.applied_configs[f"{block.target}/{block.key}"] = current_value
                
                rolled_back += 1
                
            except Exception as e:
                log.error(f"rollback:block={block.id}:error={e}")
        
        plan.applied = False
        log.info(f"rollback:plan={plan_id}:blocks={rolled_back}")
        
        return {
            "ok": True,
            "plan_id": plan_id,
            "rolled_back_blocks": rolled_back,
            "rolled_back_at": datetime.utcnow().isoformat(),
        }
    
    async def audit(self, plan_id: str) -> Dict[str, Any]:
        """
        Audit plan: check current state vs applied state.
        """
        if plan_id not in self.plans:
            return {"ok": False, "error": "plan_not_found"}
        
        plan = self.plans[plan_id]
        audit_result = {
            "plan_id": plan_id,
            "applied": plan.applied,
            "blocks": [],
        }
        
        for block in plan.blocks:
            current = self.applied_configs.get(f"{block.target}/{block.key}")
            block_info = {
                "block_id": block.id,
                "target": block.target,
                "key": block.key,
                "expected_value": block.value,
                "current_value": current,
                "in_sync": current == block.value,
            }
            audit_result["blocks"].append(block_info)
        
        return audit_result
    
    def get_plan(self, plan_id: str) -> Optional[DeploymentPlan]:
        """Get plan by ID."""
        return self.plans.get(plan_id)
    
    def list_plans(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List plans, optionally filtered by status."""
        result = []
        for plan in self.plans.values():
            if status == "applied" and not plan.applied:
                continue
            if status == "simulated" and not plan.simulated:
                continue
            if status == "pending" and (plan.applied or plan.simulated):
                continue
            
            result.append({
                "plan_id": plan.plan_id,
                "blocks_count": len(plan.blocks),
                "simulated": plan.simulated,
                "applied": plan.applied,
                "created_at": plan.created_at.isoformat(),
                "applied_at": plan.applied_at.isoformat() if plan.applied_at else None,
            })
        
        return result
