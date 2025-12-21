"""Action preview/apply with guardrails."""

import os
import shutil
from typing import Dict, List, Optional

try:
    from hormiguero.config import settings
    from hormiguero.core.actions.allowlist import validate_action
    from hormiguero.core.db import repo
except ModuleNotFoundError:
    from config import settings
    from core.actions.allowlist import validate_action
    from core.db import repo


def preview_actions(actions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    results = []
    for item in actions:
        action = item.get("action", "")
        target = item.get("target", "")
        allowed, reason = validate_action(action, target)
        results.append({"action": action, "target": target, "allowed": allowed, "reason": reason})
    return results


def _cleanup_target(path: str) -> Dict[str, str]:
    if os.path.isdir(path) and os.path.basename(path) == "__pycache__":
        shutil.rmtree(path, ignore_errors=False)
        return {"status": "ok", "detail": "dir_removed"}
    if os.path.isfile(path) and path.endswith(".pyc"):
        os.remove(path)
        return {"status": "ok", "detail": "file_removed"}
    return {"status": "skipped", "detail": "not_pyc"}


def apply_actions(
    actions: List[Dict[str, str]],
    correlation_id: Optional[str] = None,
) -> Dict[str, object]:
    if not settings.actions_enabled:
        return {"status": "denied", "reason": "HORMIGUERO_ACTIONS_ENABLED=0"}
    if not correlation_id:
        return {"status": "denied", "reason": "missing_correlation_id"}
    approval = repo.approval_status(correlation_id)
    if approval != "approved":
        return {"status": "denied", "reason": "approval_not_found"}

    results = []
    for item in actions:
        action = item.get("action", "")
        target = item.get("target", "")
        allowed, reason = validate_action(action, target)
        if not allowed:
            results.append({"action": action, "target": target, "status": "denied", "reason": reason})
            continue
        if action == "cleanup_pycache":
            try:
                outcome = _cleanup_target(target)
            except Exception as exc:
                outcome = {"status": "error", "detail": str(exc)}
            results.append({"action": action, "target": target, **outcome})
        elif action == "manifestator_patch":
            results.append({"action": action, "target": target, "status": "denied", "reason": "use_manifestator"})
        else:
            results.append({"action": action, "target": target, "status": "denied", "reason": "unsupported_apply"})
    return {"status": "ok", "results": results}
