# VX11 v7.1 — Instrucciones Canónicas para Agentes de Código IA (Fase 0+)

**Versión:** 7.1 | **Actualizado:** 2025-12-14  
**Audiencia:** Agentes IA (GitHub Copilot, Claude, etc.) trabajando en el repositorio VX11.  
**Objetivo:** Ser productivo inmediatamente sin hacer preguntas, respetando estructura canónica y seguridad.

---

## 📐 CANON VX11: Arquitectura y Layout

### Servicios Distribuidos (HTTP-Only, Zero Coupling)

| Módulo | Puerto | Responsabilidad |
|--------|--------|---|
| **Tentáculo Link** | 8000 | Gateway auth + router HTTP + circuit breaker + Context-7 TTL |
| **Madre** | 8001 | Orquestación autónoma (planning, spawning, P&P control) |
| **Switch** | 8002 | Router IA adaptativo (local/CLI/remote, token budgets) |
| **Operator Backend API** | 8011 | `/operator/chat`, persistencia de sesiones |
| **Operator Frontend** | 8020 | Nginx sirviendo dist/ (React 18, Vite) |
| Otros módulos | 8003–8009 | Hermes, Hormiguero, Manifestator, MCP, Shubniggurath, Spawner |

### Layout de Código (Producción vs Dev)

- **`operator_backend/backend/`** — Backend Operator API (PRODUCCIÓN en docker-compose.yml puerto 8011)
- **`operator_backend/frontend/`** — Frontend React compilado (PRODUCCIÓN, Docker Nginx puerto 8020)
- **`operator/`** — Sandbox/dev (NO se usa en producción)
- **Base de datos unificada** — `data/runtime/vx11.db` (SQLite single-writer)

### No Duplicados: Estructura Rígida

- NO crear `operator_v2/` o `operator_backup/` — todo en `operator_backend/` o archiva en `operator_backend/legacy/`.
- NO cambiar puertos en `docker-compose.yml` — son puntos de rigidez arquitectónica.
- NO mover módulos raíz sin autorización — afecta toda la topología HTTP.

---

## 🧹 Reglas de Limpieza Perpetua

**Nunca tracked:**
- `node_modules/`, `dist/`, `build/`, `.venv/`, `*.egg-info/`, `__pycache__/`, `.pytest_cache/`
- `logs/*.txt` (reponable), `data/runtime/` excepto schema
- Secretos: `tokens.env`, `.env.local`, cualquier API key

**Docs canónicas (versionadas en git):**
- `docs/` — APIs, arquitectura, deployment
- `docs/audit/` — Reportes de fases ejecutadas, decisiones de diseño
- `.copilot-audit/` — Auditorías exhaustivas (Operator FASE1–4)

**Legacies:**
- Si deprecas código, archiva en `src/legacy/` con nombre + fecha, no borres.
- Actualiza imports en docs y code para no referenciar accidentalmente.

---

## 🚀 Cómo Ejecutar Flujos VX11 a Bajo Coste

### Principios

1. **Preferir HTTP local** — Usa curl a endpoints locales en lugar de spawning de procesos pesados.
2. **DeepSeek R1 solo para razonamiento pesado** — Para tareas ligeras (chat corto, chequeos), usar modelo local o Copilot mismo.
3. **Intent → Madre → Spawner → Hija → BD → Muere** — Flujo operativo: envía intent a madre, ella planifica y spawnea hijas efímeras, reportan resultados a BD, se terminan automáticamente.

### Flujo Operativo Típico (HTTP-Only, Sin Imports Cruzados)

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

### Comandos Listos (HTTP-Only)

```bash
# Health checks
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8001/madre/health
curl -s http://127.0.0.1:8002/switch/health
curl -s http://127.0.0.1:8011/operator/health

# Status del gateway
curl -s http://127.0.0.1:8000/vx11/status

# Consultar Switch (route-v5)
curl -X POST http://127.0.0.1:8002/switch/route-v5 \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","task_type":"chat"}'

# Chat Operator (esperado en fase F)
curl -X POST http://127.0.0.1:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"hola","session_id":"test-session"}'

# Context-7 (sesiones TTL, si existe)
curl -s http://127.0.0.1:8000/vx11/context-7/sessions \
  -H "X-VX11-Token: vx11-local-token"
```

### Tarea Larga (Polling)

```bash
# 1. Crear tarea (via Madre o Spawner)
TASK_ID=$(curl -X POST http://127.0.0.1:8001/madre/task \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"intent":"analyze_code","priority":5}' | jq -r .task_id)

# 2. Polling (cada 2s hasta completed|failed)
while true; do
  STATUS=$(curl -s http://127.0.0.1:8001/madre/task/$TASK_ID \
    -H "X-VX11-Token: vx11-local-token" | jq -r .status)
  case $STATUS in
    completed|failed) break ;;
    *) sleep 2 ;;
  esac
done

# 3. Obtener resultado
curl -s http://127.0.0.1:8001/madre/task/$TASK_ID \
  -H "X-VX11-Token: vx11-local-token" | jq .
```

---

## 🎓 Patrones Esenciales de Código

### 1. Crear Nuevo Módulo / Endpoint

Usar [config/module_template.py](../config/module_template.py) como template:

```python
from config.module_template import create_module_app

app = create_module_app("mi_modulo")

@app.post("/mi_modulo/mi-endpoint")
async def mi_endpoint(req: dict):
    return {"resultado": "ok"}
```

**Reglas:**
- Endpoint namespaced: `/{modulo}/{versión}/{recurso}`
- Siempre async
- Validar header `X-VX11-Token` via config.tokens

### 2. Llamar Otro Módulo (HTTP, Zero Coupling)

```python
import httpx
from config.settings import settings
from config.tokens import get_token

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

async def call_switch(prompt: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.switch_url}/switch/route-v5",
            json={"prompt": prompt, "task_type": "chat"},
            headers=AUTH_HEADERS
        )
        resp.raise_for_status()
        return resp.json()
```

**Reglas:**
- NO imports entre módulos
- Siempre usar `settings.{module}_url` (DNS-aware)
- Timeout explícito
- Header `X-VX11-Token` obligatorio
- Maneja 401/404/timeout con fallback

### 3. Base de Datos (Single-Writer Pattern)

```python
from config.db_schema import get_session, Task, Context

db = get_session("mi_modulo")
try:
    task = Task(uuid="...", name="test", module="mi_modulo", status="pending")
    db.add(task)
    db.commit()
    
    # Leer
    ctx = db.query(Context).filter_by(task_id=task.uuid).first()
finally:
    db.close()  # ✅ OBLIGATORIO en finally
```

**Reglas:**
- Siempre `db.close()` en finally
- No dejar sesiones abiertas (memory leak)
- Tablas: ver [config/db_schema.py](../config/db_schema.py) (Task, Context, OperatorSession, OperatorMessage, etc.)

### 4. Autenticación y Tokens

```python
from config.tokens import get_token

# ✅ Siempre así:
TOKEN = get_token("ENV_VAR_NAME")  # lee de env, no hardcodea
HEADERS = {"X-VX11-Token": TOKEN}
```

**Reglas:**
- NUNCA hardcodear tokens
- Siempre desde `config/tokens.py` o `config/settings.py`
- Header exacto: `X-VX11-Token`

### 5. Logging y Forensics

```python
import logging
from config.forensics import write_log

log = logging.getLogger(__name__)

log.info("evento importante")
write_log("mi_modulo", "evento_importante", level="INFO")
```

---

## 📋 MODO NO-PREGUNTAR (Copilot)

**Regla de oro:** Actúa por fases, escribe REPORTs, NO pidas confirmación.

**Auto-STOP solo si:**
- Token/credencial expuesto en código (fail CI, corrije antes de commit)
- `node_modules/` o `dist/` en git (remueve, actualiza `.gitignore`)
- Tests reventados (ejecuta localmente, diagnóstica, repara o documenta bloqueador)
- Import cruzado entre módulos detectado (refactoriza a HTTP)

**Flujo:**
1. Lee plan
2. Crea rama + tag backup
3. Implementa por fase (0 → G → F → H)
4. Valida tras cada fase (tests, compile check, curl tests)
5. Commiteao lógico por fase
6. Genera REPORT per phase en `docs/audit/`
7. Cierre: `GFH_FINAL_SUMMARY.md`

---

## 🔍 Índice de Documentos Canónicos

### Arquitectura y Diseño
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — Visión general
- [docs/API_REFERENCE.md](../docs/API_REFERENCE.md) — Endpoints detallados
- [.copilot-audit/OPERATOR_AUDIT_FASE1_REAL_STATE.md](../.copilot-audit/OPERATOR_AUDIT_FASE1_REAL_STATE.md) — Auditoría Operator (qué existe, qué no)

### Operativo y Deployment
- [docs/DEPLOYMENT_TENTACULO_LINK.md](../docs/DEPLOYMENT_TENTACULO_LINK.md) — Tentáculo Link config
- [docs/WORKFLOWS_VX11_LOW_COST.md](../docs/WORKFLOWS_VX11_LOW_COST.md) — Workflows a bajo costo (fase 0)
- [docs/API_OPERATOR_CHAT.md](../docs/API_OPERATOR_CHAT.md) — Contrato `/operator/chat` (fase F)
- [docs/OPERATOR_UI_RUNTIME.md](../docs/OPERATOR_UI_RUNTIME.md) — Cómo corre UI dev vs prod (fase H)

### Código Referencia
- [config/module_template.py](../config/module_template.py) — Template módulo FastAPI
- [config/db_schema.py](../config/db_schema.py) — Schema BD, `get_session()`
- [config/settings.py](../config/settings.py) — URLs, env vars
- [config/tokens.py](../config/tokens.py) — Gestión tokens
- [operator_backend/backend/main_v7.py](../operator_backend/backend/main_v7.py) — Backend API

### Auditorías y Reportes de Fases
- [docs/audit/PHASE0_COPILOT_CONTROLPLANE_REPORT.md](../docs/audit/PHASE0_COPILOT_CONTROLPLANE_REPORT.md)
- [docs/audit/PHASEF_OPERATOR_CHAT_IMPLEMENTATION_REPORT.md](../docs/audit/PHASEF_OPERATOR_CHAT_IMPLEMENTATION_REPORT.md)
- [docs/audit/PHASEH_OPERATOR_UI_TIER1_REPORT.md](../docs/audit/PHASEH_OPERATOR_UI_TIER1_REPORT.md)
- [docs/audit/GFH_FINAL_SUMMARY.md](../docs/audit/GFH_FINAL_SUMMARY.md)

---

## 🎯 Quick Reference: Cambios Comunes

| Necesidad | Archivos a Tocar | Patrón |
|-----------|------------------|--------|
| Agregar endpoint | [operator_backend/backend/main_v7.py](../operator_backend/backend/main_v7.py) | usar `@app.post()`, validar token, delegar HTTP si es necesario |
| Agregar tabla BD | [config/db_schema.py](../config/db_schema.py) | usar `Base` + `Column`, add `create_if_not_exists`, NO migración destructiva |
| Llamar módulo remoto | Usa `httpx.AsyncClient` + `settings.{module}_url` | ver patrón "Llamar Otro Módulo" arriba |
| Agregar variable env | [config/settings.py](../config/settings.py) + `.env` | nunca hardcodear, sempre `settings.my_var` |
| Mejorar logs | [config/forensics.py](../config/forensics.py) | usar `write_log(module, event)` |

---

## ✅ Validación Pre-Commit

Antes de hacer push (o tras cada fase):

```bash
# Compilar Python
python -m compileall tentaculo_link operator_backend || exit 1

# Tests (si existen)
pytest tests/ -q --tb=short || echo "⚠️ Tests failed, review"

# Frontend (si cambias operator_backend/frontend)
cd operator_backend/frontend && npm ci && npm run build 2>&1 | tail -20

# Docker compose (si cambias docker-compose.yml)
docker-compose config > /dev/null && echo "✓ Compose valid"

# Git status
git status
git diff --stat
```

---

## 🛡️ Límites y "NO Tocar"

**❌ NUNCA CAMBIAR:**
- Puertos en `docker-compose.yml`
- Layout de módulos raíz (`switch/`, `madre/`, etc.) sin autorización
- `tokens.env.master`, `tokens.env`
- Schema de DB (solo INSERT/SELECT existentes, sin ALTER TABLE destructiva)

**✅ SEGUROS:**
- Lógica dentro de módulos (mantener endpoint namespacing)
- Frontend en [operator_backend/frontend/src/](../operator_backend/frontend/src/)
- Config en `settings.py` (env-aware, no hardcodes)
- Tests y docs
- Mensajes de log, docstrings

---

## 📞 Contacto / Escalada

Si detectas:
- Token expuesto → crea `docs/audit/STOP_BLOCKER.md`, rota credencial
- Node_modules o dist tracked → limpiar, actualizar `.gitignore`
- Tests reventados → diagnostica, repara, documenta
- Ambigüedad arquitectónica → lee [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) y `.copilot-audit/`

---

**Versión:** 7.1  
**Mantienen:** Copilot + CI + Agentes IA  
**Última actualización:** 2025-12-14 (Fase 0)
