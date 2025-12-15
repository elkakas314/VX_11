#!/usr/bin/env python3
"""
vx11_task_router.py — Router de tareas con fallback.
Inyecta intent/task via HTTP con fallback a spawner/MCP/terminal.
Registra en copilot_actions_log (crea tabla si no existe).
"""
import sys
import json
import httpx
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data/runtime/vx11.db"
API_TOKEN = "vx11-local-token"

ROUTER = [
    ("TentaculoLink", "http://localhost:8000", "/vx11/intent"),
    ("Madre", "http://localhost:8001", "/madre/daughter/spawn"),
    ("Spawner", "http://localhost:8008", "/spawner/spawn"),
    ("MCP", "http://localhost:8006", "/mcp/sandbox/exec_cmd"),
]


def get_db():
    """Obtener conexión a BD."""
    conn = sqlite3.connect(str(DB_PATH))
    return conn


def ensure_copilot_tables():
    """Crear tabla copilot_actions_log si no existe."""
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS copilot_actions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                status TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
    finally:
        conn.close()


def log_action(
    source: str,
    action: str,
    target: Optional[str] = None,
    status: str = "pending",
    details: str = "",
):
    """Registrar acción en BD."""
    ensure_copilot_tables()
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO copilot_actions_log (timestamp, source, action, target, status, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.utcnow().isoformat() + "Z",
                source,
                action,
                target,
                status,
                details,
            ),
        )
        conn.commit()
        cursor = conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]
    finally:
        conn.close()


async def try_http_post(
    base_url: str, endpoint: str, payload: dict
) -> tuple[int, dict]:
    """Intentar POST HTTP a endpoint."""
    url = f"{base_url}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"X-VX11-Token": API_TOKEN, "Content-Type": "application/json"},
            )
            try:
                return resp.status_code, resp.json()
            except:
                return resp.status_code, {"text": resp.text}
    except httpx.TimeoutException:
        return 408, {"error": "timeout"}
    except Exception as e:
        return 500, {"error": str(e)}


async def enqueue_task(text: str):
    """Encolar tarea con router."""
    print(f"[ENQUEUE] Task: {text[:50]}...")

    ensure_copilot_tables()

    # Construir payload
    payload = {
        "source": "copilot-agent",
        "intent_type": "task",
        "description": text,
        "priority": 5,
    }

    # Intentar router secuencialmente
    for target, base_url, endpoint in ROUTER:
        print(f"  → Intentando {target} {base_url}{endpoint}...", end=" ", flush=True)

        status_code, result = await try_http_post(base_url, endpoint, payload)

        if 200 <= status_code < 300:
            task_id = result.get("task_id") or result.get("id") or str(status_code)
            print(f"✅ {status_code}")
            log_action("agent", "enqueue", target, "accepted", json.dumps(result))
            print(f"✅ Task {task_id} enqueued at {target}")
            return 0

        print(f"❌ {status_code}")

    # Fallback a terminal (último recurso)
    print(f"  → Fallback: Terminal")
    log_action("agent", "enqueue", "Terminal", "fallback", text)
    print(f"⚠️ No endpoint disponible. Task registrada para ejecución manual.")
    return 1


async def watch_task(task_id: str):
    """Monitorear task en BD."""
    print(f"[WATCH] Task {task_id}")

    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT * FROM copilot_actions_log WHERE id = ? ORDER BY timestamp DESC LIMIT 1",
            (int(task_id),),
        )
        row = cursor.fetchone()
        if row:
            print(f"  Timestamp: {row[1]}")
            print(f"  Source: {row[2]}")
            print(f"  Action: {row[3]}")
            print(f"  Target: {row[4]}")
            print(f"  Status: {row[5]}")
            print(f"  Details: {row[6]}")
        else:
            print(f"❌ Task no encontrada")
    finally:
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Uso: vx11_task_router.py <enqueue|watch> [args]")
        return 1

    cmd = sys.argv[1]

    if cmd == "enqueue":
        if len(sys.argv) < 3:
            print("Uso: vx11_task_router.py enqueue '<texto>'")
            return 1
        text = sys.argv[2]

        # Usar asyncio
        import asyncio

        return asyncio.run(enqueue_task(text))

    elif cmd == "watch":
        if len(sys.argv) < 3:
            print("Uso: vx11_task_router.py watch <task_id>")
            return 1
        task_id = sys.argv[2]

        import asyncio

        asyncio.run(watch_task(task_id))
        return 0

    else:
        print(f"❌ Comando desconocido: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
