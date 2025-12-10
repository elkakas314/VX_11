# SHUB-NIGGURATH: TODO LIST CANÓNICA EXACTA DEL CANON

**Fuente:** 
- shub.txt (531 L) — Especificación de 8 módulos core
- shub2.txt (3,332 L) — Código fuente canónico (ShubCoreInitializer, DSPEngine, FXEngine, pipelines, virtual engineer)
- shubnoggurath.txt (3,577 L) — Arquitectura estudio AAA, schema PostgreSQL, módulos especializados

**Estado Actual:** 
- ✅ engines_paso8.py reescrito canonicamente (714L, 100% fidelidad a shub2.txt)
- ✅ FASE 1 COMPLETADA: shubniggurath/main.py (566L production FastAPI con health, analyze, mastering, batch APIs)

---

## 🎯 MÓDULOS CORE FALTANTES (del canon)

### 1. **reaper_rpc.py** (Integración REAPER ↔ Shub)
**Líneas del canon:** shub.txt § "ANEXO A2 — INTEGRACIÓN REAPER"
**Funcionalidad canónica exacta:**
- `list_projects()` — Listar proyectos REAPER abiertos
- `load_project(path)` — Cargar proyecto .RPP
- `analyze_project()` — Análisis de proyecto completo
- `list_tracks()` — Listar pistas
- `list_items()` — Listar items de audio
- `list_fx(track)` — Listar FX en pista
- `apply_fx_chain(track, fx_chain)` — Aplicar cadena de efectos
- `render_master(out_path)` — Renderizar master
- `update_project_metadata()` — Actualizar metadata
- `send_shub_status_to_reaper()` — Estado de Shub a REAPER
- `auto_mix()` — Mezcla automática (basado en IA de Switch)
- `auto_master()` — Mastering automático

**Protocolo:** HTTP RPC JSON, puerto 8007 (var config), token auth

**Requisitos:**
- Servidor RPC accesible desde REAPER
- Scripts LUA para integración (shub_launcher.lua, shub_apply_fx.lua, shub_master.lua, shub_ping.lua)
- Instalación en ~/.config/REAPER/Scripts/

---

### 2. **audio_batch_engine.py** (Procesamiento por lotes)
**Líneas del canon:** shub.txt § "ANEXO A1" + shub2.txt § "batch_engine.py"
**Funcionalidad canónica exacta:**
- Procesamiento de múltiples archivos de audio
- Cola inteligente con prioridades
- Gestión de recursos dinámicos
- Reporte de progreso en tiempo real
- Recuperación automática de errores
- Validación de resultados post-procesamiento

**Requisitos:**
- Integración con Hormiguero para cola distribuida
- Persistencia en BD (data/runtime/vx11.db)
- HTTP API para submit/status/cancel

---

### 3. **Pipelines Tentaculares Fase 1→8** (COMPLETAS)
**Líneas del canon:** shub2.txt § "dsp_pipeline_full.py" + "mode_c_pipeline.py"
**Fases canónicas exactas:**

#### FASE 1: Análisis Raw
- Detección de clipping digital
- Validación de NaN/Inf
- Medición de amplitud máxima

#### FASE 2: Normalización
- Peak normalization a -3 dBFS
- DC offset removal
- Detección de sobrenormalización

#### FASE 3: Análisis FFT Multi-resolución
- FFT sizes: 1024, 2048, 4096, 8192
- Análisis por bandas (sub_bass, bass, low_mid, mid, high_mid, presence, brilliance)
- Espectral flatness/crest
- Detección de picos armónicos

#### FASE 4: Clasificación Avanzada
- Combinación de análisis raw + normalizado + FFT
- Clasificación de instrumento
- Clasificación de género
- Predicción de mood

#### FASE 5: Detección de Issues
- Issues espectrales (imbalance, excesivos sub-bass, falta de highs)
- Issues dinámicos (high dynamic range, over-compressed)
- Issues de resolución del canon (clipping, DC offset, noise, phase, sibilance, resonances)

#### FASE 6: Generación de FX Chain
- Basada en clasificación e issues
- Selección inteligente de plugins
- Configuración de parámetros

#### FASE 7: Generación de Preset REAPER
- Proyecto .RPP con tracks
- Routing matrix
- Automation basada en análisis

#### FASE 8: JSON para VX11
- Salida estándar VX11 con análisis completo
- Metadata del procesamiento
- Recomendaciones de siguiente paso

---

### 4. **Ingeniería Virtual Completa** (Virtual Engineer)
**Líneas del canon:** shub2.txt § "virtual_engineer.py"
**Funcionalidad canónica exacta:**
- Sesión de ingeniería con razonamiento explícito
- Preguntas de clarificación inteligentes
- Toma de decisiones con confianza
- Análisis de impacto esperado (calidad, recursos, artístico)
- Aprendizaje automático de feedback
- Generación de recomendaciones finales

**Decisiones que debe tomar:**
1. Prioridad de procesamiento (crítico vs normal)
2. Enfoque de procesamiento (correctivo vs iterativo vs standard)
3. Delegación a Switch (y qué módulo)
4. Mastering (streaming vs album vs general)
5. Export (formatos, sample rates, bit depths)

---

### 5. **Motores Especializados** (del canon — OPCIONALES PERO EN TXT)
**Líneas del canon:** shubnoggurath.txt § "Motor de Baterías Avanzado", "Motor de Guitarras Completo", "Motor de Voz Profesional"

**Módulos opcionales para FASE 4+:**
- `drum_engine_extreme.py` — Análisis multi-pista, replacement, humanización, mezcla
- `guitar_engine_complete.py` — Amp profiling, tone matching, reamping, RIG builder
- `vocal_engine_professional.py` — Comping, pitch correction, cadenas por estilo, problem solving

---

### 6. **Sistema de Gestión de Plugins** (Advanced Plugin Manager)
**Líneas del canon:** shubnoggurath.txt § "Advanced Plugin Manager"
**Funcionalidad canónica exacta:**
- Escaneo automático de plugins VST/AU/LV2
- Validación y categorización
- Mapeo de parámetros
- Análisis de rendimiento
- Blacklisting de plugins problémicos
- Creación de recetas FX inteligentes

---

### 7. **Render y Validación Avanzados** (Advanced Render System)
**Líneas del canon:** shubnoggurath.txt § "Advanced Render System"
**Funcionalidad canónica exacta:**
- Renderizado múltiple de formatos
- Validación comprehensiva post-render
- Cumplimiento de estándares de plataforma (Spotify, Apple Music, YouTube, Tidal, Vinyl, CD)
- Corrección automática de problemas
- Renderizado por lote con gestor de recursos

---

### 8. **Asistente de Grabación Completo** (Complete Recording Assistant)
**Líneas del canon:** shubnoggurath.txt § "Complete Recording Assistant"
**Funcionalidad canónica exacta:**

#### PRE-SESIÓN:
- Wizard interactivo avanzado
- Calibración de ganancia profesional
- Análisis de sala
- Análisis de fase del sistema
- Chequeo de sistema

#### EN SESIÓN:
- Monitorización en tiempo real
- Análisis de toma comprehensivo
- Feedback inmediato al artista
- Alertas inteligentes

#### POST-SESIÓN:
- Comping automático
- Clasificación de tomas por calidad
- Sugerencias de edición
- Preparación para mezcla

---

### 9. **Gestión de Rigs Virtuales Globales** (Global Amplifier Rig System)
**Líneas del canon:** shubnoggurath.txt § "Global Amplifier Rig System"
**Funcionalidad canónica exacta:**
- Diseño completo de rig (pedales → amp → micrófono → post-processing)
- Tone matching system (referencia → DI → rig de matching)
- Ecosistema de IRs (análisis, clasificación, recomendación)

---

### 10. **Integración Real con VX11** (VX11 Integration Contracts)
**Líneas del canon:** shubnoggurath.txt § "Real VX11 Integration"
**Contratos exactos:**
- CAPABILITIES_CONTRACT (capacidades exposición a Madre)
- SWITCH_CONTRACT (routing de tareas a Switch)
- HORMIGUERO_CONTRACT (gestión de recursos)
- RealVX11Integration (registro, despliegue, flujo de tareas)

---

### 11. **Flujo "Una Pista → De 0 a 100"** (OneTrackCompleteProduction)
**Líneas del canon:** shubnoggurath.txt § "One Track Complete Production"
**Fases canónicas exactas:**
1. ANÁLISIS Y PLANIFICACIÓN COMPLETA
2. PREPRODUCCIÓN Y ARREGLOS AVANZADOS
3. PRODUCCIÓN Y GRABACIÓN VIRTUAL COMPLETA
4. MEZCLA PROFESIONAL AVANZADA
5. MASTERING MULTIFORMATO PROFESIONAL
6. CONTROL DE CALIDAD Y VALIDACIÓN
7. ENTREGA Y DOCUMENTACIÓN PROFESIONAL

---

### 12. **Base de Datos Completa** (Shub Database Schema)
**Líneas del canon:** shub2.txt § "shub_db.py" + shubnoggurath.txt § "Esquema PostgreSQL Completo"
**Tablas exactas del canon:**
- projects (shub_projects)
- tracks (shub_tracks)
- analyses (shub_analyses)
- fx_chains (shub_fx_chains)
- presets (shub_presets)
- issues (shub_issues)
- assets (shub_assets)
- decisions (shub_decisions)
- autolearn_memory (shub_autolearn_memory)
- history (shub_history)

---

## 🚀 PLAN DE IMPLEMENTACIÓN INCREMENTAL

### **PASO 1 — Cargar y analizar TODO el canon (COMPLETADO ✅)**
- ✅ shub.txt (531 L) leído
- ✅ shub2.txt (3,332 L) leído
- ✅ shubnoggurath.txt (3,577 L) leído
- ✅ TO-DO LIST EXACTA extraída

---

### **PASO 2 — Plan de implementación sin romper VX11**

**Orden de implementación recomendado:**

1. **reaper_rpc.py** → Integración REAPER (CRÍTICO)
2. **audio_batch_engine.py** → Procesamiento por lotes
3. **pipelines tentaculares (FASE 1-8)** → Completar pipelines
4. **virtual_engineer.py** → Ingeniería virtual avanzada
5. **plugin_manager.py** → Gestión de plugins
6. **render_system.py** → Render y validación
7. **recording_assistant.py** → Asistente de grabación
8. **rig_system.py** → Gestión de rigs (opcional)
9. **vx11_integration.py** → Integración completa con VX11
10. **one_track_production.py** → Flujo completo 0→100

---

## ✅ REGLAS DE IMPLEMENTACIÓN

1. **NO TOQUES** switch, madre, hormiguero, manifestator, BD
2. **SOLO** archivos nuevos en `shubniggurath/integrations/` o `shubniggurath/engines/`
3. **NO REESCRIBAS** engines_paso8.py (ya es 100% canónico)
4. **SEMPRE** crea archivo `SHUB_STEP_X.md` por paso
5. **SOLO** código canónico (sin inventos, sin lógica genérica)

---

**LISTO PARA PASO 2: Plan de implementación incremental**

Continuamos 👇
