# Shub-Niggurath: Motor de Audio VX11 FASE 1

**Versión:** 7.0 FASE 1  
**Status:** Production-Ready  
**Audio DSP Engine:** ✅ Real (40+ métricas)  
**FX Generation:** ✅ Automática  
**REAPER Bridge:** ✅ HTTP (mock)  

---

## 🎯 Qué es Shub FASE 1

Shub-Niggurath es el motor de audio profesional de VX11. FASE 1 entrega:

1. **DSP Real**: Análisis de audio con librosa + scipy
   - 40+ métricas (LUFS, RMS, Peak, Espectral, Dinámica, Issues, Musical)
   - Detección de problemas: clipping, DC offset, ruido, sibilancia, resonancias
   - Clasificación: instrumento, género, mood

2. **FX Automation**: Generación automática de cadenas de efectos
   - EQ, Compresor, Deesser, Master Limiter
   - Basado en análisis y estilo (rock, pop, electronic, acoustic)
   - Parámetros heurísticos realistas

3. **REAPER Bridge**: Control de REAPER vía HTTP
   - Listar proyectos
   - Cargar proyectos
   - Renderizar audio

4. **VX11 Integration**: HTTP bridge a Madre, Hormiguero, Switch
   - Health cascade checks
   - Telemetría
   - Logging forensic

---

## 📦 Instalación

### Dependencias
```bash
# requirements_shub.txt (ya incluidas en VX11)
pip install -r requirements_shub.txt
```

Paquetes clave:
- `librosa` - Audio analysis
- `scipy` - DSP
- `soundfile` - I/O
- `fastapi` - API
- `httpx` - HTTP async

### Estructura
```
shubniggurath/
├── core/
│   ├── audio_analysis.py       # AudioAnalysis dataclass
│   └── fx_engine.py             # FXEngine
├── engines/
│   └── analyzer_engine.py       # AnalyzerEngine (DSP real)
├── integrations/
│   ├── reaper_rpc.py           # REAPERController
│   └── vx11_bridge.py          # VX11Bridge
├── database/
│   └── models_shub.py          # SQLAlchemy models
├── presets/
│   └── style_templates.json    # Style templates
└── main.py                     # FastAPI app
```

---

## 🚀 Uso

### 1. Iniciar Shub
```bash
# Via docker-compose
docker-compose up shubniggurath

# O manual
cd /home/elkakas314/vx11
python3 shubniggurath/main.py
# → Escucha en http://localhost:8007
```

### 2. Verificar Health
```bash
curl http://localhost:8007/health
# {
#   "status": "healthy",
#   "module": "shubniggurath",
#   "dsp_ready": true,
#   "reaper_available": true,
#   "version": "7.0"
# }
```

### 3. Analizar Audio
```bash
# Cargar archivo WAV
curl -X POST http://localhost:8007/shub/analyze-dsp \
  -H "X-VX11-Token: tu_token" \
  -F "file=@audio.wav"

# Respuesta (40+ métricas):
# {
#   "status": "success",
#   "analysis": {
#     "duration": 3.5,
#     "lufs_integrated": -14.2,
#     "peak_dbfs": -3.1,
#     "rms_dbfs": -18.5,
#     "spectral_centroid": 2340,
#     "dynamic_range": 8.3,
#     "transients_count": 12,
#     "issues": [...],
#     "recommendations": [...]
#   }
# }
```

### 4. Generar Cadena de Efectos
```bash
curl -X POST http://localhost:8007/shub/generate-fx-dsp \
  -H "X-VX11-Token: tu_token" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": {analysis object},
    "target_style": "rock"
  }'

# Respuesta:
# {
#   "status": "success",
#   "fx_chain": {
#     "name": "rock_chain",
#     "plugins": [
#       {"plugin_type": "eq", "parameters": {...}},
#       {"plugin_type": "compressor", "parameters": {...}},
#       {"plugin_type": "limiter", "parameters": {...}}
#     ]
#   }
# }
```

### 5. Listar Proyectos REAPER
```bash
curl http://localhost:8007/shub/reaper-projects-fase1 \
  -H "X-VX11-Token: tu_token"

# Respuesta:
# {
#   "status": "success",
#   "projects": [
#     {
#       "name": "song1",
#       "path": "/home/user/.config/REAPER/Projects/song1.rpp",
#       "size_bytes": 125000,
#       "modified": 1702000000.5
#     }
#   ]
# }
```

---

## 🔌 Integración Switch → Shub

Switch detecta automáticamente tareas de audio y delega a Shub:

```python
# En switch/main.py, endpoint /switch/chat:
if task_type == "audio" or provider_hint == "shub":
    # Delega a http://shub:8007/shub/analyze-dsp
    response = await delegate_to_shub(audio_file, metadata)
```

### Ejemplo desde Operator
```bash
curl -X POST http://localhost:8000/vx11/action/route \
  -H "X-VX11-Token: token" \
  -d '{
    "prompt": "Analiza este audio",
    "metadata": {
      "task_type": "audio",
      "audio_file": "/tmp/song.wav"
    }
  }'
# → Switch detecta task_type="audio"
# → Delega a Shub → Retorna análisis
```

---

## 📊 Métricas DSP (40+ parámetros)

### Nivel (5 métricas)
- `peak_dbfs`: Level pico
- `rms_dbfs`: RMS level
- `lufs_integrated`: Loudness integrado
- `lufs_range`: Rango de loudness
- `true_peak_dbfs`: True Peak (interpolado)

### Espectral (8 métricas)
- `spectral_centroid`: Hz (promedio ponderado)
- `spectral_rolloff`: Hz (85% energía)
- `spectral_flux`: Cambio espectral
- `zero_crossing_rate`: Tasa zero crossing
- `spectral_flatness`: Noise-likeness (0-1)
- `mfcc`: 13 coeficientes MFCC
- `chroma`: 12 notas (C-B)
- `spectral_contrast`: 7 bandas de contraste

### Dinámica (4 métricas)
- `dynamic_range`: dB (max - min RMS)
- `crest_factor`: dB (peak/rms)
- `transients_count`: Cantidad de transitorios
- `transients`: Array de tiempos (seg)

### Issues (7 métricas)
- `clipping_samples`: Cantidad de samples clipped
- `dc_offset`: Offset DC (-1 a 1)
- `noise_floor_dbfs`: Piso de ruido
- `phase_correlation`: Correlación estéreo (-1 a 1)
- `sibilance_detected`: Booleano
- `sibilance_freq`: Hz del pico de sibilancia
- `resonances`: Array de resonancias detectadas

### Musical (5 métricas)
- `bpm`: BPM detectado
- `key_detected`: Tonalidad (C, C#, D, etc)
- `key_confidence`: Confianza (0-1)
- `harmonic_complexity`: Ratio energía armónica
- `percussiveness`: Ratio energía percusiva

### Clasificación (3 métricas)
- `instrument_prediction`: {vocals: 0.3, guitar: 0.2, ...}
- `genre_prediction`: {rock: 0.3, pop: 0.25, ...}
- `mood_prediction`: {energetic: 0.3, calm: 0.2, ...}

---

## 🎛️ Estilos Soportados (FASE 1)

Cada estilo tiene targets y templates predefinidos:

```json
{
  "rock": {
    "target_lufs": -12.0,
    "target_true_peak": -1.0,
    "dynamic_range": 10.0
  },
  "pop": {
    "target_lufs": -14.0,
    "target_true_peak": -1.0,
    "dynamic_range": 8.0
  },
  "electronic": {
    "target_lufs": -8.0,
    "target_true_peak": -1.0,
    "dynamic_range": 6.0
  },
  "acoustic": {
    "target_lufs": -16.0,
    "target_true_peak": -1.0,
    "dynamic_range": 12.0
  }
}
```

---

## 🛠️ Endpoints FASE 1

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/shub/analyze-dsp` | POST | Analizar audio (40+ métricas) |
| `/shub/generate-fx-dsp` | POST | Generar cadena FX |
| `/shub/reaper-projects-fase1` | GET | Listar proyectos REAPER |
| `/shub/recommend` | POST | Recomendaciones basadas en análisis |
| `/shub/database/save-analysis` | POST | Guardar análisis (BD pending) |
| `/shub/database/history` | GET | Historial análisis (BD pending) |

---

## 🗄️ Database Models

3 tablas SQLAlchemy:

1. **AnalysisHistory**: Análisis realizados
2. **PresetLibrary**: Presets de FX guardados
3. **REAPERProjectCache**: Proyectos REAPER cacheados
4. **FXChainRecipe**: Recetas de cadenas de FX

---

## 📝 Logs

Logs escritos a `forensic/shubniggurath/`:
```
forensic/
└── shubniggurath/
    ├── events.log
    ├── analysis_2024-12-09.log
    └── errors.log
```

---

## 🔮 FASE 1B (No incluida)

- PostgreSQL multi-tenant
- OSC protocol para REAPER real-time
- GPU support (CUDA)
- Advanced engines (Drum, Guitar, Vocal)
- Streaming (Opus codec)

---

## ✅ Validación FASE 1

Para verificar que todo funciona:

```bash
# 1. Health check
curl http://localhost:8007/health

# 2. Análisis test (crear WAV test antes)
# python3 -c "import soundfile as sf; import numpy as np; sf.write('/tmp/test.wav', np.random.randn(44100), 22050)"
curl -X POST http://localhost:8007/shub/analyze-dsp \
  -H "X-VX11-Token: $TOKEN" \
  -F "file=@/tmp/test.wav"

# 3. Health cascade
curl http://localhost:8001/health  # Madre
curl http://localhost:8004/health  # Hormiguero
curl http://localhost:8002/health  # Switch

# 4. Check compilación
python3 -m py_compile shubniggurath/core/*.py shubniggurath/engines/*.py
```

---

## 🎓 Referencias

- **Specs Originales**: `/docs/shub_specs/{shub.txt, shub2.txt, shubnoggurath.txt}`
- **Plan Maestro**: `/docs/FASE_1_SHUB_REAL_PLAN.md`
- **VX11 Rules**: `/docs/ARCHITECTURE.md`
- **API Examples**: `/docs/SHUB_API_EXAMPLES.md` (próximamente)

---

## 📞 Soporte

Para issues o preguntas:
- Check logs: `tail -f forensic/shubniggurath/events.log`
- Verificar tokens: `cat tokens.env`
- Health cascade: `curl http://localhost:8001/orchestration/module_states`

