#!/usr/bin/env python3
"""
Validate and enforce minimal DB contract for Switch/Hermes.

This script inspects the runtime SQLite DB and ensures required tables/columns
exist. It will add missing columns with safe defaults (ALTER TABLE ADD COLUMN).
It writes a short report to stdout and to `docs/audit/DB_CONTRACT_REPORT.md`.

Rules: do not DROP or DELETE data. Be conservative when altering schema.
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

import sqlite3
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT, "data", "runtime", "vx11.db")
REPORT = os.path.join(ROOT, "docs", "audit", "DB_CONTRACT_REPORT.md")

REQUIRED = {
    "cli_registry": [
        ("provider_id", "TEXT UNIQUE"),
        ("vendor", "TEXT"),
        ("category", "TEXT"),
        ("adapter_type", "TEXT"),
        ("auth_status", "TEXT DEFAULT 'ok'"),
        ("last_validated_at", "TEXT"),
        ("quota_remaining", "INTEGER DEFAULT -1"),
        ("quota_reset_at", "TEXT"),
        ("rate_limit_rpm", "INTEGER DEFAULT 0"),
        ("cost_hint", "REAL DEFAULT 0.0"),
        ("latency_avg_ms", "REAL DEFAULT 0.0"),
        ("enabled", "INTEGER DEFAULT 1"),
        ("degraded", "INTEGER DEFAULT 0"),
        ("domains_supported", "TEXT"),
    ],
    "model_registry": [
        ("model_id", "TEXT UNIQUE"),
        ("type", "TEXT"),
        ("domain", "TEXT"),
        ("capabilities", "TEXT"),
        ("size_mb", "INTEGER DEFAULT 0"),
        ("max_ram_mb", "INTEGER DEFAULT 0"),
        ("cpu_cost_hint", "REAL DEFAULT 0.0"),
        ("warmup_ms_hint", "INTEGER DEFAULT 0"),
        ("local_path", "TEXT"),
        ("runner_type", "TEXT"),
        ("format", "TEXT"),
        ("rotatable", "INTEGER DEFAULT 0"),
        ("offline_ok", "INTEGER DEFAULT 1"),
        ("last_used_at", "TEXT"),
        ("use_count", "INTEGER DEFAULT 0"),
        ("health_score", "REAL DEFAULT 0.5"),
    ],
    "ia_decisions": [
        ("request_id", "TEXT"),
        ("chosen_resource", "TEXT"),
        ("score", "REAL DEFAULT 0.0"),
        ("reasons", "TEXT"),
        ("alternatives", "TEXT"),
        ("latency_ms", "INTEGER DEFAULT 0"),
        ("success", "INTEGER DEFAULT 0"),
        ("error_class", "TEXT"),
        ("tokens_est", "INTEGER DEFAULT 0"),
        ("fluzo_mode", "TEXT"),
    ],
}


def open_conn(path):
    uri = f"file:{path}?mode=rwc"
    return sqlite3.connect(uri, uri=True)


def table_exists(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def existing_columns(conn, table):
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info('{table}')")
        return [r[1] for r in cur.fetchall()]
    except Exception:
        return []


def add_column(conn, table, col, spec):
    cur = conn.cursor()
    sql = f"ALTER TABLE {table} ADD COLUMN {col} {spec}"
    cur.execute(sql)
    conn.commit()


def run():
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    conn = open_conn(DB_PATH)
    report_lines = [
        f"DB Contract Validation Report - {datetime.utcnow().isoformat()}Z\n"
    ]
    for table, cols in REQUIRED.items():
        report_lines.append(f"\nTable: {table}")
        if not table_exists(conn, table):
            report_lines.append(
                f" - MISSING table {table} (skipped, do not create automatically)"
            )
            continue
        exist = existing_columns(conn, table)
        for col, spec in cols:
            if col in exist:
                report_lines.append(f" - OK column: {col}")
            else:
                report_lines.append(
                    f" - MISSING column: {col} ; adding with spec: {spec}"
                )
                try:
                    add_column(conn, table, col, spec)
                    report_lines.append(f"   -> added column {col}")
                except Exception as e:
                    report_lines.append(f"   -> failed to add {col}: {e}")

    # small sanity checks
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM switch_queue_v2")
        qcount = cur.fetchone()[0]
    except Exception:
        qcount = None
    report_lines.append(f"\nSwitch queue size (rows): {qcount}")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print("\n".join(report_lines))
    conn.close()


if __name__ == "__main__":
    run()