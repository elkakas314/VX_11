# FASE 1: SHUB-NIGGURATH REAL - PLAN MAESTRO v7.0

**Objetivo:** Transformar Shub de mock/stub a sistema de audio profesional real, integrado completamente con VX11 v6.7.

**Alcance:** FASE 1 entrega core audio engines funcionales, REAPER bridge, y DSP analysis. No incluye la ultra-compleja BD PostgreSQL de shubnoggurath.txt (FASE 1B).

---

## 📋 ESPECIFICACIÓN ARQUITECTURA SHUB REAL

### **1. Estructura de Carpetas (Nueva)**

```
shubniggurath/
├── Dockerfile                          # Actualizado con reqs
├── main.py                             # Router REAPER+DSP
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── dsp_engine.py                   # DSPEngine: análisis real (librosa, scipy)
│   ├── fx_engine.py                    # FXEngine: generación de cadenas FX
│   ├── reaper_bridge.py                # REAPER RPC: control real via OSC/HTTP
│   ├── audio_analysis.py               # AudioAnalysis dataclass + métricas
│   └── models.py                       # Dataclasses: Analysis, FXChain, REAPERPreset
├── engines/
│   ├── __init__.py
│   ├── analyzer_engine.py              # Análisis: LUFS, espectra, dinámica, issues
│   ├── transient_engine.py             # Transientes: onset detection, crest factor
│   ├── eq_engine.py                    # EQ automático: generación de bands
│   ├── dynamics_engine.py              # Compresor/Expander: rules-based
│   ├── stereo_engine.py                # Balance estéreo, mezcla L/R
│   ├── fx_engine.py                    # Reverb, delay, saturation
│   ├── ai_recommender.py               # IA: recomendaciones de parámetros
│   └── master_engine.py                # Mastering: LUFS target, true peak limiter
├── integrations/
│   ├── __init__.py
│   ├── reaper_rpc.py                   # RPC methods: list_projects, load, render
│   ├── vx11_bridge.py                  # HTTP to Madre, Switch, Hormiguero
│   └── opus_codec.py                   # Opcional: codec para streaming
├── database/
│   ├── __init__.py
│   ├── models_shub.py                  # SQLAlchemy: AnalysisHistory, Presets, etc
│   └── shub.db                         # SQLite local (3 tablas mínimas)
├── presets/
│   ├── eq_presets.json                 # Templates: dark, bright, neutral, vintage
│   ├── compression_presets.json        # Templates: gentle, moderate, aggressive
│   ├── style_templates.json            # rock, pop, electronic, acoustic, etc
│   └── reaper_actions.json             # Custom REAPER actions (LUA stubs)
├── utils/
│   ├── __init__.py
│   ├── audio_utils.py                  # Carga, normalización, formato audio
│   ├── metrics_utils.py                # Cálculos LUFS, RMS, Peak
│   └── logging_utils.py                # Logging a forensic/shub/
└── scripts/
    ├── install_reaper_integration.sh   # Copia Lua scripts a REAPER
    └── validate_shub.py                # Tests: analysis, FX generation, REAPER mock

```

### **2. Dependencias (requirements_shub.txt - Actualizado)**

```
librosa==0.10.0              # Audio analysis: MFCC, spectral features
numpy==1.24.3
scipy==1.11.2                # DSP: signal processing, filters
soundfile==0.12.1            # Read/write WAV, FLAC
python-osc==1.8.3            # OSC protocol for REAPER communication
httpx==0.24.1                # Async HTTP for inter-module comms
fastapi==0.103.1
uvicorn==0.23.2
sqlalchemy==2.0.21           # Database ORM
alembic==1.12.1              # Database migrations
pydantic==2.3.0
python-dotenv==1.0.0
pyloudnorm==0.1.0            # Loudness (LUFS) measurement [OPTIONAL]
```

---

## 🎯 FASE 1 IMPLEMENTACIÓN - HITOS

### **HITO 1: DSP Core (Análisis Real)**

**Archivo: `shubniggurath/core/audio_analysis.py` + `shubniggurath/engines/analyzer_engine.py`**

**Métricas Reales (NO mock):**
1. **Nivel**: LUFS (integrated), RMS, Peak, True Peak
   - Usa librosa.feature + scipy.signal
   - K-weighting simplificado (sin pyloudnorm)
2. **Espectral**: Centroide, Rolloff, Flux, Zero-Crossing, MFCC, Chroma, Contrast, Flatness
   - FFT size: 2048, hop_length: 512
3. **Dinámica**: Dynamic Range, Crest Factor, Transientes (onset detection)
4. **Issues**: Clipping, DC offset, Noise Floor, Phase issues, Sibilance, Resonancias
5. **Musical**: BPM (beat track), Key (chroma CQT), Harmonic/Percussive ratio

**Salida: `AudioAnalysis` dataclass con 40+ atributos**

---

### **HITO 2: FX Engine (Generación de Cadenas)**

**Archivo: `shubniggurath/engines/` (eq, dynamics, fx, master)**

**Generación Automática:**
1. **EQ**: 3-band heurístico basado en espectral_centroid
   - Low shelf (100 Hz), Peaking (1kHz), High shelf (5kHz)
2. **Compresor**: Threshold, ratio, attack, release basados en dynamic_range
3. **Deesser**: Automático si sibilance detectada
4. **Master Limiter**: True Peak -1.0dBFS
5. **Reverb/Delay**: Basado en estilo (reverb en acústico, delay en electronic)

**Salida: `FXChain` con lista de plugins y parámetros**

---

### **HITO 3: REAPER Bridge (Comunicación Real)**

**Archivo: `shubniggurath/integrations/reaper_rpc.py`**

**Métodos HTTP (no OSC en FASE 1, OSC es FASE 1B):**
- `GET /api/reaper/list_projects` → Lee carpeta REAPER projects
- `POST /api/reaper/load_project` → Carga .rpp en REAPER (via daemon)
- `GET /api/reaper/tracks` → Lista pistas del proyecto cargado
- `POST /api/reaper/analyze_project` → Ejecuta análisis Shub en tracks
- `POST /api/reaper/apply_fx_chain` → Genera y aplica FX chain (mock: JSON export)
- `POST /api/reaper/render` → Inicia render (mock: spawn thread)

**Estado**: Daemon HTTP que proxea a REAPER via HTTP API (REAPER con extension HTTP server)

---

### **HITO 4: VX11 Bridge (Integración)**

**Archivo: `shubniggurath/integrations/vx11_bridge.py` + `shubniggurath/main.py`**

**Endpoints Shub (puerto 8007):**

| Endpoint | Método | Propósito |
|----------|--------|----------|
| `/health` | GET | Estado + DSP ready |
| `/shub/analyze` | POST | Analizar archivo audio (JSON file path) |
| `/shub/recommend` | POST | Recomendaciones FX basadas en análisis |
| `/shub/generate-fx` | POST | Generar cadena de efectos (style, target_lufs) |
| `/shub/reaper/projects` | GET | Lista proyectos REAPER |
| `/shub/reaper/load` | POST | Cargar proyecto REAPER |
| `/shub/reaper/render` | POST | Renderizar desde REAPER |
| `/shub/database/save-analysis` | POST | Guardar análisis en DB local |
| `/shub/database/history` | GET | Historial análisis (últimos 100) |

---

### **HITO 5: Integración Switch → Shub**

**Archivo: `shubniggurath/integrations/vx11_bridge.py`**

**Desde Switch (8002):**
```python
# Cuando task_type == "audio" o request.audio_url está presente:
async def delegate_to_shub(audio_url, task_metadata):
    shub_url = settings.shub_url or f"http://shub:{settings.shub_port}"
    resp = await httpx.AsyncClient().post(
        f"{shub_url}/shub/analyze",
        headers={settings.token_header: settings.api_token},
        json={"audio_file": audio_url, "task": task_metadata}
    )
    return resp.json()
```

---

### **HITO 6: Database Local (SQLite)**

**Archivo: `shubniggurath/database/models_shub.py`**

**3 Tablas Mínimas:**

```python
# 1. AnalysisHistory
class AnalysisHistory(Base):
    id: PK
    audio_file: str
    analysis_json: JSON (40+ métricas)
    timestamp: datetime
    style_detected: str
    recommendations: JSON

# 2. PresetLibrary
class PresetLibrary(Base):
    id: PK
    name: str
    category: str (eq, compressor, master, reverb)
    parameters: JSON
    created_at: datetime

# 3. REAPERProjectCache
class REAPERProjectCache(Base):
    id: PK
    project_path: str
    last_analyzed: datetime
    analysis_result: JSON
    status: enum(loaded, rendering, ready)
```

---

## 🚀 PASOS IMPLEMENTACIÓN

### **PASO 1: Crear estructura (15 min)**
- [x] Crear carpetas `core/`, `engines/`, `integrations/`, `database/`, `presets/`, `utils/`, `scripts/`
- [ ] Crear archivos stub: `__init__.py` en cada carpeta

### **PASO 2: DSPEngine (30 min)**
- [ ] Implementar `AudioAnalysis` dataclass
- [ ] Implementar `AnalyzerEngine` con 5 métodos análisis reales
- [ ] Validate con archivo WAV test

### **PASO 3: FXEngine (25 min)**
- [ ] Implementar `FXChain` dataclass
- [ ] Implementar `FXEngine.generate_fx_chain()` heurístico
- [ ] Presets JSON: eq, compression, styles

### **PASO 4: REAPER Bridge (20 min)**
- [ ] Implementar `REAPERController` con 6 métodos
- [ ] HTTP endpoints skeleton (return mock)

### **PASO 5: Main.py + Endpoints (20 min)**
- [ ] Crear FastAPI app con 8 endpoints
- [ ] Integrar DSPEngine, FXEngine, REAPER bridge
- [ ] Agregar X-VX11-Token auth

### **PASO 6: Database (15 min)**
- [ ] Crear modelo SQLAlchemy (3 tablas)
- [ ] Integrar get_session() de config/db_schema.py
- [ ] Endpoints `/save-analysis`, `/history`

### **PASO 7: VX11 Bridge (15 min)**
- [ ] HTTP calls a Madre (`/madre/power/status`)
- [ ] HTTP calls a Hormiguero (`/health`)
- [ ] Health check CASCADE

### **PASO 8: Tests + Validation (20 min)**
- [ ] Compile: `python3 -m py_compile shubniggurath/*`
- [ ] Health: `curl http://localhost:8007/health`
- [ ] Analysis test: Upload WAV, check 40+ metrics

### **PASO 9: Integration (10 min)**
- [ ] Update `switch/main.py` para delegar audio → `/shub/analyze`
- [ ] Update `requirements_shub.txt`
- [ ] Update docker-compose.yml volumes si necesario

### **PASO 10: Documentation (10 min)**
- [ ] Create `shubniggurath/README.md`
- [ ] API examples en `docs/SHUB_API_EXAMPLES.md`

**Total FASE 1: 2-3 horas**

---

## ✅ CRITERIOS ACEPTACIÓN FASE 1

1. ✅ **DSP Real**: 40+ métricas auditadas, output JSON vs librosa.feature
2. ✅ **FX Automation**: Generación FX chain coherente, parámetros realistas
3. ✅ **REAPER Bridge**: HTTP endpoints responden (mock OK)
4. ✅ **VX11 Integration**: Endpoints Shub registrados, Switch delega
5. ✅ **Database**: 3 tablas creadas, análisis persistidos
6. ✅ **Health Cascade**: `curl http://localhost:8007/health` → 200
7. ✅ **No Breaking Changes**: Todos otros módulos aún compilan + responden
8. ✅ **Production-Ready**: Error handling, logging, token auth

---

## 🔗 INTERDEPENDENCIAS

**FASE 1 ← PREREQUISITOS:**
- ✅ VX11 v6.7 core (tentaculo, madre, switch, hormiguero, spawner)
- ✅ config/db_schema.py con get_session()
- ✅ config/settings.py con shub_port, shub_url, api_token

**FASE 2 ← DEPENDE DE FASE 1:**
- Switch+Hermes optimization (necesita Shub real)
- Operator frontend Shub panel

**FASE 3 ← DEPENDE DE FASE 2:**
- Real-time Shub dashboard

---

## 📊 RECURSOS REQUERIDOS

| Recurso | Estimado | Notas |
|---------|----------|-------|
| CPU | 2+ cores | Librosa CPU-intensive |
| RAM | 1GB | Por instancia |
| Disk | 500MB | Presets + DB |
| Tiempo | 2-3h | Implementación completa |
| Testing | 30min | Health cascade + sample audio |

---

## 🎁 BONUS - FASE 1B (NO incluido, post-FASE1)

- **PostgreSQL Shubnoggurath**: Multi-tenant, versioning, studio profiles
- **OSC Protocol**: REAPER real-time via OSC (vs HTTP mock)
- **GPU Support**: CUDA for analysis (librosa GPUified)
- **Advanced Engines**: Drum, Guitar, Vocal engines (from shubnoggurath.txt)
- **Streaming**: Opus codec, real-time processing

---

## 📝 NOTAS IMPLEMENTADOR

1. **No copy-paste shub.txt/shub2.txt**: Sintetizar solo lo esencial (DSPEngine class pattern + FXEngine + REAPER RPC)
2. **Manténer VX11 Rules**: No localhost, siempre settings, replace_string_in_file no create_file
3. **Mock es OK**: REAPER bridge HTTP/OSC puede ser mock (spy=True en tests)
4. **Error Handling**: `try/except` + logging a `forensic/shub/`
5. **Git**: Commitear tras cada hito

---

## 🎯 PRÓXIMA ACCIÓN (Usuario)

Confirma que ejecutemos FASE 1 paso a paso, o si hay cambios/prioridades en este plan.

