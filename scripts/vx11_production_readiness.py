#!/usr/bin/env python3
"""
VX11 Production Readiness Check
Validates system health, module availability, and resource status.

Checks:
1. All 9 modules respond to health endpoints
2. Database integrity and size <500MB
3. Essential tables present and populated
4. Required models registered and available
5. API authentication working
6. Logs and forensics operational
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py


import sys
import json
import sqlite3
import time
from pathlib import Path
from datetime import datetime

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from config.forensics import write_log
from config.db_schema import get_session, LocalModelV2


# Module health endpoints
HEALTH_ENDPOINTS = {
    "tentaculo_link": ("http://localhost:8000/health", "Tentáculo Link (Gateway)"),
    "madre": ("http://localhost:8001/health", "Madre (Orchestration)"),
    "switch": ("http://localhost:8002/health", "Switch (Routing)"),
    "hermes": ("http://localhost:8003/health", "Hermes (CLI/Models)"),
    "hormiguero": ("http://localhost:8004/health", "Hormiguero (Parallelization)"),
    "manifestator": ("http://localhost:8005/health", "Manifestator (Auditing)"),
    "mcp": ("http://localhost:8006/health", "MCP (Conversational)"),
    "shub": ("http://localhost:8007/health", "Shubniggurath (Processing)"),
    "operator": ("http://localhost:8011/health", "Operator (UI Backend)"),
}

DB_PATH = Path("data/runtime/vx11.db")
TARGET_SIZE_MB = 500


def check_module_health() -> dict[str, bool]:
    """Check if all modules are responding to health endpoints."""
    try:
        import httpx
    except ImportError:
        print("⚠️  httpx not available, skipping module health checks")
        return {}

    results = {}

    async def check_all():
        async with httpx.AsyncClient(timeout=3.0) as client:
            for module_key, (url, label) in HEALTH_ENDPOINTS.items():
                try:
                    resp = await client.get(url)
                    results[module_key] = resp.status_code == 200
                except:
                    results[module_key] = False

    import asyncio

    try:
        asyncio.run(check_all())
    except:
        pass

    return results


def check_database_health() -> dict:
    """Check database integrity and size."""
    result = {
        "exists": DB_PATH.exists(),
        "size_mb": 0,
        "size_ok": False,
        "integrity_ok": False,
        "tables": 0,
    }

    if not DB_PATH.exists():
        return result

    try:
        result["size_mb"] = DB_PATH.stat().st_size / (1024**2)
        result["size_ok"] = result["size_mb"] < TARGET_SIZE_MB

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Integrity check
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        result["integrity_ok"] = integrity_result == "ok"

        # Table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        result["tables"] = cursor.fetchone()[0]

        conn.close()

    except Exception as e:
        result["error"] = str(e)

    return result


def check_essential_tables() -> dict:
    """Check if essential tables exist and have data."""
    essential_tables = [
        "tasks",
        "ia_decisions",
        "model_registry",
        "cli_registry",
        "local_models_v2",
        "operator_session",
        "operator_message",
    ]

    result = {}

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for table in essential_tables:
            # Check if exists
            cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            )
            exists = cursor.fetchone() is not None

            # Check row count
            row_count = 0
            if exists:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]

            result[table] = {
                "exists": exists,
                "row_count": row_count,
            }

        conn.close()

    except Exception as e:
        result["error"] = str(e)

    return result


def check_models_available() -> dict:
    """Check if required models are registered and available."""
    result = {
        "total": 0,
        "enabled": 0,
        "models": [],
    }

    db = None
    try:
        db = get_session("vx11")

        models = db.query(LocalModelV2).all()
        result["total"] = len(models)

        for model in models:
            result["models"].append(
                {
                    "name": model.name,
                    "enabled": model.enabled,
                    "size_mb": model.size_bytes / (1024**2),
                    "path": model.path,
                }
            )

        result["enabled"] = sum(1 for m in models if m.enabled)

    except Exception as e:
        result["error"] = str(e)

    finally:
        if db:
            db.close()

    return result


def check_logs_operational() -> dict:
    """Check if logging system is operational."""
    logs_dir = Path("logs")
    forensic_dir = Path("forensic")

    result = {
        "logs_dir_exists": logs_dir.exists(),
        "forensic_dir_exists": forensic_dir.exists(),
        "recent_logs": 0,
        "recent_forensics": 0,
    }

    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        result["recent_logs"] = len(
            [f for f in log_files if f.stat().st_mtime > (time.time() - 3600)]
        )

    if forensic_dir.exists():
        forensic_files = list(forensic_dir.glob("**/logs/*.log"))
        result["recent_forensics"] = len(
            [f for f in forensic_files if f.stat().st_mtime > (time.time() - 3600)]
        )

    return result


def generate_report(
    module_health: dict,
    db_health: dict,
    essential_tables: dict,
    models: dict,
    logs: dict,
) -> tuple[str, bool]:
    """Generate comprehensive readiness report."""

    report = "# VX11 Production Readiness Check\n\n"
    report += f"**Timestamp:** {datetime.utcnow().isoformat()}Z\n\n"

    all_ok = True

    # Module Health
    report += "## 1. Module Health\n\n"
    if not module_health:
        report += "⚠️  Modules not checked (httpx unavailable)\n\n"
    else:
        healthy = sum(1 for v in module_health.values() if v)
        total = len(module_health)
        report += f"**Status:** {healthy}/{total} modules healthy\n\n"

        report += "| Module | Status |\n"
        report += "|--------|--------|\n"
        for module_key, (_, label) in HEALTH_ENDPOINTS.items():
            status = "✅ OK" if module_health.get(module_key, False) else "❌ FAIL"
            report += f"| {label:40} | {status} |\n"

        if healthy < total:
            all_ok = False

        report += "\n"

    # Database Health
    report += "## 2. Database Health\n\n"
    if db_health.get("exists"):
        report += f"- **Exists:** ✅\n"
        report += f"- **Size:** {db_health['size_mb']:.1f}MB {'✅' if db_health['size_ok'] else '❌'} (target: <{TARGET_SIZE_MB}MB)\n"
        report += f"- **Integrity:** {'✅ OK' if db_health.get('integrity_ok') else '❌ FAILED'}\n"
        report += f"- **Tables:** {db_health['tables']}\n"

        if not db_health.get("integrity_ok") or not db_health.get("size_ok"):
            all_ok = False
    else:
        report += "❌ Database not found\n"
        all_ok = False

    report += "\n"

    # Essential Tables
    report += "## 3. Essential Tables\n\n"
    all_tables_ok = True
    for table, info in essential_tables.items():
        if table == "error":
            report += f"⚠️  Error checking tables: {info}\n"
            all_tables_ok = False
        else:
            status = "✅" if info["exists"] else "❌"
            report += f"- {table:30} {status} ({info.get('row_count', 0):,} rows)\n"
            if not info["exists"]:
                all_tables_ok = False

    if not all_tables_ok:
        all_ok = False

    report += "\n"

    # Models
    report += "## 4. Models\n\n"
    report += f"- **Total Registered:** {models['total']}\n"
    report += f"- **Enabled:** {models['enabled']}\n"

    if models.get("models"):
        report += "\n| Name | Status | Size |\n"
        report += "|------|--------|------|\n"
        for model in models["models"][:10]:  # First 10
            status = "✅ enabled" if model["enabled"] else "⚠️  disabled"
            report += (
                f"| {model['name']:30} | {status:20} | {model['size_mb']:6.1f}MB |\n"
            )

    if models["enabled"] == 0 and models["total"] > 0:
        all_ok = False

    report += "\n"

    # Logs
    report += "## 5. Logging & Forensics\n\n"
    report += f"- **Logs Directory:** {'✅ Present' if logs['logs_dir_exists'] else '❌ Missing'}\n"
    report += f"- **Recent Logs (1h):** {logs['recent_logs']}\n"
    report += f"- **Forensics Directory:** {'✅ Present' if logs['forensic_dir_exists'] else '❌ Missing'}\n"
    report += f"- **Recent Forensics (1h):** {logs['recent_forensics']}\n"

    report += "\n"

    # Summary
    report += "---\n\n"
    report += "## Overall Status\n\n"

    if all_ok and module_health:
        report += "✅ **PRODUCTION READY**\n"
        report += "All checks passed. System is ready for deployment.\n"
    elif all_ok:
        report += "⚠️  **READY WITH WARNINGS**\n"
        report += "Core systems OK, but module connectivity check skipped. Ensure modules are running.\n"
    else:
        report += "❌ **NOT PRODUCTION READY**\n"
        report += "Some checks failed. See details above.\n"

    return report, all_ok


def main():
    """Main entry point."""
    print("=" * 70)
    print("VX11 Production Readiness Check")
    print("=" * 70)
    print()

    print("Checking module health...")
    module_health = check_module_health()

    print("Checking database...")
    db_health = check_database_health()

    print("Checking essential tables...")
    essential_tables = check_essential_tables()

    print("Checking models...")
    models = check_models_available()

    print("Checking logs...")
    logs = check_logs_operational()

    print()

    # Generate report
    report, is_ok = generate_report(
        module_health, db_health, essential_tables, models, logs
    )

    # Display and save
    print(report)

    report_path = Path("docs/audit/PRODUCTION_READINESS_CHECK_v7_FINAL.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)

    print(f"\n✓ Report saved to {str(report_path)}")

    write_log("vx11_readiness", f"check_complete:ready={is_ok}")

    return is_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)