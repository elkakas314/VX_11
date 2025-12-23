import httpx
import json
import time
import asyncio
from datetime import datetime

# Configuración
BASE_URL = "http://localhost"
TENTACULO_URL = f"{BASE_URL}:8000"
MADRE_URL = f"{BASE_URL}:8001"
SWITCH_URL = f"{BASE_URL}:8002"
HORMIGUERO_URL = f"{BASE_URL}:8004"
TOKEN = "vx11-local-token"
HEADERS = {"X-VX11-Token": TOKEN}


async def run_exhaustive_validation():
    print(f"=== VX11 EXHAUSTIVE FLOW VALIDATION - {datetime.utcnow().isoformat()} ===")
    metrics = {}

    # --- FLUJO 1: Tentaculo Link -> Switch -> Hermes -> Madre ---
    print("\n[1] Probando Flujo: Tentaculo Link -> Switch -> Hermes -> Madre")
    start_time = time.time()
    try:
        payload = {
            "task_type": "system",
            "payload": {
                "message": "run a test daughter task to verify spawner integration",
                "intent": "run",
            },
            "metadata": {"source": "exhaustive_test"},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{TENTACULO_URL}/operator/task", json=payload, headers=HEADERS
            )
            duration = time.time() - start_time
            metrics["flow_1_duration"] = duration

            if resp.status_code == 200:
                data = resp.json()
                print(f"[+] Respuesta recibida en {duration:.2f}s")
                # Madre v7 devuelve el plan en 'actions'
                actions = data.get("actions", [])
                steps = [a.get("step") for a in actions]
                print(f"[+] Pasos ejecutados: {steps}")
                metrics["flow_1_steps"] = steps
                metrics["flow_1_ok"] = True
            else:
                print(f"[-] Error en Flujo 1: {resp.status_code} - {resp.text}")
                metrics["flow_1_ok"] = False
    except Exception as e:
        print(f"[-] Excepción en Flujo 1: {e}")
        metrics["flow_1_ok"] = False

    # --- FLUJO 2: Madre -> Hija Efímera -> Switch -> Acción ---
    print("\n[2] Probando Flujo: Madre -> Hija Efímera -> Switch -> Acción")
    # Este flujo ya se disparó en el paso anterior si 'SPAWNER_REQUEST' estuvo en los pasos.
    # Vamos a verificar la BD para ver si la hija se creó y ejecutó.
    await asyncio.sleep(5)  # Esperar a que la hija termine

    try:
        # Consultar tareas hijas recientes
        async with httpx.AsyncClient() as client:
            # Usamos un endpoint de hormiguero o spawner si existe para ver estado,
            # o simplemente verificamos via logs/DB en el reporte final.
            # Por ahora, asumimos que si el paso SPAWNER_REQUEST fue 'daughter_spawned', el flujo inició.
            spawner_step = next(
                (a for a in actions if a.get("step") == "SPAWNER_REQUEST"), None
            )
            if (
                spawner_step
                and spawner_step.get("result", {}).get("status") == "daughter_spawned"
            ):
                print("[+] Hija efímera disparada correctamente.")
                metrics["flow_2_ok"] = True
            else:
                print("[-] No se detectó disparo de hija efímera en el plan de Madre.")
                metrics["flow_2_ok"] = False
    except Exception as e:
        print(f"[-] Error verificando Flujo 2: {e}")
        metrics["flow_2_ok"] = False

    # --- FLUJO 3: Hormiguero -> Manifestator -> Reina -> Madre/Switch ---
    print("\n[3] Probando Flujo: Hormiguero -> Manifestator -> Reina -> Madre/Switch")
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{HORMIGUERO_URL}/hormiguero/scan/once", headers=HEADERS
            )
            duration = time.time() - start_time
            metrics["flow_3_duration"] = duration

            if resp.status_code == 200:
                data = resp.json()
                print(f"[+] Scan completado en {duration:.2f}s")
                results = data.get("results", {})
                incidents = data.get("incidents", [])
                print(f"[+] Resultados de hormigas: {list(results.keys())}")
                print(f"[+] Incidentes creados: {len(incidents)}")
                metrics["flow_3_incidents"] = len(incidents)
                metrics["flow_3_ok"] = True
            else:
                print(f"[-] Error en Flujo 3: {resp.status_code} - {resp.text}")
                metrics["flow_3_ok"] = False
    except Exception as e:
        print(f"[-] Excepción en Flujo 3: {e}")
        metrics["flow_3_ok"] = False

    # --- REPORTE DE MÉTRICAS ---
    print("\n=== RESUMEN DE MÉTRICAS ===")
    print(json.dumps(metrics, indent=2))

    with open("docs/audit/20251222/EXHAUSTIVE_METRICS.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    asyncio.run(run_exhaustive_validation())
