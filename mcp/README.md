# MCP v6.3 (Hardened)

Sandbox reforzado para puente MCP.

## Docker (compose)

- **Servicio:** `mcp`
- **Puerto:** 8006
- **Health:** `GET /health`

## Endpoints
- `GET /health`
- `POST /mcp/copilot-bridge` (recursos permitidos: `/mcp/tools`, `/mcp/chat`)
- `POST /mcp/execute_safe` (eval seguro sobre módulos whitelisted)
- `POST /mcp/execute` (alias con timeout)
- `GET /mcp/sandbox/check` (estado sandbox)

## Sandbox
- Token obligatorio (`X-VX11-Token`).
- `SAFE_MODULES`: json, math, re, random.
- Sin ejecución arbitraria, sin acceso a FS ni red externa.

## Docker
```
docker build -f mcp/Dockerfile -t vx11-mcp:latest .
docker run -p 8006:8006 vx11-mcp:latest
```

## Arranque rápido (stack local)
```
docker compose up -d tentaculo_link mcp
curl -fsS http://localhost:8006/health
```
