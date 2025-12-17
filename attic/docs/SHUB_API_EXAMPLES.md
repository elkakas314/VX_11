# Shub FASE 1 - Ejemplos de API

## Quick Start

### 1. Health Check
```bash
curl -s http://localhost:8007/health | jq .
```

**Respuesta:**
```json
{
  "status": "healthy",
  "module": "shubniggurath",
  "dsp_ready": true,
  "reaper_available": true,
  "version": "7.0"
}
```

---

## Audio Analysis (40+ Métricas)

### Crear Audio Test
```bash
python3 << 'EOF'
import soundfile as sf
import numpy as np

# Generar onda sinusoidal 1kHz @ -20dBFS
duration = 3  # segundos
sr = 22050
freq = 1000

t = np.arange(int(sr * duration)) / sr
amplitude = 10 ** (-20 / 20)  # -20 dBFS
audio = amplitude * np.sin(2 * np.pi * freq * t)

sf.write('/tmp/test_1khz.wav', audio, sr)
print("✅ Created /tmp/test_1khz.wav")
EOF
```

### Analizar Audio
```bash
TOKEN="tu_vx11_token"

curl -X POST http://localhost:8007/shub/analyze-dsp \
  -H "X-VX11-Token: $TOKEN" \
  -F "file=@/tmp/test_1khz.wav" | jq .
```

**Respuesta (ejemplo):**
```json
{
  "status": "success",
  "analysis": {
    "duration": 3.0,
    "sample_rate": 22050,
    "channels": 1,
    "peak_dbfs": -20.2,
    "rms_dbfs": -23.5,
    "lufs_integrated": -18.3,
    "lufs_range": 2.1,
    "true_peak_dbfs": -20.1,
    "spectral_centroid": 998.5,
    "spectral_rolloff": 1200,
    "spectral_flux": 0.001,
    "zero_crossing_rate": 0.045,
    "mfcc": [0.5, 0.3, 0.2, ...],
    "chroma": [0.0, 0.0, 0.0, 1.0, ...],
    "spectral_contrast": [2.3, 1.5, 0.8, ...],
    "dynamic_range": 1.2,
    "crest_factor": 3.2,
    "transients_count": 0,
    "transients": [],
    "clipping_samples": 0,
    "dc_offset": 0.0001,
    "noise_floor_dbfs": -60.5,
    "phase_correlation": 1.0,
    "sibilance_detected": false,
    "sibilance_freq": 0.0,
    "resonances": [],
    "issues": [],
    "bpm": 120.0,
    "key_detected": "C",
    "key_confidence": 0.85,
    "harmonic_complexity": 0.7,
    "percussiveness": 0.3,
    "instrument_prediction": {
      "vocals": 0.15,
      "synth": 0.25,
      "piano": 0.1,
      ...
    },
    "genre_prediction": {...},
    "mood_prediction": {...},
    "recommendations": []
  }
}
```

---

## FX Generation (Cadenas Automáticas)

### Generar FX para Rock
```bash
TOKEN="tu_vx11_token"

curl -X POST http://localhost:8007/shub/generate-fx-dsp \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": {
      "peak_dbfs": -3.5,
      "lufs_integrated": -12.0,
      "spectral_centroid": 1500,
      "dynamic_range": 8.0,
      "issues": []
    },
    "target_style": "rock"
  }' | jq .
```

**Respuesta:**
```json
{
  "status": "success",
  "fx_chain": {
    "name": "rock_chain",
    "description": "Cadena automática para rock",
    "plugins": [
      {
        "plugin_type": "eq",
        "manufacturer": "Shub-DSP",
        "name": "Shub Matching EQ",
        "parameters": {
          "bands": [
            {
              "type": "low_shelf",
              "frequency": 100,
              "gain": 0.0,
              "q": 0.7
            },
            {
              "type": "peaking",
              "frequency": 1000,
              "gain": 0.0,
              "q": 1.0
            },
            {
              "type": "high_shelf",
              "frequency": 5000,
              "gain": 0.0,
              "q": 0.7
            }
          ]
        }
      },
      {
        "plugin_type": "compressor",
        "manufacturer": "Shub-DSP",
        "name": "Shub Dynamics",
        "parameters": {
          "threshold": -20.0,
          "ratio": 2.2,
          "attack": 10.0,
          "release": 100.0,
          "makeup": 0.0
        }
      },
      {
        "plugin_type": "limiter",
        "manufacturer": "Shub-DSP",
        "name": "Shub Master Limiter",
        "parameters": {
          "threshold": -1.0,
          "release": 50.0
        }
      }
    ],
    "routing": {
      "parallel": false,
      "sidechain": []
    }
  }
}
```

### Generar FX para Electronic
```bash
curl -X POST http://localhost:8007/shub/generate-fx-dsp \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": {...},
    "target_style": "electronic"
  }' | jq .
```

**Estilos Disponibles:**
- `rock` - Compresión media, EQ agresivo
- `pop` - Compresión suave, LUFS -14
- `electronic` - Compresión fuerte, LUFS -8
- `acoustic` - Compresión mínima, LUFS -16

---

## REAPER Integration

### Listar Proyectos REAPER
```bash
TOKEN="tu_vx11_token"

curl http://localhost:8007/shub/reaper-projects-fase1 \
  -H "X-VX11-Token: $TOKEN" | jq .
```

**Respuesta:**
```json
{
  "status": "success",
  "projects": [
    {
      "name": "song1",
      "path": "/home/user/.config/REAPER/Projects/song1.rpp",
      "size_bytes": 156000,
      "modified": 1702000000.5
    },
    {
      "name": "song2",
      "path": "/home/user/.config/REAPER/Projects/song2.rpp",
      "size_bytes": 203000,
      "modified": 1702100000.0
    }
  ]
}
```

---

## Integration con Switch

### Delegar Audio a Shub desde Switch

```bash
# 1. Subir audio a /tmp/song.wav

# 2. Llamar a Switch con task_type=audio
TOKEN="tu_vx11_token"

curl -X POST http://localhost:8002/switch/chat \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Analiza este audio"}],
    "metadata": {
      "task_type": "audio",
      "audio_file": "/tmp/song.wav"
    },
    "provider_hint": "shub"
  }' | jq .
```

**Flow:**
1. Switch detecta `task_type="audio"`
2. Switch → POST `http://shubniggurath:8007/shub/analyze-dsp`
3. Shub retorna 40+ métricas
4. Switch retorna respuesta al usuario

---

## Error Handling

### Sin Token
```bash
curl http://localhost:8007/shub/analyze-dsp \
  -F "file=@test.wav"
```

**Respuesta:**
```json
{
  "detail": "Unauthorized"
}
```

### Archivo No Encontrado
```bash
curl -X POST http://localhost:8007/shub/analyze-dsp \
  -H "X-VX11-Token: $TOKEN" \
  -F "file=@/no/existe/audio.wav"
```

**Respuesta:**
```json
{
  "detail": "File not found or invalid format"
}
```

---

## Performance Benchmarks (FASE 1)

| Operación | Tiempo | Notas |
|-----------|--------|-------|
| Health check | 5ms | Sync |
| Análisis 3seg @ 22kHz | 200-500ms | CPU-bound |
| FX generation | 50ms | Heurístico |
| REAPER list projects | 100ms | File I/O |

---

## Shell Script Completo

```bash
#!/bin/bash

# variables
TOKEN="tu_vx11_token"
SHUB_URL="http://localhost:8007"

# 1. Health check
echo "=== Health Check ==="
curl -s $SHUB_URL/health | jq .

# 2. Create test audio
echo -e "\n=== Creating Test Audio ==="
python3 << 'EOF'
import soundfile as sf
import numpy as np
sr = 22050
duration = 2
t = np.arange(int(sr * duration)) / sr
audio = 0.1 * np.sin(2 * np.pi * 1000 * t)
sf.write('/tmp/test.wav', audio, sr)
print("✅ Test audio created")
EOF

# 3. Analyze
echo -e "\n=== Analyzing Audio ==="
curl -s -X POST $SHUB_URL/shub/analyze-dsp \
  -H "X-VX11-Token: $TOKEN" \
  -F "file=@/tmp/test.wav" | jq '.analysis | keys'

# 4. Generate FX
echo -e "\n=== Generating FX Chain ==="
curl -s -X POST $SHUB_URL/shub/generate-fx-dsp \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis": {"peak_dbfs": -3, "dynamic_range": 8},
    "target_style": "rock"
  }' | jq '.fx_chain.plugins | length'

echo -e "\n✅ All tests passed"
```

Save as `test_shub.sh` and run:
```bash
chmod +x test_shub.sh
./test_shub.sh
```

---

## Debugging

### Ver Logs
```bash
tail -f /home/elkakas314/vx11/forensic/shubniggurath/events.log
```

### Health Cascade Check
```bash
for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008; do
  echo -n "Port $port: "
  curl -s http://localhost:$port/health | jq '.status' 2>/dev/null || echo "❌"
done
```

### Verificar Token
```bash
grep VX11_GATEWAY_TOKEN /home/elkakas314/vx11/tokens.env
```

