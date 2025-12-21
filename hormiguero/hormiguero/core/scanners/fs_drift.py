"""Filesystem drift scanner."""

import json
import os
from fnmatch import fnmatch
from typing import Dict, List, Optional, Set, Tuple

try:
    from hormiguero.config import settings
except ModuleNotFoundError:
    from config import settings


def _should_ignore(path: str) -> bool:
    for ignore in settings.fs_ignore_dirs:
        if path == ignore or path.startswith(ignore + os.sep):
            return True
    return False


def _find_canonical_map(root: str) -> Optional[str]:
    docs_root = os.path.join(root, "docs")
    if not os.path.isdir(docs_root):
        return None
    target = os.path.join(docs_root, "CANONICAL_TARGET_FS_VX11.json")
    snapshot = os.path.join(docs_root, "CANONICAL_FS_VX11.json")
    if os.path.isfile(target):
        return target
    if os.path.isfile(snapshot):
        return snapshot
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


def _load_canonical_spec(path: str) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {
            "mode": "paths",
            "paths": {p for p in data if isinstance(p, str)},
            "ignore_globs": [],
        }
    if isinstance(data, dict):
        ignore_globs = data.get("ignore_globs", [])
        if not isinstance(ignore_globs, list):
            ignore_globs = []
        for key in ("paths", "files", "tree"):
            value = data.get(key)
            if isinstance(value, list):
                return {
                    "mode": "paths",
                    "paths": {p for p in value if isinstance(p, str)},
                    "ignore_globs": [g for g in ignore_globs if isinstance(g, str)],
                }
        roots = data.get("allowed_roots")
        if isinstance(roots, list):
            return {
                "mode": "roots",
                "roots": [r for r in roots if isinstance(r, str)],
                "ignore_globs": [g for g in ignore_globs if isinstance(g, str)],
            }
    return {"mode": "paths", "paths": set(), "ignore_globs": []}


def _path_under_roots(path: str, roots: List[str]) -> bool:
    for root in roots:
        if path == root or path.startswith(root + os.sep):
            return True
    return False


def _matches_ignore(path: str, ignore_globs: List[str]) -> bool:
    if not ignore_globs:
        return False
    for pattern in ignore_globs:
        if fnmatch(path, pattern):
            return True
    return False


def _actual_paths(root: str, ignore_globs: List[str]) -> Set[str]:
    paths: Set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""
        if rel_dir and _should_ignore(rel_dir):
            dirnames[:] = []
            continue
        dirnames[:] = [
            d
            for d in dirnames
            if not _should_ignore(os.path.join(rel_dir, d))
            and not _matches_ignore(os.path.join(rel_dir, d) if rel_dir else d, ignore_globs)
        ]
        for name in filenames:
            rel = os.path.join(rel_dir, name) if rel_dir else name
            if _should_ignore(rel) or _matches_ignore(rel, ignore_globs):
                continue
            paths.add(rel)
    return paths


def _root_entries(root: str, ignore_globs: List[str]) -> Tuple[List[str], List[str]]:
    entries = []
    ignored = []
    for name in os.listdir(root):
        if name in {".git"}:
            continue
        full = os.path.join(root, name)
        if not os.path.isdir(full):
            continue
        if _matches_ignore(name, ignore_globs):
            ignored.append(name)
            continue
        entries.append(name)
    return sorted(entries), sorted(ignored)


def scan_fs_drift(root: str) -> Dict[str, object]:
    canon_path = _find_canonical_map(root)
    if not canon_path:
        return {
            "status": "no_canon",
            "details": "CANONICAL*.json not found",
        }
    spec = _load_canonical_spec(canon_path)
    ignore_globs = spec.get("ignore_globs", [])
    actual = _actual_paths(root, ignore_globs)
    if spec.get("mode") == "roots":
        roots = spec.get("roots", [])
        root_entries, ignored_roots = _root_entries(root, ignore_globs)
        missing_roots = [r for r in roots if not os.path.exists(os.path.join(root, r))]
        extra_roots = [r for r in root_entries if r not in roots]
        return {
            "status": "ok",
            "canonical_used": canon_path,
            "mode": "roots",
            "missing_roots": sorted(missing_roots)[:200],
            "extra_roots": sorted(extra_roots)[:200],
            "ignored_roots": ignored_roots[:200],
        }
    expected = spec.get("paths", set())
    expected = {p for p in expected if not _matches_ignore(p, ignore_globs)}
    missing = sorted(list(expected - actual))[:200]
    extra = sorted(list(actual - expected))[:200]
    return {
        "status": "ok",
        "canonical_used": canon_path,
        "mode": "paths",
        "missing": missing,
        "extra": extra,
        "ignored_roots": _root_entries(root, ignore_globs)[1][:200],
    }
