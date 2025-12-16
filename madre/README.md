# Madre v7 — Production Orchestrator

**Versión:** 7.0 | **Estado:** Production-Ready | **Puerto:** 8001

## 📋 Rol Canonical

Madre es el **orquestador autónomo** de VX11 v7. Su responsabilidad es:

1. **Recibir INTENTs** desde Operator, Hormiguero, Webhooks, o CLI
2. **Parsear INTENTs** con fallback a parser local si Switch no disponible
3. **Clasificar RIESGO** (LOW | MED | HIGH) + requerir confirmación si procede
4. **Generar PLANes** (secuencias de pasos) específicos para cada intent
5. **Ejecutar PLANes** delegando a Switch/Hermes/Hormiguero/Manifestator/Shub
6. **Monitorizar ESTADO** (PENDING → RUNNING → WAITING → DONE/ERROR)
7. **Persistir en BD** (intents_log, tasks, context, madre_actions, daughter_tasks si spawn requerido)

**🔴 CRITICO: Madre NO lanza hijas efímeras.** Solo GENERA SOLICITUDES a BD (daughter_tasks INSERT). La ejecución real la hace Spawner (implementación futura).

## 🏗️ Arquitectura Modular (core/)

```
madre/
├── core/
│   ├── __init__.py           # Module exports
│   ├── models.py             # Pydantic contracts (IntentV2, PlanV2, etc.)
│   ├── db.py                 # MadreDB: repository pattern (11 métodos)
│   ├── parser.py             # FallbackParser: intent parsing sin Switch
│   ├── policy.py             # PolicyEngine: risk classification + tokens
│   ├── planner.py            # Planner: intent → plan generation
│   ├── runner.py             # Runner: async plan execution
│   └── delegation.py         # DelegationClient: HTTP calls + daughter_tasks
├── main.py                   # FastAPI app (7 endpoints)
├── main_legacy.py            # Backup de versión anterior
├── main_v7_production.py     # Reference implementation (completa)
└── README.md                 # Esta documentación
```

## 🌐 Endpoints (7 Total) — Contratos P0

| Endpoint | Método | Contrato | Status |
|----------|--------|----------|--------|
| /health | GET | HealthResponse | ✅ |
| /madre/chat | POST | ChatRequest → ChatResponse | ✅ |
| /madre/control | POST | ControlRequest → ControlResponse | ✅ |
| /madre/plans | GET | → List[PlanSummary] | ✅ |
| /madre/plans/{id} | GET | → PlanDetail | ✅ |
| /madre/plans/{id}/confirm | POST | {confirm_token} → Confirmed | ✅ |

### Ejemplos de Curl

**Health check:**
```bash
curl -s http://127.0.0.1:8001/health -H "X-VX11-Token: vx11-local-token" | jq .
```

**Chat simple:**
```bash
curl -X POST http://127.0.0.1:8001/madre/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"mix these 3 stems","session_id":"sess-123"}'
```

**Chat audio (AUDIO_ENGINEER mode):**
```bash
curl -X POST http://127.0.0.1:8001/madre/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"apply eq and compression to vocal stem","session_id":"sess-123"}'
```

**Control action (HIGH RISK - requires confirmation):**
```bash
curl -X POST http://127.0.0.1:8001/madre/control \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"target":"shub","action":"delete","params":{}}'
```

## 🗄️ Base de Datos — Tablas Canónicas

**Madre SOLO escribe en:**
- `intents_log` — INSERT al inicio, UPDATE al cierre (result_status)
- `madre_actions` — INSERT audit trail (cada decision, action, confirmation)
- `tasks` — INSERT plan, UPDATE status/result/error
- `context` — INSERT session context, tokens, plan metadata
- `daughter_tasks` — INSERT ONLY (cuando spawn requerido) - Spawner ejecuta luego

**Madre NUNCA escribe en:**
- spawns, hijas_runtime, (cualquier tabla "de ejecución")

## 🔄 Pipeline Típico

**Caso simple (LOW risk, sin confirmación):**
```
POST /madre/chat "mix 3 stems"
  ↓
Crea intent_log entry
  ↓
Switch/Fallback: Extrae DSL
  ↓
PolicyEngine: risk=LOW
  ↓
Planner: genera 3 steps (CALL_SWITCH, CALL_SHUB, NOOP)
  ↓
Runner: ejecuta async
  ↓
ChatResponse(status=DONE) + UPDATE intents_log
```

**Caso HIGH risk (delete, reset, etc):**
```
POST /madre/control target=shub action=delete
  ↓
PolicyEngine: risk=HIGH, requires_confirmation=True
  ↓
Genera confirm_token (secrets.token_urlsafe)
  ↓
ControlResponse(status=pending_confirmation, token=...)
  ↓
Usuario: POST /madre/plans/{id}/confirm token=...
  ↓
PolicyEngine: valida token (timing-safe secrets.compare_digest)
  ↓
Ejecuta plan
  ↓
Response(status=confirmed)
```

## 🧪 Pruebas (P0 Mandatory)

```bash
# Verificar estructura
python3 -m py_compile madre/core/*.py madre/main.py

# Tests unitarios
cd /home/elkakas314/vx11
pytest tests/test_madre*.py -v --tb=short

# Health check en vivo
curl -s http://127.0.0.1:8001/health | jq .

# Full pipeline test
python3 scripts/test_madre_pipeline.py
```

## 🔐 Seguridad

- **Tokens:** Confirmation tokens son `secrets.token_urlsafe(16)` (22 chars, timing-safe)
- **Auth:** Todos endpoints requieren header `X-VX11-Token`
- **Audit:** Append-only forensics en `forensic/madre/logs/`
- **DB:** intents_log nunca se borra (forensic trail permanente)

## 📦 Arquitectura de Módulos

### core/models.py
Pydantic contracts (IntentV2, PlanV2, StepV2, ChatRequest, ChatResponse, etc.)
- Enums: ModeEnum, RiskLevel, StatusEnum, StepType
- Garantiza forma de response en todos endpoints

### core/db.py (MadreDB)
Repository pattern encapsula TODOS los accesos a BD:
- `create_intent_log()` — INSERT
- `close_intent_log()` — UPDATE con result_status
- `create_task()` — INSERT task
- `update_task()` — UPDATE task status/result
- `set_context()`, `get_context()` — Session state
- `record_action()` — Audit trail
- `request_spawner_task()` — INSERT daughter_tasks (sin ejecutar)

### core/parser.py (FallbackParser)
Keyword-based DSL parser. Funciona cuando Switch está DOWN:
- Detecta domain (audio, code, system, etc.)
- Extrae action (mix, eq, analyze, delete, etc.)
- Infiere risk (LOW→MED→HIGH based on keywords)

### core/policy.py (PolicyEngine)
Risk classification + confirmation tokens:
- `classify_risk(target, action)` → RiskLevel
- `requires_confirmation(risk)` → bool
- `generate_confirm_token()` → token seguro
- `validate_confirm_token(provided, stored)` → timing-safe check

### core/planner.py (Planner)
Intent → Plan conversion:
- `plan(intent)` → PlanV2
- Genera steps ordenados para MADRE o AUDIO_ENGINEER mode
- Marks blocking steps con status=WAITING

### core/runner.py (Runner)
Async plan execution:
- `execute_plan(plan)` → ejecuta steps con timeouts
- Delega a Switch, Hermes, Hormiguero, Manifestator, Shub
- Stops si blocking step en WAITING

### core/delegation.py (DelegationClient)
HTTP calls + daughter_tasks insertion:
- `call_module(module, endpoint, payload)` → httpx request
- `request_spawner_hija()` → INSERT daughter_tasks (sin ejecutar)
- `check_dependencies()` → health check a todos

## 🚀 Deployment

```bash
# Build docker image
docker build -f madre/Dockerfile -t vx11-madre:latest .

# Run
docker run -p 8001:8001 \
  -e VX11_TOKEN=vx11-local-token \
  -e DATABASE_URL=sqlite:///data/runtime/vx11.db \
  -v /data:/app/data \
  vx11-madre:latest

# Health check
curl http://127.0.0.1:8001/health
```

## 📞 Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| `/health` Switch unknown | Switch OFF pero Madre sigue ok | Usar fallback parser |
| Plan stuck en WAITING | Hijo esperando confirmación o Spawner execution | Ver daughter_tasks, verificar Spawner |
| 401 Unauthorized | Token header faltante o incorrecto | Incluir `X-VX11-Token: vx11-local-token` |
| confirm_token inválido | Token expirado o typo | Generar nuevo con POST /madre/control |

## 📚 Referencias

- [Instrucciones Copilot](../../.github/copilot-instructions.md)
- [ARQUITECTURA VX11](../docs/ARCHITECTURE.md)
- [DB Schema](../config/db_schema.py)

---

**v7.0.0** | **2025-01-08** | ✅ Production Ready
