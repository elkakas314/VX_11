#!/usr/bin/env python3
import sqlite3, json, os
from datetime import datetime

DB = "data/runtime/vx11.db"
if not os.path.exists(DB):
    raise SystemExit("DB not found: " + DB)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
# get tables
cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
)
tables = [r[0] for r in cur.fetchall()]
json_schema = {
    "generated_at": datetime.utcnow().isoformat() + "Z",
    "database": DB,
    "tables": [],
}
for t in tables:
    info = {"table": t}
    # columns
    try:
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = []
        for c in cur.fetchall():
            cols.append(
                {
                    "cid": c[0],
                    "name": c[1],
                    "type": c[2],
                    "notnull": bool(c[3]),
                    "dflt_value": c[4],
                    "pk": bool(c[5]),
                }
            )
        info["columns"] = cols
    except Exception as e:
        info["columns"] = []
    # foreign keys
    try:
        cur.execute(f"PRAGMA foreign_key_list('{t}')")
        fks = []
        for fk in cur.fetchall():
            fks.append(
                {
                    "id": fk[0],
                    "seq": fk[1],
                    "table": fk[2],
                    "from": fk[3],
                    "to": fk[4],
                    "on_update": fk[5],
                    "on_delete": fk[6],
                    "match": fk[7],
                }
            )
        info["foreign_keys"] = fks
    except Exception:
        info["foreign_keys"] = []
    # row count
    try:
        cur2 = conn.execute(f"SELECT COUNT(1) as c FROM '{t}'")
        cnt = cur2.fetchone()[0]
    except Exception:
        cnt = None
    info["rows"] = cnt
    # status
    lower = t.lower()
    status = "EMPTY (READY)" if (cnt == 0) else "ACTIVE"
    if any(x in lower for x in ("legacy", "old", "deprecated")):
        status = "LEGACY - preserved"
    info["status"] = status
    # module heuristic
    module = ""
    mod_map = [
        ("madre", "madre"),
        ("hermes", "hermes"),
        ("hija", "hormiguero"),
        ("hijas", "hormiguero"),
        ("operator", "operator"),
        ("switch", "switch"),
        ("shub", "shubniggurath"),
        ("spawner", "spawner"),
        ("cli", "hermes"),
        ("model", "hermes"),
        ("ia_decision", "switch"),
    ]
    for k, m in mod_map:
        if k in lower:
            module = m
            break
    info["module"] = module
    json_schema["tables"].append(info)

# write JSON
os.makedirs("docs/audit", exist_ok=True)
with open("docs/audit/DB_SCHEMA_v7_FINAL.json", "w", encoding="utf-8") as f:
    json.dump(json_schema, f, indent=2, ensure_ascii=False)
# write markdown map
with open("docs/audit/DB_MAP_v7_FINAL.md", "w", encoding="utf-8") as f:
    f.write("# VX11 Database Map (generated)\n\n")
    f.write(f"Generated at: {datetime.utcnow().isoformat()}Z\n\n")
    f.write(f"Database file: {DB}\n\n")
    f.write("## Tables\n\n")
    for t in json_schema["tables"]:
        f.write(f"### {t['table']} — {t['status']}\n\n")
        if t.get("module"):
            f.write(f"- Module: {t['module']}\n")
        f.write(f"- Rows: {t.get('rows')}\n")
        f.write("- Columns:\n")
        for c in t["columns"]:
            f.write(
                f"  - {c['name']} ({c['type']}){' PK' if c['pk'] else ''}{' NOT NULL' if c['notnull'] else ''}\n"
            )
        if t["foreign_keys"]:
            f.write("- Foreign keys:\n")
            for fk in t["foreign_keys"]:
                f.write(
                    f"  - {fk['from']} -> {fk['table']}.{fk['to']} (on_update={fk['on_update']}, on_delete={fk['on_delete']})\n"
                )
        f.write("\n")

print("Wrote docs/audit/DB_SCHEMA_v7_FINAL.json and docs/audit/DB_MAP_v7_FINAL.md")
# integrity check and size
try:
    cur = conn.execute("PRAGMA integrity_check;")
    integrity = cur.fetchone()[0]
except Exception as e:
    integrity = str(e)
size = os.path.getsize(DB)
with open("docs/audit/DB_MAP_v7_META.txt", "w") as f:
    f.write(f"integrity:{integrity}\nsize_bytes:{size}\n")
print("integrity:", integrity, "size_bytes", size)
conn.close()
