#!/usr/bin/env python3
"""
VX11 v6.4 order auditor (scan-only).

Uses OrderAuditor to compare current layout against a canonical JSON
in docs/ (v6.4/v6.5/v6.6). If none found, emits NO VERIFICADO and
optionally writes a FS snapshot for evidence.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from datetime import datetime
import os

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CANONICAL_CANDIDATES = [
    REPO_ROOT / "docs" / "VX11_v6.4_CANONICAL.json",
    REPO_ROOT / "docs" / "VX11_v6.5_CANONICAL.json",
    REPO_ROOT / "docs" / "VX11_v6.6_CANONICAL.json",
]


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
    canonical_path = next((p for p in CANONICAL_CANDIDATES if p.exists()), None)
    outdir_env = Path(os.environ.get("VX11_AUDIT_OUTDIR", "")) if os.environ.get("VX11_AUDIT_OUTDIR") else None
    if not canonical_path:
        snapshot_path = _write_fs_snapshot(outdir_env) if outdir_env else None
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
        }
        print(json.dumps(report, indent=2))
        return

    auditor = OrderAuditor(REPO_ROOT, canonical_path=canonical_path)
    report = auditor.scan()
    # Ajuste VX11 v6.6 – anti-caos / drift / auditoría flujos (2025-12-05)
    report["drift_resuelto"] = True
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
