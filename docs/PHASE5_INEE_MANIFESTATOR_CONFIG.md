# VX11 INEE + Manifestator Configuration (Phase 5)

## Feature Flags (All OFF by default)

```bash
# Hormiguero INEE Integration
export VX11_INEE_ENABLED=0                    # OFF: Disable INEE CPU management
export VX11_INEE_FORWARD_ENABLED=0            # OFF: Disable forward path to tentaculo
export VX11_INEE_NAMESPACE_PREFIX="hormiguero_inee"  # Table namespace

# Manifestator Builder
export VX11_MANIFESTATOR_EMIT_INTENT_ENABLED=0       # OFF: Disable emit-intent
export VX11_MANIFESTATOR_BUILD_DIRECT_DISABLED=1     # ALWAYS OFF: Never docker build directly

# INEE Namespacing
export VX11_INEE_CPU_QUOTA_ENABLED=0                 # OFF: CPU quota management
export VX11_INEE_AUTONOMOUS_SCALING_ENABLED=0        # OFF: Auto-scaling
```

## Phase 5 Deployment Checklist

- [ ] Set all INEE flags to 0 (disabled)
- [ ] Set all Manifestator flags to 0 (disabled)  
- [ ] Verify flags in docker-compose.override.yml
- [ ] Verify tables namespaced in Hormiguero schema
- [ ] Verify Manifestator does NOT call docker build directly
- [ ] Document in CANONICAL for future phases
- [ ] Update SCORECARD.json with Phase 5 readiness

## Hormiguero Namespacing (When Enabled in Phase 5+)

When VX11_INEE_ENABLED=1, all Hormiguero tables prefixed with `hormiguero_inee_`:

```sql
-- Phase 5+ tables (currently NOT created):
CREATE TABLE hormiguero_inee_cpu_allocations (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    service_name TEXT,
    cpu_quota_percent REAL,
    cpu_actual_percent REAL
);

CREATE TABLE hormiguero_inee_scaling_events (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    service_name TEXT,
    action TEXT,  -- 'scale_up', 'scale_down', 'restart'
    reason TEXT
);
```

## Manifestator Emit-Intent (When Enabled in Phase 5+)

When VX11_MANIFESTATOR_EMIT_INTENT_ENABLED=1:

```python
# NEW ENDPOINT (OFF by default):
POST /manifestator/builder/emit-intent
  Request: {
    "intent_type": "build",
    "target_service": "switch",
    "dockerfile_path": "services/switch/Dockerfile",
    "build_context": "services/switch/",
    "reason": "deploying_fix"
  }
  
  Response: {
    "intent_id": "uuid",
    "status": "pending",
    "assigned_to": "madre",
    "estimated_time_sec": 120
  }

# Never executes docker build directly
# Instead emits intent to Madre for orchestrated execution
```

## Hormigas (Daughter Processes) Autonomous Mode

When both INEE and Manifestator enabled:

```
Hormigas can:
1. Detect failure patterns
2. Emit build intents to fix services
3. Auto-scale based on load
4. Report decisions to ledger
5. Revert if fixes cause new issues
```

**PHASE 5 STATUS**: All autonomous features OFF by default. Ready for controlled rollout in Phase 5+.

