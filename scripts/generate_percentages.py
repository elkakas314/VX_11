#!/usr/bin/env python3
"""
Generate PERCENTAGES v9 (100% evidence-driven, explicit NV/deferred handling)

Usage:
    python3 scripts/generate_percentages.py \
        --outdir docs/audit/20251222T113034Z_autonomy_evidence \
        --write-root

v9 Features:
- Every metric is an OBJECT: {value, status, source, evidence_path, calculation, reason}
- status ∈ {ok, fail, NV, deferred}
- New formula: 0.35*health + 0.30*tests + 0.25*coherence + 0.10*db (weights sum to 1.0)
- Invariant: health=100, coherence=100, db=100, tests=0 => Estabilidad=70.0 EXACT
- evidence_coverage_pct: dual (strict + overall)
- metrics_flat: for backwards compatibility
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import sqlite3

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_json(fpath: Path) -> Optional[Dict]:
    """Load JSON file safely."""
    if not fpath.exists():
        return None
    try:
        with open(fpath) as f:
            return json.load(f)
    except Exception as e:
        print(f"WARN: Failed to load {fpath}: {e}", file=sys.stderr)
        return None


def count_health_services(health_results: Optional[Dict]) -> Tuple[int, int]:
    """Parse health_results.json and count ok services.

    Format: {service_name: {port, status, returncode}, ...}
    """
    if not health_results:
        return 0, 0

    ok_count = sum(
        1
        for svc_data in health_results.values()
        if isinstance(svc_data, dict) and svc_data.get("status") == "ok"
    )
    total = len(health_results)
    return ok_count, total


def compute_health_core_pct(
    health_results: Optional[Dict], evidence_path: Optional[str]
) -> Dict[str, Any]:
    """Compute health_core_pct from health_results.json"""
    if not health_results:
        return {
            "value": None,
            "status": "NV",
            "source": "health_results.json",
            "evidence_path": evidence_path,
            "calculation": "ERROR: health_results.json missing",
            "reason": "health_results.json not found in OUTDIR",
        }

    ok_count, total = count_health_services(health_results)
    pct = round((ok_count / total * 100) if total > 0 else 0.0, 2)

    return {
        "value": pct,
        "status": "ok",
        "source": "health_results.json",
        "evidence_path": evidence_path,
        "calculation": f"{ok_count}/{total} services ok => {ok_count}/{total}*100 = {pct}",
        "details": {
            "healthy": ok_count,
            "total": total,
        },
    }


def count_flows_passed(e2e_flows: Optional[list]) -> Tuple[int, int]:
    """Parse e2e_flows.json and count passed flows.

    Format: [{name, steps: [...], overall_success: bool}, ...]
    """
    if not e2e_flows:
        return 0, 0
    passed = sum(
        1 for f in e2e_flows if isinstance(f, dict) and f.get("overall_success") is True
    )
    total = len(e2e_flows)
    return passed, total


def compute_contract_coherence_pct(
    e2e_flows: Optional[list], evidence_path: Optional[str]
) -> Dict[str, Any]:
    """Compute contract_coherence_pct from e2e_flows.json (array of flows)"""
    if not e2e_flows:
        return {
            "value": None,
            "status": "NV",
            "source": "e2e_flows.json",
            "evidence_path": evidence_path,
            "calculation": "ERROR: e2e_flows.json missing",
            "reason": "e2e_flows.json not found in OUTDIR",
        }

    passed, total = count_flows_passed(e2e_flows)
    pct = round((passed / total * 100) if total > 0 else 0.0, 2)

    return {
        "value": pct,
        "status": "ok",
        "source": "e2e_flows.json",
        "evidence_path": evidence_path,
        "calculation": f"{passed}/{total} flows passed => {passed}/{total}*100 = {pct}",
        "details": {
            "passed": passed,
            "total": total,
        },
    }


def compute_tests_p0_pct(
    pytest_summary: Optional[Dict], evidence_path: Optional[str]
) -> Dict[str, Any]:
    """
    Compute tests_p0_pct.

    Rule: If VX11_INTEGRATION not run (tests skipped), status=deferred (not NV), value=0.0
    """
    if not pytest_summary:
        return {
            "value": 0.0,
            "status": "deferred",
            "source": "pytest_summary.json",
            "evidence_path": evidence_path,
            "calculation": "0 tests executed (VX11_INTEGRATION=1 not set)",
            "reason": "Integration tests skipped by default. Set VX11_INTEGRATION=1 to enable.",
        }

    passed = pytest_summary.get("passed", 0)
    failed = pytest_summary.get("failed", 0)
    total = passed + failed

    if total == 0:
        return {
            "value": 0.0,
            "status": "deferred",
            "source": "pytest_summary.json",
            "evidence_path": evidence_path,
            "calculation": "0 tests executed (VX11_INTEGRATION=1 not set)",
            "reason": "Integration tests skipped by default. Set VX11_INTEGRATION=1 to enable.",
            "details": {
                "passed": 0,
                "failed": 0,
                "total": 0,
            },
        }

    pct = round((passed / total * 100) if total > 0 else 0.0, 2)
    return {
        "value": pct,
        "status": "ok",
        "source": "pytest_summary.json",
        "evidence_path": evidence_path,
        "calculation": f"{passed}/{total} tests passed => {passed}/{total}*100 = {pct}",
        "details": {
            "passed": passed,
            "failed": failed,
            "total": total,
        },
    }


def compute_db_integrity_pct(db_path: Optional[Path]) -> Dict[str, Any]:
    """
    Compute db_integrity_pct from sqlite3 checks.

    If db checks not yet automated in runner, return deferred.
    """
    if not db_path or not db_path.exists():
        return {
            "value": None,
            "status": "deferred",
            "source": "db_integrity",
            "evidence_path": None,
            "calculation": "pending automation in runner",
            "reason": "DB integrity checks (PRAGMA integrity_check, PRAGMA foreign_key_check) not yet automated. Manual validation available.",
            "details": {"note": "See docs/audit/ for last manual audit trail"},
        }

    # Try to run PRAGMA checks (quick validation)
    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        cursor = conn.cursor()

        # Quick check
        cursor.execute("PRAGMA quick_check;")
        quick_result = cursor.fetchall()

        # Integrity check
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchall()

        conn.close()

        # If any error other than "ok", fail. Guard against empty results.
        combined = quick_result + integrity_result
        is_ok = len(combined) > 0 and all(
            (row[0] if isinstance(row, tuple) else row) == "ok"
            for row in combined
        )
        return {
            "value": 100.0 if is_ok else 0.0,
            "status": "ok",
            "source": "db_integrity",
            "evidence_path": str(db_path),
            "calculation": (
                "PRAGMA quick_check + PRAGMA integrity_check passed"
                if is_ok
                else "PRAGMA check failed"
            ),
            "details": {
                "quick_check": (
                    "ok" if len(quick_result) > 0 and all(r[0] == "ok" for r in quick_result) else "error"
                ),
                "integrity_check": (
                    "ok" if len(integrity_result) > 0 and all(r[0] == "ok" for r in integrity_result) else "error"
                ),
            },
        }
    except Exception as e:
        return {
            "value": None,
            "status": "deferred",
            "source": "db_integrity",
            "evidence_path": str(db_path),
            "calculation": f"error: {str(e)}",
            "reason": f"DB check failed: {str(e)}. Retry or see manual audit.",
        }


def compute_estabilidad_operativa_pct(
    health_pct: Optional[float],
    tests_pct: Optional[float],
    coherence_pct: Optional[float],
    db_pct: Optional[float],
) -> Dict[str, Any]:
    """
    Compute Estabilidad_operativa_pct using NEW formula v9:
    Estabilidad = 0.35*health + 0.30*tests + 0.25*coherence + 0.10*db

    Weights sum to 1.0. If any value None, use 0 for computation.
    Invariant: health=100, coherence=100, db=100, tests=0 => Estabilidad=70.0 EXACT
    Note: Deferred/NV metrics are treated as 0.0 in weighted sum (contributing 0, defensive strategy).
    """
    # Use 0 for deferred/NV metrics in calculation (so they don't penalize)
    h = health_pct if health_pct is not None else 0.0
    t = tests_pct if tests_pct is not None else 0.0
    c = coherence_pct if coherence_pct is not None else 0.0
    d = db_pct if db_pct is not None else 0.0

    estabilidad = round(0.35 * h + 0.30 * t + 0.25 * c + 0.10 * d, 2)

    return {
        "value": estabilidad,
        "status": "ok",
        "source": "derived",
        "evidence_path": None,
        "calculation": f"0.35*{h} + 0.30*{t} + 0.25*{c} + 0.10*{d} = {estabilidad}",
        "weights": {
            "health_core": 0.35,
            "tests_p0": 0.30,
            "contract_coherence": 0.25,
            "db_integrity": 0.10,
        },
        "inputs": {
            "health_core_pct": health_pct,
            "tests_p0_pct": tests_pct,
            "contract_coherence_pct": coherence_pct,
            "db_integrity_pct": db_pct,
        },
    }


def compute_evidence_coverage_pct(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute evidence_coverage_pct DUAL (strict + overall).

    coverage_strict: only metrics with source != 'derived' and status not in ['NV', 'deferred']
    coverage_overall: all metrics where status not in ['NV', 'deferred']
    """
    all_p0 = list(metrics.keys())
    total = len(all_p0)

    # Strict: real evidence only
    strict_count = sum(
        1
        for m_name, m_obj in metrics.items()
        if isinstance(m_obj, dict)
        and m_obj.get("source") != "derived"
        and m_obj.get("status") not in ["NV", "deferred"]
    )

    # Overall: derived ok, but exclude deferred/NV
    overall_count = sum(
        1
        for m_obj in metrics.values()
        if isinstance(m_obj, dict) and m_obj.get("status") not in ["NV", "deferred"]
    )

    strict_pct = round((strict_count / total * 100) if total > 0 else 0.0, 2)
    overall_pct = round((overall_count / total * 100) if total > 0 else 0.0, 2)

    return {
        "value": overall_pct,  # Primary metric is overall
        "status": "ok",
        "source": "derived",
        "evidence_path": None,
        "calculation": f"coverage_overall: {overall_count}/{total}*100 = {overall_pct}%",
        "coverage_strict": {
            "value": strict_pct,
            "calculation": f"{strict_count}/{total} real evidence (no derived/deferred) = {strict_pct}%",
            "count": strict_count,
        },
        "coverage_overall": {
            "value": overall_pct,
            "calculation": f"{overall_count}/{total} ok or derived ok (no NV/deferred) = {overall_pct}%",
            "count": overall_count,
        },
    }


def generate_percentages_v9(
    outdir: Path, db_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate PERCENTAGES v9 from evidence in outdir.
    """
    # Resolve paths
    evidence_path_health = str(outdir / "health_results.json")
    evidence_path_flows = str(outdir / "e2e_flows.json")
    evidence_path_tests = str(outdir / "pytest_summary.json")

    # Load evidence files
    health_results = load_json(outdir / "health_results.json")
    e2e_flows = load_json(outdir / "e2e_flows.json")
    pytest_summary = load_json(outdir / "pytest_summary.json")

    # If db_path not provided, try default
    if db_path is None:
        db_path = REPO_ROOT / "data" / "runtime" / "vx11.db"

    # Compute metrics
    health_metric = compute_health_core_pct(health_results, evidence_path_health)
    coherence_metric = compute_contract_coherence_pct(e2e_flows, evidence_path_flows)
    tests_metric = compute_tests_p0_pct(pytest_summary, evidence_path_tests)
    db_metric = compute_db_integrity_pct(db_path)

    # Build metrics dict
    metrics_dict = {
        "health_core_pct": health_metric,
        "contract_coherence_pct": coherence_metric,
        "tests_p0_pct": tests_metric,
        "db_integrity_pct": db_metric,
    }

    # Compute derived metrics
    estabilidad_metric = compute_estabilidad_operativa_pct(
        health_pct=health_metric.get("value"),
        tests_pct=tests_metric.get("value"),
        coherence_pct=coherence_metric.get("value"),
        db_pct=db_metric.get("value"),
    )
    metrics_dict["Estabilidad_operativa_pct"] = estabilidad_metric

    # Evidence coverage
    coverage_metric = compute_evidence_coverage_pct(metrics_dict)
    metrics_dict["evidence_coverage_pct"] = coverage_metric

    # Build metrics_flat for backwards compat
    metrics_flat = {k: v.get("value") for k, v in metrics_dict.items()}

    # Determine autonomy verdict
    estab_val = estabilidad_metric.get("value", 0)
    health_val = health_metric.get("value", 0)
    all_flows = coherence_metric.get("value", 0) == 100

    if (
        estab_val >= 75
        and coverage_metric["coverage_strict"]["value"] >= 50
        and health_val >= 90
    ):
        verdict = "OPERATIONAL"
    elif estab_val >= 50 and health_val >= 80:
        verdict = "DEGRADED"
    else:
        verdict = "CRITICAL"

    # Final JSON structure (v9 canonical)
    result = {
        "version": "9.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outdir": str(outdir),
        "audit_context": {
            "input_sources": [
                evidence_path_health,
                evidence_path_flows,
                evidence_path_tests,
                str(db_path) if db_path else "N/A",
            ],
            "evidence_complete": health_results is not None and e2e_flows is not None,
            "reason_incomplete": (
                "Missing evidence files" if not (health_results and e2e_flows) else None
            ),
        },
        "metrics": metrics_dict,
        "metrics_flat": metrics_flat,
        "autonomy_verdict": {
            "status": verdict,
            "decision_logic": {
                "Estabilidad_value": estab_val,
                "Estabilidad_threshold": f"{estab_val} >= 75.0? → {estab_val >= 75}",
                "coverage_strict_check": f"{coverage_metric['coverage_strict']['value']} >= 50%? → {coverage_metric['coverage_strict']['value'] >= 50}",
                "health_services_check": f"{health_val}% healthy → {health_val >= 90}",
                "all_flows_pass": all_flows,
                "db_integrity_status": db_metric.get("status"),
            },
        },
        "validation_checksums": {
            "invariant_check_100_0_100_100": (
                f"{estab_val} (should be 70.0)"
                if health_val == 100
                and tests_metric.get("value") == 0.0
                and coherence_metric.get("value") == 100
                and db_metric.get("value") == 100
                else "N/A"
            ),
            "weights_sum": "1.0 (0.35 + 0.30 + 0.25 + 0.10)",
            "p0_metrics_count": len(metrics_dict),
        },
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate PERCENTAGES v9 from autonomy evidence (100% evidence-driven)"
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        help="Path to evidence directory (with health_results.json, e2e_flows.json, pytest_summary.json)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to vx11.db (optional, defaults to data/runtime/vx11.db)",
    )
    parser.add_argument(
        "--write-root",
        action="store_true",
        help="Also write to docs/audit/PERCENTAGES.json (canonical root)",
    )

    args = parser.parse_args()

    # If no outdir, find the most recent autonomy evidence directory
    if args.outdir is None:
        audit_dir = REPO_ROOT / "docs" / "audit"
        evidence_dirs = sorted(
            [
                d
                for d in audit_dir.iterdir()
                if d.is_dir() and "_autonomy_evidence" in d.name
            ],
            reverse=True,
        )
        if not evidence_dirs:
            print(
                "ERROR: No evidence directory found. Provide --outdir or run evidence runner first.",
                file=sys.stderr,
            )
            sys.exit(2)
        args.outdir = evidence_dirs[0]
        print(f"[INFO] Using latest evidence dir: {args.outdir}", file=sys.stderr)

    # Validate outdir
    if not args.outdir.exists():
        print(f"ERROR: outdir not found: {args.outdir}", file=sys.stderr)
        sys.exit(1)

    # Ensure evidence files exist
    if not (args.outdir / "health_results.json").exists():
        print(f"ERROR: health_results.json not found in {args.outdir}", file=sys.stderr)
        sys.exit(2)
    if not (args.outdir / "e2e_flows.json").exists():
        print(f"ERROR: e2e_flows.json not found in {args.outdir}", file=sys.stderr)
        sys.exit(2)

    # Generate v9
    percentages_v9 = generate_percentages_v9(args.outdir, args.db_path)

    # Write to outdir/PERCENTAGES.json
    out_json = args.outdir / "PERCENTAGES.json"
    with open(out_json, "w") as f:
        json.dump(percentages_v9, f, indent=2)
    print(f"✓ Written: {out_json}", file=sys.stderr)

    # Write canonical root if requested
    if args.write_root:
        root_json = Path(REPO_ROOT) / "docs" / "audit" / "PERCENTAGES.json"
        with open(root_json, "w") as f:
            json.dump(percentages_v9, f, indent=2)
        print(f"✓ Written (root): {root_json}", file=sys.stderr)

    # Output JSON to stdout for verification
    print(json.dumps(percentages_v9, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
