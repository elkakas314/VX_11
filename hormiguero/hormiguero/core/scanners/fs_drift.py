"""Filesystem drift scanner."""

import json
import os
from typing import Dict, List, Optional, Set

from hormiguero.config import settings


def _should_ignore(path: str) -> bool:
    for ignore in settings.fs_ignore_dirs:
        if path == ignore or path.startswith(ignore + os.sep):
            return True
    return False


def _find_canonical_map(root: str) -> Optional[str]:
    docs_root = os.path.join(root, "docs")
    if not os.path.isdir(docs_root):
        return None
    candidates: List[str] = []
    for dirpath, _, filenames in os.walk(docs_root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir.startswith("docs/audit"):
            continue
        for name in filenames:
            if name.startswith("CANONICAL") and name.endswith(".json"):
                candidates.append(os.path.join(dirpath, name))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


def _load_canonical_paths(path: str) -> Set[str]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {p for p in data if isinstance(p, str)}
    if isinstance(data, dict):
        for key in ("paths", "files", "tree"):
            value = data.get(key)
            if isinstance(value, list):
                return {p for p in value if isinstance(p, str)}
    return set()


def _actual_paths(root: str) -> Set[str]:
    paths: Set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""
        if rel_dir and _should_ignore(rel_dir):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not _should_ignore(os.path.join(rel_dir, d))]
        for name in filenames:
            rel = os.path.join(rel_dir, name) if rel_dir else name
            if _should_ignore(rel):
                continue
            paths.add(rel)
    return paths


def scan_fs_drift(root: str) -> Dict[str, object]:
    canon_path = _find_canonical_map(root)
    if not canon_path:
        return {
            "status": "no_canon",
            "details": "CANONICAL*.json not found",
        }
    expected = _load_canonical_paths(canon_path)
    actual = _actual_paths(root)
    missing = sorted(list(expected - actual))[:200]
    extra = sorted(list(actual - expected))[:200]
    return {
        "status": "ok",
        "canonical_path": canon_path,
        "missing": missing,
        "extra": extra,
    }
