# 🎯 TODO_CANON_SHUB — Lista Maestra Completa

**Fuentes Combinadas:**
- ✅ SHUB_CANONICAL_TODO_LIST.md
- ✅ SHUB_REESCRITURA_FINAL.md
- ✅ PLAN_TENTACULAR_FINAL.md

**Fecha:** 10 Diciembre 2025 | **Estado:** PRE-FASE 2 | **Revisión:** v1.0

---

## 📋 SECCIÓN 1: MÓDULOS CORE COMPLETADOS ✅

### ✅ COMPLETADO: engines_paso8.py (700 L)
**Estado:** Canónico 100%, compilado, en producción
**Contiene:**
- ✅ AudioAnalysis (33 campos)
- ✅ FXChain (5 campos)
- ✅ REAPERPreset (6 campos)
- ✅ DSPEngine (6 métodos análisis paralelo)
- ✅ FXEngine (generador de cadenas)
- ✅ ShubCoreInitializer (singleton)
- ✅ Métodos de análisis: levels, spectral, dynamics, issues, musical, classification

**No Modificable:** INTOCABLE, CANÓNICO

---

### ✅ COMPLETADO: main.py (566 L)
**Estado:** Producción FastAPI, compilado
**Contiene:**
- ✅ 10 endpoints HTTP
- ✅ Lifespan manager
- ✅ Token auth + CORS
- ✅ Batch queue en memoria
- ✅ Integración engines_paso8.py

**No Modificable:** INTOCABLE (FASE 1)

---

## 📋 SECCIÓN 2: MÓDULOS CORE PENDIENTES (FASES 2-6)

### ⏳ FASE 2.1: reaper_rpc.py (INTEGRACIÓN REAPER)

**Ubicación:** `shubniggurath/integrations/reaper_rpc.py`

**Requisitos Canónicos (del canon):**

#### 12 Métodos Obligatorios:
1. ✋ `list_projects()` → `{status, projects[], total_projects}`
   - Lista proyectos .RPP abiertos en REAPER
   - Retorna path, nombre, estado

2. ✋ `load_project(path: str)` → `{status, project_path, metadata}`
   - Carga proyecto REAPER en memoria
   - Valida formato RPP

3. ✋ `analyze_project()` → `{status, analysis: {tracks, bpm, issues, recommendations}}`
   - Análisis de proyecto completo
   - Retorna diagnóstico

4. ✋ `list_tracks()` → `{status, tracks[], total_tracks}`
   - Lista todas las pistas del proyecto actual
   - Retorna GUID, nombre, volumen, mute, solo

5. ✋ `list_items(track_index?: int)` → `{status, items[], total_items}`
   - Lista items de audio (por pista o global)
   - Retorna posición, duración, media

6. ✋ `list_fx(track_index: int)` → `{status, fx[], total_fx}`
   - Lista FX chain de pista
   - Retorna nombre plugin, parámetros

7. ✋ `apply_fx_chain(track_index: int, fx_chain: FXChain)` → `{status, before, after}`
   - Aplica cadena de FX a pista
   - Retorna antes/después metrics

8. ✋ `render_master(output_path: str, format: str, sample_rate: int)` → `{status, output_info}`
   - Renderiza master a archivo
   - Soporta WAV, MP3, FLAC, AAC

9. ✋ `update_project_metadata(metadata: Dict)` → `{status, metadata_updated}`
   - Actualiza metadata del proyecto (compositor, comentarios, etc.)

10. ✋ `send_shub_status_to_reaper(status: Dict)` → `{status, reaper_acknowledged}`
    - Envía estado de Shub a REAPER
    - Bidireccional

11. ✋ `auto_mix(mix_style: str)` → `{status, changes, before_after_metrics}`
    - Mezcla automática inteligente
    - Estilos: balanced, bright, warm, loud, dynamic

12. ✋ `auto_master(master_style: str)` → `{status, master_bus_chain, before_after}`
    - Mastering automático
    - Estilos: streaming, vinyl, cd, loudness_war, dynamic

#### Extensiones Obligatorias:
- ✋ `preset_builder()` → Construcción de presets REAPER
- ✋ `pipeline_to_reaper()` → Convierte pipeline Shub a proyecto REAPER
- ✋ SWS Integration (Scripts LUA hooks)
- ✋ ReaPack Integration
- ✋ Control bidireccional REAPER ↔ VX11

**Protocolo:** HTTP JSON RPC, puerto 8007, token auth X-VX11-Token

**Validación:** Compilación + 0 errores

---

### ⏳ FASE 2.2: vx11_bridge.py (HTTP BRIDGE VX11)

**Ubicación:** `shubniggurath/integrations/vx11_bridge.py`

**Requisitos Canónicos:**

#### 9 Métodos HTTP Obligatorios:
1. ✋ `analyze()` → Notificar análisis a Madre + feedback Switch
2. ✋ `mastering()` → Workflow mastering coordinado
3. ✋ `batch_submit()` → Enviar job a Hormiguero
4. ✋ `batch_status()` → Consultar estado batch
5. ✋ `report_issue_to_hormiguero()` → Reportar issues graves
6. ✋ `notify_madre()` → Notificación genérica Madre
7. ✋ `notify_switch()` → Notificación Switch
8. ✋ `notify_hijas()` → Notificación hijas tentaculares
9. ✋ `health_cascade_check()` → Verificar salud módulos

**Protocolo:** HTTP async/await, httpx.AsyncClient, NO imports cruzados

**URLs Base:**
- Madre: `settings.madre_url or f"http://madre:{settings.madre_port}"`
- Switch: `settings.switch_url or f"http://switch:{settings.switch_port}"`
- Hormiguero: `settings.hormiguero_url or f"http://hormiguero:{settings.hormiguero_port}"`

**Validación:** Compilación + 0 errores

---

### ⏳ FASE 3: dsp_pipeline_full.py (8 FASES TENTACULARES)

**Ubicación:** `shubniggurath/core/dsp_pipeline_full.py`

**Clase Principal:** `DSPPipelineFull`

**Método Entry Point:**
```python
async def run_full_pipeline(audio_bytes: bytes, sample_rate: int, mode: str) -> Dict
# Modos: quick (5s), mode_c (30s, default), deep (120s)
```

**8 Fases Obligatorias (Canónicas):**

#### FASE 1: Análisis Raw ✋
- ✋ Detección de clipping digital
- ✋ Validación de NaN/Inf
- ✋ Medición de amplitud máxima

#### FASE 2: Normalización ✋
- ✋ Peak normalization a -3 dBFS
- ✋ DC offset removal
- ✋ Detección de sobrenormalización

#### FASE 3: FFT Multi-resolución ✋
- ✋ FFT sizes: 1024, 2048, 4096, 8192
- ✋ Análisis por bandas (7 bandas: sub_bass, bass, low_mid, mid, high_mid, presence, brilliance)
- ✋ Spectral flatness/crest
- ✋ Detección de picos armónicos

#### FASE 4: Clasificación Avanzada ✋
- ✋ Combinación: raw + normalizado + FFT
- ✋ Clasificación de instrumento (10 clases)
- ✋ Clasificación de género (8 géneros)
- ✋ Predicción de mood (5 moods)

#### FASE 5: Detección de Issues ✋
- ✋ Issues espectrales: imbalance, excess sub-bass, lack of highs
- ✋ Issues dinámicos: high range, over-compressed
- ✋ Issues técnicos: clipping, DC offset, noise, phase, sibilance, resonances

#### FASE 6: Generación FX Chain ✋
- ✋ Basada en clasificación + issues
- ✋ Selección inteligente de plugins
- ✋ Configuración automática de parámetros

#### FASE 7: Generación REAPER Preset ✋
- ✋ Proyecto .RPP con tracks
- ✋ Routing matrix
- ✋ Automation basada en análisis

#### FASE 8: JSON VX11 ✋
- ✋ Salida AudioAnalysis canónica (33 campos)
- ✋ Metadata del procesamiento
- ✋ Recomendaciones de siguiente paso

**Retorna:**
```python
{
    "status": "success",
    "pipeline_id": UUID,
    "phases_completed": [1, 2, 3, 4, 5, 6, 7, 8],
    "audio_analysis": AudioAnalysis,
    "fx_chain": FXChain,
    "reaper_preset": REAPERPreset,
    "processing_time_ms": int
}
```

**Validación:** Compilación + 0 errores

---

### ⏳ FASE 4: audio_batch_engine.py (BATCH QUEUE)

**Ubicación:** `shubniggurath/core/audio_batch_engine.py`

**Clases:**
- ✋ `BatchJob` (dataclass)
- ✋ `AudioBatchEngine`

**Métodos Obligatorios:**
1. ✋ `enqueue_job(audio_files, job_name?, analysis_type?, priority?)` → `{status, job_id, queue_position, estimated_wait_seconds}`
2. ✋ `get_status(job_id)` → `{status, job: {status, progress, estimated_remaining}}`
3. ✋ `cancel_job(job_id)` → `{status, message}`
4. ✋ `process_queue()` [internal] → Procesa cola
5. ✋ `_save_job_to_db()` [internal] → Persiste a BD

**Features Obligatorios:**
- ✋ Cola inteligente con prioridades (1-10)
- ✋ Persistencia en vx11.db (tabla batch_jobs via Task)
- ✋ Integración Hormiguero vía vx11_bridge
- ✋ Notificación a Madre de completación
- ✋ Manejo automático de errores + recuperación
- ✋ Status enum: queued → processing → completed|failed|cancelled

**Validación:** Compilación + 0 errores

---

### ⏳ FASE 5: virtual_engineer.py (SISTEMA EXPERTO)

**Ubicación:** `shubniggurath/core/virtual_engineer.py`

**Clase Principal:** `VirtualEngineer`

**5 Métodos Decisorios Obligatorios:**

1. ✋ `decide_pipeline(audio_analysis, user_preference?)` → `{status, pipeline_mode, rationale, estimated_time, phases}`
   - Heurística: complejidad > 0.7 → deep; > 0.4 → mode_c; else → quick

2. ✋ `decide_master_style(audio_analysis, genre?, user_preference?)` → `{status, master_style, target_lufs, gain_adjustment, plugins[], description}`
   - Estilos: streaming (-14 LUFS), vinyl (-16 LUFS), cd (-9 LUFS), loudness_war (-4 LUFS), dynamic (-18 LUFS)
   - Heurísticas por género

3. ✋ `decide_priority(audio_analysis, user_priority?)` → `{status, priority: 1-10, rationale, issues_severity}`
   - Heurística: priority = min(10, max(1, int(2 + issue_count*1.5 + complexity*5)))

4. ✋ `decide_delegation(audio_analysis, pipeline_mode?)` → `{status, delegations: {madre, switch?, hormiguero?}}`
   - Siempre Madre (orquestador)
   - Switch si issues > 2 o complejidad > 0.5
   - Hormiguero si deep mode

5. ✋ `generate_recommendations(audio_analysis)` → `{status, recommendations: [{action, reason, priority}], next_steps[]}`

**Helper Methods Obligatorios:**
- ✋ `_calculate_complexity_score(audio_analysis)` → 0-1
- ✋ `_choose_master_style_heuristic(audio_analysis)` → master_style

**Validación:** Compilación + 0 errores

---

## 📋 SECCIÓN 3: MÓDULOS VX11 WIRING (FASE 6)

### ⏳ FASE 6.1: Madre Integration

**Archivo:** `madre/dsl_parser.py` (SOLO PARCHES NECESARIOS)

**Requisitos:**
- ✋ Detectar dominio DSL: "AUDIO", "SHUB", "mastering", "batch"
- ✋ Crear hija tentacular cuando detecte
- ✋ Hija llama `vx11_bridge.analyze()` o `vx11_bridge.mastering()`
- ✋ Guardar resultado en BD
- ✋ Notificar Hormiguero si hay issues graves
- ✋ Notificar Operator si procede

**NO Modificable:** Resto de Madre

---

### ⏳ FASE 6.2: Switch Router

**Archivo:** `switch/shub_router.py` (SOLO PARCHES NECESARIOS)

**Requisitos:**
- ✋ HTTP-only calls a Shub (puerto 8007)
- ✋ Usar vx11_bridge para todas las comunicaciones
- ✋ Decidir delegación Hermes vs Shub vs Madre
- ✋ Respeta prioridades canónicas
- ✋ NO imports directos a shubniggurath

**NO Modificable:** Resto de Switch

---

### ⏳ FASE 6.3: Hermes Registry

**Archivo:** `hermes/discovery.py` (SOLO PARCHES NECESARIOS)

**Requisitos:**
- ✋ Registrar "remote_audio_dsp" (Shub)
- ✋ Exponer: health(), coste(), latencia()
- ✋ Service discovery para otros módulos
- ✋ Incluir capabilities contract

**NO Modificable:** Resto de Hermes

---

### ⏳ FASE 6.4: Hormiguero Feromonas

**Archivo:** `hormiguero/feromonas.py` (SOLO PARCHES NECESARIOS)

**Requisitos:**
- ✋ Añadir feromonas: audio_scan, audio_batch_fix
- ✋ Conectar a audio_batch_engine job queue
- ✋ Reina emite feromonas cuando hay issues
- ✋ Hormigas scanean archivos de audio

**NO Modificable:** Resto de Hormiguero

---

## 📋 SECCIÓN 4: MOTORES ESPECIALIZADOS (OPCIONAL FASE 7+)

### ⏳ OPCIONAL: drum_engine_extreme.py
**Módulo:** `shubniggurath/engines/drum_engine_extreme.py`
- ✋ Análisis multi-pista
- ✋ Replacement de samples
- ✋ Humanización
- ✋ Mezcla automática

**Ubicación Permitida:** `shubniggurath/engines/` (OK para crear)

---

### ⏳ OPCIONAL: guitar_engine_complete.py
**Módulo:** `shubniggurath/engines/guitar_engine_complete.py`
- ✋ Amp profiling
- ✋ Tone matching
- ✋ Reamping
- ✋ RIG builder

**Ubicación Permitida:** `shubniggurath/engines/` (OK para crear)

---

### ⏳ OPCIONAL: vocal_engine_professional.py
**Módulo:** `shubniggurath/engines/vocal_engine_professional.py`
- ✋ Comping automático
- ✋ Pitch correction
- ✋ Cadenas por estilo
- ✋ Problem solving

**Ubicación Permitida:** `shubniggurath/engines/` (OK para crear)

---

## 📋 SECCIÓN 5: SISTEMAS AVANZADOS (OPCIONAL FASE 8+)

### ⏳ OPCIONAL: plugin_manager.py
**Módulo:** `shubniggurath/api/plugin_manager.py`
- ✋ Escaneo automático VST/AU/LV2
- ✋ Validación y categorización
- ✋ Mapeo de parámetros
- ✋ Análisis de rendimiento
- ✋ Blacklist de plugins problémicos

**Ubicación Permitida:** `shubniggurath/api/` (OK para crear)

---

### ⏳ OPCIONAL: render_system.py
**Módulo:** `shubniggurath/api/render_system.py`
- ✋ Renderizado múltiple formatos
- ✋ Validación post-render
- ✋ Cumplimiento estándares plataforma
- ✋ Corrección automática
- ✋ Batch rendering

**Ubicación Permitida:** `shubniggurath/api/` (OK para crear)

---

### ⏳ OPCIONAL: recording_assistant.py
**Módulo:** `shubniggurath/api/recording_assistant.py`

**PRE-SESIÓN:**
- ✋ Wizard interactivo avanzado
- ✋ Calibración de ganancia
- ✋ Análisis de sala
- ✋ Chequeo de sistema

**EN-SESIÓN:**
- ✋ Monitorización real-time
- ✋ Análisis de toma
- ✋ Feedback al artista
- ✋ Alertas inteligentes

**POST-SESIÓN:**
- ✋ Comping automático
- ✋ Clasificación de tomas
- ✋ Sugerencias edición
- ✋ Prep para mezcla

**Ubicación Permitida:** `shubniggurath/api/` (OK para crear)

---

### ⏳ OPCIONAL: rig_system.py
**Módulo:** `shubniggurath/api/rig_system.py`
- ✋ Diseño completo rig (pedales → amp → micrófono → post)
- ✋ Tone matching system
- ✋ Ecosistema de IRs

**Ubicación Permitida:** `shubniggurath/api/` (OK para crear)

---

## 📋 SECCIÓN 6: TESTING (FASE 7)

### ⏳ tests/test_shub_dsp.py
**Ubicación Permitida:** `tests/` (OK para crear)
- ✋ Tests de pipeline DSP
- ✋ Validación de 8 fases
- ✋ Tests de análisis

---

### ⏳ tests/test_shub_core.py
**Ubicación Permitida:** `tests/` (OK para crear)
- ✋ Tests de módulos core
- ✋ Integración engines_paso8
- ✋ Tests de dataclasses

---

### ⏳ tests/test_shub_api.py
**Ubicación Permitida:** `tests/` (OK para crear)
- ✋ Tests de endpoints FastAPI
- ✋ Tests de HTTP calls
- ✋ Tests de auth

---

## 📋 SECCIÓN 7: DOCKER VALIDATION (FASE 7)

### ⏳ docker-compose.yml
**Modificaciones Necesarias:**
- ✋ Verificar servicio Shub en puerto 8007
- ✋ Healthcheck correcto
- ✋ NO romper servicios existentes
- ✋ Variables de entorno correctas

---

## 📊 RESUMEN ESTADO

| Item | Estado | Líneas | Prioridad |
|------|--------|--------|-----------|
| engines_paso8.py | ✅ COMPLETADO | 700 | CRÍTICO |
| main.py | ✅ COMPLETADO | 566 | CRÍTICO |
| reaper_rpc.py | ⏳ FASE 2.1 | ~750 | CRÍTICO |
| vx11_bridge.py | ⏳ FASE 2.2 | ~550 | CRÍTICO |
| dsp_pipeline_full.py | ⏳ FASE 3 | ~700 | CRÍTICO |
| audio_batch_engine.py | ⏳ FASE 4 | ~500 | CRÍTICO |
| virtual_engineer.py | ⏳ FASE 5 | ~500 | CRÍTICO |
| Madre wiring | ⏳ FASE 6.1 | ~50 | IMPORTANTE |
| Switch wiring | ⏳ FASE 6.2 | ~50 | IMPORTANTE |
| Hermes wiring | ⏳ FASE 6.3 | ~50 | IMPORTANTE |
| Hormiguero wiring | ⏳ FASE 6.4 | ~50 | IMPORTANTE |
| Tests | ⏳ FASE 7 | ~300 | IMPORTANTE |
| Docker | ⏳ FASE 7 | ~20 | IMPORTANTE |
| **TOTAL** | **⏳ 60% COMPLETE** | **~4,686** | - |

---

## 🎯 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

**Bloqueante:** Las fases siguientes dependen de la anterior completar

1. ✅ **COMPLETADO:** engines_paso8.py (CANÓNICO)
2. ✅ **COMPLETADO:** main.py (FastAPI)
3. 🔴 **SIGUIENTE:** reaper_rpc.py (FASE 2.1)
4. 🟡 **DESPUÉS:** vx11_bridge.py (FASE 2.2)
5. 🟡 **DESPUÉS:** dsp_pipeline_full.py (FASE 3)
6. 🟡 **DESPUÉS:** audio_batch_engine.py (FASE 4)
7. 🟡 **DESPUÉS:** virtual_engineer.py (FASE 5)
8. 🟡 **DESPUÉS:** Wiring VX11 (FASE 6)
9. 🟡 **DESPUÉS:** Tests + Docker (FASE 7)

---

## 📝 NOTAS IMPORTANTES

**PROHIBICIONES ABSOLUTAS:**
- ❌ NO modificar engines_paso8.py (INTOCABLE)
- ❌ NO modificar main.py (excepto FASE 1 ✅)
- ❌ NO crear imports cruzados entre microservicios
- ❌ NO modificar madre, switch, hermes, hormiguero (excepto wiring minimales FASE 6)
- ❌ NO usar localhost/127.0.0.1 (usar config.settings)

**PERMITIDO:**
- ✅ Crear archivos en shubniggurath/core/*, shubniggurath/integrations/*, shubniggurath/api/*, shubniggurath/config/*
- ✅ Crear tests en tests/*
- ✅ Usar HTTP async/await vía httpx
- ✅ Usar vx11_bridge para todas las llamadas VX11
- ✅ Usar config/settings.py para URLs/tokens

---

**ESTADO GLOBAL:** 🔴 **LISTO PARA INICIAR FASE 2.1 (reaper_rpc.py)**

---

*Generado: 10-12-2025 | TODO_CANON_SHUB v1.0 | LISTA MAESTRA COMPLETA*
