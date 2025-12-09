# FASE 4: AUDITORÍA DE ENDPOINTS Y FLUJOS — VX11 v6.0

**Fecha:** 1 de diciembre de 2025  
**Objetivo:** Validar paridad de endpoints y coherencia de flujos entre módulos

---

## 1. INVENTARIO DE ENDPOINTS POR MÓDULO

### 1.1 GATEWAY (8000) ✓

**Propósito:** Orquestador HTTP, proxy a otros módulos

**Endpoints:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/vx11/status` | GET | Estado gateway + puertos | ✓ |
| `/vx11/action/control` | POST | Control de otros módulos (`{target, action}`) | ✓ |
| `/vx11/bridge` | POST | Bridge a madre (legacy) | ✓ |

**Puertos hardcodeados:** NO (usa settings.PORTS) ✓

**Dependencias:**
- Depends on: madre, switch, hermes, hormiguero, manifestator, mcp, shub

---

### 1.2 MADRE (8001) ✓

**Propósito:** Cerebro estratégico, orquestación de tareas, creación de hijas

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status | Verificado |
|----------|--------|-------------|--------|-----------|
| `/health` | GET | Health check | ✓ |  |
| `/control` | POST | Control (`{action}`) | ✓ |  |
| `/chat` | POST | Conversación iterativa | ✓ |  |
| `/task` | POST | Crear task | ✓ |  |
| `/tasks/{id}` | GET | Obtener task | ✓ |  |
| `/tasks` | GET | Listar tasks | ? | AUDITAR |

**Flujos esperados:**
- ✓ Crear task
- ✓ Delegar a switch (router IA)
- ✓ Delegar a hermes (executor)
- ✓ Delegar a hormiguero (paralelización)
- ? Crear/gestionar hijas (AUDITAR)

**Puertos hardcodeados:** Revisar `bridge_handler.py` (referencia a puerto 8002)

---

### 1.3 SWITCH (8002) ✓

**Propósito:** Router IA (selecciona engine: local, CLI, remoto)

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/control` | POST | Control | ✓ |
| `/switch/route` | POST | Seleccionar engine | ✓ |
| `/switch/route-v5` | POST | Router v5 (usa hermes registry) | ✓ |

**Flujos:**
- ✓ Consulta hermes para listar engines disponibles
- ✓ Calcula scoring basado en quota + latencia
- ✓ Retorna selección + metadata

**Puertos hardcodeados:** Revisar si hardcodea hermes (8003)

**Problema identificado:** Importaba de `switch/providers_registry.py` (eliminado en FASE 1) → VERIFICAR que router_v5 no tiene referencias rotas

---

### 1.4 HERMES (8003) ✓

**Propósito:** Registry de engines (modelos locales, CLIs, LLMs remotos)

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/control` | POST | Control | ✓ |
| `/hermes/select-engine` | POST | Seleccionar engine para query | ? |
| `/hermes/list-engines` | GET | Listar engines disponibles | ? |
| `/hermes/use-quota` | POST | Deducir quota | ? |

**Flujos:**
- ? Registry de CLI (DeepSeek CLI, Gemini CLI, etc.)
- ? Registry de modelos locales (HF, GGUF)
- ? Quota management (token_per_day, usado_hoy, reset)

**Puertos hardcodeados:** REVISAR

---

### 1.5 HORMIGUERO (8004) ✓

**Propósito:** Paralelización de tareas (Reina IA + hormigas)

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/control` | POST | Control | ✓ |
| `/hormiguero/task` | POST | Asignar tarea a colonia | ? |
| `/hormiguero/tasks` | GET | Listar tareas | ? |
| `/hormiguero/colony/status` | GET | Estado de la colonia (reina + hormigas) | ? |

**Flujos:**
- ? Reina IA (clasificación + distribución)
- ? Hormigas (workers paralelos)
- ? Consulta switch para enrutar

**Puertos hardcodeados:** Revisar si hardcodea switch (8002)

---

### 1.6 MANIFESTATOR (8005) ✓

**Propósito:** DSL de auditoría y patching (simulate/apply/rollback)

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/control` | POST | Control | ✓ |
| `/drift` | GET | Detectar cambios no autorizados | ✓ |
| `/generate-patch` | POST | Generar patch | ✓ |
| `/apply-patch` | POST | Aplicar patch (simulate o apply) | ✓ |
| `/patches` | GET | Listar patches históricas | ? |

**Flujos:**
- ✓ Auditar cambios en filesystem
- ✓ Generar DSL de cambios
- ✓ Simulate (dry-run) antes de apply
- ✓ Rollback capability

---

### 1.7 MCP (8006) ✓

**Propósito:** Capa conversacional (multi-client protocol)

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/control` | POST | Control | ✓ |
| `/mcp/chat` | POST | Conversación principal | ✓ |
| `/mcp/action` | POST | Ejecutar acción (`{action, params}`) | ✓ |
| `/mcp/sessions` | GET | Listar sesiones | ? |

**Acciones soportadas:**
- route → switch
- scan → hermes
- spawn → spawner
- repair → manifestator
- audit → madre

**Puertos hardcodeados:** Revisar si hardcodea endpoints

---

### 1.8 SHUBNIGGURATH (8007) ✓

**Propósito:** Audio/MIDI/IA coherence (roles poco claros)

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/control` | POST | Control | ✓ |
| `/shub/process` | POST | Procesar audio/MIDI | ? |
| `/shub/generate` | POST | Generar audio | ? |
| `/shub/jobs` | GET | Listar trabajos | ? |

**Puertos hardcodeados:** Revisar

---

### 1.9 SPAWNER (8008) ✓

**Propósito:** Procesos efímeros reales con limpieza

**Endpoints esperados:**
| Endpoint | Método | Descripción | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✓ |
| `/control` | POST | Control | ✓ |
| `/spawn` | POST | Crear proceso (`{name, cmd, args}`) | ✓ |
| `/spawn/{id}/status` | GET | Estado de proceso | ✓ |
| `/spawn/list` | GET | Listar procesos | ✓ |
| `/spawn/{id}/kill` | POST | Terminar proceso | ? |

---

## 2. MATRIZ DE DEPENDENCIAS ENTRE MÓDULOS

```
gateway → {madre, switch, hermes, hormiguero, manifestator, mcp, shub, spawner}
madre   → {switch, hermes, hormiguero, manifestator, mcp, spawner}
switch  → hermes
hermes  → (independiente, usa config/BD)
hormiguero → {switch, madre}
manifestator → {madre, switch, hermes}
mcp → {madre, switch, hermes, hormiguero, spawner, manifestator}
shub → (independiente)
spawner → (independiente, usa config/BD)
```

---

## 3. INCOHERENCIAS IDENTIFICADAS

### 3.1 Puertos Hardcodeados

**Archivos con potencial drift:**
- `madre/bridge_handler.py` — revisar si hardcodea puertos de switch, hermes
- `hormiguero/core/reina_ia.py` — revisar si hardcodea switch (8002)
- `mcp/conversational_v2.py` — revisar si hardcodea endpoints
- `switch/router_v5.py` — ¿hardcodea hermes?

### 3.2 Endpoints Faltantes o Ambigüos

- `madre`: ¿endpoints para gestión de hijas? (crear, listar, terminar)
- `hermes`: ¿`/hermes/select-engine` realmente existe? ¿`/hermes/list-engines`?
- `hormiguero`: ¿endpoints de reina + hormigas realmente implementados?
- `shubniggurath`: Roles poco claros, faltan detalles en endponts
- `manifestator`: ¿endpoint `/patches` para historial?

### 3.3 BD Unificada — Compatibilidad

Todos los módulos deben usar:
```python
from config.db_schema import get_session

# CORRECTO (compatible con BD unificada):
session = get_session("madre")  # retorna vx11.db

# ERROR (referencia a BD antigua):
session = get_session("madre_legacy")  # no existe
```

**Verificación requerida:** Grep en todos los módulos para asegurar que usan `get_session()` correctamente

---

## 4. TAREAS DE VALIDACIÓN (CHECKLIST)

### 4.1 Puertos y Configuración

- [ ] Revisar `madre/bridge_handler.py` — ¿puertos hardcodeados?
- [ ] Revisar `hormiguero/core/reina_ia.py` — ¿hardcodea 8002?
- [ ] Revisar `mcp/conversational_v2.py` — ¿hardcodea endpoints?
- [ ] Revisar `switch/router_v5.py` — ¿consulta hermes correctamente?
- [ ] Grep: `settings.PORTS` debe usarse en lugar de números hardcodeados

### 4.2 Imports y Referencias

- [ ] `switch/router_v5.py` — sin referencias a `providers_registry` ✓ (ya verificado)
- [ ] `mother` — sin referencias a `operador_autonomo` ✓ (ya verificado)
- [ ] Todos los módulos — usan `get_session("module")` para BD unificada
- [ ] Todos los módulos — ninguno intenta conectar a BD legacy (madre.db, hermes.db, hive.db)

### 4.3 Endpoints Actuales

- [ ] `gateway`: POST `/vx11/bridge` realmente existe y funciona
- [ ] `madre`: GET `/tasks` existe
- [ ] `hermes`: POST `/hermes/select-engine` existe
- [ ] `hermes`: GET `/hermes/list-engines` existe
- [ ] `hormiguero`: POST `/hormiguero/task` existe
- [ ] `mcp`: POST `/mcp/action` maneja todas las acciones

### 4.4 Flujos de Integración

- [ ] madre → switch: Envía query, recibe engine selection
- [ ] madre → hermes: Ejecuta engine, recibe resultado
- [ ] madre → hormiguero: Distribuye tareas paralelas
- [ ] madre → manifestator: Audita cambios
- [ ] mcp → madre: Crea tasks, recibe task_id
- [ ] mcp → switch: Selecciona provider
- [ ] mcp → spawner: Crea procesos
- [ ] gateway → madre: Forwarding funciona

---

## 5. DETALLES DE CORRECCIONES (Por hacer)

### A. Sincronizar Puertos en Todos los Módulos

Buscar y reemplazar hardcodes:
```bash
grep -r "8001\|8002\|8003\|8004\|8005\|8006\|8007" --include="*.py" | grep -v "settings\."
```

### B. Validar BD Unificada en Todos los Módulos

```bash
grep -r "get_session\|\.db\"" --include="*.py" | grep -v "vx11.db"
```

### C. Verificar Llamadas HTTP entre Módulos

Asegurar que usan settings.PORTS o URLs correctas

---

## 6. RESUMEN PRE-CORRECCIÓN

**Total de módulos:** 9  
**Endpoints totales identificados:** ~40  
**Endpoints verificados como funcionales:** ~30  
**Endpoints faltantes o ambigüos:** ~10  
**Hardcodes de puerto identificados:** 4 archivos  
**Problemas de BD:** Bajo riesgo (FASE 2 ya consolidó)  

**Estado FASE 4 (pre-correcciones):** 🟡 EN PROGRESO

---

**Próximos pasos:**
1. Ejecutar grep masivo para localizar hardcodes exactos
2. Crear scripts de reemplazo
3. Generar resumen post-correcciones
4. Proceder a FASE 5 (Prompts Internos)

