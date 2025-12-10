# Instrucciones para Agentes de IA — VX11 v7.0

**Propósito:** Guiar agentes IA para ser inmediatamente productivos en este codebase modular de 10 microservicios orquestados.

## 🏗️ Arquitectura Esencial: 10 Módulos + BD Unificada

| Módulo | Puerto | Responsabilidad Clave |
|--------|--------|------|
| **Tentáculo Link** | 8000 | Frontdoor único: proxy + autenticación (`X-VX11-Token`) + orquestación de rutas |
| **Madre** | 8001 | Orquestador: ciclo 30s autónomo, P&P states, decisiones IA, planificación |
| **Switch** | 8002 | Router IA: scoring adaptativo, prioridades (shub>operator>madre>hijas), circuit breaker |
| **Hermes** | 8003 | Ejecutor: CLI registry ~50+, descubrimiento HuggingFace, modelos <2GB, `/hermes/resources` |
| **Hormiguero** | 8004 | Paralelización: reina + hormigas workers, feromonas (métricas), escalado automático |
| **Manifestator** | 8005 | Auditoría: drift detection, generación/aplicación parches, integración VS Code |
| **MCP** | 8006 | Conversacional: herramientas sandboxeadas, validación acciones, Copilot bridge |
| **Shubniggurath** | 8007 | Audio + REAPER: análisis espectral, mezcla, diagnóstico, OSC integration |
| **Spawner** | 8008 | Procesos efímeros: scripts sandbox, captura stdout/stderr, gestión PID |
| **Operator** | 8011 | Dashboard ejecutivo: React + Vite, chat, Playwright real browser, session management |

**BD Unificada:** `data/runtime/vx11.db` (SQLite single-writer, siempre una sesión por módulo).

## 🌊 Patrones de Comunicación Inter-módulo

### Red Docker + DNS Fallback
**NUNCA hardcodear `localhost` o `127.0.0.1`** — usar resolver inteligente:

```python
from config.settings import settings

# ✅ CORRECTO (Docker hostname resolution + fallback)
url = settings.switch_url or f"http://switch:{settings.switch_port}"

# ✅ CORRECTO (DNS resolver con fallback)
from config.dns_resolver import resolve_module_url
url = resolve_module_url("switch", 8002, fallback_localhost=True)

# ❌ PROHIBIDO
url = "http://localhost:8002"  # No funciona en Docker
```

### HTTP Async Client Pattern
```python
import httpx
from config.tokens import get_token
from config.forensics import write_log

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

# Patrón: single client per module, reusable
async with httpx.AsyncClient(timeout=15) as client:
    resp = await client.post(
        f"{settings.switch_url}/switch/chat",
        json={"messages": [...]},
        headers=AUTH_HEADERS
    )
    result = resp.json()
    write_log("mi_modulo", f"switch_call:ok")
```

### Flujo Tentacular Completo
```
Usuario (Operator/MCP)
  → Tentáculo Link (8000, frontdoor)
    → Madre (8001, planificación + decisiones)
      → Switch (8002, scoring + routing)
        → {Hermes, Spawner, Shub} (ejecución)
          → BD (persist Task + Context + Report)
      ← resultado
  ← respuesta JSON
```

## 🔧 Patrones de Código Obligatorios

### 1. Crear Módulo FastAPI
```python
from config.module_template import create_module_app
# Registra automáticamente: middleware forense, /health, P&P state endpoints
app = create_module_app("nombre_modulo")

@app.get("/mi-endpoint")
async def mi_endpoint():
    return {"status": "ok"}
```

### 2. Configuración Centralizada
```python
from config.settings import settings
from config.tokens import get_token, load_tokens

load_tokens()  # Carga .env/tokens.env

# Usar SIEMPRE config.settings para puertos/URLs
switch_url = settings.switch_url or f"http://switch:{settings.switch_port}"
token = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
```

### 3. Base de Datos (SQLite single-writer)
```python
from config.db_schema import get_session, Task, Context, Spawn

db = get_session("nombre_modulo")  # Sesión dedicada por módulo
try:
    task = Task(uuid="...", name="mi_tarea", module="madre", action="exec")
    db.add(task)
    db.commit()  # ⚠️ CRÍTICO: siempre commit explícito
    
    # Guardar contexto asociado
    ctx = Context(task_id=task.uuid, key="resultado", value="...")
    db.add(ctx)
    db.commit()
finally:
    db.close()
```

### 4. Auditoría Automática (Forensics)
```python
from config.forensics import write_log, write_hash_manifest, record_crash

write_log("mi_modulo", "evento_importante", level="INFO")
write_hash_manifest("mi_modulo", filter_exts={".py"})  # SHA256 manifest

# En catch block:
except Exception as exc:
    record_crash("mi_modulo", exc)
    write_log("mi_modulo", f"error: {exc}", level="ERROR")
    
# Registra en: forensic/{module}/logs/ y forensic/{module}/hashes/
```

### 5. Container State Management (P&P — Plug & Play)
```python
from config.container_state import get_active_modules, should_process

# Verificar si módulo está activo
if should_process("manifestator"):
    # procesamiento
    pass

# Obtener lista de módulos activos
active = get_active_modules()  # ["madre", "switch", ...]
```

## 📊 Flujos de Datos Concretos

### Flujo Chat Conversacional
```
Usuario → MCP/Operator
  → POST /switch/chat {"messages": [...]}
    → Switch: consulta Hermes, calcula scores
    → Elige engine (local/deepseek/etc)
    → Ejecuta en Hermes
    → Registra IADecision en BD
  → Respuesta: {"response": "...", "engine": "..."}
```

### Flujo Tareas Autónomas (Madre)
```
Madre (ciclo 30s):
  1. Consulta BD: tareas pendientes
  2. Planifica (Switch → scoring)
  3. Spawner → crea proceso efímero
  4. Captura stdout/stderr
  5. Persiste Spawn + Report
  6. Notifica Tentáculo Link
```

### Flujo Routing Adaptativo (Switch + Hermes)
```
Switch recibe: {"query": "calcula 2+2", "available_engines": [...]}
  → consulta Hermes: /hermes/resources
  → recupera EngineMetrics para cada engine
  → calcula score: latencia + error_rate + costo
  → elige ganador respetando prioridades
  → registra EngineMetrics (feedback loop para ML)
```

## 🧪 Testing & Debugging

```bash
# Verificar sintaxis
python3 -m compileall .

# Tests de módulo específico
pytest tests/test_switch_hermes_v7.py -v --tb=short

# Suite completa
pytest tests/ -v --tb=short | tee logs/pytest_phase7.txt

# Validar compose
docker-compose config

# Health check de todos módulos
for port in {8000..8008,8011}; do curl -s http://localhost:$port/health | jq .status; done

# Logs en vivo
docker-compose logs -f madre
docker-compose logs -f switch
```

**Troubleshooting:**
| Problema | Causa | Solución |
|----------|-------|----------|
| Switch no levanta | Falta token en `tokens.env` | `cp tokens.env.sample tokens.env` + agregar `DEEPSEEK_API_KEY` |
| Puerto en uso | Proceso anterior no terminó | `lsof -i :8001 \| awk '{print $2}' \| xargs kill -9` |
| DB bloqueada | Timeout en sesión | `get_session("modulo", timeout=30)` |
| Módulo no responde | Network/health issue | `curl http://localhost:PORT/health` → `docker-compose logs MODULE` |
| URLs resuelven a localhost | No dockerizado | Revisar `settings.py` — debe usar hostnames Docker |

## ⚠️ VX11 RULES (Obligatorio)

**PROHIBICIONES ABSOLUTAS:**
- ❌ NO hardcodear `localhost` o `127.0.0.1` → usar `config.settings` o `dns_resolver`
- ❌ NO usar `config.database.SessionLocal` (deprecated) → usar `config.db_schema.get_session()`
- ❌ NO crear archivos salvo explícito en requerimiento
- ❌ NO mover carpetas ni renombrar módulos (breaking changes)
- ❌ TODO parche → usar `replace_string_in_file` o `multi_replace_string_in_file`
- ❌ NO modificar `docker-compose.yml` puertos/nombres de servicios
- ❌ NO inventar rutas/funciones/modelos; usar SOLO existentes

**HERRAMIENTAS DE EDICIÓN PERMITIDAS:**
- ✅ `read_file`, `replace_string_in_file`, `multi_replace_string_in_file` (cambios en código)
- ✅ `list_dir`, `grep_search`, `file_search`, `semantic_search` (discovery)
- ✅ `run_in_terminal` (solo: `py_compile`, `pytest`, `lsof`, comandos read-only)

## 📚 Referencia Rápida

**Flujo tentacular:** usuario → Tentáculo → Madre → Switch → {Hermes, Spawner, Shub} → BD → resultado

**BD:** `data/runtime/vx11.db` — SQLite single-writer — usar `get_session("modulo_name")`

**Prioridades Switch:** shub (0) > operator (1) > madre (2) > hijas (3) — para circuit breaker + scheduling

**Estados P&P:** `active` (procesando) | `standby` (bajo consumo, pausado) | `off` (desactivado)

**Auth:** `X-VX11-Token` header — valor desde `get_token("VX11_GATEWAY_TOKEN")` o `settings.api_token`

**Puertos:** Tentáculo=8000, Madre=8001, Switch=8002, Hermes=8003, Hormiguero=8004, Manifestator=8005, MCP=8006, Shub=8007, Spawner=8008, Operator=8011

**Rutas Docker:** `/app/*` (no `/home/elkakas314/*` en contenedores) — `settings.BASE_PATH = /app`
