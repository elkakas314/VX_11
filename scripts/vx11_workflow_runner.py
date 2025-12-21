#!/usr/bin/env python3
"""
vx11_workflow_runner.py — Ejecutor de workflows (validate/ci/autosync/status).
Genera reportes MD + snapshots canónicos.
NUNCA toca tablas legacy; usa copilot_* solo.
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DOCS_AUDIT = REPO_ROOT / "docs/audit"
DATA_BACKUPS = REPO_ROOT / "data/backups"
SCRIPTS_DIR = REPO_ROOT / "scripts"

DOCS_AUDIT.mkdir(parents=True, exist_ok=True)
DATA_BACKUPS.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd, shell=False):
    """Ejecutar comando, capturar output."""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            shell=shell,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "TIMEOUT"
    except Exception as e:
        return 1, "", str(e)


def cmd_status():
    """Ejecutar runtime truth + API discovery + BD scan."""
    print("[STATUS] Ejecutando diagnostico completo...")

    report = "# VX11 Status Report\n\n"
    report += f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n\n"

    # Runtime Truth
    rc, out, err = run_cmd("python3 scripts/vx11_runtime_truth.py", shell=True)
    report += f"## Runtime Truth\n`python3 scripts/vx11_runtime_truth.py`\n```\n{out}\n```\n\n"

    # Scan & Map
    rc, out, err = run_cmd("python3 scripts/vx11_scan_and_map.py --write", shell=True)
    report += f"## Scan & Map\n`python3 scripts/vx11_scan_and_map.py --write`\n```\n{out}\n```\n\n"

    # Save report
    report_path = DOCS_AUDIT / "VX11_STATUS_REPORT.md"
    report_path.write_text(report)
    print(f"✅ Report: {report_path}")

    return 0


def cmd_validate():
    """Validar: syntax + imports + prompts."""
    print("[VALIDATE] Ejecutando validacion...")

    report = "# VX11 Validate Report\n\n"
    report += f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n\n"

    checks = [
        ("Syntax Python", "python3 -m py_compile scripts/vx11_*.py"),
        ("Prompts", "python3 scripts/validate_prompts.py"),
        ("Git Status", "git status --short"),
    ]

    for name, cmd in checks:
        rc, out, err = run_cmd(cmd, shell=True)
        status = "✅ OK" if rc == 0 else "❌ FAIL"
        report += f"### {name}\n`{cmd}`\n**Status**: {status}\n```\n{out}\n```\n\n"

    report_path = DOCS_AUDIT / "VX11_VALIDATE_REPORT.md"
    report_path.write_text(report)
    print(f"✅ Report: {report_path}")

    return 0


def cmd_ci():
    """CI: format + lint + syntax."""
    print("[CI] Ejecutando pipeline CI...")

    report = "# VX11 CI Report\n\n"
    report += f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n\n"

    steps = [
        ("Format Black", "python3 -m black --check . 2>&1 | head -20"),
        ("Lint", "python3 -m pylint scripts/vx11_*.py 2>&1 | head -20"),
        ("Tests", "pytest tests/ -v 2>&1 | head -30"),
    ]

    all_ok = True
    for name, cmd in steps:
        rc, out, err = run_cmd(cmd, shell=True)
        status = "✅ PASS" if rc == 0 else "⚠️ WARN"
        report += f"### {name}\n**Status**: {status}\n```\n{out}\n```\n\n"
        if rc != 0:
            all_ok = False

    report_path = DOCS_AUDIT / "VX11_CI_REPORT.md"
    report_path.write_text(report)
    print(f"✅ Report: {report_path}")

    return 0 if all_ok else 1


def cmd_autosync():
    """Autosync: detectar drift, sugerir patches (NO aplicar)."""
    print("[AUTOSYNC] Detectando drift...")

    report = "# VX11 Autosync Report\n\n"
    report += f"**Timestamp**: {datetime.utcnow().isoformat()}Z\n\n"

    rc, out, err = run_cmd(
        "curl -s -H 'X-VX11-Token: vx11-local-token' http://localhost:8005/manifestator/scan-drift 2>/dev/null || echo 'Manifestator no responde'",
        shell=True,
    )
    report += f"## Drift Scan\n```\n{out}\n```\n\n"

    report += "## Recomendación\n"
    report += "Si hay drift detectado:\n"
    report += "1. Review cambios con `git diff`\n"
    report += "2. Ejecutar patch con confirmación explícita\n"
    report += "3. Registrar en `copilot_actions_log`\n\n"

    report_path = DOCS_AUDIT / "VX11_AUTOSYNC_REPORT.md"
    report_path.write_text(report)
    print(f"✅ Report: {report_path}")

    return 0


def main():
    if len(sys.argv) < 2:
        print("Uso: vx11_workflow_runner.py <status|validate|ci|autosync>")
        return 1

    command = sys.argv[1]

    if command == "status":
        return cmd_status()
    elif command == "validate":
        return cmd_validate()
    elif command == "ci":
        return cmd_ci()
    elif command == "autosync":
        return cmd_autosync()
    else:
        print(f"❌ Comando desconocido: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())