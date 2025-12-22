import requests
import json
import time
import sqlite3
from pathlib import Path

BASE_URLS = {
    "tentaculo": "http://localhost:8000",
    "madre": "http://localhost:8001",
    "switch": "http://localhost:8002",
    "hormiguero": "http://localhost:8004",
    "spawner": "http://localhost:8008",
}

DB_PATH = "data/runtime/vx11.db"
TOKEN = "vx11-local-token"
HEADERS = {"X-VX11-Token": TOKEN}


def log_step(msg):
    print(f"\n>>> [STEP] {msg}")


def check_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def test_switch():
    log_step("Testing Switch Routing")
    payload = {
        "prompt": "Analiza el estado del sistema",
        "metadata": {"source": "audit_script"},
    }
    resp = requests.post(
        f"{BASE_URLS['switch']}/switch/route", json=payload, headers=HEADERS
    )
    print(f"Switch Response: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))

    # Verify DB
    rows = check_db("SELECT * FROM routing_events ORDER BY timestamp DESC LIMIT 1")
    if rows:
        print(f"DB Evidence (routing_events): Found entry.")
    else:
        print("DB Evidence (routing_events): NOT FOUND.")


def test_spawner():
    log_step("Testing Spawner Daughter Creation")
    payload = {
        "name": "audit_daughter",
        "cmd": "echo 'Audit check' > /app/sandbox/audit_check.txt",
        "task_type": "audit",
    }
    resp = requests.post(f"{BASE_URLS['spawner']}/spawn", json=payload, headers=HEADERS)
    print(f"Spawner Response: {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))

    spawn_uuid = data.get("spawn_uuid")
    if spawn_uuid:
        time.sleep(2)  # Wait for execution
        rows = check_db("SELECT * FROM spawns WHERE uuid = ?", (spawn_uuid,))
        if rows:
            print(f"DB Evidence (spawns): Found entry for {spawn_uuid}.")
        else:
            print(f"DB Evidence (spawns): NOT FOUND for {spawn_uuid}.")


def test_hormiguero():
    log_step("Testing Hormiguero Scan")
    resp = requests.post(
        f"{BASE_URLS['hormiguero']}/hormiguero/scan/once", headers=HEADERS
    )
    print(f"Hormiguero Response: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))

    # Verify DB
    rows = check_db("SELECT * FROM pheromone_log ORDER BY created_at DESC LIMIT 1")
    if rows:
        print(f"DB Evidence (pheromone_log): Found entry.")
    else:
        print("DB Evidence (pheromone_log): NOT FOUND.")


def test_integrated_flow():
    log_step("Testing Integrated Flow: Madre -> Switch -> Spawner")
    # We use Madre Chat to trigger a complex task
    payload = {
        "message": "Ejecuta un escaneo de seguridad y reporta anomalías",
        "session_id": "audit-session-001",
    }
    resp = requests.post(
        f"{BASE_URLS['madre']}/madre/chat", json=payload, headers=HEADERS
    )
    print(f"Madre Response: {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2))

    plan_id = data.get("plan_id")
    if plan_id:
        print(f"Plan ID: {plan_id}")
        # Wait for Madre to orchestrate
        time.sleep(5)
        rows = check_db("SELECT * FROM tasks WHERE id = ?", (plan_id,))
        if rows:
            print(f"DB Evidence (tasks): Found plan {plan_id}.")

        # Check if any daughter was spawned for this plan
        # Note: Madre v7 might use daughter_tasks table
        rows = check_db("SELECT * FROM daughter_tasks WHERE plan_id = ?", (plan_id,))
        if rows:
            print(
                f"DB Evidence (daughter_tasks): Found {len(rows)} entries for plan {plan_id}."
            )
        else:
            print(f"DB Evidence (daughter_tasks): NOT FOUND for plan {plan_id}.")


if __name__ == "__main__":
    print("=== VX11 AUDIT & FUNCTIONAL TESTING ===")
    test_switch()
    test_spawner()
    test_hormiguero()
    test_integrated_flow()
    print("\n=== TESTING COMPLETE ===")
