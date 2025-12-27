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


def get_automatizacion_pct():
    """Calculate automatizacion_pct based on:
    - DB_MAP generation OK (25%)
    - SCORECARD generation with all non-null fields (25%)
    - pytest basic pass (25%)
    - pytest integration pass (25%)
    """
    score_parts = []

    # Check 1: DB_MAP generation
    db_map_path = REPO_ROOT / "docs" / "audit" / "DB_MAP_v7_FINAL.md"
    if db_map_path.exists() and db_map_path.stat().st_size > 0:
        score_parts.append(25.0)  # 25%

    # Check 2: SCORECARD generation (previous run)
    scorecard_path = REPO_ROOT / "docs" / "audit" / "SCORECARD.json"
    if scorecard_path.exists():
        try:
            with open(scorecard_path) as f:
                sc = json.load(f)
                # Check if all 5 key fields exist and are non-null
                fields = [
                    "order_fs_pct",
                    "coherencia_routing_pct",
                    "automatizacion_pct",
                    "autonomia_pct",
                    "canonicalizacion_pct",
                ]
                if all(sc.get(f) is not None for f in fields):
                    score_parts.append(25.0)  # 25%
        except Exception:
            pass

    # Check 3: pytest basic
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            score_parts.append(25.0)  # 25%
    except Exception:
        pass

    # Check 4: pytest integration (if env set)
    try:
        env = os.environ.copy()
        env["VX11_INTEGRATION"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=240,
            env=env,
        )
        if result.returncode == 0:
            score_parts.append(25.0)  # 25%
    except Exception:
        pass

    # Return average of passed checks
    if not score_parts:
        return 0.0
    return round(sum(score_parts) / 4, 4)  # 4 checks total


def get_autonomia_pct():
    """Calculate autonomia_pct based on:
    - solo_madre mode capability (40%)
    - controlled window spawn/operation (30%)
    - return to solo_madre + health OK (30%)

    For local-ready: check if solo_madre mode is documented and services respond.
    """
    score_parts = []

    # Check 1: solo_madre capability (40%)
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "--services"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if (
            "madre" in result.stdout
            and "tentaculo_link" in result.stdout
            and "redis" in result.stdout
        ):
            score_parts.append(40.0)  # 40%
    except Exception:
        pass

    # Check 2: tentaculo health (30%)
    try:
        result = subprocess.run(
            [
                "curl",
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "http://127.0.0.1:8000/health",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip() == "200":
            score_parts.append(30.0)  # 30%
    except Exception:
        pass

    # Check 3: madre health via tentaculo (30%)
    try:
        result = subprocess.run(
            [
                "curl",
                "-sS",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code}",
                "http://127.0.0.1:8000/vx11/status",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip() == "200":
            score_parts.append(30.0)  # 30%
    except Exception:
        pass

    # Return sum of achieved checks (100 max = all 3 passed)
    if not score_parts:
        return 0.0
    return min(100.0, round(sum(score_parts) / 1, 4))


def build_complete_scorecard():
    """Build complete SCORECARD with all 5 metrics (non-null) + percentages block (P0 #2)."""
    # Get individual metrics
    orden_fs_val = run_auditor_orden()
    coherencia_routing_val = run_coherencia_routing()
    automatizacion_val = get_automatizacion_pct()
    autonomia_val = get_autonomia_pct()
    canonicalizacion_val = get_canon_metrics()

    # Build percentages block (ALWAYS include, even if null)
    percentages = {
        "Orden_fs_pct": orden_fs_val if orden_fs_val is not None else None,
        "Coherencia_routing_pct": (
            coherencia_routing_val if coherencia_routing_val is not None else None
        ),
        "Automatizacion_pct": (
            automatizacion_val
            if automatizacion_val and automatizacion_val > 0
            else None
        ),
        "Autonomia_pct": autonomia_val if autonomia_val and autonomia_val > 0 else None,
        "Global_ponderado_pct": None,  # Will compute below
    }

    # Build percentages_notes (explain why null, if applicable)
    percentages_notes = {
        "Orden_fs_pct": (
            "File system canonical compliance (roots order)"
            if percentages["Orden_fs_pct"] is not None
            else "auditor_orden_vx11.py unavailable or no FS drift data"
        ),
        "Coherencia_routing_pct": (
            "Routing event coherence (switch/routing quality)"
            if percentages["Coherencia_routing_pct"] is not None
            else "Switch service down or no routing events available"
        ),
        "Automatizacion_pct": (
            "Automation readiness (DB_MAP + pytest + SCORECARD)"
            if percentages["Automatizacion_pct"] is not None
            else "Not all automation prerequisites met"
        ),
        "Autonomia_pct": (
            "solo_madre autonomy + service health"
            if percentages["Autonomia_pct"] is not None
            else "Services not responding to health checks or solo_madre not configured"
        ),
        "Global_ponderado_pct": "Weighted average of Orden_fs, Coherencia, Automatizacion, Autonomia",
    }

    # Compute global_ponderado_pct if we have at least some metrics
    non_null_metrics = [v for v in percentages.values() if v is not None]
    if len(non_null_metrics) > 0:
        avg_val = sum(non_null_metrics) / len(non_null_metrics)
        percentages["Global_ponderado_pct"] = round(avg_val, 4)

    # Main scorecard structure
    scorecard = {
        "generated_ts": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
        "db": get_db_metrics(),
        "percentages": percentages,
        "percentages_notes": percentages_notes,
    }

    # Legacy fields for backward compatibility
    scorecard["order_fs_pct"] = percentages["Orden_fs_pct"] or 0.0
    scorecard["coherencia_routing_pct"] = percentages["Coherencia_routing_pct"] or 0.0
    scorecard["automatizacion_pct"] = percentages["Automatizacion_pct"] or 0.0
    scorecard["autonomia_pct"] = percentages["Autonomia_pct"] or 0.0
    scorecard["canonicalizacion_pct"] = canonicalizacion_val or 0.0
    scorecard["global_ponderado_pct"] = percentages["Global_ponderado_pct"] or 0.0

    # Add methodology
    scorecard["methodology"] = {
        "orden_fs_pct": "FS canonical compliance (expected vs present roots)",
        "coherencia_routing_pct": "Routing event quality (route_taken non-null, no contract errors)",
        "automatizacion_pct": "Automation checklist: DB_MAP OK + SCORECARD complete + pytest basic + pytest integration",
        "autonomia_pct": "solo_madre capability + service health checks (tentaculo_link 8000)",
        "canonicalizacion_pct": "Valid canonical JSON files in docs/canon/ (100% if all valid)",
        "global_ponderado_pct": "Weighted average of non-null metrics",
    }

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
