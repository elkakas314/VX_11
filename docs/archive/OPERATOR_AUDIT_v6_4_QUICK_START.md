# OPERATOR v6.4 - QUICK REFERENCE CHECKLIST

**Tabla de referencias rápidas para implementación.**

---

## ✅ QUÉ EXISTE (HECHO)

### Backend
- [x] FastAPI app en puerto 8011
- [x] WebSocket bridge a Tentáculo Link
- [x] SwitchClient (→ `/switch/route-v5`)
- [x] HermesClient (→ `/hermes/waveform`)
- [x] ShubClient (→ `/shub/run_mode_c`)
- [x] ManifestatorClient (→ `/api/manifest/validate`)
- [x] HealthAggregator (colecta 12 módulos)
- [x] JobQueue (en memoria)
- [x] AudioIntentParser
- [x] ModelRotator
- [x] Endpoints: `/health`, `/system/status`, `/intent`, `/intent/chat`, `/shub/*`, `/manifest/*`, `/jobs/*`, `/health/aggregate`, `/ws`, `/api/*`

### Frontend
- [x] React/Vite app
- [x] StatusBar (indica conexión + health count)
- [x] Dashboard (grid módulos + eventos)
- [x] ChatPanel (interface Switch)
- [x] ShubPanel (placeholder)
- [x] API service (fetchSystemStatus, validateManifest, wsConnect)

---

## ❌ QUÉ FALTA (CRÍTICO - TIER 1)

### Backend Code
- [ ] MadreClient class + methods
- [ ] SpawnerClient class + methods
- [ ] Endpoints `/plans/*` (GET list, GET detail, POST execute)
- [ ] Endpoints `/spawns/*` (GET list, GET detail, GET logs, POST kill, GET metrics)
- [ ] Endpoints `/queue/*` (GET status, GET next, POST preload-model)
- [ ] Update HealthAggregator to cover Madre + Spawner

### Frontend Components
- [ ] MadrePanel.tsx (planes, feedback, delegaciones)
- [ ] SpawnerPanel.tsx (hijas, logs, kill, metrics)
- [ ] SwitchQueuePanel.tsx (cola, modelo, próximas tareas)
- [ ] Update api.ts con nuevas funciones:
  - `fetchPlans()`, `fetchPlanDetail(id)`, `executePlan(id)`
  - `fetchSpawns()`, `fetchSpawnDetail(id)`, `killSpawn(id)`, `streamSpawnLogs(id)`
  - `fetchQueueStatus()`, `fetchQueueNext()`, `preloadModel(name)`

### Integration Tests
- [ ] Test plan creation → execution → hija spawned
- [ ] Test hija streaming logs → completion
- [ ] Test queue management + model switching

---

## ⚠️ QUÉ FALTA (MAYOR - TIER 2)

### Backend Code
- [ ] Endpoints `/models/*` (GET local, GET registry, POST download, GET usage)
- [ ] Endpoints `/audit/*` (GET executions, GET violations, GET stats)
- [ ] Endpoints `/tasks/*` (GET pending, GET in-progress, GET completed)
- [ ] WebSocket canales específicos (operador|madre|switch|hermes|spawner|mcp|hormiguero)
- [ ] JobQueue → BD persistence
- [ ] HormigueroClient class

### Frontend Components
- [ ] HermesPanel.tsx (modelos local/registry, descarga, uso)
- [ ] MCPPanel.tsx (auditoría, violaciones, stats)
- [ ] HormigueroPanel.tsx (tareas, clasificación Reina, timeline)
- [ ] Update App.tsx routing a tabs/collapsibles

### Features
- [ ] Logs streaming panel `/logs/stream?module=X`
- [ ] Export audit log button
- [ ] Priority reprioritization UI

---

## 🔮 QUÉ FALTA (MEJORA - TIER 3)

### Frontend UX
- [ ] Collapsible panels (tabs instead of fixed layout)
- [ ] Drag-n-drop reordenable
- [ ] MiniMapPanel.tsx (9-node overview, 🟢🟡🔴)
- [ ] Dark mode toggle
- [ ] Save/load layout presets
- [ ] Responsive design (mobile-friendly)

### Backend Features
- [ ] Rate limiting
- [ ] Better error handling
- [ ] Metrics export (Prometheus-ready)
- [ ] Health probe liveness/readiness

### Performance
- [ ] Virtual scrolling (large task lists)
- [ ] Component memoization
- [ ] WebSocket message deduplication
- [ ] API response caching

---

## 📋 IMPLEMENTATION CHECKLIST - TIER 1

### Day 1 - Backend Foundation

**MadreClient**
```python
# File: operator/backend/services/clients.py
class MadreClient(BaseClient):
    def __init__(self):
        base = getattr(settings, "madre_url", f"http://madre:{settings.madre_port}")
        super().__init__(base)
    
    async def get_plans(self):
        return await self.post("/orchestrate", {"action": "list_plans"})
    
    async def get_plan(self, plan_id: str):
        return await self.post("/orchestrate", {"action": "get_plan", "plan_id": plan_id})
    
    async def execute_plan(self, plan_id: str):
        return await self.post("/orchestrate", {"action": "execute", "plan_id": plan_id})

# Add to main.py
madre_client = MadreClient()

# Test: curl http://127.0.0.1:8011/plans
```

**SpawnerClient**
```python
# File: operator/backend/services/clients.py
class SpawnerClient(BaseClient):
    def __init__(self):
        base = getattr(settings, "spawner_url", f"http://spawner:{settings.spawner_port}")
        super().__init__(base)
    
    async def list_spawns(self):
        return await self.post("/spawn/list", {})
    
    async def get_spawn(self, spawn_id: str):
        return await self.post(f"/spawn/status/{spawn_id}", {})
    
    async def kill_spawn(self, spawn_id: str):
        return await self.post(f"/spawn/kill/{spawn_id}", {})

# Add to main.py
spawner_client = SpawnerClient()

# Test: curl http://127.0.0.1:8011/spawns
```

**New Endpoints in main.py**
```python
@app.get("/plans")
async def get_plans(ok=Depends(check_token)):
    return await madre_client.get_plans()

@app.get("/plans/{plan_id}")
async def get_plan(plan_id: str, ok=Depends(check_token)):
    return await madre_client.get_plan(plan_id)

@app.post("/plans/{plan_id}/execute")
async def execute_plan(plan_id: str, ok=Depends(check_token)):
    return await madre_client.execute_plan(plan_id)

@app.get("/spawns")
async def get_spawns(ok=Depends(check_token)):
    return await spawner_client.list_spawns()

@app.get("/spawns/{spawn_id}")
async def get_spawn(spawn_id: str, ok=Depends(check_token)):
    return await spawner_client.get_spawn(spawn_id)

@app.post("/spawns/{spawn_id}/kill")
async def kill_spawn(spawn_id: str, ok=Depends(check_token)):
    return await spawner_client.kill_spawn(spawn_id)

@app.get("/queue/status")
async def queue_status(ok=Depends(check_token)):
    """Get current queue state from Switch."""
    try:
        async with httpx.AsyncClient(timeout=5.0, headers=AUTH_HEADERS) as client:
            resp = await client.get(f"http://127.0.0.1:{settings.switch_port}/switch/queue/status")
            return resp.json() if resp.status_code == 200 else {"status": "unreachable"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
```

---

### Day 2 - Frontend Panels

**MadrePanel.tsx**
```tsx
import React, { useEffect, useState } from "react";
import { fetchJSON } from "../services/api";

export function MadrePanel() {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJSON("/plans")
      .then(setPlans)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="card">
      <h2>Plans (Madre Orchestration)</h2>
      {loading ? (
        <p>Loading plans...</p>
      ) : plans.length === 0 ? (
        <p>No plans created yet</p>
      ) : (
        <table style={{ width: "100%" }}>
          <thead>
            <tr>
              <th>Plan ID</th>
              <th>Status</th>
              <th>Feedback</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {plans.map((plan) => (
              <tr key={plan.plan_id}>
                <td>{plan.plan_id.slice(0, 8)}</td>
                <td>{plan.status}</td>
                <td>{plan.feedback?.model || "—"}</td>
                <td>
                  <button
                    onClick={() =>
                      fetchJSON(`/plans/${plan.plan_id}/execute`, {
                        method: "POST",
                      }).then(() => alert("Plan executed"))
                    }
                  >
                    Execute
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
```

**SpawnerPanel.tsx**
```tsx
import React, { useEffect, useState } from "react";
import { fetchJSON } from "../services/api";

export function SpawnerPanel() {
  const [spawns, setSpawns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const timer = setInterval(async () => {
      const data = await fetchJSON("/spawns");
      setSpawns(data);
    }, 2000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="card">
      <h2>Hijas (Spawner Processes)</h2>
      {spawns.length === 0 ? (
        <p>No active processes</p>
      ) : (
        spawns.map((spawn) => (
          <div key={spawn.spawn_id} style={{ marginBottom: "10px", padding: "5px", border: "1px solid #ccc" }}>
            <div>
              <strong>{spawn.cmd}</strong> (PID: {spawn.pid})
            </div>
            <div>
              Status: {spawn.status} | CPU: {spawn.cpu_percent}% | Memory: {spawn.memory_mb}MB
            </div>
            <button
              onClick={() =>
                fetchJSON(`/spawns/${spawn.spawn_id}/kill`, { method: "POST" }).then(
                  () => alert("Kill signal sent")
                )
              }
            >
              Kill
            </button>
          </div>
        ))
      )}
    </div>
  );
}
```

**SwitchQueuePanel.tsx**
```tsx
import React, { useEffect, useState } from "react";
import { fetchJSON } from "../services/api";

export function SwitchQueuePanel() {
  const [queue, setQueue] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchJSON("/queue/status")
      .then(setQueue)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="card"><p>Loading queue status...</p></div>;
  if (!queue) return <div className="card"><p>Unable to load queue</p></div>;

  return (
    <div className="card">
      <h2>Queue (Switch)</h2>
      <div>Active Model: <strong>{queue.active_model || "none"}</strong></div>
      <div>Queue Size: <strong>{queue.size || 0}</strong></div>
      <div>Mode: <strong>{queue.mode || "BALANCED"}</strong></div>
      <div style={{ marginTop: "10px" }}>
        <h3>Next Tasks:</h3>
        {queue.next_tasks && queue.next_tasks.length > 0 ? (
          <ul>
            {queue.next_tasks.slice(0, 5).map((task: any, idx: number) => (
              <li key={idx}>
                [{task.priority}] {task.prompt_preview} (ETA: {task.estimated_wait_s}s)
              </li>
            ))}
          </ul>
        ) : (
          <p>Queue empty</p>
        )}
      </div>
    </div>
  );
}
```

**Update api.ts**
```typescript
// Add to services/api.ts

export async function fetchPlans() {
  const res = await fetch(`${API_BASE}/plans`);
  return res.json();
}

export async function fetchPlanDetail(planId: string) {
  const res = await fetch(`${API_BASE}/plans/${planId}`);
  return res.json();
}

export async function executePlan(planId: string) {
  const res = await fetch(`${API_BASE}/plans/${planId}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return res.json();
}

export async function fetchSpawns() {
  const res = await fetch(`${API_BASE}/spawns`);
  return res.json();
}

export async function killSpawn(spawnId: string) {
  const res = await fetch(`${API_BASE}/spawns/${spawnId}/kill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  return res.json();
}

export async function fetchQueueStatus() {
  const res = await fetch(`${API_BASE}/queue/status`);
  return res.json();
}
```

**Update App.tsx**
```tsx
import { MadrePanel } from "./components/MadrePanel";
import { SpawnerPanel } from "./components/SpawnerPanel";
import { SwitchQueuePanel } from "./components/SwitchQueuePanel";

export default function App() {
  // ... existing state

  return (
    <div className="page">
      <StatusBar connected={connected} modules={healthSummary} />
      <div className="layout">
        <Dashboard status={status} events={events} onValidateManifest={handleManifestValidate} />
        <div className="panels">
          <ChatPanel onSend={handleSendChat} events={events} />
          <MadrePanel />
          <SpawnerPanel />
          <SwitchQueuePanel />
        </div>
      </div>
    </div>
  );
}
```

---

### Day 3 - Integration Testing

**Test script**
```bash
#!/bin/bash
# tests/test_operator_tier1.sh

set -e

echo "🧪 Testing Operator Tier 1 Integration..."

# Start services
echo "Starting services..."
./scripts/run_all_dev.sh &
sleep 5

# Test endpoints
echo "Testing /plans endpoint..."
curl -s -X GET http://127.0.0.1:8011/plans \
  -H "X-VX11-Token: $VX11_GATEWAY_TOKEN" | jq .

echo "Testing /spawns endpoint..."
curl -s -X GET http://127.0.0.1:8011/spawns \
  -H "X-VX11-Token: $VX11_GATEWAY_TOKEN" | jq .

echo "Testing /queue/status endpoint..."
curl -s -X GET http://127.0.0.1:8011/queue/status \
  -H "X-VX11-Token: $VX11_GATEWAY_TOKEN" | jq .

# Test frontend loads
echo "Testing frontend load..."
curl -s http://127.0.0.1:8011/app | grep -q "MadrePanel" && echo "✅ MadrePanel loaded"
curl -s http://127.0.0.1:8011/app | grep -q "SpawnerPanel" && echo "✅ SpawnerPanel loaded"

echo "✅ All Tier 1 tests passed!"
```

---

## 📋 VERIFICATION CHECKLIST

After implementing Tier 1, verify:

- [ ] MadreClient can reach Madre
- [ ] SpawnerClient can reach Spawner
- [ ] `/plans` returns list of plans
- [ ] `/spawns` returns list of spawns
- [ ] `/queue/status` returns queue info
- [ ] MadrePanel renders correctly
- [ ] SpawnerPanel renders correctly
- [ ] SwitchQueuePanel renders correctly
- [ ] All endpoints < 200ms latency
- [ ] WebSocket bridge still functional

---

## 📚 REFERENCES

- Full audit: `OPERATOR_AUDIT_v6_4.md`
- Architecture diagrams: `OPERATOR_AUDIT_v6_4_DIAGRAMS.md`
- Backend main: `/operator/backend/main.py`
- Frontend app: `/operator/frontend/src/App.tsx`

---

**Ready to implement? Start with Day 1 MadreClient & SpawnerClient.**
