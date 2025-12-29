# VX11 Operator v1 Endpoints

## Canonical external entrypoint
- Base URL: `http://<tentaculo_link>:8000/operator/api/v1`
- Legacy alias: `http://<tentaculo_link>:8000/operator/api/*` → `/operator/api/v1/*`

## v1 Routes (operator backend)

### Core
- `GET  /operator/api/v1/status`
- `GET  /operator/api/v1/health`
- `GET  /operator/api/v1/env`
- `GET  /operator/api/v1/topology`
- `GET  /operator/api/v1/windows`
- `POST /operator/api/v1/chat`
- `GET  /operator/api/v1/events/stream` (SSE heartbeat)
- `GET  /operator/api/v1/logs/tail`
- `GET  /operator/api/v1/audit/runs`
- `GET  /operator/api/v1/audit/runs/{run_id}`

### Madre control (intent queue)
- `POST /operator/api/v1/madre/plan`
- `POST /operator/api/v1/madre/execute`
- `POST /operator/api/v1/madre/cancel`
- `GET  /operator/api/v1/madre/status/{id}`

### Manifestator
- `GET  /operator/api/v1/manifestator/status`
- `POST /operator/api/v1/manifestator/patchplan`
- `POST /operator/api/v1/manifestator/apply`

### Hormiguero
- `GET  /operator/api/v1/hormiguero/status`
- `POST /operator/api/v1/hormiguero/scan_once`

### Shub (stubbed with OFF_BY_POLICY)
- `GET  /operator/api/v1/shub/status`
- `GET  /operator/api/v1/shub/jobs`
- `POST /operator/api/v1/shub/jobs/submit`

### Explorer
- `GET  /operator/api/v1/explorer/presets`
- `POST /operator/api/v1/explorer/query`

## curl checks
```bash
curl -i http://localhost:8000/operator/api/v1/status
curl -sf -X POST http://localhost:8000/operator/api/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"hola"}'

curl -N http://localhost:8000/operator/api/v1/events/stream | head
```

## Notes
- `X-Correlation-Id` is returned on every response, and JSON payloads include `correlation_id`.
- When the operator window is closed (SOLO_MADRE policy), endpoints return:
  ```json
  {
    "status":"OFF_BY_POLICY",
    "service":"operator_backend",
    "message":"Disabled by SOLO_MADRE policy",
    "correlation_id":"<uuid>",
    "recommended_action":"Ask Madre to open operator window"
  }
  ```
