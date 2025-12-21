#!/usr/bin/env python3
"""
VX11 Canonical DB Generation
Cleans up old records, syncs all module tables, validates size <500MB.

Steps:
1. Archive records older than 30 days
2. Clean up forensic ledger
3. Ensure all module tables present
4. Validate final DB size
5. Create backup
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py


import sys
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.db_schema import Base, unified_engine, get_session
from config.forensics import write_log


DB_PATH = Path("data/runtime/vx11.db")
TARGET_SIZE_MB = 500
ARCHIVE_DIR = Path("data/backups")


def cleanup_old_forensics(days_old: int = 30) -> int:
    """Archive old forensic ledger records."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cutoff = datetime.utcnow() - timedelta(days=days_old)
    cutoff_ts = cutoff.isoformat() + "Z"

    try:
        # Check if forensic_ledger exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='forensic_ledger'"
        )
        if not cursor.fetchone():
            print("ℹ️  forensic_ledger table not found")
            return 0

        # Count old records
        cursor.execute(
            "SELECT COUNT(*) FROM forensic_ledger WHERE created_at < ?", (cutoff_ts,)
        )
        old_count = cursor.fetchone()[0]

        if old_count > 0:
            # Archive to file (append-only)
            archive_dir = ARCHIVE_DIR
            archive_dir.mkdir(parents=True, exist_ok=True)

            archive_file = (
                archive_dir
                / f"forensic_ledger_archive_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
            )

            cursor.execute(
                "SELECT * FROM forensic_ledger WHERE created_at < ? ORDER BY created_at",
                (cutoff_ts,),
            )
            with archive_file.open("w") as f:
                for row in cursor.fetchall():
                    f.write(str(row) + "\n")

            # Delete from DB
            cursor.execute(
                "DELETE FROM forensic_ledger WHERE created_at < ?", (cutoff_ts,)
            )
            conn.commit()

            print(f"✓ Archived {old_count} old forensic records to {archive_file.name}")
            return old_count

    finally:
        conn.close()

    return 0


def cleanup_old_audit_logs(days_old: int = 30) -> int:
    """Clean up old audit logs."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cutoff = datetime.utcnow() - timedelta(days=days_old)
    cutoff_ts = cutoff.isoformat() + "Z"

    try:
        # Check if audit_logs exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"
        )
        if not cursor.fetchone():
            print("ℹ️  audit_logs table not found")
            return 0

        # Count old records
        cursor.execute(
            "SELECT COUNT(*) FROM audit_logs WHERE created_at < ?", (cutoff_ts,)
        )
        old_count = cursor.fetchone()[0]

        if old_count > 0:
            cursor.execute("DELETE FROM audit_logs WHERE created_at < ?", (cutoff_ts,))
            conn.commit()
            print(f"✓ Deleted {old_count} old audit log records")
            return old_count

    finally:
        conn.close()

    return 0


def sync_all_module_tables() -> bool:
    """Ensure all module tables are created and synced."""
    try:
        # Create all tables defined in Base
        Base.metadata.create_all(unified_engine)

        # Count tables
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        conn.close()

        print(f"✓ DB tables synced: {table_count} tables")
        write_log("vx11_canonical", f"sync:tables={table_count}")
        return True

    except Exception as e:
        print(f"❌ Error syncing tables: {e}")
        write_log("vx11_canonical", f"sync_error:{e}", level="ERROR")
        return False


def vacuum_db() -> bool:
    """Vacuum and optimize database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get current size
        size_before = DB_PATH.stat().st_size / (1024**2)

        # VACUUM to reclaim space
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()

        # Get new size
        size_after = DB_PATH.stat().st_size / (1024**2)

        if size_before > size_after:
            print(
                f"✓ VACUUM completed: {size_before:.1f}MB → {size_after:.1f}MB (saved {size_before - size_after:.1f}MB)"
            )
        else:
            print(f"✓ VACUUM completed: {size_after:.1f}MB (no change)")

        write_log(
            "vx11_canonical",
            f"vacuum:before={size_before:.1f}MB:after={size_after:.1f}MB",
        )
        return True

    except Exception as e:
        print(f"❌ VACUUM failed: {e}")
        write_log("vx11_canonical", f"vacuum_error:{e}", level="ERROR")
        return False


def validate_db_size(target_mb: int = 500) -> bool:
    """Validate DB size is under target."""
    try:
        size_mb = DB_PATH.stat().st_size / (1024**2)

        if size_mb > target_mb:
            print(f"⚠️  DB size {size_mb:.1f}MB > {target_mb}MB target")
            print(
                "   Further cleanup may be needed (archive old data, reduce model registry, etc.)"
            )
            return False

        print(f"✓ DB size OK: {size_mb:.1f}MB < {target_mb}MB target")
        write_log("vx11_canonical", f"size_ok:{size_mb:.1f}MB")
        return True

    except Exception as e:
        print(f"❌ Size validation failed: {e}")
        return False


def create_backup() -> bool:
    """Create backup of canonical DB."""
    try:
        archive_dir = ARCHIVE_DIR
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = archive_dir / f"vx11.db.canonical_{timestamp}"

        # Copy DB file
        import shutil

        shutil.copy2(DB_PATH, backup_path)

        size_mb = backup_path.stat().st_size / (1024**2)
        print(f"✓ Backup created: {backup_path.name} ({size_mb:.1f}MB)")
        write_log(
            "vx11_canonical", f"backup_created:{backup_path.name}:{size_mb:.1f}MB"
        )

        return True

    except Exception as e:
        print(f"❌ Backup failed: {e}")
        write_log("vx11_canonical", f"backup_error:{e}", level="ERROR")
        return False


def integrity_check() -> bool:
    """Run SQLite integrity check."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()

        if result[0] == "ok":
            print("✓ Database integrity check: OK")
            write_log("vx11_canonical", "integrity_check:ok")
            return True
        else:
            print(f"❌ Database integrity check failed: {result[0]}")
            write_log(
                "vx11_canonical", f"integrity_check_failed:{result[0]}", level="ERROR"
            )
            return False

    except Exception as e:
        print(f"❌ Integrity check error: {e}")
        return False


def get_db_stats() -> dict:
    """Get detailed DB statistics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Table count and row counts
        cursor.execute(
            """
            SELECT name, (SELECT COUNT(*) FROM sqlite_master WHERE type='table') as total_tables
            FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """
        )

        tables = []
        for row in cursor.fetchall():
            table_name = row[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            tables.append((table_name, row_count))

        conn.close()

        return {
            "total_tables": len(tables),
            "tables": tables,
            "size_mb": DB_PATH.stat().st_size / (1024**2),
        }

    except Exception as e:
        return {"error": str(e)}


def main():
    """Main entry point."""
    print("=" * 70)
    print("VX11 Canonical DB Generation")
    print("=" * 70)
    print()

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False

    print(f"Database: {DB_PATH}")
    print()

    # Step 1: Cleanup
    print("Step 1: Cleanup old records")
    forensic_archived = cleanup_old_forensics(days_old=30)
    audit_deleted = cleanup_old_audit_logs(days_old=30)
    print()

    # Step 2: Sync tables
    print("Step 2: Sync module tables")
    if not sync_all_module_tables():
        print("❌ Failed to sync tables")
        return False
    print()

    # Step 3: Vacuum
    print("Step 3: Optimize database (VACUUM)")
    if not vacuum_db():
        print("⚠️  VACUUM failed, continuing anyway...")
    print()

    # Step 4: Integrity check
    print("Step 4: Database integrity check")
    if not integrity_check():
        print("⚠️  Integrity check failed")
    print()

    # Step 5: Size validation
    print("Step 5: Size validation")
    size_ok = validate_db_size(target_mb=TARGET_SIZE_MB)
    print()

    # Step 6: Backup
    print("Step 6: Create backup")
    if not create_backup():
        print("⚠️  Backup failed")
    print()

    # Stats
    print("Database Statistics:")
    stats = get_db_stats()
    if "error" not in stats:
        print(f"  Total tables: {stats['total_tables']}")
        print(f"  Database size: {stats['size_mb']:.1f}MB")
        print()
        print("  Top 10 tables by row count:")
        sorted_tables = sorted(stats["tables"], key=lambda x: x[1], reverse=True)
        for table, count in sorted_tables[:10]:
            print(f"    {table:40} {count:6d} rows")
    print()

    print("=" * 70)
    if size_ok:
        print("✅ Canonical DB generation complete — DB ready for production")
    else:
        print("⚠️  Canonical DB generated, but size exceeds target (see above)")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)