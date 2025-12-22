import asyncio
import httpx
import sqlite3
import time
import uuid
from datetime import datetime

DB_PATH = "data/runtime/vx11.db"
HORMIGUERO_URL = "http://localhost:8004/hormiguero/scan/once"

async def stress_db():
    """Inserta tareas en task_queue continuamente."""
    print("[STRESS] Iniciando inserciones masivas en task_queue...")
    count = 0
    while count < 50:
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO task_queue (source, payload, status, enqueued_at) VALUES (?, ?, ?, ?)",
                ("stress_test", '{"data": "stress"}', "pending", datetime.utcnow().isoformat())
            )
            conn.commit()
            conn.close()
            count += 1
            if count % 10 == 0:
                print(f"[STRESS] {count} tareas insertadas.")
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"[STRESS] Error: {e}")
            await asyncio.sleep(0.5)

async def trigger_scans():
    """Llama al endpoint de scan de Hormiguero."""
    print("[SCAN] Iniciando scans concurrentes en Hormiguero...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(5):
            try:
                start = time.time()
                resp = await client.post(HORMIGUERO_URL)
                duration = time.time() - start
                if resp.status_code == 200:
                    print(f"[SCAN] Scan {i+1} completado en {duration:.2f}s")
                else:
                    print(f"[SCAN] Scan {i+1} falló: {resp.status_code}")
            except Exception as e:
                print(f"[SCAN] Error en scan {i+1}: {e}")
            await asyncio.sleep(0.5)

async def main():
    print("--- INICIANDO AUDITORÍA DE CONCURRENCIA: HORMIGUERO ---")
    await asyncio.gather(stress_db(), trigger_scans())
    print("--- AUDITORÍA COMPLETADA ---")

if __name__ == "__main__":
    asyncio.run(main())
