"""Automatic order auditor and organizer for VX11.

Responsibilities:
- Scan the current repo against the canonical layout (docs/VX11_v6.4_CANONICAL.json).
- Emit structured drift reports (no side effects).
- Optionally send an "organize" intent to Madre for patch generation.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from config.settings import settings
from config.tokens import get_token


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = REPO_ROOT / "docs" / "VX11_v6.4_CANONICAL.json"
LOG_PATH = REPO_ROOT / "build" / "artifacts" / "logs" / "hormiguero_organizer.log"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("vx11.hormiguero.organizer")
if not logger.handlers:
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3}


@dataclass
class Deviation:
    path: str
    issue: str
    severity: str
    suggestion: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "issue": self.issue,
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


class OrderAuditor:
    """Pure scanner. No writes, only structured deviations."""

    def __init__(self, repo_root: Path = REPO_ROOT, canonical_path: Path = CANONICAL_PATH):
        self.repo_root = repo_root
        self.canonical_path = canonical_path
        self.canonical = self._load_canonical()
        self.allowed_root_dirs = set(self.canonical.get("modules", {}).keys()) | {
            "switch",  # contains hermes per canon
            "docs",
            "config",
            "build",
            "data",
            "tests",
            "scripts",
            "tools",
            "models",
            "prompts",
            "forensic",
            "logs",
            "sandbox",
            "shub_sandbox",
            "tentaculo_link",
            ".github",
            ".devcontainer",
            ".vscode",
            ".git",
            ".tmp_copilot",
            ".pytest_cache",
        }
        self.allowed_root_files = {
            "README.md",
            "docker-compose.yml",
            "requirements.txt",
            "requirements_minimal.txt",
            "requirements_switch.txt",
            "requirements_shub.txt",
            "requirements_tentaculo.txt",
            "package.json",
            "package-lock.json",
            "vx11.code-workspace",
            "test.rest",
            "manifestator.http",
            "vx11_control.http",
            "tokens.env",
            "tokens.env.master",
            "tokens.env.sample",
            "OPERATOR_MODE_AUDIT.py",
            ".gitignore",
            ".env.example",
            "sitecustomize.py",
        }

    def _load_canonical(self) -> Dict[str, Any]:
        try:
            with self.canonical_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Canonical file missing at %s", self.canonical_path)
            return {}

    def scan(self) -> Dict[str, Any]:
        deviations: List[Deviation] = []

        deviations.extend(self._check_root_entries())
        deviations.extend(self._check_docs())
        deviations.extend(self._check_logs_and_sandboxes())
        deviations.extend(self._check_databases())
        deviations.extend(self._check_operator_files())

        max_sev = "low"
        if deviations:
            max_sev = max(deviations, key=lambda d: SEVERITY_ORDER.get(d.severity, 1)).severity

        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "canonical_version": self.canonical.get("version"),
            "deviations": [d.to_dict() for d in deviations],
            "counts": {"total": len(deviations)},
            "max_severity": max_sev,
        }
        # Ajuste VX11 v6.6 – anti-caos / drift / auditoría flujos (2025-12-05)
        symlink_targets = [
            self.repo_root / "logs",
            self.repo_root / "sandbox",
            self.repo_root / "shub_sandbox",
            self.repo_root / "forensic",
        ]
        symlinks_ok = True
        for p in symlink_targets:
            if p.exists() and p.is_symlink():
                target = p.resolve()
                if "build/artifacts" not in str(target):
                    symlinks_ok = False
        report["symlinks_ok"] = symlinks_ok
        report["drift_resuelto"] = len(deviations) == 0 and symlinks_ok
        return report

    def _check_root_entries(self) -> List[Deviation]:
        out: List[Deviation] = []
        for entry in self.repo_root.iterdir():
            name = entry.name
            if name.startswith(".") and name not in {".git", ".github", ".vscode", ".devcontainer", ".tmp_copilot"}:
                if name in self.allowed_root_files:
                    continue
                out.append(
                    Deviation(
                        path=str(entry.relative_to(self.repo_root)),
                        issue="hidden_root_entry",
                        severity="low",
                        suggestion="Review hidden entry; archive if not needed.",
                    )
                )
                continue
            if entry.is_dir() and name not in self.allowed_root_dirs:
                out.append(
                    Deviation(
                        path=str(entry.relative_to(self.repo_root)),
                        issue="untracked_root_dir",
                        severity="medium",
                        suggestion="Move to build/artifacts/backups/ or docs/archive/ if not canonical.",
                    )
                )
            elif entry.is_file() and name not in self.allowed_root_files:
                out.append(
                    Deviation(
                        path=str(entry.relative_to(self.repo_root)),
                        issue="untracked_root_file",
                        severity="medium",
                        suggestion="Archive under build/artifacts/backups/root_stray/ with timestamp.",
                    )
                )
        return out

    def _check_docs(self) -> List[Deviation]:
        out: List[Deviation] = []
        allowed_docs = {
            "API_REFERENCE.md",
            "ARCHITECTURE.md",
            "INDEX.md",
            "VX11_v6.4_CANONICAL.json",
            "VX11_v6.4_ANTI_CAOS_REPORT.md",
            "VX11_v6.5_CANONICAL.json",
            "VX11_v6.6_CANONICAL.json",
            "USO_RAPIDO_VX11_v6_6.md",
            "OPERATOR_CHAT_v6.7.md",
            "archive",
            "archive.json",
        }
        docs_dir = self.repo_root / "docs"
        if not docs_dir.exists():
            return [Deviation(path="docs", issue="docs_missing", severity="high", suggestion="Restore docs directory.")]

        for entry in docs_dir.iterdir():
            if entry.name not in allowed_docs:
                out.append(
                    Deviation(
                        path=str(entry.relative_to(self.repo_root)),
                        issue="doc_outside_archive",
                        severity="low",
                        suggestion="Move to docs/archive/ to keep docs tree tidy.",
                    )
                )
        return out

    def _check_logs_and_sandboxes(self) -> List[Deviation]:
        out: List[Deviation] = []
        build_logs = self.repo_root / "build" / "artifacts" / "logs"
        forensic_dir = self.repo_root / "forensic"
        root_logs = self.repo_root / "logs"
        root_sandbox = self.repo_root / "sandbox"
        root_shub_sandbox = self.repo_root / "shub_sandbox"

        if root_logs.exists():
            if root_logs.is_symlink():
                target = root_logs.resolve()
                if "build/artifacts" not in str(target):
                    out.append(
                        Deviation(
                            path=str(root_logs.relative_to(self.repo_root)),
                            issue="logs_outside_artifacts",
                            severity="medium",
                            suggestion="Relocate to build/artifacts/logs/legacy_root/ to consolidate logs.",
                        )
                    )
            else:
                out.append(
                    Deviation(
                        path=str(root_logs.relative_to(self.repo_root)),
                        issue="logs_outside_artifacts",
                        severity="medium",
                        suggestion="Relocate to build/artifacts/logs/legacy_root/ to consolidate logs.",
                    )
                )
        if root_sandbox.exists():
            if root_sandbox.is_symlink():
                target = root_sandbox.resolve()
                if "build/artifacts" not in str(target):
                    out.append(
                        Deviation(
                            path=str(root_sandbox.relative_to(self.repo_root)),
                            issue="sandbox_outside_artifacts",
                            severity="medium",
                            suggestion="Relocate to build/artifacts/sandbox/legacy_root/ to align with canon.",
                        )
                    )
            else:
                out.append(
                    Deviation(
                        path=str(root_sandbox.relative_to(self.repo_root)),
                        issue="sandbox_outside_artifacts",
                        severity="medium",
                        suggestion="Relocate to build/artifacts/sandbox/legacy_root/ to align with canon.",
                    )
                )
        if root_shub_sandbox.exists():
            if root_shub_sandbox.is_symlink():
                target = root_shub_sandbox.resolve()
                if "build/artifacts" not in str(target):
                    out.append(
                        Deviation(
                            path=str(root_shub_sandbox.relative_to(self.repo_root)),
                            issue="sandbox_outside_artifacts",
                            severity="medium",
                            suggestion="Relocate shub_sandbox into build/artifacts/sandbox/legacy_root/.",
                        )
                    )
            else:
                out.append(
                    Deviation(
                        path=str(root_shub_sandbox.relative_to(self.repo_root)),
                        issue="sandbox_outside_artifacts",
                        severity="medium",
                        suggestion="Relocate shub_sandbox into build/artifacts/sandbox/legacy_root/.",
                    )
                )
        if forensic_dir.exists():
            if forensic_dir.is_symlink():
                target = forensic_dir.resolve()
                if "build/artifacts" not in str(target):
                    out.append(
                        Deviation(
                            path=str(forensic_dir.relative_to(self.repo_root)),
                            issue="forensic_outside_artifacts",
                            severity="low",
                            suggestion="Archive forensic assets under build/artifacts/forensic_hashes/legacy/ to declutter root.",
                        )
                    )
            elif "build/artifacts" not in str(forensic_dir):
                out.append(
                    Deviation(
                        path=str(forensic_dir.relative_to(self.repo_root)),
                        issue="forensic_outside_artifacts",
                        severity="low",
                        suggestion="Archive forensic assets under build/artifacts/forensic_hashes/legacy/ to declutter root.",
                    )
                )

        if build_logs.exists():
            external_logs = []
            for log_file in self.repo_root.rglob("*.log"):
                if build_logs in log_file.parents:
                    continue
                if log_file.is_symlink():
                    target = log_file.resolve()
                    if "build/artifacts" in str(target):
                        continue
                skip_bases = [
                    self.repo_root / "data",
                    self.repo_root / "build" / ".venv",
                    self.repo_root / "build" / "node_modules",
                    self.repo_root / "build" / "artifacts" / "models",
                ]
                if any(base in log_file.parents for base in skip_bases):
                    continue
                external_logs.append(log_file)
            if external_logs:
                sample = [str(p.relative_to(self.repo_root)) for p in external_logs[:5]]
                out.append(
                    Deviation(
                        path=",".join(sample),
                        issue="logs_scattered",
                        severity="low",
                        suggestion="Move scattered .log files into build/artifacts/logs/; keep forensic hashes only in artifacts/forensic_hashes.",
                    )
                )
        return out

    def _check_databases(self) -> List[Deviation]:
        out: List[Deviation] = []
        db_root = self.repo_root / "data" / "runtime"
        for db_file in self.repo_root.rglob("*.db"):
            if db_root in db_file.parents:
                continue
            out.append(
                Deviation(
                    path=str(db_file.relative_to(self.repo_root)),
                    issue="db_outside_runtime",
                    severity="high",
                    suggestion="Move DBs to data/runtime/; avoid duplicates.",
                )
            )
        return out

    def _check_operator_files(self) -> List[Deviation]:
        out: List[Deviation] = []

        # package.json vs lock coherence
        pkg = self.repo_root / "package.json"
        pkg_lock = self.repo_root / "package-lock.json"
        if pkg.exists() and pkg_lock.exists():
            try:
                with pkg.open("r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
                with pkg_lock.open("r", encoding="utf-8") as f:
                    pkg_lock_data = json.load(f)
                declared = set((pkg_data.get("devDependencies") or {}).keys())
                locked = set((pkg_lock_data.get("packages", {}).get("", {}).get("devDependencies") or {}).keys())
                if declared != locked:
                    out.append(
                        Deviation(
                            path="package.json",
                            issue="package_lock_mismatch",
                            severity="medium",
                            suggestion="Align package.json and package-lock.json devDependencies to avoid ghost installs.",
                        )
                    )
            except Exception as exc:
                out.append(
                    Deviation(
                        path="package.json",
                        issue="package_parse_error",
                        severity="medium",
                        suggestion=f"Failed to parse package files: {exc}",
                    )
                )

        # OPERATOR_MODE_AUDIT module paths
        operator_audit = self.repo_root / "OPERATOR_MODE_AUDIT.py"
        if operator_audit.exists():
            try:
                content = operator_audit.read_text(encoding="utf-8")
                if "switch/hermes" not in content:
                    out.append(
                        Deviation(
                            path="OPERATOR_MODE_AUDIT.py",
                            issue="operator_audit_outdated_paths",
                            severity="medium",
                            suggestion="Update hermes reference to switch/hermes per canonical v6.4.",
                        )
                    )
                if '"version": "6.4"' not in json.dumps(self.canonical):
                    out.append(
                        Deviation(
                            path="OPERATOR_MODE_AUDIT.py",
                            issue="operator_audit_version_mismatch",
                            severity="low",
                            suggestion="Ensure audit checks align with canonical version 6.4.",
                        )
                    )
            except Exception as exc:
                out.append(
                    Deviation(
                        path="OPERATOR_MODE_AUDIT.py",
                        issue="operator_audit_read_error",
                        severity="medium",
                        suggestion=f"Cannot inspect OPERATOR_MODE_AUDIT.py: {exc}",
                    )
                )
        return out


class AutoOrganizer:
    """Periodic scanner that emits intents to Madre."""

    def __init__(self, repo_root: Path = REPO_ROOT, madre_url: Optional[str] = None):
        self.repo_root = repo_root
        self.madre_url = (madre_url or settings.madre_url or f"http://madre:{settings.madre_port}").rstrip("/")
        self.auditor = OrderAuditor(repo_root)
        self._loop_task: Optional[asyncio.Task] = None
        self._running = False

    def build_intent(self, report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        deviations = report.get("deviations") or []
        if not deviations:
            return None
        severity = report.get("max_severity") or "low"
        return {
            "type": "organize",
            "severity": severity,
            "items": deviations,
            "timestamp": report.get("timestamp"),
            "canonical_version": report.get("canonical_version"),
        }

    async def scan_and_emit(self, emit: bool = True) -> Dict[str, Any]:
        report = self.auditor.scan()
        intent = self.build_intent(report)
        if emit and intent:
            await self._send_intent(intent)
        return {"report": report, "intent": intent}

    async def _send_intent(self, intent: Dict[str, Any]) -> None:
        try:
            token = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
            headers = {settings.token_header: token}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(f"{self.madre_url}/madre/organize", json=intent, headers=headers)
                if resp.status_code != 200:
                    logger.warning("organize_intent_rejected status=%s body=%s", resp.status_code, resp.text[:200])
                else:
                    logger.info("organize_intent_sent severity=%s items=%s", intent.get("severity"), len(intent.get("items", [])))
        except Exception as exc:
            logger.error("organize_intent_error:%s", exc)

    async def run_loop(self, interval_seconds: int = 300):
        if self._running:
            return
        self._running = True
        while self._running:
            try:
                await self.scan_and_emit(emit=True)
            except Exception as exc:
                logger.error("organizer_loop_error:%s", exc)
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()


def cli_once():
    """CLI entrypoint for one-off audit."""
    import argparse
    parser = argparse.ArgumentParser(description="VX11 order auditor (scan-only).")
    parser.add_argument("--emit", action="store_true", help="Send organize intent to Madre if drift detected.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    args = parser.parse_args()

    auditor = OrderAuditor()
    report = auditor.scan()
    intent = None
    if args.emit:
        intent = AutoOrganizer().build_intent(report)
        if intent:
            asyncio.run(AutoOrganizer()._send_intent(intent))
    if args.json:
        print(json.dumps({"report": report, "intent": intent}, indent=2))
    else:
        print(f"Deviations: {report['counts']['total']} (max severity: {report['max_severity']})")


if __name__ == "__main__":
    cli_once()
