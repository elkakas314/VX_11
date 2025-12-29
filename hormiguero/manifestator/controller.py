"""
VX11 Manifestator Controller
hormiguero/manifestator/controller.py

Role: Planning-only drift validation, patchplan generation, builder spec planning (NO execution).
Integration: Reads from manifestator_lanes, manifestator_rails tables. Exposed via tentáculo_link/routes/rails.py

Core Functions:
- get_lane_status(lane_id): Retrieve lane details + findings
- validate_drift_evidence(drift_evidence): Validate filesystem drift snapshot
- generate_patchplan(drift_evidence, scope): Generate non-executable patchplan from drift
- generate_builder_spec(module, patchplan, constraints): Generate builder specification (recipe)
"""

import json
import sqlite3
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import os
from dataclasses import dataclass, asdict


@dataclass
class DriftEvidence:
    """Drift evidence snapshot from Hormiguero"""

    missing: List[str]
    extra: List[str]
    modified: Optional[List[str]] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.modified is None:
            self.modified = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class RailsController:
    """Manifestator rails + lanes controller for drift validation and patchplan generation"""

    def __init__(self, repo_root: str = "/home/elkakas314/vx11"):
        self.repo_root = Path(repo_root)
        self.db_path = self.repo_root / "data" / "runtime" / "vx11.db"

    def _get_db(self) -> sqlite3.Connection:
        """Get DB connection with Row factory"""
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def get_all_lanes(self) -> List[Dict[str, Any]]:
        """Retrieve all manifestator lanes (drift detection stages)"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT lane_id, name, description, stage, checks_json, created_at
                FROM manifestator_lanes
                ORDER BY stage DESC, created_at DESC
                """
            )
            lanes = [dict(row) for row in cursor.fetchall()]
            conn.close()

            # Parse checks_json
            for lane in lanes:
                if lane["checks_json"]:
                    try:
                        lane["checks"] = json.loads(lane["checks_json"])
                    except json.JSONDecodeError:
                        lane["checks"] = []
                else:
                    lane["checks"] = []
                del lane["checks_json"]

            return lanes
        except Exception as e:
            return []

    def get_lane_status(self, lane_id: str) -> Dict[str, Any]:
        """
        GET /api/rails/{lane_id}/status
        Retrieve detailed lane status + audit findings
        """
        try:
            conn = self._get_db()
            cursor = conn.cursor()

            # Get lane details
            cursor.execute(
                """
                SELECT lane_id, name, description, stage, checks_json, created_at
                FROM manifestator_lanes
                WHERE lane_id = ?
                """,
                (lane_id,),
            )
            lane_row = cursor.fetchone()
            if not lane_row:
                conn.close()
                return {"error": "lane_not_found", "lane_id": lane_id}

            lane = dict(lane_row)

            # Parse checks
            if lane["checks_json"]:
                try:
                    lane["checks"] = json.loads(lane["checks_json"])
                except json.JSONDecodeError:
                    lane["checks"] = []
            else:
                lane["checks"] = []
            del lane["checks_json"]

            # Get audit findings for this lane (from manifestator_audit table)
            cursor.execute(
                """
                SELECT audit_id, correlation_id, status, patch_plan_json, run_ts
                FROM manifestator_audit
                WHERE correlation_id LIKE ?
                ORDER BY run_ts DESC
                LIMIT 20
                """,
                (f"%{lane_id}%",),
            )
            audit_rows = cursor.fetchall()
            lane["audit_findings"] = []

            for audit_row in audit_rows:
                finding = dict(audit_row)
                if finding["patch_plan_json"]:
                    try:
                        finding["patch_plan"] = json.loads(finding["patch_plan_json"])
                    except json.JSONDecodeError:
                        finding["patch_plan"] = {}
                else:
                    finding["patch_plan"] = {}
                del finding["patch_plan_json"]
                lane["audit_findings"].append(finding)

            conn.close()

            return {
                "lane_id": lane_id,
                "name": lane["name"],
                "description": lane["description"],
                "stage": lane["stage"],
                "checks": lane["checks"],
                "audit_findings": lane["audit_findings"],
                "created_at": lane["created_at"],
                "status": "ok",
            }

        except Exception as e:
            return {"error": str(e), "lane_id": lane_id}

    def get_all_rails(self) -> List[Dict[str, Any]]:
        """Retrieve all manifestator rails (constraints/rules)"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT rail_id, name, description, rule_type, severity_on_violation, active, created_at
                FROM manifestator_rails
                WHERE active = TRUE
                ORDER BY severity_on_violation DESC, created_at DESC
                """
            )
            rails = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rails
        except Exception as e:
            return []

    def validate_drift_evidence(self, drift_evidence: DriftEvidence) -> Dict[str, Any]:
        """
        Validate drift evidence snapshot.
        Returns: {valid: bool, issues: [...], risk: "low|mid|high", hash: sha256}
        """
        issues = []
        risk = "low"

        # Check for missing files
        if drift_evidence.missing:
            if len(drift_evidence.missing) > 10:
                risk = "high"
                issues.append(f"Too many missing files: {len(drift_evidence.missing)}")
            else:
                risk = "mid"
                issues.append(f"Missing {len(drift_evidence.missing)} file(s)")

        # Check for extra files
        if drift_evidence.extra:
            if len(drift_evidence.extra) > 20:
                risk = "high"
                issues.append(f"Too many extra files: {len(drift_evidence.extra)}")
            else:
                issues.append(f"Extra {len(drift_evidence.extra)} file(s)")

        # Check for modified files
        if drift_evidence.modified:
            if len(drift_evidence.modified) > 30:
                risk = "high"
                issues.append(
                    f"Too many modified files: {len(drift_evidence.modified)}"
                )
            else:
                issues.append(f"Modified {len(drift_evidence.modified)} file(s)")

        # Compute hash (deterministic)
        evidence_str = json.dumps(
            {
                "missing": sorted(drift_evidence.missing or []),
                "extra": sorted(drift_evidence.extra or []),
                "modified": sorted(drift_evidence.modified or []),
            },
            sort_keys=True,
        )
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        valid = len(issues) == 0 or risk == "low"

        return {
            "valid": valid,
            "issues": issues,
            "risk": risk,
            "hash": evidence_hash,
            "timestamp": drift_evidence.timestamp,
        }

    def generate_patchplan(
        self, drift_evidence: DriftEvidence, scope: str = "local"
    ) -> Dict[str, Any]:
        """
        Generate non-executable patchplan from drift evidence.
        Planning-only; no execution.

        Returns: {plan_id, actions: [{action, target, reason}], risk, estimated_time_sec, notes}
        """
        plan_id = str(uuid.uuid4())
        actions = []
        estimated_time_sec = 0

        # Generate add actions for missing files
        for missing_file in drift_evidence.missing or []:
            actions.append(
                {
                    "action": "add",
                    "target": missing_file,
                    "reason": "File missing from filesystem; restore from backup or regenerate",
                }
            )
            estimated_time_sec += 5

        # Generate remove actions for extra files
        for extra_file in drift_evidence.extra or []:
            actions.append(
                {
                    "action": "remove",
                    "target": extra_file,
                    "reason": "File not in canonical manifest; remove if safe",
                }
            )
            estimated_time_sec += 3

        # Generate verify actions for modified files
        for modified_file in drift_evidence.modified or []:
            actions.append(
                {
                    "action": "verify",
                    "target": modified_file,
                    "reason": "File modified; verify integrity and restore if corrupted",
                }
            )
            estimated_time_sec += 10

        # Validate plan
        validation = self.validate_drift_evidence(drift_evidence)
        risk = validation["risk"]

        return {
            "plan_id": plan_id,
            "actions": actions,
            "risk": risk,
            "estimated_time_sec": estimated_time_sec,
            "notes": f"Patchplan for scope={scope}; {len(actions)} action(s); {risk} risk; planning-only (no execution)",
            "timestamp": datetime.utcnow().isoformat(),
        }

    def generate_builder_spec(
        self,
        module: str,
        patchplan: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate builder specification (recipe for module building).
        Planning-only; no execution.

        Returns: {builder_id, module, actions, artifacts, risk, estimated_time_sec, notes, hash}
        """
        builder_id = f"builder_{module}_{uuid.uuid4().hex[:8]}"

        if constraints is None:
            constraints = {}

        if patchplan is None:
            patchplan = {"actions": []}

        # Transform patchplan actions into builder spec
        actions = []
        for patchaction in patchplan.get("actions", []):
            actions.append(
                {
                    "step": f"{patchaction['action']}_{len(actions)}",
                    "type": patchaction["action"],
                    "target": patchaction["target"],
                    "executable": False,  # Planning only
                }
            )

        # Estimate artifacts (suggested, not created)
        artifacts = []
        if module:
            artifacts = [
                f"sandbox/{module}/build.log",
                f"sandbox/{module}/artifacts.tar.gz",
            ]

        # Compute deterministic hash
        spec_str = json.dumps(
            {
                "module": module,
                "actions": [
                    {"type": a["type"], "target": a["target"]} for a in actions
                ],
                "constraints": constraints,
            },
            sort_keys=True,
        )
        spec_hash = hashlib.sha256(spec_str.encode()).hexdigest()

        return {
            "builder_id": builder_id,
            "module": module,
            "actions": actions,
            "artifacts": artifacts,
            "risk": patchplan.get("risk", "low"),
            "estimated_time_sec": patchplan.get("estimated_time_sec", 0) + 30,
            "notes": [
                "Builder spec is planning-only; no execution or compilation",
                f"Module: {module}",
                f"Actions: {len(actions)}",
                f"Constraints: {constraints}",
                f"Correlation ID: {correlation_id or 'none'}",
            ],
            "hash": spec_hash,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def log_audit_finding(
        self,
        lane_id: str,
        correlation_id: str,
        status: str,
        patch_plan: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log audit finding to manifestator_audit table"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()

            audit_id = str(uuid.uuid4())
            patch_plan_json = json.dumps(patch_plan or {})

            cursor.execute(
                """
                INSERT INTO manifestator_audit
                (audit_id, correlation_id, status, patch_plan_json)
                VALUES (?, ?, ?, ?)
                """,
                (audit_id, correlation_id, status, patch_plan_json),
            )
            conn.commit()
            conn.close()

            return audit_id
        except Exception as e:
            return ""
