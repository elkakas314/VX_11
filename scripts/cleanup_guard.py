#!/usr/bin/env python3
"""Helpers to detect CORE paths from docs/audit/CLEANUP_EXCLUDES_CORE.txt"""
import os
from pathlib import Path

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


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(is_core_path(sys.argv[1]))
    else:
        print("Usage: cleanup_guard.py <path>")
