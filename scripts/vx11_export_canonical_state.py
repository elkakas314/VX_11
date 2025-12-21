#!/usr/bin/env python3
"""
VX11 Export Canonical State: Read-only extraction + muestreo + tamaño-aware.
Output:
  1) data/backups/vx11_CANONICAL_DISTILLED.db (<512MB)
  2) data/backups/vx11_CANONICAL_STATE.json (<50MB)
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py


import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import shutil

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DB = REPO_ROOT / "data" / "runtime" / "vx11.db"
BACKUPS_DIR = REPO_ROOT / "data" / "backups"
DISTILLED_DB = BACKUPS_DIR / "vx11_CANONICAL_DISTILLED.db"
STATE_JSON = BACKUPS_DIR / "vx11_CANONICAL_STATE.json"

# Sampling parameters
DEFAULT_HISTORY_ROWS = 200
DEFAULT_MESSAGES_PER_SESSION = 100
DEFAULT_MAX_MB = 480


class CanonicalExporter:
    def __init__(
        self,
        source_db,
        distilled_db,
        history_rows=DEFAULT_HISTORY_ROWS,
        messages_per_session=DEFAULT_MESSAGES_PER_SESSION,
        max_total_mb=DEFAULT_MAX_MB,
    ):
        self.source_db = source_db
        self.distilled_db = distilled_db
        self.history_rows = history_rows
        self.messages_per_session = messages_per_session
        self.max_total_mb = max_total_mb
        self.backups_dir = distilled_db.parent
        self.backups_dir.mkdir(parents=True, exist_ok=True)

        self.source_conn = None
        self.distilled_conn = None
        self.table_stats = {}

    def open_source(self):
        """Open source DB in read-only mode."""
        if not self.source_db.exists():
            raise FileNotFoundError(f"Source DB not found: {self.source_db}")
        # SQLite read-only: mode=ro
        uri = f"file:{self.source_db}?mode=ro"
        self.source_conn = sqlite3.connect(uri, uri=True, timeout=10)
        self.source_conn.row_factory = sqlite3.Row

    def open_distilled(self):
        """Create and open distilled DB."""
        if self.distilled_db.exists():
            self.distilled_db.unlink()
        self.distilled_conn = sqlite3.connect(str(self.distilled_db))
        self.distilled_conn.execute("PRAGMA journal_mode=WAL;")

    def get_tables(self):
        """List all tables in source DB."""
        cur = self.source_conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return [row[0] for row in cur.fetchall()]

    def copy_schema(self, table_name):
        """Copy table schema to distilled DB."""
        cur = self.source_conn.cursor()
        cur.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        row = cur.fetchone()
        if row and row[0]:
            create_sql = row[0]
            try:
                self.distilled_conn.execute(create_sql)
            except sqlite3.OperationalError as e:
                print(f"  [WARN] Schema copy failed for {table_name}: {e}")

    def get_table_row_count(self, table_name):
        """Count rows in a table."""
        try:
            cur = self.source_conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            return cur.fetchone()[0]
        except Exception as e:
            print(f"  [ERROR] Count failed for {table_name}: {e}")
            return 0

    def sample_table(self, table_name, limit=None):
        """Read rows from table (optionally limited)."""
        try:
            cur = self.source_conn.cursor()
            if limit:
                cur.execute(f"SELECT * FROM {table_name} LIMIT ?;", (limit,))
            else:
                cur.execute(f"SELECT * FROM {table_name};")
            return cur.fetchall()
        except Exception as e:
            print(f"  [ERROR] Sample failed for {table_name}: {e}")
            return []

    def insert_rows(self, table_name, rows):
        """Insert rows into distilled DB."""
        if not rows:
            return

        # Get column info from distilled schema
        cur = self.distilled_conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name});")
        cols = [row[1] for row in cur.fetchall()]

        placeholders = ",".join(["?" for _ in cols])
        insert_sql = (
            f"INSERT INTO {table_name} ({','.join(cols)}) VALUES ({placeholders});"
        )

        try:
            for row in rows:
                # Convert Row to tuple, handling mismatch
                vals = tuple(row[i] if i < len(row) else None for i in range(len(cols)))
                self.distilled_conn.execute(insert_sql, vals)
        except Exception as e:
            print(f"  [WARN] Insert failed for {table_name}: {e}")

    def export(self):
        """Main export flow."""
        print("\n=== Phase 1: Open source DB ===")
        self.open_source()
        tables = self.get_tables()
        print(f"Source tables: {len(tables)}")

        print("\n=== Phase 2: Open distilled DB ===")
        self.open_distilled()

        print("\n=== Phase 3: Copy schemas ===")
        for table in tables:
            print(f"  {table}...", end=" ")
            self.copy_schema(table)
            count = self.get_table_row_count(table)
            self.table_stats[table] = {"total_rows": count, "sampled_rows": 0}
            print(f"({count} rows)")

        print("\n=== Phase 4: Sample and copy data ===")
        for table in tables:
            total = self.table_stats[table]["total_rows"]

            # Determine limit based on table type
            if "message" in table.lower():
                limit = (
                    self.messages_per_session
                    if total > self.messages_per_session
                    else total
                )
            else:
                limit = self.history_rows if total > self.history_rows else total

            if total > 0:
                print(f"  {table}: sampling {limit}/{total}...", end=" ")
                rows = self.sample_table(table, limit=limit)
                self.insert_rows(table, rows)
                self.table_stats[table]["sampled_rows"] = len(rows)
                print(f"✓ {len(rows)} inserted")

        self.distilled_conn.commit()
        self.distilled_conn.close()

        # Check size
        distilled_size_mb = self.distilled_db.stat().st_size / (1024 * 1024)
        print(f"\n[SIZE] Distilled DB: {distilled_size_mb:.2f} MB")

        if distilled_size_mb > self.max_total_mb:
            print(
                f"[WARN] Distilled DB exceeds {self.max_total_mb}MB; reducing sampling..."
            )
            # Reduce and retry
            self.history_rows = max(10, self.history_rows // 2)
            self.messages_per_session = max(5, self.messages_per_session // 2)
            self.distilled_db.unlink()
            return self.export()  # Retry

        print(f"[OK] Distilled DB within {self.max_total_mb}MB limit ✓")
        self.source_conn.close()

        return self.table_stats

    def generate_state_json(self, runtime_truth_report_path=None):
        """Generate vx11_CANONICAL_STATE.json."""
        state = {
            "extracted_at": datetime.utcnow().isoformat() + "Z",
            "vx11_version_inferred": "6.7.0",
            "source_db": str(self.source_db),
            "distilled_db": str(self.distilled_db),
            "distilled_size_mb": round(
                self.distilled_db.stat().st_size / (1024 * 1024), 2
            ),
            "table_stats": self.table_stats,
            "modules": [],
            "summary": {
                "total_tables": len(self.table_stats),
                "total_sampled_rows": sum(
                    t["sampled_rows"] for t in self.table_stats.values()
                ),
            },
        }

        # Parse runtime truth if available
        if runtime_truth_report_path and Path(runtime_truth_report_path).exists():
            report_text = Path(runtime_truth_report_path).read_text()
            # Simple extraction: look for "| service_name | port | Status |" lines
            for line in report_text.split("\n"):
                if line.startswith("|") and "✓" in line or "✗" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        try:
                            state["modules"].append(
                                {
                                    "name": parts[1],
                                    "port": (
                                        int(parts[2])
                                        if parts[2].isdigit()
                                        else parts[2]
                                    ),
                                    "status": (
                                        parts[3].split()[1]
                                        if len(parts[3].split()) > 1
                                        else parts[3]
                                    ),
                                }
                            )
                        except (ValueError, IndexError):
                            pass

        STATE_JSON.write_text(json.dumps(state, indent=2))
        print(f"[JSON] {STATE_JSON}: {STATE_JSON.stat().st_size / (1024*1024):.2f} MB")

        return state


def main():
    print("=" * 70)
    print("VX11 Export Canonical State")
    print("=" * 70)

    if not SOURCE_DB.exists():
        print(f"ERROR: Source DB not found: {SOURCE_DB}")
        sys.exit(1)

    exporter = CanonicalExporter(SOURCE_DB, DISTILLED_DB)
    try:
        stats = exporter.export()
        exporter.generate_state_json(
            runtime_truth_report_path=REPO_ROOT
            / "docs"
            / "audit"
            / "VX11_RUNTIME_TRUTH_REPORT.md"
        )

        print("\n=== Verification ===")
        print(f"Distilled DB: {DISTILLED_DB}")
        print(f"  Size: {DISTILLED_DB.stat().st_size / (1024*1024):.2f} MB")
        print(f"State JSON: {STATE_JSON}")
        print(f"  Size: {STATE_JSON.stat().st_size / 1024:.2f} KB")

        print("\n✅ Export complete")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()