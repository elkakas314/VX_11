# VX11 Low-Cost Workflows (v7.1)

**Objetivo:** Patrones de uso HTTP-only, bajo consumo, sin DeepSeek excepto donde es crítico.

**Status:** AUTO-GENERATED STUB (safe)

---

## Principios Clave

1. **Preferir HTTP local** — Usa curl a endpoints locales en lugar de spawning de procesos pesados
2. **DeepSeek R1 solo para razonamiento pesado** — Para tareas ligeras (chat corto, chequeos), usar modelo local o Copilot mismo
3. **Intent → Madre → Spawner → Hija → BD → Muere** — Flujo operativo: envía intent a madre, ella planifica y spawnea hijas efímeras, reportan resultados a BD, se terminan automáticamente

---

## Flujo Operativo Típico (HTTP-Only, Sin Imports Cruzados)

```
1. INTENT (desde operator, webhook, o sistema)
   ↓
2. Tentáculo Link (gateway, valida token, circuit breaker)
   ↓
3. Madre (router table → módulo target)
   ↓
4. Switch (elige modelo: local, CLI, remote)
   ↓
5. Hermes/Local/CLI (ejecuta, responde)
   ↓
6. Response → BD (via tentaculo_link o directo)
   ↓
7. Hija efímera muere (auto-cleanup)
```

---

## Comandos Listos (HTTP-Only)

### Health checks
```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8001/madre/health
curl -s http://127.0.0.1:8002/switch/health
curl -s http://127.0.0.1:8011/operator/health
```

### Status del gateway
```bash
curl -s http://127.0.0.1:8000/vx11/status
```

### Consultar Switch (route-v5)
```bash
curl -X POST http://127.0.0.1:8002/switch/route-v5 \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","task_type":"chat"}'
```

### Chat Operator
```bash
curl -X POST http://127.0.0.1:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"hola","session_id":"test-session"}'
```

---

## Documentación Completa

Ver:
- `.github/copilot-instructions.md` — Instrucciones canónicas
- `docs/ARCHITECTURE.md` — Arquitectura completa
- `docs/API_OPERATOR_CHAT.md` — Endpoint `/operator/chat`
