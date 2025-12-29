# VX11 Operator UI - PHASE 4 Data Flow Diagrams

## Complete Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VX11 OPERATOR UI DATA FLOW                          │
│                                                                             │
│  ENTRYPOINT: tentáculo_link:8000 (http://localhost:8000/operator/api/*)   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                │
│  React 18 + TypeScript + Tailwind CSS                                    │
└──────────────────────────────────────────────────────────────────────────┘
    ↓↑
    │ (relative URLs: /operator/api/*)
    ↓↑
┌──────────────────────────────────────────────────────────────────────────┐
│                          tentáculo_link:8000                             │
│  ├─ GET /operator/api/status                                             │
│  ├─ GET /operator/api/modules                                            │
│  ├─ GET /operator/api/metrics                                            │
│  ├─ GET /operator/api/events                                             │
│  ├─ GET /operator/api/events/stream (SSE)                                │
│  ├─ GET /operator/api/rails/lanes                                        │
│  ├─ GET /operator/api/rails/lane/{lane_id}                               │
│  └─ GET /operator/api/fs/list                                            │
└──────────────────────────────────────────────────────────────────────────┘
    ↓ (routes via gateway)
    ├─→ madre:8001        (orchestration, DB queries)
    ├─→ switch:8002       (routing/engine selection)
    ├─→ redis:6379        (caching, pub/sub)
    ├─→ hormiguero:8004   (drift detection)
    ├─→ manifestator:8005 (lane validation)
    └─→ operator-backend:8011 (this API)
```

---

## Panel-by-Panel Data Flow

### 1️⃣ WindowStatusBar Data Flow

```
┌─────────────────────────────────────────────┐
│ App.tsx: useWindowStatus() hook             │
│ (Poll interval: 5 seconds)                  │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ GET /operator/api/status                    │
│ Response: {                                 │
│   ok: true,                                 │
│   data: {                                   │
│     mode: "solo_madre"|"window_active",    │
│     ttl_remaining_ms: number|null,         │
│     health: "ok"|"degraded"|"offline",     │
│     request_id: "req-abc123",              │
│     route_taken: "madre→redis→..."         │
│   }                                         │
│ }                                           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ OperatorStore.updateFromStatus(data)        │
│ Updates:                                    │
│ - mode                                      │
│ - ttl_remaining_ms                          │
│ - health                                    │
│ - request_id                                │
│ - route_taken                               │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Components re-render with new state:        │
│ ├─ <ModeIndicator mode={mode} />           │
│ ├─ <HealthStatus health={health} />        │
│ ├─ <TTLCountdown ms={ttl_remaining_ms} />  │
│ └─ <RequestMetadata id={request_id} />     │
└─────────────────────────────────────────────┘
    ↓ (5 second tick)
    ↻ Repeat poll
```

---

### 2️⃣ OverviewPanel Data Flow (Initial Load)

```
┌──────────────────────────────────────┐
│ OverviewPanel: useEffect on mount    │
└──────────────────────────────────────┘
    ↓
    ├─→ Promise.all([
    │   GET /operator/api/modules,
    │   GET /operator/api/metrics,
    │   GET /operator/api/events?limit=10,
    │   GET /operator/api/rails/lanes?limit=5
    │ ])
    │
    ├─→ Response 1: ServiceHealth[]
    │   └─→ OverviewStore.modules = [madre, redis, tentáculo, switch, ...]
    │       └─→ <ModuleHealthGrid modules={modules} />
    │
    ├─→ Response 2: MetricsSnapshot
    │   └─→ OverviewStore.metrics_snapshot = {cpu, memory, db_size, error_rate}
    │       └─→ Display in SystemHealthCard
    │
    ├─→ Response 3: Event[]
    │   └─→ OverviewStore.recent_events = [last 10 events]
    │       └─→ <RecentEventsPreview events={recent_events} />
    │
    └─→ Response 4: Lane[]
        └─→ OverviewStore.active_lanes = 12
            └─→ <LanesPreview lanes={active_lanes} />

┌──────────────────────────────────────┐
│ Poll every 10 seconds               │
└──────────────────────────────────────┘
    ↓
    └─→ setInterval(() => loadData(), 10000)
```

---

### 3️⃣ EventsPanel Real-Time Data Flow ⭐

```
┌───────────────────────────────────────────────┐
│ EventsPanel: useEventStream() hook on mount  │
└───────────────────────────────────────────────┘
    ↓
    ├─→ Try: new EventSource('/operator/api/events/stream')
    │   ↓ SUCCESS (SSE available)
    │   │
    │   ├─→ eventSource.addEventListener('event', (e) => {
    │   │   const event = JSON.parse(e.data);
    │   │   EventsStore.addEvent(event);  ← New event added to store
    │   │ })
    │   │
    │   └─→ Components re-render instantly
    │       ├─ New event appears at top of table
    │       ├─ Flash animation (pulse)
    │       └─ Auto-scroll to top (optional)
    │
    └─→ CATCH / Error → Fall back to polling
        ├─→ poll() {
        │   GET /operator/api/events?limit=50
        │   Response: Event[]
        │   └─→ EventsStore.setEvents(events)
        │       └─→ <EventTable events={events} /> re-renders
        │ }
        │
        └─→ setInterval(poll, 5000)  ← Poll every 5s

┌─────────────────────────────────────────────────┐
│ User filters (severity, module, time-range):   │
└─────────────────────────────────────────────────┘
    ↓
    EventsStore.setSeverityFilter(['critical', 'error'])
    EventsStore.setModuleFilter(['madre', 'switch'])
    EventsStore.setTimeRange(from, to)
    ↓
    Local filtering (NO API CALL):
    filtered = events.filter(e =>
      filters.severity.includes(e.severity) &&
      filters.modules.includes(e.module) &&
      e.timestamp >= filters.time_range.from &&
      e.timestamp <= filters.time_range.to
    )
    ↓
    <EventTable events={filtered} />  ← Only filtered events rendered
```

---

### 4️⃣ MetricsPanel Data Flow

```
┌────────────────────────────────────────┐
│ MetricsPanel: useEffect on time window │
│ or metric selection change             │
└────────────────────────────────────────┘
    ↓
    MetricsStore.setTimeWindow('24h')  ← User selects time window
    MetricsStore.setSelectedMetrics(['cpu', 'memory'])
    MetricsStore.setAggregation('avg')
    ↓
    GET /operator/api/metrics?
        window=24h&
        metrics=cpu_utilization,memory_usage&
        aggregation=avg
    ↓
    Response: Datapoint[] [
      { timestamp: "2025-12-29T14:00:00Z", metric_name: "cpu", value: 45.2 },
      { timestamp: "2025-12-29T14:00:00Z", metric_name: "memory", value: 2048 },
      { timestamp: "2025-12-29T14:05:00Z", metric_name: "cpu", value: 48.1 },
      ...
    ]
    ↓
    MetricsStore.datapoints = [...]
    ↓
    Transform for Recharts:
    [
      { timestamp: "...", cpu: 45.2, memory: 2048 },
      { timestamp: "...", cpu: 48.1, memory: 2105 },
      ...
    ]
    ↓
    <LineChart data={chartData}>
      <Line dataKey="cpu" stroke="#06b6d4" />
      <Line dataKey="memory" stroke="#f59e0b" />
    </LineChart>
    ↓
    User clicks Export → Generate JSON/CSV
    download(datapoints.toJSON(), 'metrics.json')
```

---

### 5️⃣ RailsPanel Data Flow

```
┌──────────────────────────────────────┐
│ RailsPanel: useEffect on mount       │
│ Poll interval: 10 seconds            │
└──────────────────────────────────────┘
    ↓
    GET /operator/api/rails/lanes
    ↓
    Response: Lane[] [
      {
        lane_id: "lane-001",
        stage: "detect",
        status: "in_progress",
        severity: "warn",
        check_count: 5,
        checks_passed: 3,
        created_at: "2025-12-29T14:00:00Z"
      },
      ...
    ]
    ↓
    RailsStore.lanes = [...]
    ↓
    <RailsGrid lanes={lanes} />
    ├─ <StageColumn stage="detect">
    │  └─ <LaneCard lane={lane} onClick={selectLane} />
    │     ├─ Lane ID
    │     ├─ Status badge
    │     ├─ Progress bar (3/5 checks)
    │     └─ Severity indicator
    │
    ├─ <StageColumn stage="plan"> ...
    ├─ <StageColumn stage="validate"> ...
    └─ <StageColumn stage="apply"> ...

┌──────────────────────────────────────┐
│ User clicks on lane:                 │
│ RailsStore.selectLane('lane-001')    │
└──────────────────────────────────────┘
    ↓
    GET /operator/api/rails/lane/lane-001
    ↓
    Response: LaneDetails {
      lane_id: "lane-001",
      stage: "detect",
      history: [
        { from: "detect", to: "plan", duration_ms: 1234 },
        ...
      ],
      checks: [
        { check_id: "...", name: "...", status: "passed", duration_ms: 100 },
        ...
      ],
      audit_findings: [
        { severity: "warn", category: "performance", message: "..." },
        ...
      ],
      related_events: [Event[], ...]
    }
    ↓
    RailsStore.lane_details = {...}
    ↓
    <LaneDetail lane_details={lane_details} />
    ├─ Timeline (detect → plan → validate → apply)
    ├─ ChecksList (with status + duration)
    ├─ AuditFindingsList (severity-coded)
    └─ RelatedEvents (linked by correlation_id)
```

---

### 6️⃣ FileExplorerPanel Data Flow

```
┌──────────────────────────────────────┐
│ FileExplorerPanel: useEffect on mount│
│ Initial path: /docs/audit            │
└──────────────────────────────────────┘
    ↓
    GET /operator/api/fs/list?path=/docs/audit
    ↓
    Response: {
      ok: true,
      data: {
        path: "/home/elkakas314/vx11/docs/audit",
        contents: [
          { name: "DB_MAP_v7_FINAL.md", type: "file", size: 102400, modified: "..." },
          { name: "codex_canonical_closure_20251218T223452Z", type: "directory", modified: "..." },
          ...
        ],
        total_items: 23
      }
    }
    ↓
    FileExplorerStore.contents = [...]
    FileExplorerStore.breadcrumb = ["", "docs", "audit"]
    ↓
    <FileExplorerBreadcrumb breadcrumb={breadcrumb} />
    ├─ / (clickable → navigate to root)
    ├─ docs (clickable → navigate to /docs)
    └─ audit (current location)
    ↓
    <ExplorerFileBrowser contents={contents} />
    ├─ DirectoryRow (name="codex_canonical_closure_20251218T223452Z")
    │  └─ onClick → navigate to that directory
    │
    ├─ FileRow (name="DB_MAP_v7_FINAL.md", size="100 KB")
    │  └─ Right-click → Copy path
    │
    └─ ExplorerMetadata
       ├─ Item count: 23
       ├─ Total size: 1.2 GB
       └─ Last refresh: 2 seconds ago

┌──────────────────────────────────────┐
│ User double-clicks directory:        │
│ FileExplorerStore.navigate(path)     │
└──────────────────────────────────────┘
    ↓
    GET /operator/api/fs/list?path=/docs/audit/codex_canonical_closure_20251218T223452Z
    ↓
    Response: new directory contents
    ↓
    FileExplorerStore.contents = [...]
    FileExplorerStore.breadcrumb = ["", "docs", "audit", "codex_canonical_closure_20251218T223452Z"]
    ↓
    <FileExplorerPanel />  ← Re-renders with new path/contents
```

---

## Global State Updates

### Zustand Store Relationships

```
┌─────────────────────────────────────────────────────┐
│              ZUSTAND STORES                         │
│         (All stores in /stores/...)                 │
└─────────────────────────────────────────────────────┘

┌─────────────────────────┐
│  OperatorStore (Global) │  ← Updates from polling /api/status
│                         │
│  - mode                 │
│  - ttl_remaining_ms     │
│  - health               │
│  - request_id           │
│  - route_taken          │
│  - last_updated         │
└─────────────────────────┘
    ↑ (used by)
    │
    ├─ <WindowStatusBar /> (displays mode, health, ttl)
    ├─ All panels check mode (to show degraded state)
    └─ <DegradedModeBanner /> (show if mode !== 'full')


┌────────────────────────┐    ┌────────────────────────┐
│ OverviewStore          │    │ EventsStore            │
│                        │    │                        │
│ - modules[]            │    │ - events[]             │
│ - metrics_snapshot     │    │ - filters              │
│ - recent_events[]      │    │ - is_streaming         │
│ - active_lanes         │    │ - loading              │
│ - loading              │    │                        │
└────────────────────────┘    └────────────────────────┘
    ↑                             ↑
    └─ OverviewPanel              └─ EventsPanel


┌────────────────────────┐    ┌────────────────────────┐
│ MetricsStore           │    │ RailsStore             │
│                        │    │                        │
│ - datapoints[]         │    │ - lanes[]              │
│ - time_window          │    │ - selected_lane_id     │
│ - selected_metrics[]   │    │ - lane_details         │
│ - aggregation          │    │ - loading              │
│ - loading              │    │                        │
└────────────────────────┘    └────────────────────────┘
    ↑                             ↑
    └─ MetricsPanel              └─ RailsPanel


┌────────────────────────┐
│ FileExplorerStore      │
│                        │
│ - current_path         │
│ - contents[]           │
│ - breadcrumb[]         │
│ - search_query         │
│ - loading              │
└────────────────────────┘
    ↑
    └─ FileExplorerPanel
```

---

## Error Handling Data Flow

```
┌─────────────────────────┐
│ API Request             │
└─────────────────────────┘
    ↓
    ├─→ Success (200)
    │   ├─→ Parse response
    │   ├─→ Update store
    │   └─→ Component re-renders
    │
    ├─→ Auth Error (401)
    │   ├─→ Store.setError('Authentication expired')
    │   ├─→ <ErrorBanner /> displays
    │   └─→ Show refresh button
    │
    ├─→ Policy Blocked (409)
    │   ├─→ Store.setError('solo_madre policy active')
    │   ├─→ <DegradedModeBanner /> shows
    │   └─→ Disable non-core endpoints
    │
    ├─→ Timeout
    │   ├─→ Store.setError('Request timed out')
    │   ├─→ <Toast type="warning" />
    │   └─→ Retry with exponential backoff
    │
    └─→ Network Error
        ├─→ Store.setError('Network error')
        ├─→ <ErrorBoundary /> catches
        ├─→ <Toast type="error" />
        └─→ Fallback to cached data (React Query)
```

---

## Caching Strategy (React Query)

```
┌──────────────────────────────────────┐
│ useQuery({                           │
│   queryKey: ['events', filters],     │
│   queryFn: apiClient.events,         │
│   staleTime: 30000,       (30s)      │
│   cacheTime: 300000,      (5 min)    │
│   retry: 3,                          │
│   retryDelay: exponential backoff    │
│ })                                   │
└──────────────────────────────────────┘
    ↓
    ├─→ First request: CACHE_MISS
    │   └─→ Fetch from /api/events
    │       └─→ Cache result for 30s
    │
    ├─→ Second request (within 30s): CACHE_HIT
    │   └─→ Return cached data instantly
    │
    ├─→ Third request (after 30s): STALE
    │   └─→ Return stale data + refetch in background
    │
    ├─→ Fourth request (after 5 min): EXPIRED
    │   └─→ Fetch fresh data
    │       └─→ Update cache
    │
    └─→ On error:
        ├─→ Retry 1: 1s delay
        ├─→ Retry 2: 2s delay
        ├─→ Retry 3: 4s delay
        └─→ Finally: Return cached or error
```

---

## Performance Optimizations

```
┌─────────────────────────────────────────┐
│ Virtual Scrolling (react-window)       │
│ For EventsPanel with 1000+ events      │
└─────────────────────────────────────────┘
    ↓
    WITHOUT: 1000 EventRow components in DOM
    │ - Rendering: ~500ms
    │ - Memory: ~50MB
    │ - Scrolling: Janky (< 30 FPS)
    │
    WITH: Only ~50 visible rows in DOM
    │ - Rendering: ~50ms
    │ - Memory: ~2MB
    │ - Scrolling: Smooth (60 FPS)
    │
    └─ Scroll event → Calculate visible range → Update DOM


┌────────────────────────────────────────┐
│ React Query Background Refetching      │
│ For EventsPanel streaming              │
└────────────────────────────────────────┘
    ↓
    - Window focus → Auto-refetch
    - Interval refresh → Every 5s (if enabled)
    - Manual refetch on button click
    - Automatic retry on network error


┌────────────────────────────────────────┐
│ Code Splitting (Lazy Load Views)       │
└────────────────────────────────────────┘
    ↓
    const OverviewPanel = lazy(() => import('./panels/Overview'))
    const EventsPanel = lazy(() => import('./panels/Events'))
    │
    ├─ Initial bundle: ~80KB (core + LayoutWrapper)
    ├─ OverviewPanel: ~20KB (loaded on first tab click)
    ├─ EventsPanel: ~35KB (loaded on tab click)
    └─ MetricsPanel: ~28KB (loaded on tab click)
```

---

## Real-Time Update Example: New Event Arrives

```
┌────────────────────────────────────────────┐
│ SSE Server sends event                    │
│ data: {"id":"evt-123",...,"severity":...} │
└────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────┐
│ Browser receives SSE 'event'               │
│ eventSource.addEventListener('event', ...) │
└────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────┐
│ Parse JSON + create Event object           │
│ const event = JSON.parse(e.data)           │
└────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────┐
│ Update Zustand store                       │
│ EventsStore.addEvent(event)                │
│ ↓                                          │
│ events = [newEvent, ...oldEvents]          │
└────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────┐
│ Component subscribes to store               │
│ useEventsStore(s => s.events)              │
│ ↓                                          │
│ NEW RENDER with updated events[]           │
└────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────┐
│ Virtual list re-renders (only visible rows)│
│ New event flashes (pulse animation)        │
│ Auto-scroll to top (optional)               │
└────────────────────────────────────────────┘

Timeline: ~50-100ms from server → UI update
```

---

This diagram set shows how data flows through the entire system, from API requests to component rendering to caching and optimization. Each panel has a dedicated flow, and all flows respect the single entrypoint constraint (tentáculo_link:8000).

