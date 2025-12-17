# VX11 Canonical Event Architecture (v8.0+)

**Authority:** OPERATOR_VX11_V8_CANONICAL.md  
**Status:** Canonical (immutable)  
**Last Updated:** 2025-12-13  
**Version:** 1.0

---

## 🎯 Philosophy

Operator observes, compre hende y recuerda.  
**VX11 decides and acts.**  
If Operator executes something, the design is broken.

All events are **signals**, never **commands**.  
All events flow through **Tentáculo Link only**.  
Operator receives **7 canonical events** and nothing else.

---

## 📡 Canonical Event Whitelist (7 Events)

| # | Event | Emitter | Consumer | Severity | Nature | Throttle |
|---|-------|---------|----------|----------|--------|----------|
| 1 | `system.alert` | Tentáculo Link | Operator | critical, error, warning, info | Signal | On-demand |
| 2 | `system.correlation.updated` | Tentáculo Link | Operator | info | Meta | On-change (>10% delta) |
| 3 | `system.state.summary` | Tentáculo Link | Operator | info | Meta | ≥10 min OR major change |
| 4 | `forensic.snapshot.created` | Tentáculo Link | Operator | info | Forensic | On-demand |
| 5 | `madre.decision.explained` | Madre (via Tentáculo Link) | Operator | info | Signal | After decision |
| 6 | `switch.system.tension` | Switch (via Tentáculo Link) | Operator | warning, info | Signal | ≥10s |
| 7 | `shub.action.narrated` | Shub (via Tentáculo Link) | Operator | info | Signal | On-action |

---

## 🔍 Event Details

### 1. system.alert

**Emitter:** Tentáculo Link (synthetically)  
**Trigger:** When Madre, Switch, Hormiguero, or Shub report critical conditions  
**Payload:**

```json
{
  "type": "system.alert",
  "timestamp": 1702479413000,
  "severity": "critical|error|warning|info",
  "message": "Human-readable alert text",
  "source": "madre|switch|hormiguero|shub"
}
```

**Consumer behavior:** Operator shows toast/banner, logs event, no action.

---

### 2. system.correlation.updated

**Emitter:** Tentáculo Link (synthetically from Switch/Madre)  
**Trigger:** When Madre/Switch detect correlations between incidents  
**Payload:**

```json
{
  "type": "system.correlation.updated",
  "timestamp": 1702479413000,
  "data": {
    "nodes": [
      { "id": "node_1", "label": "incident_1", "module": "hormiguero" },
      { "id": "node_2", "label": "decision_A", "module": "madre" }
    ],
    "edges": [
      { "source": "node_1", "target": "node_2", "weight": 0.85 }
    ]
  }
}
```

**Consumer behavior:** Operator renders correlation grafo (max 50 nodes). Lazy init, no polling.

---

### 3. system.state.summary

**Emitter:** Tentáculo Link (synthetically)  
**Trigger:** Every ≥10 minutes OR major module state change  
**Payload:**

```json
{
  "type": "system.state.summary",
  "timestamp": 1702479413000,
  "data": {
    "madre": { "status": "active", "cycle_time_ms": 30000 },
    "switch": { "routing": "adaptive", "pending_requests": 2 },
    "hormiguero": { "queen_alive": true, "ant_count": 8, "incidents_active": 3 },
    "hermes": { "engines_ready": 4, "models_loaded": 2 },
    "manifestator": { "last_drift_scan": 1702479400000, "patches_pending": 0 }
  }
}
```

**Consumer behavior:** Operator updates system status dashboard. Low-priority, cached.

---

### 4. forensic.snapshot.created

**Emitter:** Tentáculo Link (synthetically)  
**Trigger:** On-demand via Operator `/operator/snapshot?t={timestamp}` endpoint  
**Payload:**

```json
{
  "type": "forensic.snapshot.created",
  "timestamp": 1702479413000,
  "data": {
    "snapshot_id": "snap_20251213_134500",
    "timestamp_requested": 1702479300000,
    "state": {
      "madre_state": { ... },
      "switch_state": { ... },
      "hormiguero_state": { ... }
    }
  }
}
```

**Consumer behavior:** Operator displays "Lense of Time" snapshot panel. Historical readonly view.

---

### 5. madre.decision.explained

**Emitter:** Madre (directly to Tentáculo Link)  
**Trigger:** After Madre reaches decision  
**Payload:**

```json
{
  "type": "madre.decision.explained",
  "timestamp": 1702479413000,
  "data": {
    "decision": "Execute repair scan",
    "reasoning": "3 incidents detected, confidence=0.92",
    "path": [
      { "step": 1, "action": "Detected anomaly in Hormiguero" },
      { "step": 2, "action": "Consulted Switch: 0.85 confidence" },
      { "step": 3, "action": "Decision: repair scan" }
    ],
    "alternatives": [
      {
        "option": "Escalate to human",
        "pros": ["100% safe", "human oversight"],
        "cons": ["slow", "waits for response"],
        "confidence": 0.15
      }
    ],
    "confidence": 0.92
  }
}
```

**Consumer behavior:** Operator renders decision tree in Chat panel. User can confirm or reject (confirmation sent via REST, NOT WS).

---

### 6. switch.system.tension

**Emitter:** Switch (directly to Tentáculo Link)  
**Trigger:** Every ≥10 seconds OR significant change  
**Payload:**

```json
{
  "type": "switch.system.tension",
  "timestamp": 1702479413000,
  "data": {
    "value": 42,
    "components": {
      "queue_depth": 10,
      "response_latency": 250,
      "error_rate": 0.01,
      "memory_pressure": 0.35
    }
  }
}
```

**Consumer behavior:** Operator displays "System Tension" donut widget (green <30, yellow 30-70, red >70). Real-time indicator only.

---

### 7. shub.action.narrated

**Emitter:** Shub (directly to Tentáculo Link)  
**Trigger:** When Shub performs audio analysis or applies preset  
**Payload:**

```json
{
  "type": "shub.action.narrated",
  "timestamp": 1702479413000,
  "data": {
    "action": "Apply mix preset: Jazz Mastering",
    "narrative": "Detected 3 high-frequency peaks. Applied gentle EQ and compression. Estimated loudness: -14 LUFS.",
    "audio_url": "https://shub:8007/narration/aaa_bbb_ccc.mp3"
  }
}
```

**Consumer behavior:** Operator displays action card with narrative text + optional audio playback link (NO auto-play). Read-only confirmation.

---

## 🚫 Events NOT in Canonical Set

### Rejected / Degraded to Logs

These events are **rejected at Tentáculo Link** and logged as DEBUG:

- `hermes.cli.invoked` — internal only
- `switch.route.selected` — internal only
- `hormiguero.state.summary` — use system.state.summary instead
- `*.requested`, `*.invoked`, `*.selected` — non-canonical naming
- Present-tense events (`querying`, `executing`, etc.) — use past tense

Example rejection in Tentáculo Link logs:

```
[DEBUG] event_rejected:type=hermes.cli.invoked:reason=not in canonical whitelist
```

---

## 🔧 Implementation Requirements

### For Tentáculo Link

1. **Event Validation Middleware:**
   ```python
   CANONICAL_EVENT_WHITELIST = {
       "system.alert",
       "system.correlation.updated",
       "system.state.summary",
       "forensic.snapshot.created",
       "madre.decision.explained",
       "switch.system.tension",
       "shub.action.narrated",
   }
   
   def validate_event_type(event_type: str) -> bool:
       return event_type in CANONICAL_EVENT_WHITELIST
   ```

2. **Synthetic Event Creation:**
   - `system.alert` ← synthesized from module alerts
   - `system.correlation.updated` ← synthesized from Switch/Madre
   - `system.state.summary` ← synthesized from module health
   - `forensic.snapshot.created` ← synthesized on `/operator/snapshot` request

3. **Broadcast Only to Canonical:**
   ```python
   async def broadcast(event: dict):
       if validate_event_type(event["type"]):
           # send to all Operator clients
       else:
           # reject silently
   ```

### For Operator (Frontend)

1. **Listener Strict Compliance:**
   ```typescript
   const CANONICAL_TYPES: CanonicalEventType[] = [
     "system.alert",
     "system.correlation.updated",
     "system.state.summary",
     "forensic.snapshot.created",
     "madre.decision.explained",
     "switch.system.tension",
     "shub.action.narrated",
   ];
   
   function isCanonicalEvent(event: any): boolean {
     return CANONICAL_TYPES.includes(event.type);
   }
   ```

2. **Ignore Non-Canonical:**
   ```typescript
   ws.onmessage = (e) => {
     const event = JSON.parse(e.data);
     if (isCanonicalEvent(event)) {
       handleCanonicalEvent(event);
     }
     // else: silently ignore
   };
   ```

3. **Graceful Degradation:**
   - If event doesn't arrive in 5s → fallback UI value
   - No polling to replace WS
   - No automatic retry loops

---

## ⚡ Performance Constraints

| Constraint | Requirement | Why |
|-----------|-------------|-----|
| Event payload size | <5 KB average | Network bandwidth |
| WS message rate | ≥100ms throttle | CPU at frontend |
| Canonical events only | STRICT | Reduce noise, increase signal |
| No synthetic events in modules | STRICT | Prevents double-emitting |
| Cache TTL for snapshots | 5 min max | Memory footprint |
| Correlation graph size | max 50 nodes | Rendering perf |
| System tension update | ≥10s | Smooth visualization |

---

## 🚀 Migration Path (Future)

### Phase 1 (NOW)
- ✅ Tentáculo Link validates all events
- ✅ Only 7 canonical types broadcast
- ✅ Non-canonical logged as DEBUG
- ✅ Operator implements strict listener

### Phase 2 (TBD)
- Módulos emiten directamente a Tentáculo Link (no DB interim)
- Real-time BD snapshots for forensic timeline
- WebSocket real connection (end-to-end)

### Phase 3 (TBD)
- Advanced correlation AI (DeepSeek R1 input)
- Predictive tension alerts
- Operator video UI (3D representation)

---

## ✅ Validation Checklist

```
[✅] 7 and only 7 canonical events allowed
[✅] All events conform to <module>.<action>.<result> (past tense)
[✅] Tentáculo Link synthesizes system.* events only
[✅] Non-canonical events rejected at gateway
[✅] Operator ignores non-whitelist events
[✅] Event payloads <5 KB
[✅] No polling loops in Operator
[✅] WS throttle ≥100ms
[✅] Operator stays 100% passive (observation only)
[✅] Confirmation sent via REST, never WS
```

---

**Author:** VX11 Design Team  
**Consensus:** ✅ CANONICAL — Do not modify without consensus  
**Last Review:** 2025-12-13
