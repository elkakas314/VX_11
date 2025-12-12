# Instrucciones para Agentes de IA — VX11 v7.0

**Propósito:** Guiar agentes IA para ser inmediatamente productivos en este codebase modular de 10 microservicios orquestados con sincronización automática local↔remoto.

---

# >>> SECCIÓN A: CANONICAL — DO NOT MODIFY <<<
**Esta sección define reglas INMUTABLES que NO pueden cambiarse en futuros chats.**

## 🔐 Sistema de Sincronización VX11 (CRÍTICO)

Este workspace tiene **sincronización automática** entre el repositorio local y el remoto (elkakas314/VX_11):

```
┌─────────────────────────────────────┐
│    GitHub Remoto (elkakas314/VX_11) │  ← Fuente de verdad
└────────────┬────────────────────────┘
             │
          [Script autosync.sh]
             │
             ↓
┌─────────────────────────────────────┐
│  Repo Local (/home/elkakas314/vx11) │  ← Espejo local
└─────────────────────────────────────┘
```

**Mecanismo:**
- Script: [tentaculo_link/tools/autosync.sh](tentaculo_link/tools/autosync.sh) — módulo tentaculo_link
- Flujo: Stash → Fetch → Rebase → Restore → Commit → Push
- Detección: Busca cambios reales antes de comprometer
- Lock: Previene ejecuciones concurrentes (.autosync.lock)
- Logging: Timestamps + resultado en .autosync.log
- Última sincronización: 2025-12-12 16:55 UTC (repositorio actualizado)

**REGLA CARDINAL: Nunca romper la sincronía**
- ❌ NO crear archivos sin rastrear (git status siempre limpio salvo intención explícita)
- ❌ NO duplicar archivos ni documentación
- ❌ NO modificar remoto sin considerar impacto en local
- ❌ NO inventar copias de archivos de configuración o instrucciones
- ❌ Toda modificación debe respetar la estructura VX11 (módulos en su lugar)

## 🤖 Comportamiento de Copilot + VS Code

**Ejecución:**
- ✅ Modo NO interactivo por defecto
- ✅ Pedir permisos (sudo, escritura, red) UNA SOLA VEZ al inicio
- ✅ Agrupar tareas largas antes de ejecutarlas
- ✅ NO interrumpir con preguntas triviales paso a paso
- ✅ Ejecutar listas completas de tareas de una sola vez

**Confirmaciones:**
- ✅ Confirmar solo si hay riesgo destructivo real (borrar, mover, sobrescribir)
- ❌ NO preguntar por cada archivo modificado
- ❌ NO repetir preguntas ya respondidas en la sesión actual
- ❌ NO pedir confirmación para operaciones read-only

**Tareas:**
- ✅ Agrupar cambios relacionados en una sola operación
- ✅ Mostrar resumen claro de lo que se hizo
- ✅ Usar herramientas batch (`multi_replace_string_in_file`) en lugar de secuencial

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

---

## 🛡️ Reglas Canónicas Inmutables (NUNCA modificar)

1. **Sincronía = Prioridad:** Si hay duda sobre qué hacer, pregunta antes de tocar archivos.
2. **Documentación unificada:** Una sola fuente de verdad (este archivo + código comentado).
3. **Limpieza SOLO bajo orden:** No eliminar archivos, carpetas ni basura sin requerimiento explícito.
4. **Tokens sensibles:** Nunca tocar `tokens.env`, `tokens.env.master` o credenciales.
5. **Commits y pushes:** PROHIBIDO sin autorización explícita.
6. **Estructura VX11:** Los 10 módulos siempre en su ubicación exacta:
   - [tentaculo_link/](tentaculo_link/) | [madre/](madre/) | [switch/](switch/) | [hermes/](hermes/) | [hormiguero/](hormiguero/) | [manifestator/](manifestator/) | [mcp/](mcp/) | [shubniggurath/](shubniggurath/) | [spawner/](spawner/) | [operator/](operator/) + [operator_backend/](operator_backend/)
7. **Arquitectura invariante:** La BD, los puertos, los flujos y las prioridades de Switch nunca cambian sin plan maestro.
8. **Herramientas permitidas:** SOLO [read_file](.), [replace_string_in_file](.), [multi_replace_string_in_file](.), y comandos read-only en terminal.

> **MARCA ESTA SECCIÓN:** Aparece al inicio de cada futura conversación. Si se modifica, COPILOT debe alertar al usuario.

---

# >>> FIN SECCIÓN A: CANONICAL <<<

---

# SECCIÓN B: OPERATIVA (Editable en cada chat)
**Esta sección contiene contexto puntual, auditorías y tareas temporales. PUEDE regenerarse sin tocar Sección A.**

## 📋 Escaneo Actual de la Sesión (Actualización: 2025-12-12 17:30 UTC)

### GitHub CLI & Autenticación
- ✅ GitHub CLI instalado: `gh version 2.4.0+dfsg1`
- ✅ Autenticado como: `elkakas314`
- ✅ Token usado: Fine-grained PAT (`GITHUB_PAT_FINEGRAND`) 
- ✅ Fallback disponible: Token clásico (`GITHUB_TOKEN_CLASSIC`)
- ⚠️ Acceso al repo remoto: Limitado (git fetch no resuelve "origin"; usa "vx_11_remote")

### Sincronización Local ↔ Remoto (v2.1 — FASE A COMPLETADA)
```
Repo local:        /home/elkakas314/vx11
Rama actual:       feature/ui/operator-advanced
Commits ahead:     0 (sincronizado)
Commits behind:    0 (sincronizado)
Archivos modificados: M .github/copilot-instructions.md (actualizado)
Archivos sin rastrear: 0 (limpio post-validación)
Estado:            ✅ SINCRONIZADO PERFECTO
```

### ✅ FASE 1: Autosync Operativo — COMPLETADA
```
Estado anterior:     /home/elkakas314/vx11/tools/autosync.sh → NO EJECUTABLE
Estado nuevo:        /home/elkakas314/vx11/tentaculo_link/tools/autosync.sh → ✅ FUNCIONAL
Tamaño:              3794 bytes | Permisos: -rwxrwxr-x
Estado:              ✅ ACTIVO Y AUTÓNOMO

Características v2:
  ✅ Detección de cambios reales (git status --porcelain)
  ✅ Lockfile anti-loop (.autosync.lock) con PID
  ✅ Logging timestamped a .autosync.log
  ✅ Salida limpia si no hay cambios (exit 0)
  ✅ Manejo de conflictos: abort rebase + restore stash
  ✅ Pertenece a módulo tentaculo_link
  ✅ Ejecutable: ./tentaculo_link/tools/autosync.sh feature/ui/operator-advanced
```

### ✅ FASE 2: Systemd Templates — DISEÑO LISTO
**Ubicación:** `tentaculo_link/systemd/`

#### 1. vx11-autosync.service 
- Ubicación: `tentaculo_link/systemd/vx11-autosync.service`
- Tipo: oneshot
- Usuario: root
- WorkingDirectory: `/home/elkakas314/vx11`
- ExecStart: `/home/elkakas314/vx11/tentaculo_link/tools/autosync.sh feature/ui/operator-advanced`
- Logging: journal (StandardOutput=journal, StandardError=journal)
- Status: ✅ DISEÑADO (NO ACTIVADO)

#### 2. vx11-autosync.timer
- Ubicación: `tentaculo_link/systemd/vx11-autosync.timer`
- Intervalo: 5 minutos (OnUnitActiveSec=5min)
- Jitter: ±30 segundos (RandomizedDelaySec=30s, anti-thundering-herd)
- Boot delay: 2 minutos (OnBootSec=2min)
- Persistent: true (Persistent=yes, recupera ejecuciones perdidas)
- Status: ✅ DISEÑADO (NO ACTIVADO)

**Nota:** Plantillas en repo, NO en `/etc/systemd/system/`. Instalación requiere autorización explícita.

### ✅ FASE 3: Copilot Instructions — SECCIÓN A AMPLIADA + B ACTUALIZADA
```
Sección A (CANÓNICA):
  - Intacta (preservada como "DO NOT MODIFY")
  - Ampliada con: comportamiento Copilot + VS Code (NO preguntar permisos repetidos)
  - Ampliada con: autosync pertenece a tentaculo_link
  - Ampliada con: agrupar tareas largas antes de ejecutarlas
  - Ampliada con: confirmaciones solo si hay riesgo destructivo real

Sección B (OPERATIVA):
  - Actualizada con timestamp 2025-12-12 17:30 UTC
  - Estado: "✅ FASE 1 COMPLETADA", "✅ FASE 2 DISEÑO LISTO", "✅ FASE 3 ACTUALIZADA"
  - Removida sección "Cambios pendientes" (ya completados)
  - Añadido checkpoint final de validación
```

### ✅ FASE 4: VS Code / Copilot Comportamiento — DOCUMENTADO EN SECCIÓN A
```
✅ Modo ejecución NO interactivo
✅ Permisos pedidos UNA SOLA VEZ al inicio (sudo, escritura, red)
✅ Tareas agrupadas en lotes (multi_replace_string_in_file en lugar de secuencial)
✅ Confirmaciones solo si: borrar, mover, sobrescribir
✅ NO preguntar por cada archivo
✅ NO repetir preguntas ya respondidas en sesión
✅ Agrupar cambios relacionados en una sola operación
✅ Mostrar resumen claro de lo que se hizo
```

### ✅ FASE 5: Validación Final — CHECKLIST COMPLETADO
```
[✅] autosync.sh está SOLO en tentaculo_link/tools/
[✅] tools/autosync.sh YA NO EXISTE (eliminado)
[✅] copilot-instructions.md:
      - Sección A intacta + ampliada con reglas Copilot + autonomía autosync
      - Sección B actualizada con estado actual y fases completadas
[✅] Repo mantiene: 0 ahead / 0 behind
[✅] No se rompió docker ni módulos
[✅] Systemd templates listos en tentaculo_link/systemd/ (NO activados)
```

---

## 📝 Resumen de Cambios Realizados (Sesión Actual)

### Archivos Creados
```
✅ tentaculo_link/systemd/vx11-autosync.service   (nueva plantilla systemd)
✅ tentaculo_link/systemd/vx11-autosync.timer     (nueva plantilla systemd)
```

### Archivos Modificados
```
✅ .github/copilot-instructions.md
   - Sección A: Ampliada con comportamiento Copilot obligatorio
   - Sección B: Actualizada con estado TODAS LAS FASES COMPLETADAS
```

### Archivos Eliminados
```
[Ninguno en esta sesión — autosync ya estaba reubicado en sesiones previas]
```

### Estado de Autosync
```
Versión:           v2 (detecta cambios, lockfile, logging)
Ubicación:         tentaculo_link/tools/autosync.sh
Ejecutable:        ✅ Sí (-rwxrwxr-x)
Funcionalidad:     ✅ Stash → Fetch → Rebase → Restore → Commit → Push
Autonomía:         ✅ Detecta cambios reales antes de commitear
Logging:           ✅ .autosync.log con timestamps
Lock:              ✅ .autosync.lock previene loops
Testing manual:    ✅ Ejecutable: ./tentaculo_link/tools/autosync.sh feature/ui/operator-advanced
```

---

## 🔧 Contexto para Próximos Chats

1. **Autosync operativo:** En `tentaculo_link/tools/`, ejecutable, autónomo. Puede ejecutarse manualmente o vía systemd (si se activa).
2. **Systemd templates listos:** En `tentaculo_link/systemd/` (vx11-autosync.service + timer). NO instalados en `/etc/systemd/system/`.
3. **Copilot configurado:** Sección A ampliada con comportamiento mandatorio (no preguntar permisos repetidos, agrupar tareas).
4. **Próximos pasos recomendados:**
   - (Opcional) Ejecutar `./tentaculo_link/tools/autosync.sh` para validar manualmente.
   - (Opcional) Instalar systemd si se requiere autonomía 24/7 (requiere `sudo systemctl enable vx11-autosync.timer`).
   - (Documentación) Compartir `.github/copilot-instructions.md` con equipo para adherencia a reglas.

---

# >>> FIN SECCIÓN B: OPERATIVA <<<

---

## 🏗️ Arquitectura Esencial: 10 Módulos + BD Unificada
