#!/usr/bin/env python3
"""
VX11 Runtime Truth: Sondar servicios, endpoints, y generar reporte.
No-destructive: solo lectura de vx11.db si escribes a copilot_*, en modo UPSERT.
Output: docs/audit/VX11_RUNTIME_TRUTH_REPORT.md
"""

import os
import sys
import json
import socket
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("ERROR: requests not installed. Install with: pip install requests")
    sys.exit(1)

import sqlite3

# Config
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "runtime" / "vx11.db"
REPORT_PATH = REPO_ROOT / "docs" / "audit" / "VX11_RUNTIME_TRUTH_REPORT.md"

# Services to probe
SERVICES = [
    {
        "name": "tentaculo_link",
        "port": 8000,
        "endpoints": ["/health", "/healthz", "/vx11/status"],
    },
    {
        "name": "madre",
        "port": 8001,
        "endpoints": ["/health", "/healthz", "/madre/health"],
    },
    {
        "name": "switch",
        "port": 8002,
        "endpoints": ["/health", "/healthz", "/switch/health"],
    },
    {
        "name": "hermes",
        "port": 8003,
        "endpoints": ["/health", "/healthz", "/hermes/health"],
    },
    {
        "name": "hormiguero",
        "port": 8004,
        "endpoints": ["/health", "/healthz", "/hormiguero/status"],
    },
    {
        "name": "manifestator",
        "port": 8005,
        "endpoints": ["/health", "/healthz", "/drift"],
    },
    {"name": "mcp", "port": 8006, "endpoints": ["/health", "/healthz"]},
    {
        "name": "shubniggurath",
        "port": 8007,
        "endpoints": ["/health", "/healthz", "/shub/health"],
    },
    {"name": "spawner", "port": 8008, "endpoints": ["/health", "/healthz"]},
    {
        "name": "operator",
        "port": 8011,
        "endpoints": ["/health", "/healthz", "/operator/vx11/overview"],
    },
]


def get_token():
    """Read VX11_TOKEN from env if available."""
    return os.environ.get("VX11_TOKEN", "vx11-local-token")


def request_with_retry(url, timeout=5, max_retries=1):
    """HTTP GET with retries."""
    session = requests.Session()
    retry = Retry(total=max_retries, connect=1, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    token = get_token()
    headers = {"X-VX11-Token": token}

    try:
        resp = session.get(url, timeout=timeout, headers=headers)
        return resp.status_code, resp.text[:200], time.time()
    except requests.exceptions.Timeout:
        return None, "timeout", time.time()
    except requests.exceptions.ConnectionError:
        return None, "connection_error", time.time()
    except Exception as e:
        return None, str(e)[:50], time.time()


def probe_service(service):
    """Probe a single service; return status dict."""
    name = service["name"]
    port = service["port"]

    result = {
        "name": name,
        "port": port,
        "status": "UNKNOWN",
        "http_code": None,
        "latency_ms": None,
        "endpoint_ok": None,
        "snippet": None,
    }

    for endpoint in service["endpoints"]:
        url = f"http://127.0.0.1:{port}{endpoint}"
        start = time.time()
        code, body, _ = request_with_retry(url, timeout=3)
        elapsed_ms = (time.time() - start) * 1000

        if code == 200:
            result["status"] = "OK"
            result["http_code"] = 200
            result["latency_ms"] = round(elapsed_ms)
            result["endpoint_ok"] = endpoint
            result["snippet"] = body[:100]
            break
        elif code and code >= 400:
            if result["http_code"] is None:
                result["http_code"] = code
                result["latency_ms"] = round(elapsed_ms)

    if result["http_code"] is None and result["status"] == "UNKNOWN":
        result["status"] = "BROKEN"
    elif result["status"] == "UNKNOWN":
        result["status"] = "BROKEN" if result["http_code"] else "UNKNOWN"

    return result


def write_db_copilot_tables(results):
    """Write results to copilot_runtime_services (UPSERT)."""
    if not DB_PATH.exists():
        print(f"[DB] {DB_PATH} not found; skipping DB write.")
        return

    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        # Check if copilot_runtime_services exists; if not, we'll skip (read-only mode)
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='copilot_runtime_services';"
        )
        if not cur.fetchone():
            print("[DB] copilot_runtime_services not found; skipping write.")
            conn.close()
            return
        conn.close()
    except Exception as e:
        print(f"[DB] Error checking table: {e}")
        return

    # Try write mode if possible (fallback to print only)
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        for r in results:
            cur.execute(
                """
                INSERT OR REPLACE INTO copilot_runtime_services 
                (service_name, port, status, http_code, latency_ms, endpoint_ok, snippet, checked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    r["name"],
                    r["port"],
                    r["status"],
                    r["http_code"],
                    r["latency_ms"],
                    r["endpoint_ok"],
                    r["snippet"],
                    datetime.utcnow().isoformat(),
                ),
            )
        conn.commit()
        print(f"[DB] Written {len(results)} rows to copilot_runtime_services")
        conn.close()
    except Exception as e:
        print(f"[DB] Write skipped (read-only or error): {e}")


def generate_report(results):
    """Generate markdown report."""
    report_lines = [
        "# VX11 Runtime Truth Report",
        f"\n**Generated:** {datetime.utcnow().isoformat()}Z",
        "\n## Service Status Matrix",
        "\n| Service | Port | Status | HTTP Code | Latency (ms) | Endpoint | Snippet |",
        "|---------|------|--------|-----------|--------------|----------|---------|",
    ]

    for r in results:
        status_emoji = (
            "✓" if r["status"] == "OK" else "✗" if r["status"] == "BROKEN" else "?"
        )
        report_lines.append(
            f"| {r['name']} | {r['port']} | {status_emoji} {r['status']} | {r['http_code'] or '—'} | "
            f"{r['latency_ms'] or '—'} | {r['endpoint_ok'] or '—'} | {r['snippet'][:30] if r['snippet'] else '—'}... |"
        )

    # Summary
    ok_count = sum(1 for r in results if r["status"] == "OK")
    broken_count = sum(1 for r in results if r["status"] == "BROKEN")
    unknown_count = sum(1 for r in results if r["status"] == "UNKNOWN")

    report_lines.extend(
        [
            "\n## Summary",
            f"- **OK:** {ok_count}/{len(results)}",
            f"- **BROKEN:** {broken_count}/{len(results)}",
            f"- **UNKNOWN:** {unknown_count}/{len(results)}",
            "\n## Details",
            "```json",
            json.dumps(results, indent=2),
            "```",
        ]
    )

    return "\n".join(report_lines)


def main():
    print("=" * 70)
    print("VX11 Runtime Truth: Service Probe")
    print("=" * 70)

    results = []
    for service in SERVICES:
        print(f"  Probing {service['name']} (port {service['port']})...", end=" ")
        result = probe_service(service)
        results.append(result)
        print(f"→ {result['status']}")

    print("\n[Report] Generating markdown...", end=" ")
    report = generate_report(results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    print(f"✓ {REPORT_PATH}")

    print("[DB] Writing to copilot_runtime_services...", end=" ")
    write_db_copilot_tables(results)
    print()

    print("\n" + "=" * 70)
    print("✅ Runtime truth complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
