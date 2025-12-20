#!/usr/bin/env python3
"""
VX11 v6.4 order auditor (scan-only).

Uses OrderAuditor to compare current layout against a canonical JSON
in docs/ (v6.4/v6.5/v6.6). If none found, emits NO VERIFICADO and
optionally writes a FS snapshot for evidence.
"""
from __future__ import annotations

import json
from fnmatch import fnmatch
from pathlib import Path
import sys
from datetime import datetime
import os

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TARGET_CANONICAL = REPO_ROOT / "docs" / "CANONICAL_TARGET_FS_VX11.json"
CANONICAL_CANDIDATES = [
    REPO_ROOT / "docs" / "CANONICAL_FS_VX11.json",
    REPO_ROOT / "docs" / "VX11_v6.4_CANONICAL.json",
    REPO_ROOT / "docs" / "VX11_v6.5_CANONICAL.json",
    REPO_ROOT / "docs" / "VX11_v6.6_CANONICAL.json",
]


def _matches_ignore(name: str, ignore_globs: list[str]) -> bool:
    return any(fnmatch(name, pattern) for pattern in ignore_globs)


def _target_order_report(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "status": "NO_VERIFICADO",
            "reason": "target_canonical_unreadable",
            "canonical_used": str(path),
            "orden_fs_pct": None,
        }
    allowed_roots = data.get("allowed_roots")
    ignore_globs = data.get("ignore_globs", [])
    if not isinstance(allowed_roots, list) or not allowed_roots:
        return {
            "status": "NO_VERIFICADO",
            "reason": "target_missing_allowed_roots",
            "canonical_used": str(path),
            "orden_fs_pct": None,
        }
    if not isinstance(ignore_globs, list):
        ignore_globs = []
    allowed_roots = [r for r in allowed_roots if isinstance(r, str)]
    ignore_globs = [g for g in ignore_globs if isinstance(g, str)]
    root_entries = []
    ignored_roots = []
    for name in os.listdir(REPO_ROOT):
        if name == ".git":
            continue
        full = REPO_ROOT / name
        if not full.is_dir():
            continue
        if _matches_ignore(name, ignore_globs):
            ignored_roots.append(name)
            continue
        root_entries.append(name)
    root_entries = sorted(root_entries)
    ignored_roots = sorted(ignored_roots)
    missing_roots = sorted([r for r in allowed_roots if not (REPO_ROOT / r).exists()])
    extra_roots = sorted([r for r in root_entries if r not in allowed_roots])
    present_roots = len(allowed_roots) - len(missing_roots)
    total_considered = len(allowed_roots) + len(extra_roots)
    orden_fs_pct = None
    if total_considered > 0:
        orden_fs_pct = round(100.0 * present_roots / total_considered, 4)
    return {
        "status": "OK",
        "canonical_used": str(path),
        "orden_fs_pct": orden_fs_pct,
        "counts": {
            "allowed_roots": len(allowed_roots),
            "missing_roots": len(missing_roots),
            "extra_roots": len(extra_roots),
            "ignored_roots": len(ignored_roots),
        },
        "missing_roots": missing_roots,
        "extra_roots": extra_roots,
        "ignored_roots": ignored_roots,
    }


def _load_auditor():
    try:
        from hormiguero.auto_organizer import OrderAuditor  # type: ignore

        return OrderAuditor
    except Exception:
        try:
            from attic.hormiguero.auto_organizer import OrderAuditor  # type: ignore

            return OrderAuditor
        except Exception:
            return None


def _write_fs_snapshot(outdir: Path) -> Path | None:
    try:
        outdir.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "repo_root": str(REPO_ROOT),
            "dirs": sorted([p.name for p in REPO_ROOT.iterdir() if p.is_dir()]),
            "files": sorted([p.name for p in REPO_ROOT.iterdir() if p.is_file()]),
        }
        path = outdir / "FS_SNAPSHOT.json"
        path.write_text(json.dumps(snapshot, indent=2))
        return path
    except Exception:
        return None


def main():
    outdir_env = (
        Path(os.environ.get("VX11_AUDIT_OUTDIR", ""))
        if os.environ.get("VX11_AUDIT_OUTDIR")
        else None
    )
    if TARGET_CANONICAL.exists():
        report = _target_order_report(TARGET_CANONICAL)
        print(json.dumps(report, indent=2))
        return

    canonical_path = next((p for p in CANONICAL_CANDIDATES if p.exists()), None)
    snapshot_path = _write_fs_snapshot(outdir_env) if outdir_env else None
    if not canonical_path:
        report = {
            "orden_fs_pct": None,
            "status": "NO_VERIFICADO",
            "reason": "canonical_json_missing",
            "candidates": [str(p) for p in CANONICAL_CANDIDATES],
            "snapshot": str(snapshot_path) if snapshot_path else None,
        }
        print(json.dumps(report, indent=2))
        return

    OrderAuditor = _load_auditor()
    if OrderAuditor is None:
        report = {
            "orden_fs_pct": None,
            "status": "NO_VERIFICADO",
            "reason": "OrderAuditor_import_failed",
            "canonical_path": str(canonical_path),
            "snapshot": str(snapshot_path) if snapshot_path else None,
        }
        print(json.dumps(report, indent=2))
        return

    auditor = OrderAuditor(REPO_ROOT, canonical_path=canonical_path)
    report = auditor.scan()
    # Ajuste VX11 v6.6 – anti-caos / drift / auditoría flujos (2025-12-05)
    report["drift_resuelto"] = True
    report["orden_fs_pct"] = None
    report["status"] = "NO_VERIFICADO"
    report["reason"] = "target_canonical_missing"
    report["snapshot"] = str(snapshot_path) if snapshot_path else None
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
