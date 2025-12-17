"""Auto patch builder for anti-caos intents.

Generates a minimal patch plan from an "organize" intent emitted by Hormiguero.
Operations are non-destructive and prefer moving into backups/legacy buckets.
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config.settings import settings


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = REPO_ROOT / "docs" / "VX11_v6.4_CANONICAL.json"


def _ensure_deepseek_env(repo_root: Path = REPO_ROOT) -> bool:
    """Load DEEPSEEK_API_KEY from tokens.env if not already exported."""
    if os.environ.get("DEEPSEEK_API_KEY"):
        return True
    env_path = repo_root / "tokens.env"
    if not env_path.exists():
        return False

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key == "DEEPSEEK_API_KEY" and value.strip():
                os.environ.setdefault("DEEPSEEK_API_KEY", value.strip().strip('"').strip("'"))
                return True
    except Exception:
        return False
    return False


class PatchBuilder:
    """Translate organize intents into patch operations."""

    def __init__(self, repo_root: Path = REPO_ROOT, canonical_path: Path = CANONICAL_PATH):
        self.repo_root = repo_root
        self.canonical_path = canonical_path
        self.canonical = self._load_canonical()
        _ensure_deepseek_env(repo_root)  # prepare DeepSeek R1 if needed by callers

    def _load_canonical(self) -> Dict[str, Any]:
        try:
            with self.canonical_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _resolve_path(self, path_str: str) -> Optional[Path]:
        try:
            candidate = Path(path_str)
            if not candidate.is_absolute():
                candidate = self.repo_root / candidate
            return candidate.resolve()
        except Exception:
            return None

    def build_patch(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        items = intent.get("items") or []
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_root = self.repo_root / "build" / "artifacts" / "backups" / timestamp
        operations: List[Dict[str, Any]] = []
        unresolved: List[Dict[str, Any]] = []

        for item in items:
            issue = item.get("issue")
            path_str = item.get("path")
            if not path_str:
                continue
            path = self._resolve_path(path_str.split(",")[0])  # first entry if multiple
            if not path:
                unresolved.append({"path": path_str, "issue": issue or "unknown", "reason": "unresolvable_path"})
                continue

            if issue == "logs_outside_artifacts":
                target = self.repo_root / "build" / "artifacts" / "logs" / "legacy_root" / path.name
                operations.append(self._move_op(path, target))
            elif issue == "sandbox_outside_artifacts":
                target = self.repo_root / "build" / "artifacts" / "sandbox" / "legacy_root" / path.name
                operations.append(self._move_op(path, target))
            elif issue == "forensic_outside_artifacts":
                target = self.repo_root / "build" / "artifacts" / "forensic_hashes" / "legacy" / path.name
                operations.append(self._move_op(path, target))
            elif issue == "doc_outside_archive":
                target = self.repo_root / "docs" / "archive" / path.name
                operations.append(self._move_op(path, target))
            elif issue in {"untracked_root_dir", "untracked_root_file"}:
                target = backup_root / "root_stray" / path.relative_to(self.repo_root)
                operations.append(self._move_op(path, target))
            elif issue == "logs_scattered":
                unresolved.append({"path": path_str, "issue": issue, "reason": "requires manual selection"})
            elif issue == "operator_audit_outdated_paths":
                operations.append(
                    {
                        "op": "edit_replace",
                        "file": str((self.repo_root / "OPERATOR_MODE_AUDIT.py").resolve()),
                        "search": "hermes",
                        "replace": "switch/hermes",
                        "max_replacements": 1,
                    }
                )
            else:
                unresolved.append({"path": path_str, "issue": issue or "unknown", "reason": "no_automatic_fix"})

        patch = {
            "intent": intent,
            "generated_at": timestamp,
            "backup_root": str(backup_root),
            "operations": operations,
            "unresolved": unresolved,
            "canonical_version": self.canonical.get("version"),
        }
        return patch

    @staticmethod
    def _move_op(src: Path, dst: Path) -> Dict[str, Any]:
        return {"op": "mv", "from": str(src), "to": str(dst)}
