# CORE MVP: Execution Flow

## Flow Diagram

```
Client (external)
    |
    | POST /vx11/intent + token
    |
    v
[tentaculo_link:8000]
    |
    +---> TokenGuard (validate X-VX11-Token)
    |
    +---> Check require.switch
    |        |
    |        +---> If true → return 200 ERROR off_by_policy
    |        |
    |        +---> If false → continue
    |
    +---> HTTP POST http://madre:8001/vx11/intent (proxy)
    |
    v
[madre:8001]
    |
    +---> Store in intent_log DB
    |
    +---> Check require.spawner
    |        |
    |        +---> If true → create spawner task, return QUEUED
    |        |
    |        +---> If false → execute fallback plan, return DONE
    |
    v
Return to tentaculo_link
    |
    v
Return to client (200 + response)
```

## Request/Response Example

### REQUEST: require.switch=false (synchronous)

```bash
POST /vx11/intent HTTP/1.1
Host: localhost:8000
X-VX11-Token: vx11-test-token
Content-Type: application/json

{
  "intent_type": "chat",
  "text": "Analyze system status",
  "require": {"switch": false, "spawner": false},
  "priority": "P0"
}
```

### RESPONSE: 200 OK (DONE)

```json
{
  "correlation_id": "19049ea7-02ca-4fce-8efc-dfa3d3dc3050",
  "status": "DONE",
  "mode": "MADRE",
  "provider": "fallback_local",
  "response": {
    "plan_id": "a1fbd2f4-8c43-4833-891e-08d6c89971b4",
    "steps_executed": 1,
    "result": "intent_processed",
    "notes": "fallback_local execution"
  },
  "error": null,
  "degraded": false,
  "timestamp": "2026-01-01T15:34:40.821645"
}
```

---

### REQUEST: require.switch=true (off_by_policy)

```bash
POST /vx11/intent HTTP/1.1
Host: localhost:8000
X-VX11-Token: vx11-test-token
Content-Type: application/json

{
  "intent_type": "exec",
  "text": "Execute via switch",
  "require": {"switch": true, "spawner": false},
  "priority": "P1"
}
```

### RESPONSE: 200 OK (ERROR off_by_policy)

```json
{
  "correlation_id": "94da7e0b-c607-434f-8c3f-1d823313aed9",
  "status": "ERROR",
  "mode": "FALLBACK",
  "provider": null,
  "response": {
    "reason": "switch required but SOLO_MADRE policy active",
    "policy": "SOLO_MADRE"
  },
  "error": "off_by_policy",
  "degraded": false,
  "timestamp": "2026-01-01T15:34:40.891882"
}
```

---

### REQUEST: require.spawner=true (async)

```bash
POST /vx11/intent HTTP/1.1
Host: localhost:8000
X-VX11-Token: vx11-test-token
Content-Type: application/json

{
  "intent_type": "spawn",
  "text": "Spawn a task",
  "require": {"switch": false, "spawner": true},
  "priority": "P1",
  "payload": {"task_name": "analysis", "ttl": 60}
}
```

### RESPONSE: 200 OK (QUEUED)

```json
{
  "correlation_id": "1a251e05-d181-4e10-be50-352e08f38412",
  "status": "QUEUED",
  "mode": "SPAWNER",
  "provider": "spawner",
  "response": {
    "task_id": "a821f10c-3130-44e3-a2de-6cd6a8be3549"
  },
  "error": null,
  "degraded": false,
  "timestamp": "2026-01-01T15:34:40.949794"
}
```

---

### GET RESULT

```bash
GET /vx11/result/1a251e05-d181-4e10-be50-352e08f38412 HTTP/1.1
Host: localhost:8000
X-VX11-Token: vx11-test-token
```

### RESPONSE: 200 OK

```json
{
  "correlation_id": "1a251e05-d181-4e10-be50-352e08f38412",
  "status": "DONE",
  "result": {
    "note": "synchronous execution completed"
  },
  "error": null,
  "mode": "MADRE",
  "provider": "fallback_local",
  "timestamp": "2026-01-01T15:34:41.037137"
}
```

---

## Key Decisions

1. **200 Status Code for Policy Errors**: off_by_policy returns 200 with error field (not 423) for MVP simplicity
2. **Fallback Execution**: No real plan computation (MVP), just acknowledge intent + return status
3. **SOLO_MADRE Default**: switch never available (policy enforced in tentaculo_link)
4. **Spawner Path**: If `require.spawner=true`, immediate QUEUED response with task_id (async)
5. **Token from Env**: Never hardcoded; resolved at runtime from docker-compose env vars

---

## Troubleshooting

### No response from /vx11/intent
- Check madre logs: `docker-compose logs madre`
- Verify token in request matches `VX11_TENTACULO_LINK_TOKEN` from docker-compose.full-test.yml
- Ensure madre container is healthy: `docker-compose ps`

### off_by_policy always returned
- This is expected for `require.switch=true` (SOLO_MADRE policy)
- To enable switch: would need to modify policy (future enhancement, Phase 2)

### Spawner task not executing
- Spawner service may not be levantado (check `docker-compose ps`)
- Status is QUEUED but execution depends on spawner availability
- For MVP, spawner is optional (graceful degradation)
