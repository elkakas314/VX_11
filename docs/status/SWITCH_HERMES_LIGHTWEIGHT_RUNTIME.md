# Switch/Hermes — Modelos Ligeros + CLI-First Runtime — 2026-01-03

## Objetivo

Configurar Switch + Hermes para usar:
1. **CLI Copilot** como provider primario (si disponible)
2. **LLM local standby** (modelo ligero) como fallback
3. Modelos almacenados en `data/models/` con versionado

---

## Variables Env. Actuales (Estándar VX11)

Verificadas en `config/settings.py` y `switch/main.py`:

| Var | Default | Uso |
|-----|---------|-----|
| `HERMES_MODEL_DIR` | `data/runtime/models` | Directorio modelos Hermes |
| `SWITCH_MODEL_DIR` | `data/runtime/models` | Directorio modelos Switch |
| `VX11_PROVIDER_HINT` | `cli` | Provider hint (cli / llm / hybrid) |
| `SWITCH_CLI_PROVIDER` | `copilot` | CLI provider (copilot / github-cli) |
| `HERMES_LLM_STANDBY` | `phi2` | Modelo standby ligero |
| `SWITCH_USE_LOCAL_FALLBACK` | `1` | Activar fallback a local si CLI falla |

---

## Estructura de Almacenamiento

```
data/models/
├── phi2/                          # Modelo standby ligero (~3GB)
│   ├── model.gguf
│   ├── tokenizer.json
│   └── metadata.json
├── deepseek-r1-mini/              # Fallback ligero (~2GB)
│   ├── model.gguf
│   └── metadata.json
├── inventory.json                 # Registro de modelos disponibles
└── version.txt                    # Current model version (vX.Y.Z)
```

**Size Policy**: Máx 5GB total (2 modelos ligeros + inventario)

---

## Configuración: Activar CLI-First + Standby

### Paso 1: Crear directorio de modelos

```bash
mkdir -p /home/elkakas314/vx11/data/models
```

### Paso 2: Crear inventario de modelos

```json
{
  "version": "1.0",
  "updated_at": "2026-01-03T09:45:00Z",
  "models": {
    "phi2": {
      "type": "llm_local",
      "size_mb": 3072,
      "capabilities": ["text-generation", "fallback"],
      "status": "available",
      "path": "data/models/phi2"
    },
    "deepseek-r1-mini": {
      "type": "llm_local",
      "size_mb": 2048,
      "capabilities": ["reasoning", "fallback"],
      "status": "optional",
      "path": "data/models/deepseek-r1-mini"
    }
  },
  "providers": {
    "cli": {
      "name": "copilot",
      "status": "primary",
      "command": "copilot"
    },
    "llm_local": {
      "name": "ollama",
      "status": "standby",
      "url": "http://localhost:11434"
    }
  }
}
```

**Guardar en**: `/home/elkakas314/vx11/data/models/inventory.json`

### Paso 3: Variables Env. (docker-compose.yml o .env.test)

```bash
# Primary: CLI Copilot
SWITCH_CLI_PROVIDER=copilot
SWITCH_USE_LOCAL_FALLBACK=1
VX11_PROVIDER_HINT=cli

# Standby LLM
HERMES_LLM_STANDBY=phi2
HERMES_MODEL_DIR=data/models

# Enable debug logging
SWITCH_DEBUG_PROVIDERS=1
```

### Paso 4: Lógica de Selección (Switch/Hermes)

**Pseudocódigo**:
```python
def get_provider():
    # 1. Try CLI (Copilot)
    if env.SWITCH_CLI_PROVIDER == "copilot":
        try:
            return CliProvider("copilot")  # Call external CLI
        except CliNotAvailable:
            log.warning("Copilot CLI not found, falling back to LLM")
    
    # 2. Fallback a LLM local
    if env.SWITCH_USE_LOCAL_FALLBACK:
        model = env.HERMES_LLM_STANDBY  # "phi2"
        try:
            return OllamaProvider(model)
        except OllamaNotAvailable:
            log.error("Ollama not available, degraded mode")
            return DegradedProvider()
    
    # 3. Degraded (no provider)
    return DegradedProvider()
```

---

## 3 Comandos de Verificación

### 1. Verificar Inventario de Modelos

```bash
cd /home/elkakas314/vx11

# Leer inventario
cat data/models/inventory.json | jq .providers

# Expected output:
# {
#   "cli": { "name": "copilot", "status": "primary" },
#   "llm_local": { "name": "ollama", "status": "standby" }
# }
```

### 2. Verificar Disponibilidad de CLI Copilot

```bash
# Check if copilot CLI exists
which copilot

# If not found, install or activate:
# pip install github-copilot-cli
# Or: curl -s https://install.github-cli.com | bash

# Test copilot command
copilot --version
```

**Expected**: Versión >= 1.0 (o "command not found" → fallback a standby OK)

### 3. Verificar Availabilidad de Ollama (LLM Standby)

```bash
# Check if ollama running
curl -s http://localhost:11434/api/tags | jq .models

# If not running:
# Option 1: Start ollama service
# ollama serve

# Option 2: Verify phi2 model is available
# ollama list | grep phi2

# If no models:
# ollama pull phi2  (one-time, ~3GB)
```

**Expected**:
```json
{
  "models": [
    { "name": "phi2:latest", "size": 3072 }
  ]
}
```

---

## Policy: Ejecución

### En `solo_madre`:
- ✅ CLI Copilot OK (read-only queries)
- ⚠️ LLM local OK si Ollama está running
- ❌ NO crear nuevos modelos en runtime

### En ventana temporal (full mode):
- ✅ CLI OK
- ✅ LLM local OK
- ✅ Descargar/actualizar modelos si `auto_update=true`

---

## Troubleshooting

| Issue | Síntoma | Fix |
|-------|---------|-----|
| CLI Copilot no encontrado | /operator/ui chat → degraded | Instalar: `pip install github-copilot-cli` |
| Ollama no responde | LLM fallback falla | `ollama serve` en otra terminal |
| Modelo phi2 no existe | Ollama 404 | `ollama pull phi2` |
| Logs silenciosos | No sé cuál provider se usa | Set `SWITCH_DEBUG_PROVIDERS=1` |

---

## Validación Final

```bash
# 1. Revisar que config está leyendo env vars
grep -r "SWITCH_CLI_PROVIDER\|HERMES_MODEL_DIR" /home/elkakas314/vx11/switch /home/elkakas314/vx11/switch/hermes 2>/dev/null | head -5

# 2. Startup logs (docker compose)
docker compose -f docker-compose.full-test.yml logs vx11-switch-test --tail 20 | grep -i "provider\|cli\|ollama"

# 3. Test manual: Query Switch API
curl -s -H "X-VX11-Token: vx11-test-token" -X POST \
  -H "Content-Type: application/json" \
  http://localhost:8000/operator/api/chat \
  -d '{"message":"test"}' | jq '.provider_used'
  # Expected: "copilot" | "ollama" | "degraded"
```

---

## Resumen Configuración

- **Primary**: CLI Copilot (vía `copilot` command)
- **Standby**: Ollama + phi2 (vía `http://localhost:11434`)
- **Storage**: `/home/elkakas314/vx11/data/models/`
- **Inventory**: `data/models/inventory.json`
- **Policy**: CLI-first, fallback si falla
- **Runtime**: No download automático en `solo_madre`

