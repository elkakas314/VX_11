#!/usr/bin/env python3
"""
VX11 Functional Flow Test Script
Generado por DeepSeek R1 (Simulado) para auditoría exhaustiva de módulos.
"""

import httpx
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# --- CONFIGURACIÓN DE SERVICIOS ---
BASE_URL = "http://localhost"
# Puertos solicitados: 8000-8008 y 8011
PORTS = {
    "tentaculo_link": 8000,
    "madre": 8001,
    "switch": 8002,
    "hermes": 8003,
    "hormiguero": 8004,
    "manifestator": 8005,
    "mcp": 8006,
    "shubniggurath": 8007,
    "spawner": 8008,
    "operator-backend": 8011,
}

# Ruta de reporte según solicitud
AUDIT_TS = "20251222T080000Z"
AUDIT_DIR = Path(f"docs/audit/{AUDIT_TS}")
RESULTS_FILE = AUDIT_DIR / "functional_flow_results.json"


def load_tokens_from_file() -> Dict[str, str]:
    """Carga tokens desde tokens.env si existe."""
    tokens = {}
    env_file = Path("tokens.env")
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    tokens[k.strip()] = v.strip().strip('"').strip("'")
    return tokens


def get_auth_headers() -> Dict[str, str]:
    """
    Resuelve el token canónico para X-VX11-Token.
    Prioridad: Env Var > tokens.env > Default (vx11-local-token)
    """
    file_tokens = load_tokens_from_file()
    token = (
        os.environ.get("VX11_TOKEN")
        or file_tokens.get("VX11_TOKEN")
        or file_tokens.get("VX11_TENTACULO_LINK_TOKEN")
        or "vx11-local-token"
    )
    return {
        "X-VX11-Token": token,
        "Content-Type": "application/json",
        "User-Agent": "VX11-Functional-Tester/1.0",
    }


def main():
    headers = get_auth_headers()
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": {
            "token_used": (
                f"{headers['X-VX11-Token'][:4]}...{headers['X-VX11-Token'][-4:]}"
                if len(headers["X-VX11-Token"]) > 8
                else "***"
            ),
            "header": "X-VX11-Token",
        },
        "health_checks": {},
        "functional_tests": {},
    }

    print(f"[*] Iniciando VX11 Functional Flow Test...")
    print(f"[*] Destino: {BASE_URL}")
    print(f"[*] Token: {results['environment']['token_used']}")

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:

        # 1. VERIFICACIÓN DE /health (8000-8008, 8011)
        print("[*] Ejecutando Health Checks...")
        for name, port in PORTS.items():
            url = f"{BASE_URL}:{port}/health"
            try:
                resp = client.get(url, headers=headers)
                results["health_checks"][name] = {
                    "port": port,
                    "status": "UP" if resp.status_code == 200 else "DOWN",
                    "code": resp.status_code,
                    "payload": resp.json() if resp.status_code == 200 else resp.text,
                }
            except Exception as e:
                results["health_checks"][name] = {
                    "port": port,
                    "status": "ERROR",
                    "error": str(e),
                }

        # 2. TEST MADRE (Directo 8001)
        print("[*] Probando Madre Chat (Directo)...")
        try:
            resp = client.post(
                f"{BASE_URL}:8001/madre/chat",
                json={"message": "Hola Madre, ¿estás lista?"},
                headers=headers,
            )
            results["functional_tests"]["madre_chat"] = {
                "endpoint": "/madre/chat",
                "ok": resp.status_code == 200,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
            }
        except Exception as e:
            results["functional_tests"]["madre_chat"] = {"ok": False, "error": str(e)}

        # 3. TEST SWITCH (Directo 8002)
        print("[*] Probando Switch Route (Directo)...")
        try:
            payload = {
                "prompt": "Necesito procesar un flujo de audio DSP para Shubniggurath",
                "metadata": {"type": "audio_dsp", "priority": "high"},
                "source": "functional_test",
            }
            resp = client.post(
                f"{BASE_URL}:8002/switch/shub/route", json=payload, headers=headers
            )
            results["functional_tests"]["switch_route"] = {
                "endpoint": "/switch/shub/route",
                "ok": resp.status_code == 200,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
            }
        except Exception as e:
            results["functional_tests"]["switch_route"] = {"ok": False, "error": str(e)}

        # 4. TEST SPAWNER (Puerto 8008)
        print("[*] Probando Spawner (Puerto 8008)...")
        try:
            payload = {
                "name": "dummy_functional_test",
                "cmd": "echo 'VX11_SPAWN_SUCCESS'",
                "ttl_seconds": 30,
                "intent": "test",
            }
            resp = client.post(
                f"{BASE_URL}:8008/spawner/spawn", json=payload, headers=headers
            )
            results["functional_tests"]["spawner_spawn"] = {
                "endpoint": "/spawner/spawn",
                "ok": resp.status_code == 200,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
            }
        except Exception as e:
            results["functional_tests"]["spawner_spawn"] = {
                "ok": False,
                "error": str(e),
            }

        # 5. TEST HORMIGUERO (Directo 8004)
        print("[*] Probando Hormiguero Status...")
        try:
            resp = client.get(f"{BASE_URL}:8004/hormiguero/status", headers=headers)
            results["functional_tests"]["hormiguero_status"] = {
                "endpoint": "/hormiguero/status",
                "ok": resp.status_code == 200,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
            }
        except Exception as e:
            results["functional_tests"]["hormiguero_status"] = {
                "ok": False,
                "error": str(e),
            }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"[+] Auditoría completada con éxito.")
    print(f"[+] Resultados guardados en: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
