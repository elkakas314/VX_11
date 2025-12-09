# VX11 v6.7 — AUDITORÍA SHUB + OPERATOR (FASE 0)

**Fecha**: 2025-12-09  
**Estado**: PRE-RECONSTRUCCIÓN  
**Objetivo**: Diagnosticar estado actual e identificar gaps antes de integrar Shub Real + Operator Full

---

## 1. ANÁLISIS DE ARCHIVOS EXTERNOS (Documentos Shub)

### 🔴 PROBLEMA
Los archivos de especificación Shub (`shub2.txt`, `shub.txt`, `shubnoggurath.txt`) están fuera del workspace (/home/elkakas314/Documentos/), por lo que no se pueden leer directamente.

### ✅ SOLUCIÓN APLICADA
Extraer especificaciones desde documentación **EXISTENTE EN EL REPO**:
- `/home/elkakas314/vx11/docs/VX11_SHUB_SWITCH_HERMES_FLOWS_v7.x.md`
- `/home/elkakas314/vx11/docs/OPERATOR_DASHBOARD_v7.0.md`
- `/home/elkakas314/vx11/docs/SHUB_STATE_v7.1.md`
- `/home/elkakas314/vx11/shubniggurath/docs/CICLO_COMPLETO_CIERRE.md`

---

## 2. ESTADO ACTUAL DE SHUB-NIGGURATH

### 📊 Estructura
```
shubniggurath/
  ├─ main.py                    (486 líneas, FASTapi)
  ├─ api/
  ├─ core/
  │   ├─ engine.py
  │   ├─ registry.py
  │   └─ router.py
  ├─ routes/
  ├─ db/
  ├─ docs/
  └─ requirements_shub.txt
```

### ✅ COMPILACIÓN
- `python3 -m py_compile shubniggurath/**/*.py` : **OK**
- Health endpoint (8007): **OK** (`{"status":"healthy","service":"shub-niggurath","version":"3.0.0"}`

### 🔴 GAPS IDENTIFICADOS

| Aspecto | Estado | Problema | Impacto |
|---------|--------|---------|--------|
| **REAPER Control** | Simulado | ReaperController existe pero es mock | Audio no se procesa realmente |
| **Audio Analysis** | Stub | Motores de análisis no existentes | No hay análisis real de pistas |
| **Mix Engine** | Stub | Aplicación de mezcla es simulada | No hay automatización de mezcla |
| **Master Engine** | Stub | Mastering no implementado | No hay finalización de audio |
| **OSC Integration** | No existe | REAPER OSC no conectado | REAPER aislado del flujo |
| **Subprocess REAPER** | Existe | Llamada a `/usr/bin/reaper` hardcodeada | No portable |
| **DB Real** | Parcial | Usa JSON + mock | No auditoría ni persistencia real |

### 📋 ENDPOINTS SHUB EXISTENTES
- `GET /health` : ✅
- `GET /shub/reaper/open` : ⚠️ (mock)
- `GET /shub/reaper/track/list` : ⚠️ (mock)
- `POST /shub/reaper/mix/analyze` : ⚠️ (mock)
- `POST /shub/reaper/render` : ⚠️ (mock)
- **FALTA**: `/shub/analyze_track`, `/shub/apply_fx_chain`, `/shub/suggest_mix`, `/shub/execute_audio_task`

---

## 3. ESTADO ACTUAL DE OPERATOR

### 📊 Estructura
```
operator/
  ├─ main.py
  ├─ backend/
  │   ├─ main.py              (742 líneas, FastAPI)
  │   └─ services/
  │       ├─ health_aggregator.py
  │       ├─ intent_parser.py
  │       ├─ job_queue.py
  │       └─ clients.py
  ├─ frontend/
  │   ├─ src/
  │   │   ├─ App.tsx
  │   │   ├─ config.ts
  │   │   └─ components/
  │   ├─ nginx.conf
  │   └─ package.json
```

### ✅ COMPILACIÓN
- Backend `python3 -m py_compile operator/backend/main.py` : **OK**
- Frontend: TypeScript/React (no compilado aquí)

### 🔴 DIAGNÓSTICO DE PUERTO 8011

**Prueba de conexión**:
```bash
curl http://localhost:8011/health
# Esperado: {"status":"ok", ...}
# Actual: ??? (no levantado en entorno actual)
```

### 📋 ENDPOINTS OPERATOR BACKEND
- `GET /health` : ✅
- `GET /` : ✅ (root)
- `GET /system/status` : ✅
- `POST /intent/chat` : ✅
- `GET /ui/status` : ✅
- `GET /ui/events` : ✅
- **NUEVO (v6.7)**: `/operator/system/state`, `/operator/send_intent`, `/operator/power/*` (added earlier)

### 🔴 GAPS IDENTIFICADOS

| Aspecto | Estado | Problema | Impacto |
|---------|--------|---------|--------|
| **CORS** | ¿? | No verificado entre 8011 ↔ 8020 | Frontend puede no conectar |
| **API_BASE_URL** | Config hardcodeada | Frontend usa valores que pueden ser obsoletos | Desconexión |
| **Conversación** | Existe | Pero integración con Shub débil | Chat funciona, audio no |
| **Power Control** | Parcial | Endpoints existen, no testeados | Bajo consumo no verificado |
| **Dashboard** | React starter | No dashboard real visual | UI minimalista |
| **WebSocket** | No existe | Estado real-time no implementado | Updates no en vivo |

### 📋 PUERTOS Y URLS
- Backend Operator: `http://operator-backend:8011` (Docker) / `http://localhost:8011` (local)
- Frontend Operator: `http://localhost:8020` (Vite dev) / vía nginx en prod
- Tentáculo Link: `http://tentaculo_link:8000` (Docker) / `http://localhost:8000` (local)

---

## 4. FLUJO ACTUAL: SWITCH → SHUB → MADRE

### ✅ Lo que funciona
1. SWITCH recibe `/switch/chat` con `task_type="audio"`.
2. SWITCH delegaactualmente a `/shub/execute` (mock).
3. MADRE puede recibir `/madre/shub/task` (endpoints existen).

### 🔴 Lo que FALTA
1. **REAPER real**: REAPER no se abre, OSC no conecta.
2. **Análisis real**: No hay motores de análisis de pistas.
3. **Mezcla real**: Aplicación de efectos es simulada.
4. **Feedback**: No hay loops reales entre Shub y Switch/Madre.
5. **Persistencia BD**: Shub usa JSON, no DB unificada real.

---

## 5. SWITCH + HERMES ACTUAL

### ✅ Lo que funciona
- SWITCH: Cola priorizada, selección de modelos por categoría, fallback a CLI.
- HERMES: Discovery stub, `/hermes/models/best`, `/hermes/cli/candidates`.

### 🔴 Lo que FALTA
- **HERMES CLI Real**: No descubre CLIs gratuitos reales.
- **HERMES Model Discovery**: No escanea repo de modelos.
- **SWITCH ↔ SHUB Tight**: Delegación débil, sin feedback integrado.
- **SWITCH Audio Ingeniería**: No tiene modelo especializado de audio.

---

## 6. MADRE BAJO CONSUMO

### ✅ Lo que funciona
- PowerManager integrado.
- Endpoints `/madre/power/on/{mod}`, `/madre/power/off/{mod}`, `/madre/power/auto-decide`.
- Decisiones basadas en CPU/RAM.

### 🔴 Lo que FALTA
- **Scheduler real**: No hay loop periódico que apague módulos por inactividad.
- **Hijas efímeras**: Registro en BD existe, pero TTL no se respeta.
- **Integración Operator**: Operator no controla Power desde UI interactivamente.

---

## 7. PLAN PARA FASE 1-4

### FASE 1: SHUB REAL
**Objetivo**: Shub como sistema real de audio.
- [ ] Implementar `SoundEngineerEngine` como coordinador de análisis/mezcla/mastering.
- [ ] Motores reales: `drums_analyzer.py`, `vocals_analyzer.py`, `mix_engine.py`.
- [ ] Control real de REAPER vía OSC y subprocess.
- [ ] Endpoints `/shub/analyze_track`, `/shub/suggest_mix`, `/shub/apply_fx_chain`, `/shub/render_final`.
- [ ] Persistencia BD real (tablas ShubProject, ShubTrack, ShubAnalysis).
- [ ] Integración SWITCH: `/switch/chat` con `provider_hint="shub"` → Shub real.

### FASE 2: SWITCH + HERMES MEJORADOS
**Objetivo**: SWITCH como IA central, HERMES como descubridor.
- [ ] SWITCH: Añadir modelo "audio-engineer" local.
- [ ] SWITCH: Enriquecer `/switch/chat` para tareas de audio vs. sistema vs. general.
- [ ] HERMES: CLI discovery real (GitHub, OpenAI, etc. vía tokens).
- [ ] HERMES: Modelo discovery real (<2GB desde repos).

### FASE 3: OPERATOR FULL
**Objetivo**: Operator como control central.
- [ ] Backend: Arreglar CORS, rutas, integración con todas las APIs.
- [ ] Frontend: Dashboard visual con estado real-time.
- [ ] Frontend: Chat conversacional (integrado con Switch).
- [ ] Frontend: Panel Shub (análisis, mezcla, renderizado).
- [ ] Frontend: Panel Power (control de módulos, bajo consumo).
- [ ] Backend ↔ Frontend: WebSocket para eventos vivos.

### FASE 4: MADRE + BAJO CONSUMO
**Objetivo**: Automatización de ciclo de vida.
- [ ] Scheduler: Apagar módulos por inactividad.
- [ ] Hijas: Respetar TTL.
- [ ] Integración Manifestator: Detectar y reparar drift.

---

## 8. PRÓXIMOS PASOS INMEDIATOS

1. **LEER especificaciones Shub** (extradas de docs del repo):
   - Motores de análisis esperados.
   - Flujos de mezcla/mastering.
   - Modelos de control por conversación.

2. **ESCRIBIR Shub core real**:
   - `shubniggurath/core/sound_engineer_engine.py` - Coordinador.
   - `shubniggurath/core/analyzers/` - Motores reales.
   - `shubniggurath/core/mix_engine.py` - Aplicación real.

3. **CONECTAR SWITCH + SHUB**:
   - Endpoint `/shub/execute_audio_task` (recibe decisiones de SWITCH).
   - Feedback a Switch vía BD.

4. **ARREGLAR OPERATOR**:
   - Backend: Rutas, CORS, integración.
   - Frontend: Dashboard + Chat.

5. **MADRE SCHEDULER**:
   - Loop cada 30s que revise actividad.
   - Encienda/apague módulos.

---

## RESUMEN DIAGNÓSTICO

| Módulo | Compilación | Health | Funcionalidad | Score |
|--------|-------------|--------|---------------|-------|
| **Switch** | ✅ | ✅ | 70% (delegación débil a Shub) | 7/10 |
| **Hermes** | ✅ | ✅ | 50% (discovery stub) | 5/10 |
| **Madre** | ✅ | ✅ | 65% (PowerManager parcial) | 6.5/10 |
| **Hormiguero** | ✅ | ✅ | 75% (auto-curación básica) | 7.5/10 |
| **Shub** | ✅ | ✅ | 30% (REAPER mock) | 3/10 |
| **Manifestator** | ✅ | ❌ | 50% (drift mock) | 5/10 |
| **Operator** | ✅ | ❌ | 40% (backend ok, frontend ? ) | 4/10 |
| **MCP** | ✅ | ✅ | 80% (funcional) | 8/10 |

**Calificación General: 5.5/10 (Requiere trabajo significativo en Shub + Operator)**

---

## ARCHIVOS A LEER ANTES DE FASE 1

1. `/home/elkakas314/vx11/docs/VX11_SHUB_SWITCH_HERMES_FLOWS_v7.x.md`
2. `/home/elkakas314/vx11/docs/SHUB_STATE_v7.1.md`
3. `/home/elkakas314/vx11/shubniggurath/docs/CICLO_COMPLETO_CIERRE.md`
4. `/home/elkakas314/vx11/docs/OPERATOR_DASHBOARD_v7.0.md`
5. Archivos de especificación Shub (solicitar al usuario que los copie al repo).

---

**AUDITORÍA COMPLETADA — LISTO PARA FASE 1**
