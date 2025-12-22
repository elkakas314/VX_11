import httpx
import json
import time

BASE_URL = "http://localhost:8001"
TOKEN = "vx11-local-token"
HEADERS = {"X-VX11-Token": TOKEN, "Content-Type": "application/json"}


def test_integrated_flow():
    print("[*] Enviando comando a Madre para disparar flujo integrado...")
    payload = {"message": "run a test daughter task to verify spawner integration"}

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{BASE_URL}/madre/chat", json=payload, headers=HEADERS)
            print(f"[*] Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"[*] Respuesta de Madre: {json.dumps(data, indent=2)}")

                # Verificar si hay un paso de SPAWNER_REQUEST
                actions = data.get("actions", [])
                spawn_step = next(
                    (a for a in actions if "SPAWNER_REQUEST" in str(a.get("step", ""))),
                    None,
                )

                if spawn_step:
                    print(
                        "[+] Flujo integrado detectado: Madre generó una solicitud de Spawner."
                    )
                    print(f"[+] Resultado del paso: {spawn_step.get('result')}")
                else:
                    print("[-] No se detectó el paso de Spawner en la respuesta.")
            else:
                print(f"[-] Error: {resp.text}")
    except Exception as e:
        print(f"[-] Excepción: {e}")


if __name__ == "__main__":
    test_integrated_flow()
