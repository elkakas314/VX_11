#!/usr/bin/env python3
"""E2E debug: llama al endpoint /switch/debug/select-provider del switch local.

Usa urllib para no depender de paquetes externos.
"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:8002/switch/debug/select-provider"

payload = {
    "prompt": "Prueba E2E: seleccionar proveedor",
    "metadata": {"task_type": "chat", "category": "general"},
    "source": "operator",
}


def main():
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            print("Response:", body)
            try:
                obj = json.loads(body)
            except Exception as e:
                print("ERROR: invalid json response", e)
                return 2

            if "provider" in obj:
                print("E2E OK: provider=", obj.get("provider"))
                return 0
            else:
                print("E2E FAIL: no provider in response")
                return 3

    except Exception as e:
        print("E2E ERROR: request failed:", e)
        return 4


if __name__ == "__main__":
    sys.exit(main())
