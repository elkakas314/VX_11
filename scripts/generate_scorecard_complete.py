#!/usr/bin/env python3
"""Generate complete SCORECARD.json with all percentage metrics."""
import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_auditor_orden():
    """Get orden_fs_pct from auditor_orden_vx11.py"""
    try:
        result = subprocess.run(
            [sys.executable, "scripts/auditor_orden_vx11.py"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("orden_fs_pct")
    except Exception as e:
        print(f"[WARN] auditor_orden_vx11 failed: {e}", file=sys.stderr)
    return None


def run_coherencia_routing():
    """Get coherencia_routing_pct from calc_coherencia_routing.py"""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/calc_coherencia_routing.py",
                "--db",
                "data/runtime/vx11.db",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("coherencia_routing_pct")
    except Exception as e:
        print(f"[WARN] calc_coherencia_routing failed: {e}", file=sys.stderr)
    return None


def get_db_metrics():
    """Get DB size, row count, and integrity metrics."""
    db_path = REPO_ROOT / "data" / "runtime" / "vx11.db"
    metrics = {
        "size_bytes": 0,
        "total_rows": 0,
        "quick_check": "unknown",
        "integrity_check": "unknown",
        "foreign_key_check": "unknown",
    }

    if not db_path.exists():
        return metrics

    metrics["size_bytes"] = db_path.stat().st_size

    # Quick check
    try:
        result = subprocess.run(
            [
                "sqlite3",
                "-cmd",
                "PRAGMA busy_timeout=5000;",
                str(db_path),
                "PRAGMA quick_check;",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            metrics["quick_check"] = result.stdout.strip().split("\n")[-1]
    except Exception as e:
        print(f"[WARN] quick_check failed: {e}", file=sys.stderr)

    # Integrity check
    try:
        result = subprocess.run(
            [
                "sqlite3",
                "-cmd",
                "PRAGMA busy_timeout=5000;",
                str(db_path),
                "PRAGMA integrity_check;",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            metrics["integrity_check"] = result.stdout.strip().split("\n")[-1]
    except Exception as e:
        print(f"[WARN] integrity_check failed: {e}", file=sys.stderr)

    # Foreign key check
    try:
        result = subprocess.run(
            [
                "sqlite3",
                "-cmd",
                "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON;",
                str(db_path),
                "PRAGMA foreign_key_check;",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            metrics["foreign_key_check"] = (
                "ok" if not output else f"violations: {len(output.split(chr(10)))}"
            )
    except Exception as e:
        print(f"[WARN] foreign_key_check failed: {e}", file=sys.stderr)

    # Row count
    try:
        result = subprocess.run(
            [
                "sqlite3",
                str(db_path),
                "SELECT COUNT(*) FROM (SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%');",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            table_count = int(result.stdout.strip())
            metrics["total_tables"] = table_count
    except Exception as e:
        print(f"[WARN] table count failed: {e}", file=sys.stderr)

    return metrics


def get_canon_metrics():
    """Calculate canonicalization metric."""
    canon_dir = REPO_ROOT / "docs" / "canon"
    if not canon_dir.exists():
        return None

    canon_files = list(canon_dir.glob("*.json"))
    if not canon_files:
        return None

    valid_count = 0
    for cf in canon_files:
        try:
            with open(cf) as f:
                json.load(f)
            valid_count += 1
        except Exception:
            pass

    if len(canon_files) == 0:
        return None

    return round(100.0 * valid_count / len(canon_files), 4)


def build_complete_scorecard():
    """Build complete SCORECARD with all metrics."""
    scorecard = {
        "generated_ts": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        "db": get_db_metrics(),
        "order_fs_pct": run_auditor_orden(),
        "coherencia_routing_pct": run_coherencia_routing(),
        "automatizacion_pct": None,  # TODO: implement
        "autonomia_pct": None,  # TODO: implement
        "canonicalizacion_pct": get_canon_metrics(),
    }

    # Calculate global weighted percentage if enough metrics are available
    metrics = [
        scorecard.get("order_fs_pct"),
        scorecard.get("coherencia_routing_pct"),
        scorecard.get("canonicalizacion_pct"),
    ]
    available = [m for m in metrics if m is not None]
    if available:
        scorecard["global_ponderado_pct"] = round(sum(available) / len(available), 4)
    else:
        scorecard["global_ponderado_pct"] = None

    return scorecard


def main():
    scorecard = build_complete_scorecard()
    output_path = REPO_ROOT / "docs" / "audit" / "SCORECARD.json"

    with open(output_path, "w") as f:
        json.dump(scorecard, f, indent=2)

    print(f"✓ SCORECARD regenerated: {output_path}")
    print(json.dumps(scorecard, indent=2))


if __name__ == "__main__":
    main()
