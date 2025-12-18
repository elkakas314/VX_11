#!/usr/bin/env python3
"""
Acceptance E2E runner for Switch/Hermes (local, mockable).

Steps:
 - Enqueue N tasks via local HTTP /switch/task
 - Run QueueConsumer.run_once() in a loop to process them
 - Collect results and write report to docs/audit/SWITCH_HERMES_ACCEPTANCE.md

This script is safe for local runs; it respects `VX11_MOCK_PROVIDERS`.
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

import sys
import time
import json
import urllib.request
import urllib.error
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
REPORT = os.path.join(ROOT, "docs", "audit", "SWITCH_HERMES_ACCEPTANCE.md")
DB_REPORT = os.path.join(ROOT, "docs", "audit", "SWITCH_HERMES_ACCEPTANCE_DB.json")

N = int(os.getenv("E2E_N", "5"))
URL = "http://127.0.0.1:8002/switch/task"
TOKEN = os.getenv("VX11_TOKEN", os.getenv("VX11_LOCAL_TOKEN", "vx11-local-token"))


def post_task(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=data,
        headers={"Content-Type": "application/json", "X-VX11-Token": TOKEN},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return f"HTTPError: {e.code} {e.reason}"
    except Exception as e:
        return f"ERROR: {e}"


def run_consumer_loops(limit=30):
    # run python consumer in-process
    import sys

    sys.path.insert(0, ROOT)
    from switch.workers.queue_consumer import QueueConsumer

    qc = QueueConsumer()
    processed_total = 0
    for _ in range(limit):
        p = qc.run_once()
        processed_total += p
        if p == 0:
            time.sleep(0.2)
        else:
            time.sleep(0.05)
    return processed_total


def inspect_db():
    import sqlite3

    db = os.path.join(ROOT, "data", "runtime", "vx11.db")
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    rows = {}
    try:
        cur.execute("SELECT COUNT(*) FROM switch_queue_v2")
        rows["switch_queue_v2"] = cur.fetchone()[0]
    except Exception:
        rows["switch_queue_v2"] = None
    try:
        cur.execute("SELECT COUNT(*) FROM ia_decisions")
        rows["ia_decisions"] = cur.fetchone()[0]
    except Exception:
        rows["ia_decisions"] = None
    conn.close()
    return rows


def main():
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    report = [f"Acceptance E2E - {datetime.utcnow().isoformat()}Z"]
    report.append(f"Enqueueing {N} tasks to {URL}")
    for i in range(N):
        payload = {
            "task_type": "language",
            "payload": {"text": f"E2E test {i}", "idx": i},
            "source": "operator",
        }
        resp = post_task(payload)
        report.append(f"task {i} enqueue resp: {resp}")

    report.append("Running consumer loops (30 iterations)...")
    processed = run_consumer_loops(limit=60)
    report.append(f"Processed total: {processed}")

    db_stats = inspect_db()
    report.append("DB Stats:")
    report.append(json.dumps(db_stats, indent=2))

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    with open(DB_REPORT, "w", encoding="utf-8") as f:
        json.dump(db_stats, f, indent=2)
    print("Acceptance report written:", REPORT)


if __name__ == "__main__":
    main()