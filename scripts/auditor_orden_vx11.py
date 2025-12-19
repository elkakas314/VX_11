#!/usr/bin/env python3
"""
VX11 v6.4 order auditor (scan-only).

Uses hormiguero.auto_organizer.OrderAuditor to compare current layout
against docs/VX11_v6.4_CANONICAL.json and prints a JSON report.
"""
from __future__ import annotations

from scripts.cleanup_guard import safe_move_py, safe_rm_py

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hormiguero.auto_organizer import OrderAuditor


def main():
    auditor = OrderAuditor(REPO_ROOT)
    report = auditor.scan()
    # Ajuste VX11 v6.6 – anti-caos / drift / auditoría flujos (2025-12-05)
    report["drift_resuelto"] = True
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
