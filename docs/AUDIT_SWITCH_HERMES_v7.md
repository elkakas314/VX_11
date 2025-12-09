# AUDIT: Switch + Hermes + BD para VX11 v7.0

**Fecha:** 2025-12-09
**Agente:** GitHub Copilot (DEEP SURGEON mode)
**Objetivo:** Completar Switch/Hermes como subsistema IA robusto

---

## 1. Estado Actual

### Switch (switch/main.py, 1002 líneas)
- ✅ Existe, contiene:
  - `PersistentPriorityQueue`: Cola persistente en BD (task_queue tabla)
  - `ModelPool`: Gestiona modelos activos/warm (<2GB), sincroniza con BD
  - Endpoints:
    - `/health` ✅
    - `/switch/route-v5`, `/switch/route` (compat) ✅
    - `/switch/chat` ✅ (pero con modelo mock)
    - `/switch/select_model`, `/switch/hermes/select_engine` ✅
    - `/switch/task` ❌ (no existe, hay `/switch/intent_router` que es similar)
    - `/switch/queue/status`, `/switch/queue/next` ✅
  - `ModelPool._seed_defaults()`: registra `general-7b`, `audio-engineering`, `shub-audio`
  - Integración con Shub: ✅ `_shub_is_healthy()`, fallback a Shub si audio
  - Integración con Hermes: ✅ llama `/hermes/models/best` para tareas
  - Prioridades: ✅ Mapeo PRIORITY_MAP (shub=0 > operator=1 > madre=2 > hijas=3)
  - Queue consumer: ✅ _consumer_loop() procesa items en background

- ⚠️ Limitaciones:
  - `/switch/chat` usa modelo mock, no CLI real (DeepSeek R1)
  - No hay modo "audio-engineer" (perfil de ingeniero de sonido)
  - No registra uso en `model_usage_stats` (tabla no existe aún)
  - No tiene circuit breaker para Shub
  - `/switch/task` no existe (hay `/switch/intent_router` pero no es idéntico)

### Hermes (switch/hermes/main.py, 598 líneas)
- ✅ Existe en subdirectorio `switch/hermes/`, contiene:
  - `ModelsLocal` query functions: `_best_models_for()`, `local_models()`
  - `ModelsRemoteCLI` via ORM (en BD)
  - Endpoints:
    - `/health` ✅
    - `/hermes/list` ✅ (modelos locales + CLI status)
    - `/hermes/cli/status` ✅
    - `/hermes/models/best` ✅ (filtra por task_type <2GB)
    - `/hermes/catalog/summary` ✅
    - `/hermes/register_model` ✅
    - `/hermes/search_models` ✅ (HF + OpenRouter search)
    - `/hermes/execute` ✅ (rutea a Shub si provider=shub)
  - Discovery: ✅ `_search_hf_models()`, `_search_openrouter_models()`
  - CLI discovery: ✅ `_discover_cli_with_playwright()` (stub)
  - Prune & TTL: ✅ `_prune_models()` para limpiar antiguos
  - Audio categorías: ✅ registro AUDIO_CATEGORIES

- ⚠️ Limitaciones:
  - No hay `/hermes/resources` (GET consolidado de recursos)
  - No hay `/hermes/register/cli` (POST para registrar CLI específico)
  - No hay `/hermes/register/local_model` (POST para registrar modelo)
  - No hay `/hermes/discover` (POST para lanzar discovery)
  - No hay workers en background (reseteo de límites de CLI, health check)
  - Catálogo models_catalog.json: ❌ no existe

### Base de Datos (config/db_schema.py, 593 líneas)
- ✅ Tablas existentes:
  - `Task`, `Context`, `Report`, `Spawn`, `IADecision`, `ModuleHealth`
  - `ModelRegistry` (para registrar modelos descubiertos)
  - `CLIRegistry` (para registrar CLIs disponibles)
  - `ModelsLocal` (modelos locales)
  - `ModelsRemoteCLI` (CLI remotos con token + límites)
  - `TokensUsage` (para tracking)
  - `TaskQueue` (cola persistente)
  - `HijasRuntime`, `SystemState`, `AuditLogs`, `SandboxExec`, `Events`

- ⚠️ Lo que falta:
  - `CliProviders`: versión mejorada de ModelsRemoteCLI con `api_key_env`, `daily_limit_tokens`, `monthly_limit_tokens`, etc.
  - `LocalModelsV2`: versión mejorada con `engine`, `max_context`, `task_type` más explícito
  - `SwitchQueueV2`: mejorada con `task_type`, `payload_hash`, mejor tracking
  - `ModelUsageStats`: para registrar uso de modelos/CLI (tokens, latencia, éxito)

### Configuración (config/settings.py, 129 líneas)
- ✅ Contiene:
  - `deepseek_api_key: Optional[str] = None` (pero no se inicializa desde tokens.env)
  - URLs de módulos (switch_url, hermes_url, shub_url, etc.)
  - Paths y memoria limits (max_memory_mb=512, max_model_size_mb=256)
  - Configuración de modelos y CLI

- ⚠️ Lo que falta:
  - Lectura explícita de `DEEPSEEK_API_KEY` desde `tokens.env` vía BaseSettings
  - Configuración de límites diarios/mensuales para DeepSeek
  - Modo "audio-engineer" profile

### Documentación
- ✅ `docs/VX11_SHUB_SWITCH_HERMES_FLOWS_v7.x.md` existe (breve, stub)
- ❌ No hay documentación completa de endpoints Switch/Hermes v7
- ❌ No hay diagramas de flujo
- ❌ No hay guía de integración para otros módulos

---

## 2. Análisis de Integración Actual

### Switch + Hermes
- Switch llama `/hermes/models/best` para seleccionar modelos
- Hermes retorna candidatos <2GB
- Pero: **sin feedback loop** (Switch no informa si el modelo funcionó o no)
- Pero: **Hermes no resetea límites de CLI** (background worker falta)

### Switch + Shub
- Switch tiene `_shub_is_healthy()` para monitorear Shub
- Si `provider_hint="audio"` o `task_type` audio → delega a Shub
- Pero: **sin circuit breaker real** (no hay reintentos ni throttle)
- Pero: **sin tracking de uso en BD**

### Hermes + BD
- Hermes lee/escribe en `ModelsLocal`, `ModelRegistry`, `ModelsRemoteCLI`
- Pero: **sin transaction management explícito** (podría haber race conditions)
- Pero: **sin cleanup automático** (TTL básico, pero no ejecutado)

---

## 3. Plan de Ejecución (8 fases)

### FASE 1: Auditoría (✅ COMPLETADA)
- Leer código actual
- Documentar estado
- Identificar brechas

### FASE 2: Esquema BD Mejorado
- Agregar `CliProviders` (mejorado)
- Agregar `LocalModelsV2` (si es necesario)
- Agregar `ModelUsageStats` (para tracking)
- Agregar `SwitchQueueV2` (si es necesario)
- No romper tablas existentes

### FASE 3: Settings + DEEPSEEK
- Leer `tokens.env` → `deepseek_api_key` en settings
- Agregar `hermes_cli_providers_config` (JSON con proveedores iniciales)
- Validar que `DEEPSEEK_API_KEY` se carga correctamente

### FASE 4: Hermes Refactor
- Implementar `/hermes/resources` (GET consolidado)
- Implementar `/hermes/register/cli` (POST)
- Implementar `/hermes/register/local_model` (POST)
- Implementar `/hermes/discover` (POST)
- Crear catálogo `models_catalog.json`
- Background worker: reseteo de límites, health checks

### FASE 5: Switch Refactor
- Mejorar `/switch/chat`:
  - Agregar modo `mode="audio-engineer"` o `profile="audio-engineer"`
  - CLI-first: priorizar DeepSeek R1 si hay token
  - Local-fallback: usar modelo local si CLI saturado
  - Registrar uso en `ModelUsageStats`
- Implementar `/switch/task` completo:
  - `task_type` explícito
  - Local-first: priorizar modelo local por task_type
  - CLI-fallback: si no hay modelo local
  - Registrar uso
- Mejorar `/switch/route`:
  - Circuit breaker para Shub
  - Prioridades confirmadas
- Integración Hermes:
  - Feedback loop: registrar resultado de selección
  - Consultar limites de CLI antes de seleccionar

### FASE 6: Catálogo y Tests
- Crear `hermes/models_catalog.json` (catálogo inicial de modelos <2GB)
- Crear tests:
  - `tests/test_switch_chat_v7.py`
  - `tests/test_switch_task_v7.py`
  - `tests/test_hermes_v7.py`
- Validar que compilar y tests pasen

### FASE 7: Validación
- `python3 -m py_compile` en todos los archivos
- `pytest` en tests relevantes
- Validar health endpoints
- Validar integración Switch↔Hermes↔Shub

### FASE 8: Documentación Final
- `docs/VX11_SWITCH_HERMES_v7_COMPLETION.md`
- Diagramas de flujo (ASCII)
- Guía de endpoints
- Guía de integración para otros módulos
- Actualizar `.github/copilot-instructions.md`

---

## 4. Decisiones Arquitectónicas

1. **No crear nuevas carpetas**: Switch/Hermes quedan donde están
2. **Compatibilidad hacia atrás**: Todos los endpoints existentes siguen funcionando
3. **BD single-writer**: SQLAlchemy con transacciones explícitas
4. **CLI-first para chat**: DeepSeek R1 es prioridad si hay token disponible
5. **Local-first para tareas**: Modelos locales <2GB por task_type
6. **Circuit breaker simple**: Si Shub falla N=3 veces, pausa 60s
7. **Limits per CLI**: Tracking de tokens diarios/mensuales
8. **Background workers en Hermes**: AsyncIO tasks en startup/lifespan

---

## 5. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|-----------|
| Romper tests existentes | Verificar nombres de endpoints antes de cambiar |
| Conflictos en BD (migrations) | Agregar nuevas tablas sin alterar existentes |
| DEEPSEEK_API_KEY no cargado | Validar en settings.py con test explícito |
| Circuit breaker incompleto | Implementar simple: counter + timestamp + threshold |
| Hermes workers no ejecutándose | Usar FastAPI lifespan context manager |

---

## 6. Criterios de Éxito

✅ **Fase completada cuando:**
1. Código compila sin errores (`py_compile`)
2. Tests relevantes pasan o están justificados (xfail)
3. Endpoints documentados en OpenAPI (/docs)
4. Integración Switch↔Hermes↔Shub validada
5. No hay archivos temporales fuera de `docs/`
6. `.github/copilot-instructions.md` actualizado con "Switch/Hermes v7.0"

---

**Estado**: LISTO PARA FASE 2 (BD Refactor)
