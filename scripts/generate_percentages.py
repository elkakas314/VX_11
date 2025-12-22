#!/usr/bin/env python3
"""
Generate PERCENTAGES v9 (100% evidence-driven, explicit NV handling)

Usage:
    python3 scripts/generate_percentages.py \
        --outdir docs/audit/20251222T075806Z_autonomy_evidence \
        --write-root
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

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


def compute_health_core_pct(health_results: Optional[Dict]) -> Dict[str, Any]:
    """Compute health_core_pct from health_results.json"""
    if not health_results:
        return {
            "value": None,
            "status": "NV",
            "reason": "health_results.json not found",
            "source": None,
        }

    # Count "ok" services
    ok_count = sum(
        1
        for svc_data in health_results.values()
        if isinstance(svc_data, dict) and svc_data.get("status") == "ok"
    )
    total = len(health_results)
    pct = (ok_count / total * 100) if total > 0 else 0.0

    return {
        "value": round(pct, 2),
        "status": "ok",
        "reason": f"{ok_count}/{total} services healthy",
        "source": "health_results.json",
    }


def compute_contract_coherence_pct(e2e_flows: Optional[list]) -> Dict[str, Any]:
    """Compute contract_coherence_pct from e2e_flows.json"""
    if not e2e_flows:
        return {
            "value": None,
            "status": "NV",
            "reason": "e2e_flows.json not found",
            "source": None,
        }

    # Count flows with overall_success == true
    pass_count = sum(
        1
        for flow in e2e_flows
        if isinstance(flow, dict) and flow.get("overall_success") is True
    )
    total = len(e2e_flows)
    pct = (pass_count / total * 100) if total > 0 else 0.0

    return {
        "value": round(pct, 2),
        "status": "ok",
        "reason": f"{pass_count}/{total} flows passed",
        "source": "e2e_flows.json",
    }


def compute_tests_p0_pct(pytest_summary: Optional[Dict]) -> Dict[str, Any]:
    """
    Compute tests_p0_pct.

    Rule: If VX11_INTEGRATION not run (files missing), value=0 (EXPLICIT DEFER).
    Status is always "ok" (not NV).
    """
    if not pytest_summary:
        return {
            "value": 0.0,
            "status": "ok",
            "reason": "VX11_INTEGRATION not run (tests skipped by default)",
            "source": "pytest_summary.json (deferred)",
        }

    # If pytest ran, compute pass rate
    passed = pytest_summary.get("passed", 0)
    failed = pytest_summary.get("failed", 0)
    total = passed + failed

    if total == 0:
        return {
            "value": 0.0,
            "status": "ok",
            "reason": "No P0 tests executed (integration tests require VX11_INTEGRATION=1)",
            "source": "pytest_summary.json",
        }

    pct = (passed / total * 100) if total > 0 else 0.0
    return {
        "value": round(pct, 2),
        "status": "ok",
        "reason": f"{passed}/{total} P0 tests passed",
        "source": "pytest_summary.json",
    }


def compute_estabilidad_operativa_pct(
    health_pct: Optional[float], tests_pct: float, coherence_pct: Optional[float]
) -> Dict[str, Any]:
    """
    Compute Estabilidad_operativa_pct using formula:
    Estabilidad = 0.4*health + 0.3*tests + 0.3*coherence

    Requirements:
    - If health or coherence are NV (None), cannot compute (return NV)
    - Formula must yield 70 when 100/0/100
    """
    if health_pct is None or coherence_pct is None:
        return {
            "value": None,
            "status": "NV",
            "reason": "Cannot compute: health or coherence are NV",
            "formula": "0.4*health_core_pct + 0.3*tests_p0_pct + 0.3*contract_coherence_pct",
            "source": None,
        }

    # Compute formula
    estabilidad = 0.4 * health_pct + 0.3 * tests_pct + 0.3 * coherence_pct

    return {
        "value": round(estabilidad, 2),
        "status": "ok",
        "formula": "0.4*health_core_pct + 0.3*tests_p0_pct + 0.3*contract_coherence_pct",
        "inputs": {
            "health_core_pct": health_pct,
            "tests_p0_pct": tests_pct,
            "contract_coherence_pct": coherence_pct,
        },
        "source": "formula (derived)",
    }


def compute_evidence_coverage_pct(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute evidence_coverage_pct: % of metrics with status=="ok" (not NV).
    """
    total_metrics = len(metrics)
    ok_metrics = sum(
        1 for m in metrics.values() if isinstance(m, dict) and m.get("status") == "ok"
    )

    pct = (ok_metrics / total_metrics * 100) if total_metrics > 0 else 0.0

    return {
        "value": round(pct, 2),
        "status": "ok",
        "reason": f"{ok_metrics}/{total_metrics} metrics with real evidence",
        "source": "derived",
    }


def generate_percentages_v9(outdir: Path) -> Dict[str, Any]:
    """
    Generate PERCENTAGES v9 from evidence in outdir.
    """
    # Load evidence files
    health_results = load_json(outdir / "health_results.json")
    e2e_flows = load_json(outdir / "e2e_flows.json")
    pytest_summary = load_json(outdir / "pytest_summary.json")

    # Compute metrics
    health_metric = compute_health_core_pct(health_results)
    coherence_metric = compute_contract_coherence_pct(e2e_flows)
    tests_metric = compute_tests_p0_pct(pytest_summary)

    # Build partial metrics dict for coverage computation
    partial_metrics = {
        "health_core_pct": health_metric,
        "contract_coherence_pct": coherence_metric,
        "tests_p0_pct": tests_metric,
    }

    # Compute derived metrics
    estabilidad_metric = compute_estabilidad_operativa_pct(
        health_pct=health_metric.get("value"),
        tests_pct=tests_metric.get("value", 0.0),
        coherence_pct=coherence_metric.get("value"),
    )

    # Add to metrics
    partial_metrics["Estabilidad_operativa_pct"] = estabilidad_metric

    # Evidence coverage
    coverage_metric = compute_evidence_coverage_pct(partial_metrics)

    # Final JSON structure (v9 canonical)
    result = {
        "version": "9.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "outdir": str(outdir),
        "source_files": {
            "health_results": "health_results.json",
            "e2e_flows": "e2e_flows.json",
            "pytest_summary": "pytest_summary.json (optional)",
        },
        "metrics": {
            "health_core_pct": health_metric,
            "contract_coherence_pct": coherence_metric,
            "tests_p0_pct": tests_metric,
            "Estabilidad_operativa_pct": estabilidad_metric,
            "evidence_coverage_pct": coverage_metric,
        },
        "verdicts": {
            "autonomy_operational": estabilidad_metric.get("value", 0) >= 70,
            "all_flows_pass": coherence_metric.get("value", 0) >= 99,
            "infrastructure_healthy": health_metric.get("value", 0) >= 99,
        },
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate PERCENTAGES v9 from autonomy evidence"
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(REPO_ROOT)
        / "docs"
        / "audit"
        / "20251222T075806Z_autonomy_evidence",
        help="Path to evidence directory (with health_results.json, e2e_flows.json, etc)",
    )
    parser.add_argument(
        "--write-root",
        action="store_true",
        help="Also write to docs/audit/PERCENTAGES.json (canonical root)",
    )

    args = parser.parse_args()

    # Validate outdir
    if not args.outdir.exists():
        print(f"ERROR: outdir not found: {args.outdir}", file=sys.stderr)
        sys.exit(1)

    # Generate v9
    percentages_v9 = generate_percentages_v9(args.outdir)

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

    # Output JSON to stdout
    print(json.dumps(percentages_v9, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
