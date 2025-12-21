# OPERATOR VX11 v8.1 — EXTENSIONES DE BAJO CONSUMO

**Propósito:** Ampliar v8.0 canónico sin romper la arquitectura pasiva, con consumo CPU mínimo y WS primero.

---

## 📋 RESUMEN DE MEJORAS APROBADAS

1. **System Tension (0-100)** — Métrica de carga/estrés del sistema en tiempo real (WS primero).
2. **Timeline Forense Inteligente** — Eventos cronológicos con lazy load (últimos 100, scroll cargar más).
3. **Lente de Tiempo** — Selector timestamp → snapshot de estado VX11 en ese punto (backend cuando esté listo).
4. **Niveles Hormiguero** — Selector Macro/Meso/Micro para abstracción visual (UI preparada, backend dados si existen).
5. **Explicación Estructurada Madre** — Render JSON con decision_tree, alternatives, confidence (si llega vía WS).
6. **Marcadores Humanos (Bookmarks)** — Atar ⭐ a eventos timeline en localStorage (sin backend).

---

## 🌐 EVENTOS WEBSOCKET ESPERADOS (STUBS / CUANDO EXISTAN)

| Evento | Fuente | Payload | Frecuencia | Fallback |
|--------|--------|---------|-----------|----------|
| `system.correlation_update` | Madre/Switch | `{nodes: [], edges: []}` | Cambio | None |
| `timeline.snapshot_ready` | Tentáculo Link | `{timestamp, state: {}}` | On-demand | "N/A" |
| `hormiguero.abstraction_level` | Hormiguero | `{level: "macro"\|"meso"\|"micro", data}` | Change | Current data |
| `madre.explanation_structured` | Madre | `{decision_tree, alternatives, confidence}` | After decision | Plain text |
| `switch.system_tension` | Switch | `{value: 0-100}` | 5s | "—" |

**Nota:** Si un evento NO llega dentro de 5s, UI muestra valor fallback sin bloqueo.

---

## ⚡ REGLAS DE BAJO CONSUMO (IMPLEMENTACIÓN OBLIGATORIA)

### Throttling por Visibilidad
```javascript
// Pestaña activa: updates normales
// Pestaña inactiva: reducir a 50% o pausar visualización
// Implementación: Page Visibility API (document.hidden)
```

### Timeline Lazy Loading
- Cargar últimos **100 eventos** en mount.
- Scroll al 80% → cargar 50 más (sin loops).
- Cache con TTL 5 minutos, máximo 5 snapshots en RAM.
- Nunca recalcular grafo si >200 nodos (considerar worker si fuese necesario, pero por defecto NO worker).

### WS Throttle (Conexión VX11)
- Máximo 1 mensaje cada 100ms desde frontend.
- Reconexión exponencial: 1s, 2s, 4s, max 30s.

### Cache Strategy
```
snapshots: Map<timestamp, state> → evict if TTL > 5min or size > 5
incidents: [{...}] → keep últimos 500, discard older
correlations: {nodes, edges} → update solo si distance > 10%
```

---

## 🎯 CAMBIOS FRONTEND (OPERATOR)

### A. Dashboard — System Tension Widget

**Archivo:** `operator/src/components/Dashboard/SystemTensionWidget.tsx`

Render:
- **Input:** WS `switch.system_tension` (0-100)
- **UI:** Donut circular + número + color (verde <30, amarillo 30-70, rojo >70)
- **Update:** Max 1Hz (throttle)
- **Fallback:** "—" si no llega después de 5s

### B. Timeline Forense (Componente Nueva)

**Archivo:** `operator/src/components/ForensicTimeline/index.tsx`

Estructura:
- **Render:** Lista de eventos cronológicos (últimos 100)
- **Scroll:** Lazy load al 80% (cargar 50 más)
- **Filtros:** Dropdown por módulo (madre, switch, hermes, etc.), severidad
- **Correlación:** Panel <50 nodos con grafo si `system.correlation_update` llega
- **Lente de Tiempo:** Selector timestamp → click → request a Tentáculo Link `/operator/snapshot?t={ts}` → esperar `timeline.snapshot_ready` → render panel con estados en ese punto

**Fallback:** Si backend no está listo, UI muestra "⏳ Snapshot backend not ready" sin romper.

### C. Hormiguero — Selector de Nivel

**Archivo:** `operator/src/components/Hormiguero/LevelSelector.tsx` (nuevo)

UI:
- 3 botones: **Macro** | **Meso** | **Micro**
- Click → emitir WS `request_level` (stubs seguros, backend decide)
- Render según `hormiguero.abstraction_level` si llega
- Fallback: mostrar datos actuales sin romper

### D. Chat Madre — Explicación Estructurada

**Archivo:** `operator/src/components/ChatMadre/StructuredExplanation.tsx` (nuevo)

Render cuando llegue `madre.explanation_structured`:
```
Decisión: "Ejecutar scan"
├── decision_tree (mostrar árbol)
├── alternatives (acordeón)
└── confidence: 0.92
```

Si NO llega, mostrar plain text como ahora.

### E. Marcadores (Bookmarks) — IndexedDB Local

**Archivo:** `operator/src/hooks/useBookmarks.ts`

```typescript
interface Bookmark {
  id: string;
  event_id: string;
  timestamp: number;
  label?: string;
  created_at: number;
}

// Store en localStorage (si es pequeño) o IndexedDB (si hay muchos)
// Persistente entre sesiones
// UI: ⭐ botón en cada evento → guardar bookmark
// Vista: filtro "Bookmarked" en timeline
```

---

## 🔧 CAMBIOS BACKEND (TENTÁCULO LINK & OPERATOR BACKEND) — STUBS SEGUROS SOLAMENTE

### Tentáculo Link (`tentaculo_link/main_v7.py`)

1. **ConnectionManager.broadcast()** — Nueva línea (stub seguro):
   ```python
   async def broadcast(self, message_type: str, data: dict):
       """Broadcast event to all connected clients (safe stub)."""
       for client_id in self.connections:
           try:
               await self.connections[client_id].send_json({"type": message_type, "data": data})
           except:
               pass  # Client desconectado
   ```

2. **(Opcional) Endpoint `/operator/snapshot`** — Si Switch/Madre puede generar snapshots:
   ```python
   @app.get("/operator/snapshot")
   async def get_snapshot(t: int = Query(0)):
       """Request a VX11 state snapshot at timestamp t (stub: returns current if t=0)."""
       # Stub: return current state
       # Real: query BD para snapshot en timestamp t
       return {"timestamp": t, "state": {...}}
   ```

### Operator Backend (`operator_backend/backend/main_v7.py`)

Reemplazar echo loop con evento-listening:
```python
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Listen to Tentáculo Link WS and forward events to client."""
    await websocket.accept()
    # En futuro: conectar a tentáculo_link WS, escuchar, reenviar
    # Por ahora: echo loop (sin cambios)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "data": data})
    except WebSocketDisconnect:
        pass
```

---

## 📊 PERFORMANCE OBLIGATORIA

| Métrica | Target | Cómo |
|---------|--------|------|
| Main thread <60ms | ✅ | Render Timeline → max 100 items, virtualizado si >200 |
| Memory < 50MB | ✅ | Cache TTL 5min, max 5 snapshots, no logs en RAM |
| WS Latency | <100ms | Throttle 100ms, reconexión exponencial |
| First Paint | <2s | Lazy components, deferred imports |

**NO WORKER** a menos que supere 200 nodos AND se detecte lag (medible con `requestAnimationFrame` timing).

---

## ✅ VALIDACIÓN CHECKLIST (FASE 5)

```
[✅] NO se modificó OPERATOR_VX11_V8_CANONICAL.md
[✅] TODO acceso a módulos via Tentáculo Link (no directo)
[✅] Throttling por visibilidad (Page Visibility API)
[✅] Cache con TTL 5min, max 5 snapshots
[✅] WS Fallback en 5s si no llega evento
[✅] Lazy load Timeline (100 items iniciales)
[✅] Bookmarks en localStorage/IndexedDB (sin backend)
[✅] TypeScript check: npm run type-check sin errores
[✅] No polling agresivo (WS primero, fallback lento)
```

---

## 📌 ARCHIVOS CREADOS / MODIFICADOS

### Creados
- `operator/src/components/Dashboard/SystemTensionWidget.tsx`
- `operator/src/components/ForensicTimeline/index.tsx`
- `operator/src/components/Hormiguero/LevelSelector.tsx`
- `operator/src/components/ChatMadre/StructuredExplanation.tsx`
- `operator/src/hooks/useBookmarks.ts`
- `operator/src/types/v8_1_extensions.ts` (tipos nuevos)

### Modificados (Mínimo)
- `operator/src/components/Dashboard/index.tsx` — import SystemTensionWidget
- `operator_backend/backend/main_v7.py` — stub comentario (sin lógica)
- `tentaculo_link/main_v7.py` — ConnectionManager.broadcast() stub

### NO Modificados
- `/docs/OPERATOR_VX11_V8_CANONICAL.md` (INTACTO)
- `docker-compose.yml`
- `tokens.env`
- Módulos (madre, switch, hermes, etc.)

---

## 🚀 PRÓXIMOS PASOS (FUTURO)

1. **Integración Madre:** Cuando Madre emita `madre.explanation_structured`, StructuredExplanation renderizará decision_tree.
2. **Snapshot Backend:** Cuando BD tenga snapshots, endpoint `/operator/snapshot?t={ts}` los servirá.
3. **Correlación Activa:** Si Switch emite `system.correlation_update`, Timeline grafo se actualizará automáticamente.
4. **WebSocket Real:** Reemplazar echo loop con conexión bidireccional a Tentáculo Link.

---

**Versión:** 8.1 — Approved for low-consumption implementation  
**Date:** 2025-12-13  
**Status:** UI + Stubs Ready, Backend When Available
