# FASE 4B: Switch/Hermes Lightweight Runtime Setup

**Date**: 2025-01-05  
**Status**: ✅ COMPLETE (Configuration Documentation)  
**Target**: Define lightweight model strategy for Switch + Hermes  

---

## Executive Summary

VX11 uses a **CLI-first + LLM standby** strategy to minimize resource usage while maintaining inference capability:

1. **Primary Route**: Copilot CLI → DeepSeek R1 or GPT-4 via OpenAI SDK
2. **Fallback Route**: Switch service (local lightweight model) when CLI unavailable
3. **Model Size**: ≤ 3GB (quantized 7B) or ≤ 1GB (quantized 3B)
4. **Framework**: Ollama or llama.cpp for local inference
5. **Storage Location**: `data/models/` (mounted from host, persistent)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────┐
│  Operator Frontend / Copilot CLI            │
│  (Primary route: API call to OpenAI)        │
└────────────────┬────────────────────────────┘
                 │
                 ├─── Switch Fallback (HTTP)
                 │    ↓
                 └──> Hermes Local Model (Ollama/llama.cpp)
                      ↑
                      │
                    data/models/
                    ├── hermes-7b-q4.gguf (2.4GB)
                    └── mistral-3b-q4.gguf (1.2GB)
```

**Traffic Flow**:
- **Normal**: User request → Copilot → DeepSeek R1 (reasoning) or GPT-4 (fast)
- **Degraded** (solo_madre): User request → Switch → Hermes local model
- **Unavailable**: Request fails gracefully with "Service degraded" message

---

## Environment Configuration

### Backend Setup (Docker + Host)

#### 1. Volume Mount Configuration

**File**: `docker-compose.yml` or `docker-compose.full-test.yml`

```yaml
services:
  switch:
    image: vx11-switch:latest
    environment:
      # Hermes local model configuration
      HERMES_ENABLE: "true"
      HERMES_MODEL_DIR: "/app/models"
      HERMES_MODEL_NAME: "hermes-7b-q4"  # or mistral-3b-q4
      HERMES_FRAMEWORK: "ollama"  # or llama-cpp
      HERMES_CONTEXT_LENGTH: 2048
      HERMES_MAX_TOKENS: 512
      HERMES_TEMPERATURE: 0.7
      
      # Fallback to OpenAI API for testing
      OPENAI_API_KEY: "${OPENAI_API_KEY}"
      OPENAI_MODEL: "gpt-4"
      
      # Resource limits
      HERMES_MAX_CONCURRENT: 1
      HERMES_TIMEOUT: 30  # seconds
    volumes:
      - type: bind
        source: ./data/models
        target: /app/models
        read_only: false
      - type: bind
        source: ./data/switch_cache
        target: /app/cache
    ports:
      - "8002:8000"  # Internal; not exposed via tentaculo_link
    networks:
      - vx11-net
```

#### 2. Model Directory Structure

```
data/models/
├── README.md
├── download_models.sh
├── hermes-7b-q4.gguf          (2.4GB) ← Main model for solo_madre
├── mistral-3b-q4.gguf         (1.2GB) ← Ultra-lightweight backup
└── ollama_models/
    ├── hermes7b.gguf          (symlink or copy)
    └── mistral3b.gguf         (symlink or copy)
```

#### 3. Setup Script

**File**: `scripts/setup_switch_models.sh`

```bash
#!/bin/bash
set -e

MODELS_DIR="${1:-./data/models}"
TARGET_SIZE="${2:-7b}"  # 7b or 3b

echo "=== VX11 Switch/Hermes Model Setup ==="
echo "Target: $TARGET_SIZE model"
echo "Location: $MODELS_DIR"
echo ""

# Create directory
mkdir -p "$MODELS_DIR"

# Check existing models
if [ -f "$MODELS_DIR/hermes-7b-q4.gguf" ]; then
  echo "✓ Hermes 7B model already present"
  MODEL_FILE="$MODELS_DIR/hermes-7b-q4.gguf"
  MODEL_SIZE=$(ls -lh "$MODEL_FILE" | awk '{print $5}')
  echo "  Size: $MODEL_SIZE"
elif [ "$TARGET_SIZE" = "7b" ]; then
  echo "ℹ Model not found. To download:"
  echo "  1. Install Ollama: https://ollama.ai"
  echo "  2. Run: ollama pull hermes:7b-q4_0"
  echo "  3. Or download manually from HuggingFace: hermes-7b-q4.gguf"
  echo ""
  echo "For now, using OpenAI fallback..."
else
  echo "ℹ 3B model not configured. Add manually if needed."
fi

# Create config file
cat > "$MODELS_DIR/.config.json" << 'EOF'
{
  "available_models": [
    {
      "name": "hermes-7b-q4",
      "path": "hermes-7b-q4.gguf",
      "size_gb": 2.4,
      "context_length": 2048,
      "quantization": "q4_0",
      "framework": "ollama",
      "recommended": true
    },
    {
      "name": "mistral-3b-q4",
      "path": "mistral-3b-q4.gguf",
      "size_gb": 1.2,
      "context_length": 2048,
      "quantization": "q4_0",
      "framework": "ollama",
      "recommended": false
    }
  ],
  "default_model": "hermes-7b-q4",
  "fallback_model": "mistral-3b-q4",
  "framework": "ollama"
}
EOF

echo ""
echo "✓ Configuration created: $MODELS_DIR/.config.json"
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Download model (Ollama or manual)"
echo "2. Verify model in: $MODELS_DIR/"
echo "3. Start Docker: docker-compose up -d"
echo "4. Test: curl -X POST http://localhost:8000/switch/infer -d '{\"prompt\":\"test\"}'"
```

**Usage**:
```bash
chmod +x scripts/setup_switch_models.sh
./scripts/setup_switch_models.sh data/models 7b
```

---

## Endpoint Specifications

### Switch Inference Endpoint

**Purpose**: Local LLM inference via Hermes  
**Route**: Mounted at tentaculo_link:8000/switch/infer  
**Auth**: X-VX11-Token header (same as all operator endpoints)

#### Request

```bash
curl -X POST http://localhost:8000/switch/infer \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "context_length": 1024,
    "max_tokens": 256,
    "temperature": 0.7,
    "timeout_seconds": 30
  }'
```

#### Response (200 OK)

```json
{
  "inference_id": "inf_1234567890",
  "prompt": "What is the capital of France?",
  "response": "The capital of France is Paris.",
  "model": "hermes-7b-q4",
  "tokens_used": 15,
  "latency_ms": 1250,
  "source": "local_hermes"
}
```

#### Response (503 Service Unavailable)

```json
{
  "error": "Model not loaded or unavailable",
  "model": "hermes-7b-q4",
  "fallback": "Use OpenAI API or CLI",
  "source": "degraded"
}
```

### Switch Health Check

**Purpose**: Check if Hermes model is loaded  
**Route**: `/switch/health`  
**Auth**: None required

#### Request

```bash
curl -s http://localhost:8000/switch/health | jq .
```

#### Response (200 OK)

```json
{
  "status": "ok",
  "model": "hermes-7b-q4",
  "framework": "ollama",
  "memory_usage_mb": 2400,
  "context_ready": true
}
```

#### Response (503 Service Unavailable)

```json
{
  "status": "degraded",
  "reason": "Model not loaded",
  "model": "hermes-7b-q4",
  "fallback_available": true
}
```

---

## Model Selection & Tuning

### Hermes 7B (Recommended for solo_madre)

```json
{
  "model_id": "hermes-7b-q4_0",
  "source": "NousResearch/Hermes-2-Pro-Mistral-7B",
  "quantization": "Q4_0",
  "size_gb": 2.4,
  "context_length": 2048,
  "capabilities": [
    "multi-turn conversation",
    "task decomposition",
    "reasoning",
    "JSON output"
  ],
  "recommended_settings": {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 512,
    "context_window": 2048
  }
}
```

### Mistral 3B (Ultra-lightweight backup)

```json
{
  "model_id": "mistral-7b-instruct-v0.2-q4_0",
  "source": "mistralai/Mistral-7B-Instruct-v0.2",
  "quantization": "Q4_0",
  "size_gb": 2.6,
  "context_length": 8192,
  "capabilities": [
    "instruction following",
    "summarization",
    "basic reasoning"
  ],
  "recommended_settings": {
    "temperature": 0.3,
    "top_p": 0.9,
    "max_tokens": 256,
    "context_window": 4096
  }
}
```

---

## Verification Commands

### Command 1: Check Model Downloaded

```bash
ls -lh data/models/hermes-7b-q4.gguf
# Expected: 2.4G (or size close to it)
```

### Command 2: Verify Switch Service is Running

```bash
curl -s http://localhost:8000/switch/health | jq .
# Expected: {"status":"ok", "model":"hermes-7b-q4", ...}
```

### Command 3: Test Inference (with token)

```bash
TOKEN="vx11-test-token"
curl -s -X POST http://localhost:8000/switch/infer \
  -H "X-VX11-Token: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","max_tokens":50}' | jq .
# Expected: {"inference_id":"...", "response":"...", "model":"hermes-7b-q4"}
```

### Command 4: Monitor Resource Usage

```bash
# In Docker container:
docker exec vx11-switch nvidia-smi  # GPU (if available)
# OR CPU + memory:
docker stats vx11-switch --no-stream
# Expected: ~2.4GB memory for 7B model, ~100-200% CPU during inference
```

---

## Degradation Strategy

### Policy: CLI > Switch > Fail

```
┌─ User Request (frontend/CLI)
│
├─ Try: Copilot CLI → OpenAI API (DeepSeek R1)
│  ├─ Success: Return response
│  └─ Fail: Continue
│
├─ Try: tentaculo_link → Switch service
│  ├─ If Hermes model loaded: Inference
│  │  ├─ Success: Return response (marked "degraded")
│  │  └─ Timeout: Continue (fallback)
│  └─ If model unavailable: Continue
│
└─ Fail: Return "Service unavailable" (503)
   Message: "Chat unavailable. Hermes model not loaded. Use OpenAI API or CLI."
```

### Timeout & Retry Logic

```python
# pseudocode
async def infer_with_fallback(prompt):
    try:
        # Try Switch/Hermes with 30s timeout
        result = await switch.infer(prompt, timeout=30)
        return {
            "response": result.text,
            "source": "local_hermes",
            "degraded": true
        }
    except TimeoutError:
        # Fallback to static message
        return {
            "response": "[Timeout] Model taking too long. Try again or use CLI.",
            "source": "degraded_fallback",
            "degraded": true
        }
    except ServiceUnavailableError:
        # Model not loaded
        raise HTTPException(503, "Hermes model unavailable")
```

---

## Environment Variables (Complete Reference)

### Docker compose

```yaml
environment:
  # Model Configuration
  HERMES_ENABLE: "true"
  HERMES_MODEL_DIR: "/app/models"
  HERMES_MODEL_NAME: "hermes-7b-q4"
  HERMES_FRAMEWORK: "ollama"  # ollama, llama-cpp, etc.
  HERMES_CONTEXT_LENGTH: "2048"
  HERMES_MAX_TOKENS: "512"
  HERMES_TEMPERATURE: "0.7"
  
  # Fallback Configuration
  OPENAI_API_KEY: "${OPENAI_API_KEY}"  # From .env
  OPENAI_MODEL: "gpt-4"
  OPENAI_ORG_ID: "${OPENAI_ORG_ID}"    # Optional
  
  # Resource Limits
  HERMES_MAX_CONCURRENT: "1"
  HERMES_TIMEOUT: "30"
  HERMES_MAX_MEMORY_MB: "4096"
  
  # Logging
  LOG_LEVEL: "INFO"
  LOG_INFERENCE_TIME: "true"
```

---

## Resource Constraints

### Minimum Hardware (solo_madre + Hermes 7B)

```
CPU:     2 cores minimum (4+ recommended for <5s inference)
Memory:  4GB available (2.4GB model + 1.6GB OS/runtime)
Disk:    10GB (model + runtime + cache)
Network: No special requirements
GPU:     Not required (but beneficial for <2s inference)
```

### Recommended Hardware (production)

```
CPU:     8 cores (for concurrent requests if needed)
Memory:  8GB available
Disk:    50GB (with model cache + training data)
GPU:     NVIDIA 6GB+ (for <1s inference time)
Network: 1Gbps (for model updates + distributed setup)
```

---

## Troubleshooting

### Issue 1: "Model not found" Error

```
Error: RuntimeError: Could not find model: hermes-7b-q4.gguf
Fix:
  1. Verify file exists: ls -lh data/models/hermes-7b-q4.gguf
  2. Check HERMES_MODEL_DIR env var: echo $HERMES_MODEL_DIR
  3. Download model: scripts/setup_switch_models.sh
  4. Restart Switch service: docker-compose restart switch
```

### Issue 2: Timeout on Inference

```
Error: {"error": "Model took too long (>30s)"}
Possible causes:
  1. Model loading first time (normal, can take 30-60s)
  2. Underpowered hardware (CPU only inference slow)
  3. High concurrent load (max 1 by default)
Fix:
  1. Increase timeout: HERMES_TIMEOUT=60
  2. Reduce concurrent requests: HERMES_MAX_CONCURRENT=1
  3. Use GPU if available: docker --gpus all
```

### Issue 3: Out of Memory

```
Error: RuntimeError: CUDA out of memory or system OOM
Possible causes:
  1. Model size too large for available VRAM
  2. Memory leak in Switch service
  3. High load causing memory fragmentation
Fix:
  1. Switch to smaller model: mistral-3b-q4
  2. Reduce context: HERMES_CONTEXT_LENGTH=1024
  3. Restart Switch: docker-compose restart switch
  4. Monitor: docker stats vx11-switch
```

---

## Next Steps

1. **Setup Model Directory** (5 min)
   ```bash
   mkdir -p data/models
   chmod 755 data/models
   ```

2. **Download Model** (30-60 min, depending on connection)
   ```bash
   ./scripts/setup_switch_models.sh data/models 7b
   # OR manually via Ollama:
   ollama pull hermes:7b-q4_0
   ```

3. **Verify Docker Volume Mount** (5 min)
   - Check docker-compose.yml has `data/models` mapped
   - Restart: `docker-compose up -d`

4. **Test Endpoints** (5 min)
   - Run verification commands above
   - Check logs: `docker logs vx11-switch | tail -50`

5. **Integrate into Chat** (10 min)
   - Verify `/switch/infer` used by ChatView fallback
   - Test in Operator UI with token

6. **Monitor & Optimize** (ongoing)
   - Log inference times: `HERMES_LOG_INFERENCE_TIME=true`
   - Tune temperature/context based on usage

---

## References

- **Models Source**: HuggingFace (NousResearch Hermes, MistralAI)
- **Framework**: Ollama (local inference server)
- **Docker Setup**: docker-compose.full-test.yml
- **Integration**: operator/frontend/src/views/ChatView.tsx
- **Fallback Logic**: operator/backend/services/chat.py

---

Generated: 2025-01-05T22:25:00Z  
Session: COPILOT/CODEX FASES 1-6
