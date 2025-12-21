# Auditoría Shubniggurath v7 — Estado Actual & Roadmap

**Fecha:** 9 dic 2025  
**Estado VX11:** v7.0 Production Ready (10/10 servicios UP)  
**Objetivo:** Mapear Shub completo, identificar vigente vs obsoleto, y definir TODOs para v8

---

## 1. Resumen Ejecutivo

**Shubniggurath** es el módulo de audio/procesamiento IA de VX11 v7.0. 

### Estado Actual
- ✅ **Servicio Docker UP**: Contenedor `vx11-shubniggurath` en puerto 8007, saludable
- ✅ **API Mínima Vigente**: Endpoints `/health`, `/shub/analyze`, `/shub/mix`, `/shub/master`, `/shub/fx-chain/generate`, `/shub/reaper/*`, `/shub/assistant/chat`
- ✅ **Autenticación**: Respeta token `X-VX11-Token` y `settings.api_token`
- ✅ **Lazy Initialization**: No carga engines pesados al arrancar; inicializa on-demand
- ⚠️ **Endpoints Mock**: Todos devuelven `{"status": "queued"}` sin procesamiento real
- ⚠️ **Subcarpetas Parcialmente Vigentes**: `core/`, `dsp/`, `ops/` tienen código, pero no están integradas en main.py

### Estado Deseado para v8
- Full integration de engines (`core/dsp_engine.py`, `engines/`, `pipelines/`)
- Real audio processing (análisis, mezcla, masterización)
- REAPER integration funcional
- Chat con IA para ingeniería de sonido
- Persistencia en BD (SharedDB o PostgreSQL local)

---

## 2. Árbol de Ficheros Detallado

```
shubniggurath/
├── main.py                           [VIGENTE] API FastAPI, lazy init, endpoints mock
├── __init__.py                        [VIGENTE] Py package marker
├── Dockerfile                         [VIGENTE] Build v7, 512m mem, uvicorn 8007
├── README.md                          [VIGENTE] Documentación general (v3.0)
├── README_FASE1.md                    [LEGACY] Outdated roadmap (pre-v7)
│
├── dsp_pipeline.py                    [EXPERIMENTAL] Pipeline DSP, no usado en main
│
├── shub_copilot_bridge_adapter.py     [EXPERIMENTAL] Adaptador Copilot, no integrado
├── shub_core_init.py                  [LEGACY] Inicialización antigua, deprecado
├── shub_db_schema.py                  [EXPERIMENTAL] Schema DB, no utilizado
├── shub_reaper_bridge.py              [EXPERIMENTAL] Bridge REAPER, no integrado
├── shub_routers.py                    [LEGACY] Routers obsoletos, reemplazados por main.py
├── shub_vx11_bridge.py                [EXPERIMENTAL] Bridge VX11, no integrado
│
├── api/                               [EMPTY] Subcarpeta sin contenido funcional
│
├── core/
│   ├── __init__.py
│   ├── audio_analysis.py              [EXPERIMENTAL] Análisis de audio
│   ├── dsp_engine.py                  [EXPERIMENTAL] Motor DSP central
│   ├── engine.py                      [EXPERIMENTAL] Base engine class
│   ├── fx_engine.py                   [EXPERIMENTAL] Motor de efectos
│   ├── initializer.py                 [EXPERIMENTAL] Inicializador de motores
│   └── registry.py                    [EXPERIMENTAL] Registro de engines
│
├── database/
│   ├── __init__.py
│   ├── models.py                      [EXPERIMENTAL] Modelos SQLAlchemy
│   ├── models_shub.py                 [EXPERIMENTAL] Modelos Shub específicos
│   ├── migrations/                    [EMPTY]
│   └── schema_14_tables.sql           [LEGACY] Schema PostgreSQL no utilizado
│
├── db/                                [EMPTY] Placeholder
│
├── docker/
│   └── docker_shub_compose.yml        [LEGACY] Compose separado no usado
│
├── docs/
│   ├── API_SHUB_VX11.md               [EXPERIMENTAL] Doc API
│   ├── CICLO_COMPLETO_CIERRE.md       [LEGACY] Cierre fase anterior
│   ├── ÍNDICE_FINAL.md                [LEGACY] Índice viejo
│   ├── MODO_DEPLOY_FASE5_COMPLETED.txt [LEGACY] Deploy fase 5
│   ├── MODO_OPERADOR_CIERRE_VISUAL.txt [LEGACY] UI cierre visual
│   ├── README_START_HERE.txt          [LEGACY] Start guide viejo
│   ├── SHUB_AUDIT.json                [LEGACY] Audit data
│   └── SHUB_AUDIT_STRUCTURAL.json     [LEGACY] Audit structural
│
├── dsp/
│   ├── __init__.py
│   ├── analyzers.py                   [EXPERIMENTAL] Analizadores DSP
│   ├── filters.py                     [EXPERIMENTAL] Filtros DSP
│   └── segmenter.py                   [EXPERIMENTAL] Segmentador de audio
│
├── engines/
│   ├── __init__.py
│   ├── ai_assistant_engine.py         [EXPERIMENTAL] Motor asistente IA
│   ├── analyzer_engine.py             [EXPERIMENTAL] Motor analizador
│   ├── master_engine.py               [EXPERIMENTAL] Motor masterización
│   ├── mix_engine.py                  [EXPERIMENTAL] Motor mezcla
│   └── spectral_engine.py             [EXPERIMENTAL] Motor espectral
│
├── integrations/
│   ├── __init__.py
│   ├── db_sync.py                     [EXPERIMENTAL] Sync con BD VX11
│   ├── reaper_rpc.py                  [EXPERIMENTAL] RPC REAPER
│   └── vx11_bridge.py                 [EXPERIMENTAL] Bridge VX11
│
├── models/
│   ├── __init__.py
│   ├── llm_audio/                     [EMPTY]
│   └── ml_local/                      [EMPTY]
│
├── ops/
│   ├── __init__.py
│   ├── comp_ops.py                    [EXPERIMENTAL] Operaciones compresión
│   ├── diagnostic_ops.py              [EXPERIMENTAL] Diagnósticos
│   ├── mix_ops.py                     [EXPERIMENTAL] Operaciones mezcla
│   └── stem_ops.py                    [EXPERIMENTAL] Operaciones stems
│
├── pipelines/
│   ├── __init__.py
│   ├── analysis.py                    [EXPERIMENTAL] Pipeline análisis
│   ├── audio_analyzer.py              [EXPERIMENTAL] Analizador audio
│   ├── mastering.py                   [EXPERIMENTAL] Pipeline masterización
│   ├── mixing.py                      [EXPERIMENTAL] Pipeline mezcla (viejo)
│   ├── mix_pipeline.py                [EXPERIMENTAL] Pipeline mezcla (nuevo)
│   └── reaper_pipeline.py             [EXPERIMENTAL] Pipeline REAPER
│
├── presets/
│   └── style_templates.json           [EXPERIMENTAL] Presets de estilos
│
├── pro/
│   ├── __init__.py
│   ├── analysis.py                    [LEGACY] Análisis "pro" antigua
│   ├── audio_io.py                    [LEGACY] I/O audio
│   ├── core.py                        [LEGACY] Core antiguo
│   ├── dsp_engine.py                  [LEGACY] Engine DSP viejo
│   ├── dsp_fx.py                      [LEGACY] FX DSP viejo
│   ├── dsp_pipeline_full.py           [LEGACY] Pipeline DSP completo viejo
│   ├── dsp.py                         [LEGACY] DSP funciones básicas
│   └── exporter.py                    [LEGACY] Exportador
│
├── reaper/
│   ├── __init__.py
│   ├── osc_bridge.py                  [EXPERIMENTAL] Bridge OSC REAPER
│   ├── project_manager.py             [EXPERIMENTAL] Gestor proyectos REAPER
│   ├── track_manager.py               [EXPERIMENTAL] Gestor pistas REAPER
│   └── templates/                     [EXPERIMENTAL] Templates REAPER
│
├── router/
│   ├── __init__.py
│   └── dispatcher.py                  [EXPERIMENTAL] Dispatcher de rutas
│
├── routes/
│   ├── __init__.py
│   └── schemas.py                     [EXPERIMENTAL] Schemas FastAPI
│
├── scripts/                           [EMPTY]
│
├── tests/
│   ├── __init__.py
│   ├── test_shub_core.py              [EXPERIMENTAL] Tests core
│   ├── test_shub_pipelines.py         [EXPERIMENTAL] Tests pipelines
│   └── test_shub_reaper_bridge.py     [EXPERIMENTAL] Tests REAPER bridge
│
├── utils/
│   └── __init__.py                    [EMPTY]
│
└── workspace/
    ├── cache/                         [EMPTY] Cache runtime
    └── tmp/                           [EMPTY] Temp runtime
```

---

## 3. Matriz VIGENTE vs OBSOLETO

| Categoría | Archivos | Estado | Acción |
|-----------|----------|--------|--------|
| **API Activa** | `main.py` | VIGENTE | Mantener, expandir con real processing en v8 |
| **Docker** | `Dockerfile`, docker-compose entrada | VIGENTE | Mantener, optimizar mem si es necesario |
| **Core Engines** | `core/`, `engines/`, `dsp/` | EXPERIMENTAL | Revisar, documentar, integrar en v8 |
| **Pipelines** | `pipelines/` | EXPERIMENTAL | Revisar duplicados, consolidar en v8 |
| **Integrations** | `integrations/` | EXPERIMENTAL | Preparar para v8 |
| **REAPER Support** | `reaper/`, `integrations/reaper_rpc.py` | EXPERIMENTAL | Preparar para v8 |
| **BD Models** | `database/`, `shub_db_schema.py` | EXPERIMENTAL | Diseñar para v8 con SharedDB |
| **Pro Subfolder** | `pro/` | LEGACY | Remover o archivar en v8 |
| **Old Bridges** | `shub_*_bridge.py` (no integrados) | LEGACY | Archivar para referencia |
| **Docs en pro/** | Varios `.md` en `docs/` | LEGACY | Archivar, crear nuevas en v8 |

---

## 4. Flujos Reales Vigentes

### 4.1. Health Check (Funcional)
```
GET /health
→ Retorna {"status": "healthy", "version": "7.0", ...}
```

### 4.2. Envío de Tarea (Funcional, pero Mock)
```
POST /shub/analyze (con X-VX11-Token)
Payload: {"file_path": "...", "options": {...}}
→ Retorna {"status": "queued", "task_id": "mock-task-001"}
```

**Nota:** La respuesta es mock; no hay procesamiento real.

### 4.3. Integración Esperada (No Vigente)
```
Madre → Spawner → /shub/analyze
→ Shub procesa real
→ Resultado en BD
→ Madre consulta y retorna a usuario
```

Esta integración está **diseñada pero no implementada** en main.py.

---

## 5. Flujos Rotos o Incompletos

| Flujo | Problema | Causa |
|-------|----------|-------|
| **REAPER Integration** | Endpoints `/shub/reaper/*` devuelven mock | No hay conexión real a REAPER RPC |
| **Real Audio Processing** | `/shub/analyze`, `/shub/mix`, `/shub/master` no procesan | Engines no cargados en main.py |
| **Assistant Chat** | `/shub/assistant/chat` retorna mock | IA no integrada |
| **BD Sync** | Sin persistencia | No hay conexión a SharedDB o PostgreSQL |
| **Lazy Init Completo** | Engines nunca se inicializan realmente | `_engines = {}` siempre vacío en main.py |

---

## 6. TODOs Ordenados para v8

### Priority 1: Core Engine Integration
- [ ] Integrar `core/dsp_engine.py` en main.py (init on first request)
- [ ] Implementar real audio analysis en `/shub/analyze`
- [ ] Implementar real mixing en `/shub/mix`
- [ ] Implementar real mastering en `/shub/master`
- [ ] Crear tests para cada engine

### Priority 2: Database & Persistence
- [ ] Definir schema final SharedDB (tasks, audio_files, results, etc.)
- [ ] Implementar `integrations/db_sync.py` para guardar resultados
- [ ] Crear migrations en `database/migrations/`

### Priority 3: REAPER Integration
- [ ] Implementar conexión real a REAPER RPC (`integrations/reaper_rpc.py`)
- [ ] Completar `/shub/reaper/projects`, `/shub/reaper/apply-fx`, `/shub/reaper/render`
- [ ] Tests con REAPER mock/real

### Priority 4: AI Assistant
- [ ] Integrar Switch/Hermes para chat con IA
- [ ] Implementar `/shub/assistant/chat` real
- [ ] Prompts y contexto para ingeniero de sonido

### Priority 5: Cleanup
- [ ] Remover/archivar carpeta `pro/` (código obsoleto)
- [ ] Remover/archivar `shub_*_bridge.py` no integrados (o documentar para referencia)
- [ ] Limpiar docs legacy en `docs/` (mover a `docs/archive/`)
- [ ] Consolidar `pipelines/mixing.py` + `mix_pipeline.py` (hay duplicados)

### Priority 6: Documentation
- [ ] Crear `shubniggurath/README_v8_IMPLEMENTATION.md` con checklist
- [ ] Documentar API final en OpenAPI/Swagger
- [ ] Crear guía de extensión: "Cómo agregar un nuevo engine"

---

## 7. Análisis de Subcarpetas Principales

### 7.1. `core/`
**Estado:** EXPERIMENTAL (código hay, pero no usado)

**Archivos:**
- `dsp_engine.py` — Motor DSP central, parece completo
- `engine.py` — Base class para engines
- `fx_engine.py` — Efectos de audio
- `initializer.py` — Setup de engines
- `registry.py` — Registro de motores

**Uso Actual:** Ninguno (main.py no importa)

**Acción v8:** Importar en main.py, crear instancias on-demand, testar

---

### 7.2. `engines/`
**Estado:** EXPERIMENTAL (código hay)

**Archivos:**
- `analyzer_engine.py`
- `master_engine.py`
- `mix_engine.py`
- `spectral_engine.py`
- `ai_assistant_engine.py`

**Uso Actual:** Ninguno

**Acción v8:** Revisar, limpiar duplicados con `core/`, integrar en dispatcher

---

### 7.3. `pipelines/`
**Estado:** EXPERIMENTAL (parcialmente duplicado)

**Archivos:**
- `analysis.py` + `audio_analyzer.py` (¿duplicados?)
- `mixing.py` + `mix_pipeline.py` (¿duplicados?)
- `mastering.py`
- `reaper_pipeline.py`

**Acción v8:** Consolidar, eliminar duplicados, integrar en main.py flows

---

### 7.4. `pro/`
**Estado:** LEGACY (código viejo, no utilizado)

**Decisión:** Remover o archivar en v8 (no merece espacio en production)

---

### 7.5. `database/`
**Estado:** EXPERIMENTAL (models hay, no usados)

**Problema:** Schema es para PostgreSQL; VX11 usa SQLite (`data/runtime/vx11.db`)

**Acción v8:** Alinear con SharedDB schema o crear tablas Shub en vx11.db

---

## 8. Recomendaciones de Limpieza Inmediata (v7 Final)

**NO BORRES NADA.** Solo marca, organiza, documenta:

1. **Crear archivo de "legacy mapping":**
   ```
   shubniggurath/docs/LEGACY_MAPPING_v8.md
   - Mapea carpeta `pro/` → qué guardar/descartar
   - Mapea archivos `shub_*_bridge.py` → si reutilizar o no
   ```

2. **Actualizar `shubniggurath/README.md`:**
   - Aclarar que v7 es "lazy init" con endpoints mock
   - Explicar que v8 tendrá real processing

3. **Crear `shubniggurath/TODO_v8.md`:**
   - Copiar TODOs de esta auditoría
   - Detallar steps de integración

4. **Sin romper nada:**
   - Dejar main.py como está (funciona, saludable)
   - No tocar Dockerfile, docker-compose
   - No eliminar carpetas experimentales (solo documentar)

---

## 9. Comandos Útiles para Referencia

```bash
# Test health
curl http://localhost:8007/health | jq .

# Test endpoint analyze (mock)
curl -X POST http://localhost:8007/shub/analyze \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/data/audio.wav"}'

# Ver logs
docker-compose logs -f shubniggurath

# Entrar en contenedor
docker exec -it vx11-shubniggurath bash

# Ver estructura codigo
find shubniggurath -name "*.py" -type f | head -30
```

---

## 10. Conclusiones

- ✅ **Shub está SALUDABLE en v7:** API minimalista pero funcional, sin crashes
- ⚠️ **Shub está EXPERIMENTAL:** Código existe pero no integrado (core, engines, pipelines)
- 🎯 **Shub necesita INTEGRACIÓN para v8:** Real processing, REAPER, IA, BD
- 📋 **Limpieza RECOMENDADA:** Archivar legacy (`pro/`, old bridges), consolidar duplicados

**Para v8 y más allá:** Seguir este roadmap sin prisa, testeando cada step. VX11 es autónomo, Shub será también.

---

**Auditoría completada:** 9 dic 2025, por agente IA VX11
