"""Allowlist enforcement for Hormiguero actions."""

import os
from typing import Tuple


ALLOWED_ACTIONS = {
    "cleanup_pycache",
    "move_duplicate",
    "manifestator_patch",
}


def _repo_root() -> str:
    env = os.getenv("HORMIGUERO_REPO_ROOT")
    if env:
        return os.path.abspath(env)
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "../../../../.."))


def _is_within(path: str, root: str) -> bool:
    abs_path = os.path.abspath(path)
    root = os.path.abspath(root)
    return abs_path == root or abs_path.startswith(root + os.sep)


def validate_action(action: str, target: str) -> Tuple[bool, str]:
    if action not in ALLOWED_ACTIONS:
        return False, "action_not_allowed"
    repo_root = _repo_root()
    if not _is_within(target, repo_root):
        return False, "outside_repo_root"
    if "forensic" in os.path.abspath(target).split(os.sep):
        return False, "forensic_protected"
    if action == "cleanup_pycache":
        if target.endswith(".pyc") or os.path.basename(target) == "__pycache__":
            return True, "ok"
        return False, "cleanup_pycache_requires_pyc_or___pycache__"
    if action == "move_duplicate":
        if "docs/audit/archived" in os.path.abspath(target):
            return True, "ok"
        return False, "move_duplicate_requires_docs_audit_archived"
    if action == "manifestator_patch":
        return True, "ok"
    return False, "unknown"
