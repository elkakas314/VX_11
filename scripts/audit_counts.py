#!/usr/bin/env python3
import sqlite3, json, time, sys


def main(db_path):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    rows = [r[0] for r in cur.fetchall()]
    out = []
    total_rows = 0
    for t in rows:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}";')
            c = cur.fetchone()[0]
        except Exception as e:
            c = str(e)
        out.append({"table": t, "rows": c})
        if isinstance(c, int):
            total_rows += c
    payload = {
        "tables": out,
        "total_tables": len(rows),
        "total_rows": total_rows,
        "ts": time.strftime("%Y%m%dT%H%M%SZ"),
    }
    sys.stdout.write(json.dumps(payload, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: audit_counts.py /path/to/db")
        sys.exit(2)
    main(sys.argv[1])
