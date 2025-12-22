import httpx
import json


def test_mcp():
    url = "http://localhost:8006/mcp/copilot-bridge"
    payload = {
        "method": "POST",
        "resource": "/mcp/chat",
        "params": {"message": "hello from test script"},
    }
    headers = {"X-VX11-Token": "vx11-local-token"}

    print(f"[*] Enviando solicitud a MCP: {payload}")
    try:
        resp = httpx.post(url, json=payload, headers=headers)
        print(f"[*] Status Code: {resp.status_code}")
        print(f"[*] Respuesta: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"[-] Error: {e}")


if __name__ == "__main__":
    test_mcp()
