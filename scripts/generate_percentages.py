#!/usr/bin/env python3
"""Generate PERCENTAGES.json with NV-aware handling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return None


def _metric_value(value):
    return value if value is not None else "NV"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--db-schema", default="docs/audit/DB_SCHEMA_v7_FINAL.json")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    schema_path = Path(args.db_schema)

    auditor_path = outdir / "auditor_orden_vx11.json"
    auditor = _read_json(auditor_path) or {}
    orden_fs_pct = auditor.get("orden_fs_pct")

    orden_db_module_assignment_pct = None
    if schema_path.exists():
        schema = _read_json(schema_path) or {}
        tables = schema.get("tables", [])
        if isinstance(tables, list) and tables:
            assigned = sum(1 for t in tables if t.get("module"))
            orden_db_module_assignment_pct = round(100.0 * assigned / len(tables), 4)

    health_files = [
        outdir / "madre_health.json",
        outdir / "tentaculo_health.json",
        outdir / "switch_health.json",
        outdir / "spawner_health.json",
        outdir / "hormiguero_health.json",
    ]
    health_values = []
    for hf in health_files:
        data = _read_json(hf)
        if isinstance(data, dict) and data.get("status") == "ok":
            health_values.append(100.0)
        elif data is None:
            health_values.append(None)
        else:
            health_values.append(0.0)
    health_core_pct = None if any(v is None for v in health_values) else round(
        sum(health_values) / len(health_values), 4
    )

    tests_p0_txt = _read_text(outdir / "tests_p0.txt")
    if tests_p0_txt is None or "NV" in tests_p0_txt:
        tests_p0_pct = None
    elif "PASS" in tests_p0_txt:
        tests_p0_pct = 100.0
    elif "FAIL" in tests_p0_txt:
        tests_p0_pct = 0.0
    else:
        tests_p0_pct = None

    contracts_json = _read_json(outdir / "contracts_17of17.json") or {}
    contracts_status = contracts_json.get("status")
    if contracts_status == "PASS":
        contract_coherence_pct = 100.0
    elif contracts_status == "FAIL":
        contract_coherence_pct = 0.0
    elif contracts_status is None:
        contract_coherence_pct = None
    else:
        contract_coherence_pct = None

    coherencia_json = _read_json(outdir / "coherencia_routing_calc.json") or {}
    coherencia_total_routing_pct = coherencia_json.get("coherencia_total_routing_pct")

    integrity_txt = _read_text(outdir / "db_integrity_check.txt")
    if integrity_txt is None:
        integrity_check = "NV"
    elif "ok" in integrity_txt.lower():
        integrity_check = "ok"
    elif "fail" in integrity_txt.lower():
        integrity_check = "fail"
    else:
        integrity_check = "NV"

    automatizacion_pct = None
    autonomia_pct = None

    orden_total = None
    if orden_fs_pct is not None and orden_db_module_assignment_pct is not None:
        orden_total = round(0.5 * orden_fs_pct + 0.5 * orden_db_module_assignment_pct, 4)

    if integrity_check == "ok":
        if any(v is None for v in (health_core_pct, tests_p0_pct, contract_coherence_pct)):
            estabilidad_operativa_pct = None
        else:
            estabilidad_operativa_pct = round(
                0.4 * health_core_pct + 0.3 * tests_p0_pct + 0.3 * contract_coherence_pct,
                4,
            )
    elif integrity_check == "fail":
        estabilidad_operativa_pct = 0.0
    else:
        estabilidad_operativa_pct = None

    weights = {
        "Orden_total": 0.15,
        "Estabilidad_operativa_pct": 0.25,
        "Coherencia_total_routing_pct": 0.30,
        "Automatizacion_pct": 0.15,
        "Autonomia_pct": 0.15,
    }
    components = {
        "Orden_total": orden_total,
        "Estabilidad_operativa_pct": estabilidad_operativa_pct,
        "Coherencia_total_routing_pct": coherencia_total_routing_pct,
        "Automatizacion_pct": automatizacion_pct,
        "Autonomia_pct": autonomia_pct,
    }
    available_weight = sum(
        weight for key, weight in weights.items() if components.get(key) is not None
    )
    if available_weight == 1.0:
        global_ponderado_pct = round(
            sum(weights[k] * components[k] for k in weights.keys()), 4
        )
        global_parcial_pct = None
        coverage_pct = 100.0
    elif available_weight == 0.0:
        global_ponderado_pct = None
        global_parcial_pct = None
        coverage_pct = 0.0
    else:
        global_ponderado_pct = None
        global_parcial_pct = round(
            sum(weights[k] * components[k] for k in weights.keys() if components[k] is not None)
            / available_weight,
            4,
        )
        coverage_pct = round(available_weight * 100.0, 4)

    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "formulas": {
            "Orden_total": "0.5*Orden_fs_pct + 0.5*Orden_db_module_assignment_pct",
            "Estabilidad_operativa_pct": "gate(integrity_check == ok) ? 0.4*health_core_pct + 0.3*tests_p0_pct + 0.3*contract_coherence_pct : 0",
            "Global_ponderado_pct": "0.15*Orden_total + 0.25*Estabilidad_operativa_pct + 0.30*Coherencia_total_routing_pct + 0.15*Automatizacion_pct + 0.15*Autonomia_pct",
        },
        "metrics": {
            "Orden_fs_pct": {
                "value": _metric_value(orden_fs_pct),
                "source": str(auditor_path),
            },
            "Orden_db_module_assignment_pct": {
                "value": _metric_value(orden_db_module_assignment_pct),
                "source": str(schema_path) if schema_path.exists() else None,
            },
            "health_core_pct": {
                "value": _metric_value(health_core_pct),
                "source": [str(p) for p in health_files],
            },
            "tests_p0_pct": {
                "value": _metric_value(tests_p0_pct),
                "source": str(outdir / "tests_p0.txt"),
            },
            "contract_coherence_pct": {
                "value": _metric_value(contract_coherence_pct),
                "source": str(outdir / "contracts_17of17.json"),
            },
            "Coherencia_total_routing_pct": {
                "value": _metric_value(coherencia_total_routing_pct),
                "source": str(outdir / "coherencia_routing_calc.json"),
            },
            "Automatizacion_pct": {
                "value": _metric_value(automatizacion_pct),
                "source": None,
            },
            "Autonomia_pct": {
                "value": _metric_value(autonomia_pct),
                "source": None,
            },
            "integrity_check": {
                "value": integrity_check,
                "source": str(outdir / "db_integrity_check.txt"),
            },
        },
        "computed": {
            "Orden_total": _metric_value(orden_total),
            "Estabilidad_operativa_pct": _metric_value(estabilidad_operativa_pct),
            "Global_ponderado_pct": _metric_value(global_ponderado_pct),
            "Global_parcial_pct": _metric_value(global_parcial_pct),
            "coverage_pct": coverage_pct,
        },
    }

    out_json = outdir / "PERCENTAGES.json"
    out_txt = outdir / "PERCENTAGES_REDUCED.txt"
    out_json.write_text(json.dumps(report, indent=2) + "\n")
    reduced = [
        f"Orden_fs_pct={_metric_value(orden_fs_pct)}",
        f"Orden_db_module_assignment_pct={_metric_value(orden_db_module_assignment_pct)}",
        f"Orden_total={_metric_value(orden_total)}",
        f"Estabilidad_operativa_pct={_metric_value(estabilidad_operativa_pct)}",
        f"Coherencia_total_routing_pct={_metric_value(coherencia_total_routing_pct)}",
        f"Automatizacion_pct={_metric_value(automatizacion_pct)}",
        f"Autonomia_pct={_metric_value(autonomia_pct)}",
        f"Global_ponderado_pct={_metric_value(global_ponderado_pct)}",
        f"Global_parcial_pct={_metric_value(global_parcial_pct)}",
        f"coverage_pct={coverage_pct}",
    ]
    out_txt.write_text("\n".join(reduced) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
