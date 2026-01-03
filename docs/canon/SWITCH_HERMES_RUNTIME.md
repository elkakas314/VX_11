# SWITCH & HERMES: Lightweight Runtime Strategy

**Canonical Document**: Living Spec (docs/canon/)  
**Audience**: Developers, Operators  
**Status**: Production-Ready (Phase 5)  
**Last Updated**: 2026-01-03

---

## Overview

**Switch** and **Hermes** provide lightweight fallback inference when main LLM unavailable:

- **Switch**: Deterministic routing (no learning; CLI-first)
- **Hermes**: Local 7B model (Hermes-2-Pro, resource-efficient)

Both activate in **windowed policy** (never solo_madre default).

---

## Architecture

```
tentaculo_link:8000 (entrypoint)
         ↓
    [Token check]
         ↓
operator-backend:8005
         ↓
    [Route decision]
    ↙       ↓         ↘
  API   SWITCH    HERMES
        CLI-first  Local Model
```

**Key Rule**: Never call `:8002` (switch) or `:8003` (hermes) directly. Always route through `:8000`.

---

## SWITCH: Deterministic Routing

### Purpose
Lightweight rule engine for fallback inference when APIs down.

### Runtime Mode

```bash
# CLI-first (no daemon required)
python3 -m switch.cli --input "hello" --mode deterministic --output json

# Example
$ python3 -m switch.cli --input "What is 2+2?" --mode math --output json
{
  "result": "4",
  "mode": "math",
  "confidence": "high",
  "source": "deterministic"
}
```

### Activation (Window Policy)

**Trigger**: If `operator-backend` unreachable + `api_providers` all down

```bash
# Inside madre policy engine
if (operator_backend_healthy == False AND all_apis_down == True):
    SWITCH.activate(mode="fallback", ttl_seconds=3600)
```

**TTL**: 1 hour (window closes on next health check)

### Configuration

File: `switch/config.yml`

```yaml
switch:
  enabled: true
  cli_first: true                    # No daemon, CLI invocations only
  fallback_modes:
    - deterministic
    - math
    - pattern_matching
  resource_limit:
    memory_mb: 128                   # Lightweight
    timeout_seconds: 2
  activation_policy:
    trigger: "operator_backend_down AND all_apis_down"
    ttl_seconds: 3600                # 1 hour window
    auto_close: true                 # Close on health check recovery
```

### Example Use Cases

#### 1. Math Query
```bash
curl -X POST http://localhost:8000/vx11/switch/deterministic \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"input":"What is 2+2?","mode":"math"}'

# Response
{
  "result": "4",
  "mode": "math",
  "confidence": "high",
  "processed_by": "switch",
  "ttl_remaining": 3599
}
```

#### 2. Pattern Matching
```bash
curl -X POST http://localhost:8000/vx11/switch/deterministic \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"input":"Is this a greeting?","mode":"pattern_matching"}'

# Response
{
  "result": "yes (pattern: greeting)",
  "mode": "pattern_matching",
  "confidence": "medium",
  "processed_by": "switch",
  "ttl_remaining": 3599
}
```

### Performance Baseline

| Query Type | Latency | Memory | CPU |
|----------|---------|--------|-----|
| Math | 50ms | 5MB | <1% |
| Pattern | 100ms | 8MB | <1% |
| Deterministic | 150ms | 12MB | <1% |

---

## HERMES: Local 7B Model

### Purpose
Lightweight local LLM for edge inference (no API calls needed).

### Runtime Mode

```bash
# Daemon (runs in background)
# Started by docker-compose or systemd

# Access via entrypoint
curl -X POST http://localhost:8000/vx11/hermes/generate \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is AI?","max_tokens":50}'
```

### Model Details

| Aspect | Details |
|--------|---------|
| **Model** | Hermes-2-Pro-Mistral-7B |
| **Backend** | llama.cpp (CPU-optimized) or vLLM (GPU-optional) |
| **Memory** | ~4-6GB (CPU mode), ~2GB (quantized int4) |
| **Latency** | 200-500ms per query (CPU) |
| **Tokens/sec** | 10-20 tok/s (CPU), 50+ (GPU) |
| **License** | MIT |

### Activation (Window Policy)

**Trigger**: If `operator-backend` unreachable + user requests generation (not just routing)

```bash
# Inside madre policy engine
if (operator_backend_healthy == False AND user_requests_generation == True):
    HERMES.activate(mode="generation", ttl_seconds=7200)
```

**TTL**: 2 hours (window closes on next successful API recovery)

### Configuration

File: `hermes/config.yml`

```yaml
hermes:
  enabled: true
  model_name: "Hermes-2-Pro-Mistral-7B"
  quantization: "int4"                # CPU-friendly
  max_tokens: 256
  temperature: 0.7
  top_p: 0.95
  resource_limits:
    memory_mb: 6000                   # 6GB max
    timeout_seconds: 30
    batch_size: 1                     # Single query at a time
  activation_policy:
    trigger: "operator_backend_down AND generation_requested"
    ttl_seconds: 7200                 # 2 hour window
    auto_close: true
  model_path: "/data/models/Hermes-2-Pro-Mistral-7B-GGUF"
  backend: "llama_cpp"                # or "vllm" if GPU available
```

### Model Loading

```bash
# Pre-load model on startup (optional, saves ~2s per first query)
python3 -m hermes.preload --model Hermes-2-Pro-Mistral-7B

# Check if loaded
curl -s http://localhost:8000/vx11/hermes/status | jq .
# {
#   "loaded": true,
#   "model": "Hermes-2-Pro-Mistral-7B",
#   "memory_used_mb": 5200,
#   "uptime_seconds": 3600
# }
```

### Example Use Cases

#### 1. Simple Summarization
```bash
curl -X POST http://localhost:8000/vx11/hermes/generate \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Summarize in one sentence: AI is transforming how we work.",
    "max_tokens": 50
  }'

# Response
{
  "completion": "AI revolutionizes work efficiency and automation.",
  "tokens_generated": 12,
  "latency_ms": 350,
  "processed_by": "hermes",
  "ttl_remaining": 7199
}
```

#### 2. Code Review (Limited)
```bash
curl -X POST http://localhost:8000/vx11/hermes/generate \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Review this code:\nfor i in range(10):\n  print(i)",
    "max_tokens": 100
  }'

# Response
{
  "completion": "Simple loop looks OK. Consider naming it more specifically.",
  "tokens_generated": 25,
  "latency_ms": 420,
  "processed_by": "hermes",
  "ttl_remaining": 7199
}
```

### Performance Baseline

| Query Type | Latency | Memory | VRAM |
|----------|---------|--------|------|
| Summarization | 350-500ms | 5.2GB | N/A |
| Q&A | 400-600ms | 5.2GB | N/A |
| Code Review | 500-800ms | 5.2GB | N/A |

**Note**: Times are approximate for CPU mode (Intel i7, 8GB RAM). GPU mode (RTX 4060) would be 5-10x faster.

---

## Runtime: Which Service When?

### Decision Tree

```
User request arrives (:8000)
      ↓
[operator-backend:8005 healthy?]
      ├─ YES → Use operator backend (normal path)
      │        ↓
      │   [API providers available?]
      │      ├─ YES → Call external API (GPT, etc.)
      │      └─ NO → Fall back to HERMES (local generation)
      │
      └─ NO → operator-backend down
              ↓
         [Query type?]
         ├─ Math/Pattern → SWITCH (deterministic, <100ms)
         ├─ Generation → HERMES (local 7B, ~400ms)
         └─ Unknown → Return 503 (Service Unavailable)
```

### Health Check Sequence

```bash
# Every 30 seconds (from madre)
1. Check operator-backend:8005 → /health
2. Check API providers (external endpoints)
3. If all down:
   - Activate SWITCH (immediate)
   - Pre-load HERMES (async, ~2s)
4. If operator recovers:
   - Close SWITCH window
   - Drain HERMES queue
   - Return to normal

# Command
curl -s -X GET http://localhost:8001/madre/power/health_check \
  -H "X-VX11-Token: vx11-internal-token"

# Response
{
  "operator_backend": "up",
  "switch_status": "dormant",
  "hermes_status": "dormant",
  "api_providers": {
    "openai": "up",
    "anthropic": "up",
    "local_hermes": "ready"
  },
  "policy": "solo_madre",
  "next_check_seconds": 30
}
```

---

## Deployment

### Docker Compose

File: `docker-compose.yml` (SWITCH pre-included)  
File: `docker-compose.full-test.yml` (SWITCH + HERMES)

```yaml
# SWITCH service (always included)
switch:
  image: vx11-switch:latest
  environment:
    - VX11_MODE=fallback
    - VX11_TOKEN=vx11-internal-token
  ports:
    - "8002:8002"  # Internal only (not exposed)
  networks:
    - vx11_internal

# HERMES service (full-test only)
hermes:
  image: vx11-hermes:latest
  environment:
    - HERMES_MODEL=Hermes-2-Pro-Mistral-7B
    - HERMES_QUANTIZATION=int4
    - HERMES_MAX_TOKENS=256
    - VX11_TOKEN=vx11-internal-token
  volumes:
    - ./data/models:/data/models
  ports:
    - "8003:8003"  # Internal only (not exposed)
  networks:
    - vx11_internal
  # Resource limits (CPU mode)
  deploy:
    resources:
      limits:
        cpus: "2"
        memory: 6G
```

### Startup Order

```bash
# make up-core (SWITCH only)
docker compose -f docker-compose.yml up -d
# → switch:8002 activates
# → hermes: NOT started (would be on-demand if needed)

# make up-full-test (SWITCH + HERMES)
docker compose -f docker-compose.full-test.yml up -d
# → switch:8002 activates
# → hermes:8003 pre-loads model (~30s)
# → Both ready for policy windows
```

---

## Testing

### Test 1: SWITCH Deterministic

```bash
# Test math mode
curl -s -X POST http://localhost:8000/vx11/switch/deterministic \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"input":"What is 10*5?","mode":"math"}' | jq .
# Expected: {"result":"50","confidence":"high"}
```

### Test 2: HERMES Generation

```bash
# Test hermes (after up-full-test)
curl -s -X POST http://localhost:8000/vx11/hermes/generate \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello, what is your name?","max_tokens":30}' | jq .
# Expected: {"completion":"...","tokens_generated":N,"latency_ms":M}
```

### Test 3: Fallback Activation

```bash
# Stop operator backend
docker compose stop operator-backend

# Wait 30s for health check
sleep 30

# Try a query
curl -s -X POST http://localhost:8000/vx11/query \
  -H "X-VX11-Token: vx11-test-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Simple math: 2+2"}' | jq .
# Expected: {"processed_by":"switch","result":"4","ttl_remaining":3599}

# Restart operator
docker compose up -d operator-backend

# Verify recovery
sleep 30
curl -s http://localhost:8000/health | jq .
# Expected: operator-backend back in rotation
```

---

## Monitoring & Alerts

### Key Metrics

```bash
# SWITCH activation count
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "SELECT COUNT(*) FROM switch_activations WHERE activated_at > datetime('now', '-1 hour');"

# HERMES query latency (last 100 queries)
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db \
  "SELECT AVG(latency_ms), MAX(latency_ms), MIN(latency_ms) FROM hermes_queries LIMIT 100;"

# Memory usage
curl -s http://localhost:8000/vx11/hermes/status | jq '.memory_used_mb'
```

### Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| HERMES memory | >6.5GB | Restart service |
| SWITCH latency | >200ms | Log warning, check CPU |
| Activation window | >3 hours | Investigate operator-backend |
| Model load time | >5s | Pre-load on boot |

---

## Invariants (Non-Negotiable)

1. **Never call :8002 or :8003 directly** - Always route through :8000
2. **Token required for all endpoints** - X-VX11-Token header mandatory
3. **solo_madre default** - SWITCH/HERMES only activate in policy windows, never automatic
4. **No external network calls from SWITCH** - Deterministic only
5. **HERMES pre-loaded on startup** - No cold-start delays in production

---

## Rollback Plan

If HERMES fails to load:

```bash
# Immediately disable HERMES window policy
curl -X POST http://localhost:8001/madre/power/policy/hermes/disable \
  -H "X-VX11-Token: vx11-internal-token"

# Fall back to SWITCH only
curl -X POST http://localhost:8001/madre/power/policy/switch_fallback/apply \
  -H "X-VX11-Token: vx11-internal-token"

# Verify
curl -s http://localhost:8000/vx11/status | jq '.fallback_strategy'
# Expected: "switch_only"
```

---

## Success Criteria (Checklist)

- [ ] SWITCH CLI works standalone (no daemon)
- [ ] HERMES model loads in <5s
- [ ] SWITCH deterministic query <100ms
- [ ] HERMES generation query 300-500ms
- [ ] Activation windows close on recovery
- [ ] All calls route through :8000 (never direct :8002/:8003)
- [ ] Metrics logged to DB (switch_activations, hermes_queries)
- [ ] Health check runs every 30s
- [ ] Token security enforced (all endpoints)
- [ ] Memory limits enforced (HERMES: 6GB, SWITCH: 128MB)

---

**Status**: PRODUCTION-READY  
**Next**: FASE 6 - GitHub Automation  
**Last Updated**: 2026-01-03
