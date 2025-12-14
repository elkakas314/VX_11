# VX11 v7.1 — Instrucciones Canónicas para Agentes de Código IA

























































































































































































































































































































































→ Testa y ¡listo! 🚀→ Implementa según **OPERATOR_FASE3_AI_INTEGRATION.md**→ Luego **OPERATOR_FASE2_BACKEND_CONTRACT.md**→ Empieza por **OPERATOR_RESUMEN_EJECUTIVO.md****¿LISTO?**---```✓ Typing animation suave✓ Error messages claros✓ Persistencia localStorage✓ Fallback a local si backend down✓ Token auth funciona✓ Backend real conectado✓ Chat no es echo✓ Operator renderiza```## ✅ ÉXITO = CUANDO---**Mejoras (FASE 4):** +3-4h (próximas semanas)| **Total** | **5-6h** | MVP listo || Deployment | 30 min | Deploy checklist || Testing | 1-2h | Test checklist || Implementar backend | 2-3h | FASE2 + FASE3 || Leer auditoría | 1.5h | RESUMEN + FASE1-3 ||-------|--------|-----------|| Tarea | Tiempo | Referencia |## 📊 TIMEFRAME ESTIMADO---```3. Implementa TIER 1 primero2. Verifica "❌ MEJORAS A NO HACER"1. Consulta FASE4 "Mejoras TIER 1/2/3"```### Para mejoras```3. Valida tests2. Checa FASE3 "Error Cases"1. Consulta FASE1 "🚨 RIESGOS ACTUALES"```### Para bugs```5. Testa (10 min)4. Implementa3. Lee FASE2 + FASE3 (45 min)2. Entiende qué implementar1. Lee RESUMEN_EJECUTIVO.md (15 min)```### Para iniciar## 🎯 QUICK REFERENCE---8. ✅ **Timeouts** — 15s default para operaciones7. ✅ **Error handling** — No crash nunca6. ✅ **Logging** — write_log(module, event) siempre5. ✅ **Single-writer BD** — db.close() en finally4. ✅ **Type hints** — Python 3.10+ obligatorio3. ✅ **Async/await** — Todo I/O es async2. ✅ **Token auth** — X-VX11-Token en todos los headers1. ✅ **HTTP-only** — No imports entre módulos**NUNCA OLVIDES:**## 🎓 CONVENCIONES VX11---```  → URLs de módulos (switch_url, operator_backend_url)config/settings.py    → Cómo obtener VX11_OPERATOR_TOKENconfig/tokens.py    → Patrón FastAPI canónico (imita)config/module_template.py```### Archivos de Referencia```  ✅ NO CAMBIEStentaculo_link/main_v7.py    ✅ NO CAMBIESmadre/main.py    ✅ NO CAMBIES, solo LLAMAswitch/main.py    ✅ Todo está OK, NO CAMBIESoperator/src/```### Archivos a NO Modificar```  → Agregar OperatorSession, OperatorMessageconfig/db_schema.py    → Agregar @app.post("/operator/chat")operator_backend/backend/main_v7.py```### Archivos a Modificar## 📞 REFERENCIAS INTERNAS---- [ ] Logging/forensics registra eventos- [ ] Token auth funciona- [ ] LocalStorage persist funciona- [ ] Fallback a local si backend down- [ ] Chat recibe respuestas reales- [ ] Operator frontend auto-detecta backend- [ ] Tests pasando (curl happy path + error cases)- [ ] Env variables configuradas (.env)- [ ] DB tables creadas (OperatorSession, OperatorMessage)- [ ] Backend `/operator/chat` implementado## 🚀 DEPLOYMENT CHECKLIST---```5. Debería recibir respuesta real (no echo)4. Escribe "test"3. Debería decir "◆ Backend conectado" en header2. Chat tab1. Abre http://localhost:5173```### Test 4: Frontend puede conectar```# Esperado: timeout, Operator frontend fallback a local# Timeout (15+ seconds)# Esperado: 401 Unauthorized  -d '{"message": "test"}'  -H "X-VX11-Token: wrong" \curl -X POST http://localhost:8011/operator/chat \# Token invalid```bash### Test 3: Error cases```# Esperado: { "reply": "...", "session_id": "...", "metadata": {...} }  -d '{"message": "¿Qué es Madre?"}'  -H "X-VX11-Token: vx11-local-token" \  -H "Content-Type: application/json" \curl -X POST http://localhost:8011/operator/chat \```bash### Test 2: Happy path```# Esperado: 200 OK o 404 (frontend detecta y switchea a local)  -H "X-VX11-Token: vx11-local-token"curl -X OPTIONS http://localhost:8011/operator/chat \# Frontend debe detectar endpoint```bash### Test 1: Backend detectable## 🧪 VALIDAR IMPLEMENTACIÓN---**Ahora sí, implementa**   - [ ] Sé variables de entorno   - [ ] Sé timeouts y error cases   - [ ] Sé qué no cambiar (Operator frontend, Switch, Madre)   - [ ] Sé dónde (operator_backend/backend/main_v7.py)   - [ ] Sé exactamente qué implementar4. Confirma:   - Conoce error handling   - Entiende BD persistence   - Ve flujo completo3. Lee **FASE3_AI_INTEGRATION.md** (25 min)   - Sabe variables de entorno   - Conoce especificación exacta2. Lee **FASE2_BACKEND_CONTRACT.md** (20 min)   - Sabe qué implementar   - Entiende qué existe1. Lee **RESUMEN_EJECUTIVO.md** (15 min)**Antes de escribir código:**## 📋 CHECKLIST ANTES DE IMPLEMENTAR---```OperatorSession, OperatorMessage (tablas a crear)```python→ FASE3, sección "💾 FLUJO DE PERSISTENCIA"### "¿Cuál es el esquema de BD?"→ FASE1, sección "🚨 RIESGOS ACTUALES"→ FASE4, sección "❌ MEJORAS A NO HACER"### "¿Qué puede romper?"→ FASE3, sección "💾 FLUJO DE PERSISTENCIA"→ FASE2, sección "📊 VARIABLES DE ENTORNO FINALES"### "¿Qué variables de entorno se necesitan?"```8 pasos desde Frontend → Backend → Switch → DeepSeek → Frontend```→ FASE3, diagrama ASCII grande en inicio### "¿Cómo fluye un mensaje desde chat a IA?"```Todos los headers y campos opcionalesRequest/Response JSON exacto```→ FASE2, sección "📋 CONTRATO MÍNIMO DE CHAT"### "¿Cuál es el contrato exacto del endpoint?"```Explicación detallada de cada componenteLines: useChat.ts (185 L), ChatView.tsx (125 L), chat-api.ts (111 L)```→ FASE1, sección "💬 CHAT ACTUAL — ESTADO DETALLADO"### "¿Cómo funciona el chat ahora?"## 🔍 CÓMO BUSCAR INFORMACIÓN ESPECÍFICA---```    └─ Resultado final    ├─ Riesgos mitigados    ├─ Plan 3-semana    ├─ Qué NO hacer    ├─ Mejoras TIER 3 (futuro, bloqueado)    ├─ Mejoras TIER 2 (nice to have)    ├─ Mejoras TIER 1 (implementar primero)└── OPERATOR_FASE4_ENHANCEMENTS.md (mejoras)││   └─ Resultado final│   ├─ Cambios por módulo│   ├─ Error cases│   ├─ Observabilidad│   ├─ Seguridad & validaciones│   ├─ Qué hace cada módulo│   ├─ Persistencia en BD│   ├─ Flujo paso a paso│   ├─ Arquitectura completa (diagrama ASCII)├── OPERATOR_FASE3_AI_INTEGRATION.md (implementación)││   └─ Arquitectura final│   ├─ Env variables│   ├─ Timeouts│   ├─ Autenticación│   ├─ Testing del contrato│   ├─ Flujo Frontend→Backend→IA│   ├─ Dónde vivir el endpoint│   ├─ Contrato mínimo de chat├── OPERATOR_FASE2_BACKEND_CONTRACT.md (especificación)││   └─ Riesgos│   ├─ Qué funciona│   ├─ Qué está desconectado│   ├─ Configuración│   ├─ WebSocket client│   ├─ chat-api service│   ├─ useChat hook (flow detallado)│   ├─ Chat actual (línea por línea)│   ├─ Arquitectura UI│   ├─ Bootstrap chain├── OPERATOR_AUDIT_FASE1_REAL_STATE.md (auditoría sin cambios)││   └─ Próximos pasos│   ├─ Implementación recomendada│   ├─ DB schema│   ├─ Flujo completo│   ├─ Contrato endpoint│   ├─ Análisis detallado│   ├─ 4 Fases de auditoría│   ├─ Visión general├── OPERATOR_RESUMEN_EJECUTIVO.md (entrada principal).copilot-audit/```## 📖 ESTRUCTURA DE DOCUMENTOS---- Tabla de archivos y líneas- Sección "💬 CHAT ACTUAL — ESTADO DETALLADO"- Sección "📋 QUÉ FUNCIONA AHORA"→ Lee: **OPERATOR_AUDIT_FASE1_REAL_STATE.md**### Escenario 5: "Necesito entender la estructura del código"- Qué NO hacer- Mejoras TIER 2 (bajo riesgo)- Mejoras TIER 1 (0 riesgo)→ Lee: **OPERATOR_FASE4_ENHANCEMENTS.md**### Escenario 4: "Quiero agregar mejoras a Operator"- Checklist de componentes- Sección "🚨 RIESGOS ACTUALES"- Sección "🎯 QUÉ ESTÁ DESCONECTADO AHORA"→ Lee: **OPERATOR_AUDIT_FASE1_REAL_STATE.md**### Escenario 3: "El chat no funciona, ¿qué está roto?"**Salida esperada:** Código completo en `operator_backend/backend/main_v7.py`3. **OPERATOR_FASE3_AI_INTEGRATION.md** (cómo conectar a Switch/DeepSeek)2. **OPERATOR_FASE2_BACKEND_CONTRACT.md** (especificación exacta)1. **OPERATOR_RESUMEN_EJECUTIVO.md** (visión general)→ Lee en orden:### Escenario 2: "Necesito implementar `/operator/chat` backend"- Flujo completo de chat- Qué funciona, qué NO existe- Qué es Operator→ Lee: **OPERATOR_RESUMEN_EJECUTIVO.md** (15 min)### Escenario 1: "Quiero entender qué hace Operator"## 🎯 ESCENARIOS TÍPICOS---**Para:** Agentes IA trabajando en Operator o integraciones con Operator**Actualizado:** 2025-12-14 | **Versión:** 7.1 | **Enfoque:** Productividad inmediata en codebase tentacular + arquitectura autónoma.

---

## 🏛️ Arquitectura Canónica (The Big Picture)

**10 Módulos Independientes (HTTP-Only Communication):**

| Módulo | Puerto | Responsabilidad |
|--------|--------|---|
| **Tentáculo Link** | 8000 | Gateway auth + proxy HTTP + CONTEXT-7 session tracking |
| **Madre** | 8001 | Orquestación autónoma (planning, spawning, P&P control) |
| **Switch** | 8002 | Router IA adaptativo (GA optimizer, Hermes CLI fusion, Shub detection) |
| **Hermes** | 8003 | Registry distribuido (modelos locales, CLI tools, proveedores remote) |
| **Hormiguero** | 8004 | Paralelización inteligente (Queen + 8 Ants, GA operadores, pheromones) |
| **Manifestator** | 8005 | Auditoría + drift detection + patch generation + aplicación |
| **MCP** | 8006 | Conversacional (Model Context Protocol, VS Code bridge) |
| **Shubniggurath** | 8007 | DSP audio + audio reasoning (pipelines: analyzer, mix, reaper) |
| **Spawner** | 8008 | Gestor de procesos efímeros (daughter tasks, reintentos) |
| **Operator** | 8011 | Dashboard ejecutivo (React 18, chat, browser automation, monitoring) |

**BD Unificada:** `data/runtime/vx11.db` (SQLite 3, single-writer, acceso seguro via `config.db_schema.get_session()`)

**Autenticación:** Header `X-VX11-Token` (gestión centralizada en `config.tokens.get_token("VX11_GATEWAY_TOKEN")`)

---

## 🔗 Patrones Obligatorios VX11

### 1️⃣ Inicializar Módulo FastAPI
```python
from config.module_template import create_module_app

app = create_module_app("mi_modulo")
# ✅ Incluye: middleware forense, /health, /control, logging centralizado, crash dumps

@app.get("/mi_modulo/health")
def health():
    return {"module": "mi_modulo", "status": "ok"}

# ✅ Todos los endpoints bajo /mi_modulo/* (namespaced)
```

### 2️⃣ Acceso a Base de Datos (Single-Writer Pattern)
```python
from config.db_schema import get_session, Task, Context

db = get_session("mi_modulo")
try:
    task = Task(name="test", module="mi_modulo", action="exec", status="pending")
    db.add(task)
    db.commit()
    
    # Leer contexto
    ctx = db.query(Context).filter_by(task_id=task.uuid).first()
finally:
    db.close()  # ✅ SIEMPRE cerrar en finally
```

### 3️⃣ Comunicación HTTP Inter-Módulos (HTTP-Only, Zero Coupling)
```python
import httpx
from config.settings import settings
from config.tokens import get_token

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

# ✅ Usar settings.switch_url, settings.madre_url, etc. (DNS-aware)
async with httpx.AsyncClient(timeout=8.0) as client:
    resp = await client.post(
        f"{settings.switch_url}/switch/route-v5",
        json={"prompt": "test", "metadata": {}},
        headers=AUTH_HEADERS
    )
    result = resp.json()  # ✅ Siempre JSON
```

### 4️⃣ Convenciones de Código Esenciales
- **Async/await:** Todo I/O es async (httpx.AsyncClient, FastAPI)
- **Type hints:** Obligatorio Python 3.10+ (improve IDE support)
- **Logging:** `log = logging.getLogger(__name__)` + `write_log(module_name, event)`
- **Tokens:** NUNCA hardcode; siempre via `get_token(env_var)` o `settings.api_token`
- **Puertos:** NO cambiar en docker-compose.yml (rigidez arquitectónica = estabilidad)

---

## 🛡️ Límites de Edición (INMUTABLES)

**❌ NO TOCAR:**
- `tokens.env`, `tokens.env.master` — credenciales prohibidas
- Puertos en `docker-compose.yml` — no renombrar servicios
- Módulos raíz (`switch/`, `madre/`, etc.) — movimientos sin autorización
- DB schema migrations — solo GET/POST existentes, no ALTER
- Imports cruzados entre módulos — sólo HTTP permitido

**✅ SÍ EDITAR:**
- Lógica dentro de módulos (mantener namespacing de endpoints)
- Frontend operator (React/TypeScript bajo `operator/src/`)
- Config valores en `settings.py` (env-aware, no hardcodes)
- Tests y documentación
- Mensajes de log, docstrings, comments

---

## ⚙️ Workflows Prácticos

### Ejecutar Tests (CI-like local validation)
```bash
# Configurar Python environment
cd /home/elkakas314/vx11
source .venv/bin/activate

# Ejecutar suite completa (~52 tests)
pytest tests/ -v --tb=short 2>&1 | tee logs/pytest_phase7.txt

# Test específico
pytest tests/test_switch_hermes_v7.py::TestSwitchV7 -v

# Con coverage
pytest tests/ --cov=. --cov-report=term-missing
```

### Levantar Sistema Local (Docker)
```bash
docker-compose config  # ✅ Validar primero
docker-compose up -d   # ✅ Daemon mode
sleep 5 && docker-compose ps  # Verificar

# Health check de todos los módulos
for port in {8000..8008,8011}; do
  echo "Port $port:" && curl -s http://127.0.0.1:$port/health | jq .
done
```

### Debugging Inter-módulos
```bash
# Rastrear request entre módulos
curl -X POST http://127.0.0.1:8000/vx11/gateway-trace \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"module": "switch", "endpoint": "/switch/route-v5"}'

# Ver logs en tiempo real
docker-compose logs -f tentaculo_link madre switch

# Verificar estado de base de datos
sqlite3 data/runtime/vx11.db ".tables"
```

### Integración con VS Code + MCP
```bash
# MCP server escucha en :8006
curl http://127.0.0.1:8006/mcp/health

# Verificar CONTEXT-7 sessions (middleware)
curl -X GET "http://127.0.0.1:8000/vx11/context-7/sessions" \
  -H "X-VX11-Token: vx11-local-token"
```

---

## 📚 Referencias Rápidas

| Referencia | Ubicación | Propósito |
|-----------|-----------|----------|
| **Module bootstrap** | [config/module_template.py](../config/module_template.py) | Patrón FastAPI canónico |
| **DB layer** | [config/db_schema.py](../config/db_schema.py) | 40+ tablas, single-writer, schema v7.1 |
| **Settings & tokens** | [config/settings.py](config/settings.py) + `config/tokens.py` | URLs módulos, env-aware, Docker DNS |
| **Frontend** | [operator/src/](operator/src/) | React 18 + Vite + Tailwind |
| **Tests** | [tests/](tests/) | ~52 tests (pytest, mocks, conftest.py disables auth) |
| **Docker compose** | [docker-compose.yml](docker-compose.yml) | 10 servicios + volúmenes, puertos 8000–8011 |
| **Autosync** | [tentaculo_link/tools/autosync.sh](tentaculo_link/tools/autosync.sh) | Git workflow automation |

---

## 🎨 Frontend Operator (React 18 + Vite + TypeScript + Tailwind)

**Ubicación:** [operator/](operator/) (monorepo: `/operator/src/` frontend + `/operator_backend/` API)

### Stack Recomendado
- **React 18.3.1** — Componentes + hooks (useDashboardEvents)
- **Tailwind 4.0** — Styling reactivo, dark mode automático
- **TypeScript 5.7** — Type safety (tipos canónicos en `canonical-events.ts`)
- **Vite 7.2** — Dev server + HMR + build producción
- **ReactFlow 11.11** — Diagramas DAG (correlaciones, flujos Madre)

### Estructura
```
operator/
  ├── src/
  │   ├── types/canonical-events.ts     # Events whitelist
  │   ├── services/                     # HTTP clients (Switch, Madre, etc)
  │   ├── hooks/useDashboardEvents.ts   # WebSocket/polling
  │   ├── components/Dashboard/         # Main UI + 6 paneles
  │   └── App.tsx, main.tsx, index.css
  ├── package.json (dev deps)
  ├── vite.config.ts
  └── tailwind.config.js
```

### Comandos Frecuentes
```bash
cd operator
npm install && npm run build     # Compilar TypeScript + Tailwind
npm run dev                      # Dev: http://localhost:5173 (HMR activo)
npm run type-check               # Validar tipos TS sin build

# Producción
npm run build
# → dist/ lista para servir (Nginx, Docker)
```

### Integración con Backend (8011)
```typescript
// operator/src/services/operator-api.ts
import { VX11_API_BASE } from './config'

const client = new VX11OperatorClient(VX11_API_BASE, {
  headers: { 'X-VX11-Token': localStorage.getItem('token') }
})

await client.chat.sendMessage(sessionId, message)
await client.modules.getStatus()
```

### Build Output
```
✓ dist/index.html              0.46 kB | gzip: 0.30 kB
✓ dist/assets/index.css        2.24 kB | gzip: 1.08 kB
✓ dist/assets/index.js       201.86 kB | gzip: 68.42 kB
```

---

## 🔄 Flujos Clave VX11 (Data Flows)

### Flujo 1: Chat Operator → Madre/Switch
```
Frontend (React) →
  POST /operator/chat {message, session_id} →
    operator_backend:8011 (FastAPI) →
      Tentáculo Link:8000 (proxy + CONTEXT-7) →
        Switch:8002 (routing) o Madre:8001 (orchestration) →
          [Local modelo | DeepSeek | Hermes CLI] →
        respuesta JSON → Frontend renderiza
```

### Flujo 2: Madre Autónoma (cada 30s)
```
Madre timer →
  1. Query BD (daughter_tasks con status=pending) →
  2. Planning: selecciona via Switch routing →
  3. Spawns hijas efímeras (via Spawner:8008) →
  4. Espera finalización, persiste resultado en BD →
  5. Reporte → Manifestator (drift check) ↔ Hormiguero (parallelization)
```

### Flujo 3: Audio DSP (Shub Detection)
```
Switch recibe request →
  `detect_audio_domain()` (8 categorías) →
    Si audio: POST /shub/analyze → Shubniggurath:8007 →
      DSP pipelines (analyzer→mix→reaper) →
        Respuesta audio + narrativa → Frontend visualiza
```

---

## 📊 Patrón de Testing (pytest)

**Configuración:**
```python
# tests/conftest.py (shared fixtures)
@pytest.fixture(scope="session", autouse=True)
def disable_auth_for_tests():
    settings.enable_auth = False  # Disable durante tests
```

**Ejemplo de test inter-módulos:**
```python
# tests/test_switch_hermes_v7.py
@pytest.mark.asyncio
async def test_switch_task_structure():
    """POST /switch/task con payload correcto"""
    payload = {
        "prompt": "code review",
        "task_type": "chat",
        "source": "operator"
    }
    # mock db, httpx, etc.
    # assert result ok
```

**Ejecutar:**
```bash
pytest tests/ -v --tb=short          # Todos
pytest tests/test_madre*.py -v       # Solo Madre
pytest tests/ -k "hermes" --lf       # Last failed filter
```

---

## 🚀 Deployment (Docker)

**Build local:**
```bash
docker-compose build operator-frontend  # O builder imagen propia
docker-compose up -d

# Verificar
curl http://localhost:8020  # Nginx sirviendo dist/
curl http://localhost:8011/operator/chat  # Backend API
```

**Puertos Finales:**
- `8000`: Tentáculo Link (gateway)
- `8001-8008`: 8 módulos + Spawner
- `8011`: Operator Backend API
- `8020`: Operator Frontend (nginx)
- `5173`: Dev server (npm run dev)

---

## 📝 Convenciones VX11 Clave

| Aspecto | Regla | Ejemplo |
|--------|-------|---------|
| **Endpoints** | `/{modulo}/{versión}/{recurso}` | `/switch/v7/route-v5` |
| **Namespacing** | TODO bajo prefijo módulo | `/madre/tasks`, `/madre/chat` |
| **DB Queries** | Single-writer, close en finally | `db.add()` → `db.commit()` → `db.close()` |
| **Tokens** | Header `X-VX11-Token` siempre | `get_token("VX11_GATEWAY_TOKEN")` |
| **Async** | Todo I/O es async | `async def`, `await httpx.post()` |
| **Type hints** | Obligatorio (Python 3.10+) | `def route(prompt: str) -> Dict[str, Any]:` |
| **Logging** | Centralizado + forensics | `log.info()` + `write_log("module", "event")` |
| **Error Handling** | Circuit breaker + retry | Try/except + backoff exponencial |

---

## 🎯 Guía Rápida para Agentes IA

1. **Necesitas agregar endpoint:** Usa [config/module_template.py](config/module_template.py) como template
2. **BD queries:** Siempre `db.close()` en finally (single-writer pattern)
3. **Llamar otro módulo:** `httpx.AsyncClient` + `settings.{module}_url` + `AUTH_HEADERS`
4. **Frontend:** Solo edita bajo [operator/src/](operator/src/); tipos en `canonical-events.ts`
5. **Testing:** `pytest tests/ -v`; auth disabled via conftest.py
6. **Deploy:** `npm run build` → Docker puerto 8020

**Validar cambios:**
```bash
pytest tests/ -v --tb=short
npm run type-check          # Si tocas frontend
docker-compose config       # Si tocas docker-compose
```

---

## 📊 OPERATOR AUDITORÍA COMPLETA (Diciembre 2025)

**Para trabajar en Operator (frontend React 18 + chat), consulta auditoría exhaustiva:**

| Documento | Contenido | Lectura |
|-----------|----------|---------|
| [OPERATOR_RESUMEN_EJECUTIVO.md](.copilot-audit/OPERATOR_RESUMEN_EJECUTIVO.md) | Visión general, estado actual, próximos pasos | 15 min |
| [OPERATOR_AUDIT_FASE1_REAL_STATE.md](.copilot-audit/OPERATOR_AUDIT_FASE1_REAL_STATE.md) | Auditoría sin cambios (qué existe, qué funciona, qué falta) | 30 min |
| [OPERATOR_FASE2_BACKEND_CONTRACT.md](.copilot-audit/OPERATOR_FASE2_BACKEND_CONTRACT.md) | Especificación exacta de `/operator/chat` endpoint | 20 min |
| [OPERATOR_FASE3_AI_INTEGRATION.md](.copilot-audit/OPERATOR_FASE3_AI_INTEGRATION.md) | Flujo completo Frontend→Backend→DeepSeek R1 | 25 min |
| [OPERATOR_FASE4_ENHANCEMENTS.md](.copilot-audit/OPERATOR_FASE4_ENHANCEMENTS.md) | Mejoras sin romper nada (roadmap 3 semanas) | 20 min |

**Quick Start:** Lee RESUMEN_EJECUTIVO → luego elige FASE según tarea
