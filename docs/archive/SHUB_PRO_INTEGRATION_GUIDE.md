# Shub Pro: Guía de Integración y Uso

**Versión:** 1.0  
**Estado:** ✓ Completado y validado  
**Tests:** 29/29 pasando  

---

## 📋 Resumen Ejecutivo

**Shub Pro** es el módulo de procesamiento de audio profesional de VX11 v6.3. Proporciona:

- **DSP Engine**: Análisis de audio completo (LUFS, dinámico, espectral, musical)
- **FX Chain**: Cadena de efectos parametrizable (EQ, compresión, limitación, distorsión)
- **Pipelines**: Orquestación de análisis → procesamiento → export
- **Mode C**: Variantes optimizadas para streaming, batch y realtime
- **Virtual Engineer**: Agente IA que recomienda procesamiento basado en análisis
- **Core Init**: Inicialización secuencial con verificación de salud

---

## 🚀 Inicio Rápido

### 1. Instalación

```bash
# Requisitos: Python 3.10+, numpy, FastAPI, SQLAlchemy
pip install -r requirements.txt

# Opcional (para análisis avanzado):
pip install librosa scipy
```

### 2. Setup BD

```python
from shubniggurath.pro.shub_db import init_shub_db

# Crear tablas
init_shub_db()
```

### 3. Inicialización Completa

```python
from shubniggurath.pro.shub_core_init import initialize_shub_pro
import asyncio

result = await initialize_shub_pro()
print(f"Status: {result['success']}")
print(f"Tiempo total: {result['total_time_s']:.2f}s")
```

---

## 📦 Módulos Principales

### `shub_pro/dsp_engine.py`

Motor de análisis DSP. Proporciona:

- **Análisis de niveles**: Peak, RMS, LUFS, True Peak
- **Análisis dinámico**: Rango dinámico, factor cresta, transitorios
- **Análisis espectral**: Centroide, rolloff, MFCC, chroma, contraste
- **Análisis musical**: BPM, clave estimada, complejidad armónica
- **Detección de problemas**: Clipping, DC offset, ruido

**Uso:**

```python
from shubniggurath.pro.dsp_engine import DSPEngine
import numpy as np

engine = DSPEngine()

# Cargar audio
audio, sr = np.zeros(48000), 48000

# Analizar
result = await engine.analyze_audio(audio, sr)

print(f"LUFS: {result.lufs_integrated}")
print(f"Pico: {result.peak_dbfs} dB")
print(f"Issues: {result.issues}")
print(f"Recomendaciones: {result.recommendations}")
```

### `shub_pro/dsp_fx.py`

Cadena de efectos parametrizable. Soporta:

- **Ganancia** (Gain)
- **Compresor** (Compressor)
- **Limitador** (Limiter)
- **Ecualizador** (3 bandas)
- **Filtros** (High-pass, Low-pass)
- **Distorsión** (Distortion)

**Uso:**

```python
from shubniggurath.pro.dsp_fx import FXChain, EffectConfig, EffectType

chain = FXChain(sample_rate=48000)

# Agregar efectos
chain.add_effect_config(EffectConfig(
    type=EffectType.EQ,
    params={"low_gain_db": 2, "high_gain_db": 1}
))

chain.add_effect_config(EffectConfig(
    type=EffectType.COMPRESSOR,
    params={"threshold_db": -20, "ratio": 3.0}
))

# Procesar
output = chain.process(audio)

# Guardar preset
preset = chain.save_preset()
```

**Presets predefinidos:**

- `PRESET_MASTERING`: Para masterización
- `PRESET_CLEAN_VOICE`: Para voz limpia
- `PRESET_BRIGHT`: Para brillo adicional

### `shub_pro/dsp_pipeline_full.py`

Orquestador completo del pipeline. Flujo:

1. Cargar audio
2. Análisis DSP
3. Procesamiento (FX)
4. Export
5. Persistencia en BD

**Uso:**

```python
from shubniggurath.pro.dsp_pipeline_full import get_pipeline, PipelineConfig

pipeline = get_pipeline()

config = PipelineConfig(
    job_id="job_001",
    session_id="sess_001",
    input_path="input.wav",
    output_path="output.wav",
    enable_analysis=True,
    fx_chain_config=[
        {"type": "limiter", "enabled": True, "params": {"threshold_db": -3}},
    ]
)

result = await pipeline.run_pipeline(config)
print(f"Éxito: {result['success']}")
print(f"Output: {result['output_path']}")
```

### `shub_pro/mode_c_pipeline.py`

Pipelines optimizados para casos específicos:

- **BATCH**: Máxima calidad, buffer grande (4096 muestras)
- **STREAMING**: Balance (2048 muestras), latencia ~50ms
- **REALTIME**: Ultra-baja latencia (512 muestras), sin análisis

**Uso:**

```python
from shubniggurath.pro.mode_c_pipeline import create_mode_c_pipeline, ProcessingMode

# Crear para caso específico
pipeline = create_mode_c_pipeline(ProcessingMode.STREAMING)

# Configurar FX
pipeline.configure_fx_chain([
    {"type": "highpass", "params": {"cutoff_hz": 20}},
])

# Procesar en batch
result = await pipeline.process_batch(audio, sample_rate=48000)
```

### `shub_pro/virtual_engineer.py`

Agente IA que recomienda procesamiento:

- Análisis automático del audio
- Consulta al router IA (Switch)
- Generación de cadena FX basada en análisis
- Fallback a recomendaciones por reglas

**Uso:**

```python
from shubniggurath.pro.virtual_engineer import get_virtual_engineer

engineer = get_virtual_engineer()

# Recomendaciones automáticas
result = await engineer.analyze_and_recommend(
    analysis=analysis_result,
    user_intent="Masterización",
    target_lufs=-14,
)

fx_chain = result["fx_chain"]
reasoning = result["reasoning"]
```

### `shub_pro/shub_db.py`

Esquema de BD extendido. Tablas:

- **ShubSession**: Sesiones de trabajo
- **AdvancedAnalysis**: Análisis DSP completo
- **ShubJob**: Tracking de jobs (análisis, procesamiento)
- **ShubSandbox**: Entornos aislados

**Uso:**

```python
from shubniggurath.pro.shub_db import get_shub_session, ShubJob

session = get_shub_session()

# Crear job
job = ShubJob(
    uuid="job_001",
    name="Análisis Track 1",
    status="running",
    input_path="track.wav",
    session_id="sess_001"
)

session.add(job)
session.commit()
```

### `shub_pro/shub_core_init.py`

Inicializador de Shub Pro. Secuencia:

1. Base de datos
2. DSP Engine
3. FX Chains
4. Pipelines (full + Mode C)
5. Ingeniero Virtual
6. Caché y warmup

**Uso:**

```python
from shubniggurath.pro.shub_core_init import initialize_shub_pro

result = await initialize_shub_pro()

# Verificar
for step, details in result["steps"].items():
    print(f"{step}: {details['success']} ({details['time_ms']:.1f}ms)")
```

---

## 🧪 Testing

### Ejecutar tests

```bash
# Tests simples (29 tests, ~1s)
pytest tests/test_shub_pro_simple.py -v

# Tests específicos
pytest tests/test_shub_pro_simple.py::TestEffectsSimple -v
pytest tests/test_shub_pro_simple.py::TestModeCSimple -v
pytest tests/test_shub_pro_simple.py::TestImports -v
```

### Cobertura

- ✓ **Effects**: Gain, Limiter, Distortion, Chain, Presets
- ✓ **Mode C**: Batch, Streaming, Realtime, StreamBuffer
- ✓ **Virtual Engineer**: Presets, Recomendaciones
- ✓ **Core Init**: DSP, FX, Pipelines
- ✓ **Imports**: Todos los módulos importan correctamente

---

## 🔌 Integración VX11

### 1. Gateway (API HTTP)

```bash
# Health
curl http://localhost:8000/vx11/health

# Status
curl http://localhost:8000/vx11/status
```

### 2. Madre (Orquestador)

Las sesiones de Shub Pro pueden ser coordinadas por Madre:

```python
# En madre/main.py o módulos
from shubniggurath.pro.dsp_pipeline_full import get_pipeline

pipeline = get_pipeline()
result = await pipeline.run_pipeline(config)
```

### 3. Switch (IA)

Virtual Engineer usa Switch para recomendaciones IA:

```python
# En virtual_engineer.py
async with httpx.AsyncClient() as client:
    resp = await client.post(
        f"http://127.0.0.1:{settings.switch_port}/route",
        json={"prompt": analysis_summary},
    )
```

### 4. Storage Unified

BD compartida: `data/vx11.db`

```python
from shubniggurath.pro.shub_db import get_shub_session
from config.db_schema import Task, Context

# Acceso a tablas VX11 y Shub Pro desde sesión unificada
session = get_shub_session()
```

---

## 📊 Ejemplos Prácticos

### Ejemplo 1: Análisis + Recomendación + Procesamiento

```python
from shubniggurath.pro.dsp_engine import DSPEngine
from shubniggurath.pro.virtual_engineer import get_virtual_engineer
from shubniggurath.pro.dsp_fx import FXChain
from shubniggurath.pro.audio_io import load_audio, save_wav

# 1. Cargar audio
audio, sr = load_audio("input.wav")

# 2. Analizar
engine = DSPEngine()
analysis = await engine.analyze_audio(audio, sr)

# 3. Pedir recomendaciones
engineer = get_virtual_engineer()
reco = await engineer.analyze_and_recommend(analysis, target_lufs=-14)

# 4. Construir cadena
chain = FXChain(sample_rate=sr)
for fx_config in reco["fx_chain"]:
    from shubniggurath.pro.dsp_fx import EffectConfig, EffectType
    config = EffectConfig(
        type=EffectType(fx_config["type"]),
        params=fx_config.get("params", {})
    )
    chain.add_effect_config(config)

# 5. Procesar
output = chain.process(audio)

# 6. Exportar
save_wav(output, "output.wav", sample_rate=sr)
```

### Ejemplo 2: Streaming Realtime

```python
from shubniggurath.pro.mode_c_pipeline import create_mode_c_pipeline, ProcessingMode

pipeline = create_mode_c_pipeline(ProcessingMode.REALTIME)

async def get_chunk():
    # Obtener chunk de entrada
    return audio_chunk

async def put_chunk(chunk):
    # Enviar chunk de salida
    pass

result = await pipeline.process_realtime(
    get_input_chunk=get_chunk,
    put_output_chunk=put_chunk,
    duration_ms=5000,
    target_latency_ms=20,
)

print(f"Chunks: {result['chunks_processed']}")
print(f"Latencia promedio: {result['avg_latency_ms']:.1f}ms")
```

### Ejemplo 3: Batch Processing

```python
from shubniggurath.pro.dsp_pipeline_full import get_pipeline, PipelineConfig
import uuid

pipeline = get_pipeline()

configs = [
    PipelineConfig(
        job_id=str(uuid.uuid4()),
        session_id="batch_001",
        input_path=f"track_{i}.wav",
        output_path=f"output_{i}.wav",
    )
    for i in range(10)
]

# Procesar en paralelo (máx 2 jobs simultáneos)
results = await pipeline.batch_process(configs, parallel_jobs=2)

for result in results:
    print(f"Job {result['job_id']}: {result['success']}")
```

---

## ⚙️ Configuración Avanzada

### Variables de Entorno

```bash
# BD
SHUB_PRO_DB_URL=sqlite:///./data/vx11.db

# IA (para Virtual Engineer)
DEEPSEEK_API_KEY=sk-...
SWITCH_PORT=8002
```

### Configuración Mode C Personalizada

```python
from shubniggurath.pro.mode_c_pipeline import ModeCPipeline, ModeCConfig, ProcessingMode

config = ModeCConfig(
    mode=ProcessingMode.STREAMING,
    chunk_size=1024,
    buffer_size=16384,
    target_latency_ms=30,
    analysis_skip_percent=50,  # Skip 50% de análisis
    max_workers=2,
)

pipeline = ModeCPipeline(config)
```

---

## 🐛 Troubleshooting

### Error: "librosa no disponible"

**Solución:** Instala librosa para análisis espectral completo

```bash
pip install librosa
```

Sin librosa, análisis básico (niveles, dinámico) sigue disponible.

### Error: "scipy no disponible"

**Solución:** Instala scipy para análisis de picos precisos

```bash
pip install scipy
```

### Error: "ShubSession: Attribute name 'metadata' is reserved"

**Causa:** Campo 'metadata' conflictúa con SQLAlchemy API

**Solución:** Renombrado a 'session_metadata' en shub_db.py (ya corregido)

### Error: BD locks

**Solución:** SQLite es single-writer. Para contención alta:

```python
from sqlalchemy import create_engine
engine = create_engine(
    "sqlite:///./data/vx11.db",
    connect_args={"timeout": 30}
)
```

---

## 📈 Mapa de Arquitectura

```
┌─────────────────────────────────────────────┐
│              Gateway (8000)                 │
│         HTTP → /shub/pipeline, etc.         │
└────────────────────┬────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │    Madre Orquestador  │
         │     (8001)            │
         └───────────┬───────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌─────┐    ┌─────────┐   ┌──────────┐
    │ DSP │    │   FX    │   │ Pipeline │
    │Engine   │ Chain   │   │Full      │
    └─────┘    └─────────┘   └──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
            ┌────────▼────────┐
            │   Mode C        │
            │   (Batch/       │
            │    Streaming/   │
            │    Realtime)    │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌──────────┐ ┌──────┐  ┌──────────┐
    │ Virtual  │ │ Core │  │   DB     │
    │ Engineer │ │ Init │  │ Unified  │
    └──────────┘ └──────┘  └──────────┘
```

---

## 🎯 Checklist de Integración

- [ ] Instalación: `pip install -r requirements.txt`
- [ ] Setup BD: `init_shub_db()`
- [ ] Inicialización: `await initialize_shub_pro()`
- [ ] Tests: `pytest tests/test_shub_pro_simple.py -v`
- [ ] Verificar servicios: `curl http://localhost:8000/vx11/status`
- [ ] Documentación leída: ✓
- [ ] Ejemplos probados: ✓
- [ ] Integración en producción: Pendiente

---

## 📞 Soporte

**Módulos:** 7 módulos nuevos (~1700 líneas)
- dsp_engine.py (370 líneas)
- dsp_fx.py (220 líneas)
- dsp_pipeline_full.py (280 líneas)
- mode_c_pipeline.py (250 líneas)
- virtual_engineer.py (180 líneas)
- shub_core_init.py (180 líneas)
- shub_db.py (150 líneas, extendido)

**Tests:** 29 tests pasando
**Status:** ✓ Completado y validado

---

**Última actualización:** 2024  
**Compatible con:** VX11 v6.3+  
**Licencia:** Privada (VX11)
