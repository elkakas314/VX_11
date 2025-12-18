#!/usr/bin/env python3
"""Run select provider and scoring/breaker tests directly (no pytest)."""
import runpy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def run_module_tests(module_path: str):
    spec = runpy.run_path(module_path, run_name="__main__")


if __name__ == "__main__":
    tests = [
        "tests/test_switch_scoring_breaker.py",
        "tests/test_hermes_registry_db.py",
        "tests/test_hermes_cli_registry_module.py",
        "tests/test_switch_registry_enqueue.py",
    ]
    failures = []
    for t in tests:
        path = REPO_ROOT / t
        print(f"Running {t}...")
        try:
            exec(compile(path.read_text(), str(path), "exec"), {})
            print(f"TEST PASS: {t}")
        except Exception as e:
            print(f"TEST FAIL: {t}: {e}")
            failures.append((t, str(e)))

    if failures:
        print("Some tests failed:")
        for f in failures:
            print(f)
        raise SystemExit(1)
    else:
        print("All tests passed")
from scripts.cleanup_guard import safe_move_py, safe_rm_py
