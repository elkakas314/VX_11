#!/usr/bin/env python3
"""Helpers to detect CORE paths from docs/audit/CLEANUP_EXCLUDES_CORE.txt"""
import os
from pathlib import Path
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]
EXCLUDES_FILE = REPO_ROOT / "docs" / "audit" / "CLEANUP_EXCLUDES_CORE.txt"


def load_excludes():
    if not EXCLUDES_FILE.exists():
        return []
    with EXCLUDES_FILE.open("r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines


def is_core_path(p: str) -> bool:
    ppath = Path(p)
    if not ppath.is_absolute():
        ppath = (REPO_ROOT / ppath).resolve()
    else:
        ppath = ppath.resolve()
    for pat in load_excludes():
        cand = (
            (REPO_ROOT / pat).resolve()
            if not Path(pat).is_absolute()
            else Path(pat).resolve()
        )
        try:
            if str(ppath).startswith(str(cand)):
                return True
        except Exception:
            continue
    return False


def safe_move_py(src: str, dst: str):
    """Python wrapper for moving files with CORE-path protection."""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

    if is_core_path(src) or is_core_path(dst):
        raise RuntimeError(f"ABORT: move would touch CORE path. src={src} dst={dst}")
    safe_move_py(src, dst)


def safe_rm_py(target: str):
    """Python wrapper for removing files/dirs with CORE-path protection."""
    if is_core_path(target):
        raise RuntimeError(f"ABORT: rm would touch CORE path: {target}")
    p = Path(target)
    if p.is_dir():
        safe_rm_py(p)
    elif p.exists():
        p.unlink()
    # if doesn't exist, nothing to do


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(is_core_path(sys.argv[1]))
    else:
        print("Usage: cleanup_guard.py <path>")