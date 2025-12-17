# Shub-Niggurath v7.1

**The Infinite Black Goat of the Woods with a Thousand Young**  
Audio AI Assistant for VX11

---

## Status (v7.1)

- ✅ **VIGENTE:** FastAPI mock server (lazy initialization)
- ✅ **STABLE:** 9 endpoints, token auth, health check
- 🔜 **v8 ROADMAP:** Real DSP, REAPER integration, multi-tenant

---

## Quick Start

```bash
# Start Shub (docker)
docker-compose up shubniggurath

# Test health
curl -s http://localhost:8007/health | jq .

# Expected: {"status": "healthy", "initialized": false, "version": "7.0"}

# Analyze audio (mock)
curl -X POST http://localhost:8007/shub/analyze \
  -H "X-VX11-Token: $VX11_GATEWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file": "song.wav"}'

# Expected: {"status": "queued", "task_id": "mock-task-001"}
```

---

## Architecture

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **Assistant** | `shub_core_init.py` | Main AI assistant + pipeline |
| **Routers** | `shub_routers.py` | 7 REST API routers |
| **Bridges** | `shub_vx11_bridge.py` | VX11 integration (safe) |
| **Copilot** | `shub_copilot_bridge_adapter.py` | Copilot entry point |
| **Database** | `shub_db_schema.py` | Audio project schema |

### Integration Points

- **Conversational:** Copilot → Shub (`/v1/assistant/copilot-entry`)
- **Orchestration:** Shub → Madre (task coordination)
- **Routing:** Shub → Switch (intelligent provider selection)
- **Intelligence:** Shub → MCP (when require_action=true)

---

## API Endpoints

### Assistant
- `POST /v1/assistant/command` — Execute command
- `GET /v1/assistant/status` — Current status
- `POST /v1/assistant/copilot-entry` — Copilot integration point

### Analysis
- `POST /v1/analysis/analyze` — Start audio analysis
- `GET /v1/analysis/results/{project_id}` — Get results

### Mixing
- `POST /v1/mixing/mix` — Start automatic mixing
- `GET /v1/mixing/mix/{mix_session_id}` — Get mix status

### Mastering
- `POST /v1/mastering/master` — Start mastering
- Automatic LUFS normalization to -14 LUFS

### Preview
- `GET /v1/preview/play/{track_id}` — Play track
- `GET /v1/preview/stop` — Stop playback

### Headphones
- `POST /v1/headphones/calibrate` — Calibrate
- `GET /v1/headphones/profile` — Get profile

### Maintenance
- `POST /v1/maintenance/cleanup` — System cleanup
- `GET /v1/maintenance/health` — Health check

---

## Database

```bash
# Create database
sqlite3 /app/data/shub_niggurath.db < db/migrations_shub.sql

# Or automatic on first run
```

### Tables
- `project_audio_state` — Audio projects
- `reaper_tracks` — REAPER integration
- `reaper_item_analysis` — Item analysis results
- `analysis_cache` — Analysis cache
- `assistant_sessions` — Chat sessions
- `mixing_sessions` — Mix sessions
- `mastering_sessions` — Master sessions

---

## Integration with VX11

### Via Copilot

```bash
curl -X POST http://localhost:9000/v1/assistant/copilot-entry \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "analyze the mix",
    "require_action": true,
    "context": {"project_id":"proj_123"}
  }'
```

### Via Madre (Orchestration)

Shub can create tasks in Madre for complex workflows.

### Via MCP (Conversational)

When `require_action=true`, Shub delegates to VX11 MCP for intelligent action routing.

---

## Environment

```bash
# .env (if running standalone)
SHUB_DB=sqlite:////data/shub_niggurath.db
SHUB_MODE=api
LOG_LEVEL=INFO

# For VX11 integration
VX11_GATEWAY_URL=http://localhost:8000
VX11_MADRE_URL=http://localhost:8001
VX11_SWITCH_URL=http://localhost:8002
VX11_MCP_URL=http://localhost:8006
```

---

## Development

### Run tests

```bash
python3 -m pytest tests/test_shub_core.py -v
```

### Validation

```bash
# Syntax check
python3 -m py_compile shub_*.py

# Type hints (optional)
mypy shub_core_init.py
```

---

## Security & Restrictions

✅ **Safe:** Shub operates in isolation, does NOT modify VX11

❌ **Prohibited:**
- Modify `/vx11/` files outside `/shub/`
- Touch VX11 puertos (8000-8008)
- Modify docker-compose (VX11)
- Activate operator_mode
- Alter VX11 database

---

## Troubleshooting

### "VX11 not available"
→ VX11 not running. Shub works offline.

### "Port 9000 in use"
→ Change port in `main.py` or kill process on 9000

### Database locked
→ Wait 2 seconds or restart Shub

### Tests fail with httpx error
→ `pip install httpx` (optional, for VX11 bridge tests)

---

## Documentation

- `docs/SHUB_MANUAL.md` — Complete manual
- `docs/SHUB_ROUTES.md` — Route reference
- `docs/SHUB_VX11_INTEGRATION.md` — Integration guide

---

## Roadmap

- [ ] **v3.1:** REAPER native API
- [ ] **v3.2:** Distributed processing
- [ ] **v3.3:** ML-based beat detection
- [ ] **v4.0:** Real-time streaming

---

**Version:** 3.0.0  
**Status:** Production-ready  
**Last Updated:** 2 de diciembre de 2025  
**Maintainer:** GitHub Copilot  
