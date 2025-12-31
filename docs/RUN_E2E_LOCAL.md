# VX11 E2E (Local Docker)

These flows require Docker Compose on a local machine.

## Boot (production single-entrypoint)

```bash
docker compose -f docker-compose.production.yml up -d --build
```

Wait for health:

```bash
curl -f http://localhost:8000/health
```

## E2E 1 — Single entrypoint

```bash
curl -s http://localhost:8000/health | jq
curl -s http://localhost:8000/vx11/status | jq
```

## E2E 2 — Operator chat (no bypass)

```bash
curl -s -H "X-VX11-Token: $VX11_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"status"}' \
  http://localhost:8000/operator/api/chat | jq
```

## E2E 3 — Spawn daughters

```bash
curl -s -H "X-VX11-Token: $VX11_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"service":"spawner"}' \
  http://localhost:8000/operator/power/service/start | jq
```

## E2E 4 — Power windows

```bash
curl -s -H "X-VX11-Token: $VX11_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"services":["switch","spawner"],"ttl_sec":300}' \
  http://localhost:8000/operator/api/chat/window/open | jq

curl -s -H "X-VX11-Token: $VX11_TOKEN" \
  http://localhost:8000/operator/api/chat/window/status | jq
```

## Shutdown

```bash
docker compose -f docker-compose.production.yml down
```
