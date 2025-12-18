#!/usr/bin/env python3
"""
Deep canonical extractor v2 for VX11 (read-only against runtime DB).

Produces in data/backups/:
 - vx11_CANONICAL_DISTILLED.db.new
 - vx11_CANONICAL_STATE.json.new

Follows rules: read-only runtime, aggregate large tables, no service restarts.
"""
import sqlite3
import json
import os
import time
import sys
from pathlib import Path

try:
    from scripts.cleanup_guard import is_core_path
except Exception:
    # best-effort: if helper missing, proceed but warn
    def is_core_path(p):
        return False


from datetime import datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
RUNTIME_DB = os.path.join(ROOT, "data", "runtime", "vx11.db")
BACKUP_DIR = os.path.join(ROOT, "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)
DISTILLED_DB_NEW = os.path.join(BACKUP_DIR, "vx11_CANONICAL_DISTILLED.db.new")
STATE_JSON_NEW = os.path.join(BACKUP_DIR, "vx11_CANONICAL_STATE.json.new")


def open_runtime_db(path):
    # open read-only
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def list_tables(conn):
    cur = conn.cursor()
    q = "SELECT name, type, sql FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name"
    return [
        {"name": r[0], "type": r[1], "sql": r[2]} for r in cur.execute(q).fetchall()
    ]


def table_info(conn, table):
    cur = conn.cursor()
    cols = cur.execute(f"PRAGMA table_info('{table}')").fetchall()
    cols = [
        {
            "cid": c[0],
            "name": c[1],
            "type": c[2],
            "notnull": c[3],
            "dflt_value": c[4],
            "pk": c[5],
        }
        for c in cols
    ]
    indexes = []
    try:
        for ix in cur.execute(f"PRAGMA index_list('{table}')").fetchall():
            name = ix[1]
            idxinfo = cur.execute(f"PRAGMA index_info('{name}')").fetchall()
            indexes.append(
                {
                    "name": name,
                    "unique": bool(ix[2]),
                    "columns": [c[2] for c in idxinfo],
                }
            )
    except Exception:
        pass
    return cols, indexes


def rowcount(conn, table):
    cur = conn.cursor()
    try:
        return cur.execute(f"SELECT COUNT(*) FROM '{table}'").fetchone()[0]
    except Exception:
        return None


def sample_rows(conn, table, limit=3):
    cur = conn.cursor()
    try:
        rows = cur.execute(f"SELECT * FROM '{table}' LIMIT {limit}").fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def detect_time_columns(cols):
    names = [c["name"].lower() for c in cols]
    cand = [
        n
        for n in names
        if any(
            s in n
            for s in (
                "created_at",
                "updated_at",
                "started_at",
                "ended_at",
                "timestamp",
                "time",
            )
        )
    ]
    return cand


def top_values(conn, table, col, limit=20):
    cur = conn.cursor()
    try:
        q = f"SELECT {col} as val, COUNT(*) as c FROM '{table}' GROUP BY {col} ORDER BY c DESC LIMIT {limit}"
        return [{"value": r[0], "count": r[1]} for r in cur.execute(q).fetchall()]
    except Exception:
        return []


def min_max_time(conn, table, col):
    cur = conn.cursor()
    try:
        q = f"SELECT MIN({col}) as mn, MAX({col}) as mx FROM '{table}' WHERE {col} IS NOT NULL"
        r = cur.execute(q).fetchone()
        return r[0], r[1]
    except Exception:
        return None, None


def collect_big_table_stats(conn, name, cnt, cols):
    stats = {"table": name, "rowcount": cnt}
    # detect time columns
    tcols = detect_time_columns(cols)
    time_ranges = {}
    for tc in tcols:
        mn, mx = min_max_time(conn, name, tc)
        time_ranges[tc] = {"min": mn, "max": mx}
    stats["time_ranges"] = time_ranges
    # top values for likely columns
    likely = [
        c["name"]
        for c in cols
        if c["name"].lower()
        in (
            "module",
            "service",
            "status",
            "level",
            "model",
            "provider",
            "task_type",
            "session_id",
            "task_id",
        )
    ]
    tops = {}
    for c in likely:
        tops[c] = top_values(conn, name, c, limit=20)
    stats["top_values"] = tops
    # distinct counts for id-like
    id_like = [c["name"] for c in cols if c["name"].lower().endswith(("id", "_id"))]
    distinct = {}
    cur = conn.cursor()
    for col in id_like:
        try:
            distinct[col] = cur.execute(
                f"SELECT COUNT(DISTINCT {col}) FROM '{name}'"
            ).fetchone()[0]
        except Exception:
            distinct[col] = None
    stats["distinct_counts"] = distinct
    return stats


def build_distilled_db(table_catalog, big_stats, flows, autonomy_scores):
    if os.path.exists(DISTILLED_DB_NEW):
        safe_rm_py(DISTILLED_DB_NEW)
    out = sqlite3.connect(DISTILLED_DB_NEW)
    oc = out.cursor()
    oc.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
    oc.execute(
        "INSERT INTO meta(key,value) VALUES(?,?)",
        ("generated_at", datetime.utcnow().isoformat() + "Z"),
    )
    oc.execute(
        "CREATE TABLE big_table_stats(table_name TEXT, rowcount INTEGER, json_stats TEXT)"
    )
    oc.execute(
        "CREATE TABLE flows(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, sample_json TEXT)"
    )
    oc.execute("CREATE TABLE autonomy(module TEXT, score REAL, explanation TEXT)")
    for b in big_stats:
        oc.execute(
            "INSERT INTO big_table_stats(table_name,rowcount,json_stats) VALUES(?,?,?)",
            (b["table"], b["rowcount"], json.dumps(b, default=str)),
        )
    for f in flows:
        oc.execute(
            "INSERT INTO flows(name,sample_json) VALUES(?,?)",
            (f.get("name", "flow"), json.dumps(f, default=str)),
        )
    for m, sc in autonomy_scores.items():
        oc.execute(
            "INSERT INTO autonomy(module,score,explanation) VALUES(?,?,?)",
            (m, sc["score"], str(sc.get("explanation", ""))),
        )
    out.commit()
    out.close()


def compute_flows(conn):
    cur = conn.cursor()
    flows = []
    # Heuristic: find recent intents in intents_log or operator_message and follow by tasks with similar timestamps
    try:
        msgs = cur.execute(
            "SELECT session_id, content, created_at FROM operator_message ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    except Exception:
        msgs = []
    for m in msgs:
        sample = {"session_id": m[0], "content": m[1], "created_at": m[2], "trace": []}
        try:
            tasks = cur.execute(
                "SELECT uuid,name,module,status,created_at FROM tasks WHERE result IS NOT NULL OR session_id = ? ORDER BY created_at DESC LIMIT 5",
                (m[0],),
            ).fetchall()
        except Exception:
            tasks = []
        for t in tasks:
            sample["trace"].append(
                {
                    "task_uuid": t[0],
                    "name": t[1],
                    "module": t[2],
                    "status": t[3],
                    "created_at": t[4],
                }
            )
        flows.append({"name": f"operator_session_{m[0]}", "sample": sample})
    return flows


def compute_autonomy(conn, table_stats):
    # signals per module: intents_log, task activity, daughter activity, pheromone
    cur = conn.cursor()
    modules = defaultdict(lambda: {"signals": 0, "details": {}})
    try:
        rows = cur.execute(
            "SELECT source, COUNT(*) as c FROM intents_log GROUP BY source"
        ).fetchall()
        for r in rows:
            modules[r[0]]["signals"] += r[1]
            modules[r[0]]["details"]["intents"] = r[1]
    except Exception:
        pass
    try:
        rows = cur.execute(
            "SELECT module, COUNT(*) as c FROM tasks GROUP BY module"
        ).fetchall()
        for r in rows:
            modules[r[0]]["signals"] += r[1]
            modules[r[0]]["details"]["tasks"] = r[1]
    except Exception:
        pass
    try:
        rows = cur.execute(
            "SELECT module_creator, COUNT(*) as c FROM daughters GROUP BY module_creator"
        ).fetchall()
        for r in rows:
            k = r[0] or "unknown"
            modules[k]["signals"] += r[1]
            modules[k]["details"]["daughters"] = r[1]
    except Exception:
        pass
    try:
        rows = cur.execute(
            "SELECT module, COUNT(*) as c FROM feromona_events GROUP BY module"
        ).fetchall()
        for r in rows:
            modules[r[0]]["signals"] += r[1]
            modules[r[0]]["details"]["pheromones"] = r[1]
    except Exception:
        pass
    max_sig = max((v["signals"] for v in modules.values()), default=0)
    autonomy = {}
    for m, v in modules.items():
        score = (v["signals"] / max_sig) if max_sig > 0 else 0.0
        autonomy[m] = {"score": round(score, 3), "explanation": v["details"]}
    return autonomy


def main():
    conn = open_runtime_db(RUNTIME_DB)
    tables = list_tables(conn)
    table_catalog = {"generated_at": datetime.utcnow().isoformat() + "Z", "tables": {}}
    table_stats = {}
    big_stats = []
    for t in tables:
        name = t["name"]
        cols, indexes = table_info(conn, name)
        cnt = rowcount(conn, name)
        sample = sample_rows(conn, name, limit=3)
        table_catalog["tables"][name] = {
            "count": cnt,
            "columns": cols,
            "indexes": indexes,
            "sample": sample,
        }
        table_stats[name] = cnt
        if isinstance(cnt, int) and cnt > 100000:
            b = collect_big_table_stats(conn, name, cnt, cols)
            big_stats.append(b)
    catalog_path = os.path.join(BACKUP_DIR, "canonical.table_catalog.json.new")
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(table_catalog, f, indent=2, ensure_ascii=False, default=str)
    flows = compute_flows(conn)
    autonomy = compute_autonomy(conn, table_stats)
    build_distilled_db(table_catalog, big_stats, flows, autonomy)
    state = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "tables_count": len(tables),
            "big_tables": [b["table"] for b in big_stats],
            "empty_tables": [n for n, c in table_stats.items() if c == 0],
            "autonomy_level": (
                "low" if sum(v["score"] for v in autonomy.values()) < 1 else "medium"
            ),
        },
        "table_catalog_path": catalog_path,
        "flows_sample_count": len(flows),
        "autonomy": autonomy,
        "modules_detected": sorted(list({n.split("_")[0] for n in table_stats.keys()})),
    }
    with open(STATE_JSON_NEW, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    conn.close()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    final_db = os.path.join(BACKUP_DIR, "vx11_CANONICAL_DISTILLED.db")
    final_json = os.path.join(BACKUP_DIR, "vx11_CANONICAL_STATE.json")
    for p in (final_db, final_json):
        if os.path.exists(p):
            # abort if target is considered CORE
            if is_core_path(p):
                print(f"ABORT: existing path marked CORE: {p}", file=sys.stderr)
                sys.exit(2)
            bak = p + f".bak_{timestamp}"
            safe_move_py(p, bak)
    safe_move_py(DISTILLED_DB_NEW, final_db)
    safe_move_py(STATE_JSON_NEW, final_json)
    print("FINAL_DB=", final_db)
    print("FINAL_JSON=", final_json)
    print("CATALOG=", catalog_path)


if __name__ == "__main__":
    main()
