#!/usr/bin/env python3
"""
Generate VX11 Database Schema Map
Creates comprehensive documentation of DB schema, indices, and relationships.

Output:
- docs/audit/DB_MAP_v7_FINAL.md (human-readable schema map)
- docs/audit/DB_SCHEMA_v7_FINAL.json (machine-readable schema)
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.forensics import write_log


DB_PATH = Path("data/runtime/vx11.db")
OUTPUT_DIR = Path("docs/audit")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_all_tables() -> list[str]:
    """Get list of all tables in database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    conn.close()
    return tables


def get_table_schema(table_name: str) -> dict:
    """Get schema info for a single table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for col_id, name, type_, not_null, default, pk in cursor.fetchall():
        columns.append(
            {
                "id": col_id,
                "name": name,
                "type": type_,
                "nullable": not_null == 0,
                "default": default,
                "primary_key": pk == 1,
            }
        )

    # Get indices
    cursor.execute(f"PRAGMA index_list({table_name})")
    indices = []
    for seq, name, unique, origin, partial in cursor.fetchall():
        # Get index columns
        cursor.execute(f"PRAGMA index_info({name})")
        index_cols = [col[2] for col in cursor.fetchall()]

        indices.append(
            {
                "name": name,
                "unique": unique == 1,
                "columns": index_cols,
            }
        )

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]

    # Get table size (approximate)
    cursor.execute(
        f"SELECT page_count * page_size FROM (SELECT page_count FROM pragma_page_count()) a, (SELECT page_size FROM pragma_page_size()) b"
    )
    try:
        total_size = cursor.fetchone()[0]
    except:
        total_size = 0

    conn.close()

    return {
        "name": table_name,
        "row_count": row_count,
        "columns": columns,
        "indices": indices,
        "approximate_size_bytes": (
            total_size // len(get_all_tables()) if get_all_tables() else 0
        ),
    }


def generate_markdown_schema() -> str:
    """Generate markdown documentation of schema."""
    tables = get_all_tables()

    md = "# VX11 Database Schema Map\n\n"
    md += f"**Generated:** {datetime.utcnow().isoformat()}Z\n"
    md += f"**Database:** {DB_PATH}\n"
    md += f"**Total Tables:** {len(tables)}\n\n"

    # Database size info
    try:
        db_size_mb = DB_PATH.stat().st_size / (1024**2)
        md += f"**Database Size:** {db_size_mb:.1f}MB\n\n"
    except:
        pass

    # Table of contents
    md += "## Table of Contents\n\n"
    for i, table in enumerate(tables, 1):
        md += f"{i}. [{table}](#{table})\n"

    md += "\n---\n\n"

    # Detailed schemas
    total_rows = 0
    for table in tables:
        schema = get_table_schema(table)
        total_rows += schema["row_count"]

        md += f"## {table}\n\n"
        md += f"**Rows:** {schema['row_count']:,}\n\n"

        if schema["indices"]:
            indices_list = ", ".join([f"`{idx['name']}`" for idx in schema["indices"]])
            md += f"**Indices:** {indices_list}\n\n"

        md += "### Columns\n\n"
        md += "| # | Name | Type | PK | Nullable | Default |\n"
        md += "|---|------|------|----|---------|---------|\n"

        for col in schema["columns"]:
            pk_mark = "✓" if col["primary_key"] else ""
            nullable_mark = "✓" if col["nullable"] else ""
            default_val = col["default"] or ""

            md += f"| {col['id']} | `{col['name']}` | {col['type']} | {pk_mark} | {nullable_mark} | {default_val} |\n"

        md += "\n"

    # Summary
    md += "---\n\n"
    md += "## Summary Statistics\n\n"
    md += f"- **Total Tables:** {len(tables)}\n"
    md += f"- **Total Rows:** {total_rows:,}\n"
    md += f"- **Database Size:** {DB_PATH.stat().st_size / (1024**2):.1f}MB\n"

    return md


def generate_json_schema() -> dict:
    """Generate JSON schema document."""
    tables = get_all_tables()

    schema_map = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "database_path": str(DB_PATH),
            "database_size_mb": DB_PATH.stat().st_size / (1024**2),
            "total_tables": len(tables),
        },
        "tables": {},
    }

    for table in tables:
        schema = get_table_schema(table)
        schema_map["tables"][table] = schema

    return schema_map


def main():
    """Main entry point."""
    print("=" * 70)
    print("VX11 Database Schema Map Generator")
    print("=" * 70)
    print()

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return False

    print(f"Reading schema from: {DB_PATH}")
    print()

    # Generate markdown
    print("Generating Markdown schema...")
    md_content = generate_markdown_schema()
    md_path = OUTPUT_DIR / "DB_MAP_v7_FINAL.md"
    md_path.write_text(md_content)
    print(f"✓ Created: {str(md_path)}")

    # Generate JSON
    print("Generating JSON schema...")
    json_schema = generate_json_schema()
    json_path = OUTPUT_DIR / "DB_SCHEMA_v7_FINAL.json"
    json_path.write_text(json.dumps(json_schema, indent=2))
    print(f"✓ Created: {str(json_path)}")

    # Print summary
    print()
    print("=" * 70)
    tables = get_all_tables()
    print(f"✅ Schema map generated:")
    print(f"   Tables: {len(tables)}")
    print(f"   Markdown: {md_path.name}")
    print(f"   JSON: {json_path.name}")
    print("=" * 70)

    write_log("vx11_canonical", f"schema_map_generated:tables={len(tables)}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
