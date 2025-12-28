# SOLO_MADRE_CORE — Official Definition

## What is SOLO_MADRE_CORE?

**SOLO_MADRE_CORE** is the VX11 runtime default and minimum operating state that guarantees:

1. **Single external entrypoint**: All client requests arrive via `tentaculo_link:8000`
2. **Core infrastructure only**: `madre` (orchestration) + `redis` (cache)
3. **Frontdoor always available**: `tentaculo_link` never stops, even in low-power mode
4. **No app services**: No switch, hermes, spawner, hormiguero, manifestator, shubniggurath, mcp, operator

## Component Breakdown

| Service | Port | Role | Always On | Reason |
|---------|------|------|-----------|--------|
| **tentaculo_link** | 8000 | Single Entrypoint / Gateway | ✅ YES | Required for all external access |
| **madre** | 8001 | Orchestration / Power Manager | ✅ YES | Manages windows, policies, service control |
| **redis** | 6379 | Cache Backend | ✅ YES | Fast health check, circuit breaker state |

## Proof: Docker Compose Configuration

### Services with NO profile (unconditional):
```yaml
tentaculo_link:
  # NO profile - always runs
  # entrypoint: uvicorn tentaculo_link.main_v7:app --host 0.0.0.0 --port 8000

madre:
  # NO profile - always runs
  # entrypoint: sh -c 'apt-get update && python -m madre.main'

redis:
  # NO profile - always runs
  # image: redis:7-alpine
```

### Services with profile="core":
```yaml
switch:
  profiles: ["core"]

hermes:
  profiles: ["core"]

spawner:
  profiles: ["core"]

# ... and 5 others
```

## Runtime Behavior

### Mode: Default (no --profile)
```bash
docker compose up -d
```
**Result**: Only madre + tentaculo_link + redis

### Mode: With Core Services (--profile core)
```bash
docker compose --profile core up -d
```
**Result**: madre + tentaculo_link + redis + [all 8 core services]

### Mode: Operator Profile
```bash
docker compose --profile operator up -d
```
**Result**: madre + tentaculo_link + redis + operator-backend + operator-frontend

## INVARIANT ENFORCEMENT

### INV-1: Single Entrypoint
- ✅ Tentaculo_link has NO profile → always included
- ✅ Never restricted by profile logic
- ✅ Gateway routes all `/operator/power/*` to madre internal APIs

### INV-2: Frontdoor Always Up
- ✅ Even in "hard_off" or "idle_min" modes, tentaculo_link remains healthy
- ✅ Madre can orchestrate windows via tentaculo_link proxy
- ✅ External clients never lose connection point

### INV-3: Low Resource Footprint
- ✅ Default mode: 3 services, ~1.1 GB total (madre 512m + redis 128m + tentaculo 512m)
- ✅ No application logic in default state
- ✅ Core infrastructure only

## Health Check Endpoints

```bash
# Check SOLO_MADRE_CORE health
curl http://localhost:8000/health        # Tentaculo frontdoor
curl http://localhost:8001/health        # Madre orchestration
curl http://localhost:6379/ping          # Redis (telnet or redis-cli)

# Status check via gateway
curl http://localhost:8000/vx11/status   # Aggregate health from tentaculo
curl http://localhost:8001/power/status  # Detailed power state from madre
```

## Policy: SOLO_MADRE_CORE Maintenance

After EVERY power window close or emergency shutdown:
1. Verify only mother + tentaculo_link + redis are running
2. Call `POST /madre/power/policy/solo_madre/apply` to enforce
3. Audit log: Record timestamp and reason in `docs/audit/<TS>_policy_apply/`

## Transitions

```
SOLO_MADRE_CORE (default)
    ↓ [window open]
CORE_SERVICES (switch + hermes + spawner + ...)
    ↓ [on close]
SOLO_MADRE_CORE (guaranteed return)
```

---

**Version**: FASE A audit (2025-12-28)  
**Status**: ✅ Validated & Enforced  
**Next Step**: FASE B - Implement core healthchecks + hardening
