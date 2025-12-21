#!/usr/bin/env python3
import argparse
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request


def _find_table(conn: sqlite3.Connection) -> Optional[str]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in cur.fetchall()]
    if "routing_events" in tables:
        return "routing_events"
    for name in tables:
        if "routing" in name and "event" in name:
            return name
    return None


def _pick_columns(conn: sqlite3.Connection, table: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    provider = (
        "selected_provider"
        if "selected_provider" in cols
        else ("provider" if "provider" in cols else ("provider_id" if "provider_id" in cols else None))
    )
    cost = (
        "estimated_cost"
        if "estimated_cost" in cols
        else ("cost_estimated" if "cost_estimated" in cols else ("score" if "score" in cols else None))
    )
    reason = (
        "reason"
        if "reason" in cols
        else (
            "explainability"
            if "explainability" in cols
            else ("explanation" if "explanation" in cols else ("reasoning_short" if "reasoning_short" in cols else None))
        )
    )
    ts = "created_at" if "created_at" in cols else ("timestamp" if "timestamp" in cols else ("created" if "created" in cols else None))
    return provider, cost, reason, ts


def _calc_from_db(db_path: str, limit: int) -> Dict:
    conn = sqlite3.connect(db_path)
    table = _find_table(conn)
    if not table:
        conn.close()
        return {"status": "NV", "reason": "routing_events table not found"}
    provider_col, cost_col, reason_col, ts_col = _pick_columns(conn, table)
    if not (provider_col and cost_col and reason_col):
        conn.close()
        return {
            "status": "NV",
            "reason": "required columns missing",
            "table": table,
            "columns": {"provider": provider_col, "cost": cost_col, "reason": reason_col, "timestamp": ts_col},
        }
    order = f"ORDER BY {ts_col} DESC" if ts_col else "ORDER BY rowid DESC"
    query = f"SELECT {provider_col}, {cost_col}, {reason_col} FROM {table} {order} LIMIT {limit}"
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    coherent = 0
    breakdown = Counter()
    for provider, cost, reason in rows:
        ok_provider = provider is not None and str(provider).strip() != ""
        ok_cost = cost is not None or cost == 0
        ok_reason = reason is not None and str(reason).strip() != ""
        if ok_provider and ok_cost and ok_reason:
            coherent += 1
        if provider is not None:
            breakdown[str(provider)] += 1
    total = len(rows)
    pct = round((coherent / total * 100) if total else 0.0, 4)
    return {
        "status": "OK",
        "source": "db",
        "table": table,
        "query": query,
        "N": total,
        "coherent": coherent,
        "coherencia_pct": pct,
        "breakdown_by_provider": breakdown,
    }


def _calc_from_http(limit: int) -> Dict:
    url = "http://127.0.0.1:8002/switch/debug/select-provider"
    coherent = 0
    total = 0
    breakdown = Counter()
    samples = []
    for i in range(limit):
        req = urllib.request.Request(
            url,
            data=json.dumps({"prompt": f"routing check {i}"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            return {"status": "NV", "reason": f"http error: {exc}"}
        total += 1
        provider = body.get("selected_provider") or body.get("provider")
        cost = body.get("estimated_cost") if "estimated_cost" in body else body.get("cost_estimated")
        reason = body.get("reason") or body.get("explainability") or body.get("explanation")
        ok_provider = provider is not None and str(provider).strip() != ""
        ok_cost = cost is not None or cost == 0
        ok_reason = reason is not None and str(reason).strip() != ""
        if ok_provider and ok_cost and ok_reason:
            coherent += 1
        if provider is not None:
            breakdown[str(provider)] += 1
        if len(samples) < 5:
            samples.append(body)
    pct = round((coherent / total * 100) if total else 0.0, 4)
    return {
        "status": "OK",
        "source": "http",
        "url": url,
        "N": total,
        "coherent": coherent,
        "coherencia_pct": pct,
        "breakdown_by_provider": breakdown,
        "samples": samples,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/runtime/vx11.db")
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    result = _calc_from_db(args.db, args.limit)
    if result.get("status") != "OK":
        result = _calc_from_http(25)
    result["generated_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    out_path = outdir / "coherencia_routing_calc.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
