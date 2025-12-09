# OPERATOR v6.4 - DIAGRAMA DE ARQUITECTURA Y FLUJOS

**Documento complementario a: `OPERATOR_AUDIT_v6_4.md`**  
Contiene diagramas Mermaid, matrices de decisión y visualización de flujos tentaculares.

---

## 📐 DIAGRAMA 1: ARQUITECTURA ACTUAL vs REQUERIDA

### ACTUAL (Estado real hoy)

```mermaid
graph TB
    User["👤 User/Client"]
    Op["🎛️ Operator Backend<br/>(FastAPI 8011)"]
    TL["🐙 Tentáculo Link<br/>(8000)"]
    
    Switch["🔀 Switch<br/>(8002)"]
    Hermes["📚 Hermes<br/>(8003)"]
    Shub["🎵 Shub<br/>(8007)"]
    Manifest["🎯 Manifestator<br/>(8005)"]
    
    Madre["👑 Madre<br/>(8001)"]
    Spawner["👶 Spawner<br/>(8008)"]
    MCP["⚙️ MCP<br/>(8006)"]
    Hormiguero["🐜 Hormiguero<br/>(8004)"]
    
    FE["🖥️ Frontend React<br/>(Vite)"]
    
    User -->|REST/WS| Op
    Op -->|WebSocket Bridge| TL
    Op -->|ClientHTTP| Switch
    Op -->|ClientHTTP| Hermes
    Op -->|ClientHTTP| Shub
    Op -->|ClientHTTP| Manifest
    
    TL -->|Proxy| Switch
    TL -->|Proxy| Madre
    TL -->|Proxy| Spawner
    TL -->|Proxy| MCP
    TL -->|Proxy| Hormiguero
    
    FE -->|fetch /system/status| Op
    FE -->|WebSocket /ws| Op
    
    style Op fill:#4CAF50,stroke:#2E7D32,color:#fff
    style TL fill:#FF9800,stroke:#E65100,color:#fff
    style Switch fill:#2196F3,stroke:#0D47A1,color:#fff
    style Madre fill:#9C27B0,stroke:#4A148C,color:#fff
    style FE fill:#607D8B,stroke:#37474F,color:#fff
```

### REQUERIDA (v6.4 completo)

```mermaid
graph TB
    User["👤 User/Client"]
    Op["🎛️ Operator Backend<br/>(FastAPI 8011)"]
    TL["🐙 Tentáculo Link<br/>(8000)"]
    
    Madre["👑 Madre<br/>(8001)<br/>Plans|Feedback"]
    Switch["🔀 Switch<br/>(8002)<br/>Queue|Models"]
    Hermes["📚 Hermes<br/>(8003)<br/>Registry|CLI"]
    Hormiguero["🐜 Hormiguero<br/>(8004)<br/>Reina|Tasks"]
    Manifest["🎯 Manifestator<br/>(8005)"]
    MCP["⚙️ MCP<br/>(8006)<br/>Sandbox|Audit"]
    Shub["🎵 Shub<br/>(8007)"]
    Spawner["👶 Spawner<br/>(8008)<br/>Hijas|TTL"]
    
    FE["🖥️ Frontend React<br/>(Vite)"]
    
    DB["💾 BD Unificada<br/>(vx11.db)<br/>Plans|Tasks|Spawns"]
    
    User -->|REST/WS| Op
    Op -->|WebSocket Bridge| TL
    Op -->|MadreClient| Madre
    Op -->|SwitchClient| Switch
    Op -->|HermesClient| Hermes
    Op -->|HormigueroClient| Hormiguero
    Op -->|ManifestatorClient| Manifest
    Op -->|MCPClient| MCP
    Op -->|ShubClient| Shub
    Op -->|SpawnerClient| Spawner
    
    Madre -->|Store Plan| DB
    Switch -->|Store Queue| DB
    Spawner -->|Store Hija| DB
    MCP -->|Audit Log| DB
    
    TL -->|Broadcast Events| Op
    Op -->|WebSocket Events| FE
    FE -->|Dashboard Panels| User
    
    style Op fill:#4CAF50,stroke:#2E7D32,color:#fff
    style TL fill:#FF9800,stroke:#E65100,color:#fff
    style Madre fill:#9C27B0,stroke:#4A148C,color:#fff
    style Switch fill:#2196F3,stroke:#0D47A1,color:#fff
    style Spawner fill:#E91E63,stroke:#880E4F,color:#fff
    style MCP fill:#00BCD4,stroke:#006064,color:#fff
    style DB fill:#FFC107,stroke:#F57F17,color:#000
    style FE fill:#607D8B,stroke:#37474F,color:#fff
```

---

## 🔄 DIAGRAMA 2: FLUJO ORQUESTACIÓN COMPLETO

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant Op as Operator
    participant TL as Tentáculo
    participant Madre as Madre
    participant Switch as Switch
    participant Spawner as Spawner
    
    U->>FE: "Validar sistema"
    FE->>Op: POST /intent/chat {msg}
    Op->>Switch: SwitchClient.chat()
    Switch->>Switch: select_model()
    Switch-->>Op: {model, reply}
    
    Op->>Madre: MadreClient.orchestrate()
    Note over Madre: Plan creation
    Madre->>DB: Store Plan
    Madre->>Op: {plan_id, feedback}
    
    Op->>Switch: POST /switch/queue
    Note over Switch: Enqueue task
    Switch->>DB: Update queue
    
    Op->>Spawner: SpawnerClient.spawn()
    Note over Spawner: Create hija
    Spawner->>Spawner: fork process
    Spawner->>DB: Register hija
    
    Spawner-->>Op: {spawn_id, pid}
    Op->>TL: POST /events/ingest
    TL->>FE: WebSocket broadcast
    FE->>FE: render SpawnerPanel
    FE->>U: Show hija running
    
    Note over Spawner: Process runs...
    Spawner->>DB: Update TTL
    
    par Monitor
        Op->>Spawner: GET /spawns/{id}/status
        Op->>Switch: GET /queue/status
        Op->>Madre: GET /plans/{id}
    end
    
    Spawner->>Spawner: Complete
    Spawner->>DB: Mark hija done
    Op->>TL: Event: spawn_complete
    TL->>FE: WebSocket broadcast
    FE->>U: Hija completed
```

---

## 📊 DIAGRAMA 3: ESTADO DE COMPONENTES UI

```mermaid
graph LR
    App["App.tsx<br/>(root)"]
    
    SB["StatusBar ✅<br/>(health indicators)"]
    DB["Dashboard ✅<br/>(modules grid)"]
    CP["ChatPanel ✅<br/>(switch interface)"]
    SP["ShubPanel ❌<br/>(placeholder)"]
    
    MP["MadrePanel ❌<br/>(NEW: planes)"]
    HiP["SpawnerPanel ❌<br/>(NEW: hijas)"]
    QP["SwitchQueuePanel ❌<br/>(NEW: queue)"]
    HP["HermesPanel ❌<br/>(NEW: models)"]
    AP["MCPPanel ❌<br/>(NEW: audit)"]
    TP["HormigueroPanel ❌<br/>(NEW: tasks)"]
    MmP["MiniMapPanel ❌<br/>(NEW: overview)"]
    LP["LogsPanel ❌<br/>(NEW: streaming)"]
    
    App --> SB
    App --> DB
    App --> CP
    App --> SP
    
    App -.-> MP
    App -.-> HiP
    App -.-> QP
    App -.-> HP
    App -.-> AP
    App -.-> TP
    App -.-> MmP
    App -.-> LP
    
    style App fill:#4CAF50
    style SB fill:#2196F3
    style DB fill:#2196F3
    style CP fill:#2196F3
    style SP fill:#FF5722
    
    style MP fill:#FFC107,stroke:#dashed
    style HiP fill:#FFC107,stroke:#dashed
    style QP fill:#FFC107,stroke:#dashed
    style HP fill:#FFC107,stroke:#dashed
    style AP fill:#FFC107,stroke:#dashed
    style TP fill:#FFC107,stroke:#dashed
    style MmP fill:#FFC107,stroke:#dashed
    style LP fill:#FFC107,stroke:#dashed
```

---

## 🔌 DIAGRAMA 4: ENDPOINTS REQUIRED BY COMPONENT

### MadrePanel Requires

```
GET /plans                    → [{ plan_id, prompt, status, feedback, delegations }]
GET /plans/{plan_id}          → { plan_id, full_detail, steps, results }
POST /plans/{plan_id}/execute → { status: "accepted" }
```

### SpawnerPanel Requires

```
GET /spawns                   → [{ spawn_id, status, pid, memory, cpu, ttl }]
GET /spawns/{id}              → { spawn_id, cmd, status, metrics, logs_tail }
GET /spawns/{id}/logs         → WebSocket stream of stdout/stderr
POST /spawns/{id}/kill        → { status: "terminated" }
GET /spawns/{id}/metrics      → { cpu_percent, memory_mb, uptime_s }
```

### SwitchQueuePanel Requires

```
GET /queue/status             → { size, active_model, mode, next_tasks }
GET /queue/next               → [{ task_id, priority, source, prompt_preview }]
POST /queue/preload/{model}   → { status: "preloading" }
GET /models/active            → { name, memory_mb, loaded_at }
```

### HermesPanel Requires

```
GET /models                   → { local: [...], registry: [...], cli: [...] }
GET /models/local             → [{ name, size_gb, location, loaded }]
GET /models/registry          → [{ name, source, size_gb, available }]
POST /models/download/{name}  → { status: "downloading", progress }
GET /models/{name}/usage      → { memory_mb, last_used, usage_count }
```

### MCPPanel Requires

```
GET /audit/executions         → [{ exec_id, timestamp, status, duration, output }]
GET /audit/violations         → [{ exec_id, violation_type, code_snippet }]
GET /audit/stats              → { total, violations, avg_time_ms, security_score }
GET /audit/executions/{id}    → { full_details, code, imports, audit_log }
```

### HormigueroPanel Requires

```
GET /tasks                    → { pending: [...], in_progress: [...], completed: [...] }
GET /tasks/pending            → [{ task_id, description, classification, priority }]
GET /tasks/{id}               → { task_id, classification, progress_pct, queen_info }
POST /tasks/{id}/priority     → { status: "reprioritized" }
```

---

## 🎯 DIAGRAMA 5: MATRIZ DE IMPLEMENTACIÓN

```mermaid
gantt
    title Operator v6.4 Implementation Roadmap
    dateFormat YYYY-MM-DD
    
    section Tier 1 (Critical)
    MadreClient:m1, 2025-12-04, 2d
    SpawnerClient:m2, 2025-12-04, 2d
    Endpoints /plans:m3, after m1, 2d
    Endpoints /spawns:m4, after m2, 2d
    MadrePanel:m5, after m3, 3d
    SpawnerPanel:m6, after m4, 3d
    SwitchQueuePanel:m7, 2025-12-04, 2d
    
    section Tier 2 (Major)
    HermesPanel:m8, after m7, 2d
    MCPPanel:m9, after m8, 2d
    HormigueroPanel:m10, after m9, 2d
    WebSocket Channels:m11, 2025-12-09, 2d
    JobQueue→BD:m12, 2025-12-09, 1d
    
    section Tier 3 (Polish)
    Collapsibles:m13, after m12, 1d
    Dark Mode:m14, after m13, 1d
    Minimapa:m15, after m14, 2d
```

---

## 💾 DIAGRAMA 6: DATABASE SCHEMA REFERENCE

```mermaid
erDiagram
    PLANS ||--o{ TASKS : contains
    TASKS ||--o{ SPAWNS : creates
    SPAWNS ||--o{ SPAWN_OUTPUT : generates
    TASKS ||--o{ CONTEXT : uses
    SANDBOX_EXEC ||--o{ AUDIT_LOGS : creates
    TASK_QUEUE ||--|| SWITCH_MODELS : references
    
    PLANS {
        string plan_id PK
        string prompt
        string status
        json feedback
        json delegations
        timestamp created_at
    }
    
    TASKS {
        string task_id PK
        string plan_id FK
        string classification
        string priority
        float progress_percent
        timestamp created_at
        timestamp completed_at
    }
    
    SPAWNS {
        string spawn_id PK
        string task_id FK
        int pid
        string status
        float memory_mb
        float cpu_percent
        int ttl_seconds
        timestamp started_at
    }
    
    SPAWN_OUTPUT {
        string output_id PK
        string spawn_id FK
        string stream_type
        text content
        timestamp logged_at
    }
    
    SANDBOX_EXEC {
        string exec_id PK
        string code_hash
        string status
        int duration_ms
        json imports
        text output
        timestamp executed_at
    }
    
    AUDIT_LOGS {
        string audit_id PK
        string exec_id FK
        string violation_type
        text details
        timestamp recorded_at
    }
    
    TASK_QUEUE {
        string queue_id PK
        string task_id FK
        int priority
        timestamp enqueued_at
        timestamp dequeued_at
    }
    
    SWITCH_MODELS {
        string model_id PK
        string name
        int memory_mb
        timestamp activated_at
    }
```

---

## 🎨 DIAGRAMA 7: LAYOUT SUGERIDO (MOCKUP ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ OPERATOR v6.4 Dashboard                                    [≡] [🌙] [⚙️]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🟢 Connected | Health: 9/9 ✓ | CPU: 35% | Mem: 2.3/8.0 GB | Uptime: 12:34 │
├─────────────────────────────────────────────────────────────────────────────┤
│ [📋 Plans] [👶 Hijas] [🔀 Queue] [📚 Models] [🔐 Audit] [🐜 Tasks] [🗺️ Map]│
├──────────────────────────────────────┬──────────────────────────────────────┤
│                                      │                                      │
│ 📋 PLANES (Madre)                    │ 👶 HIJAS (Spawner)                   │
│ ┌────────────────────────────────┐   │ ┌────────────────────────────────┐   │
│ │ Plan #1: Validar sistema       │   │ │ [▶] validate.py (pid=1234)     │   │
│ │ Status: executing ▓▓▓░░░░░░░░ │   │ │ CPU: 45% | Mem: 128MB | TTL: 47s│   │
│ │ Feedback: deepseek             │   │ │ [logs] [kill]                   │   │
│ │ Delegations:                   │   │ │                                 │   │
│ │ ├─ [✓] switch (route_v5)       │   │ │ [■] cleanup.py (pid=5678)      │   │
│ │ ├─ [▶] hermes (search)         │   │ │ CPU: 0% | Mem: 64MB | TTL: 120s│   │
│ │ └─ [○] spawner (spawn)         │   │ │ [logs] [kill]                   │   │
│ │                                │   │ │                                 │   │
│ │ [▶] Execute | [📋] Copy ID     │   │ │ [✓] analyze.py (pid=9999)      │   │
│ └────────────────────────────────┘   │ │ Completed 2 minutes ago         │   │
│                                      │ │ [view output]                   │   │
│ 🔀 QUEUE (Switch)                    │ └────────────────────────────────┘   │
│ ┌────────────────────────────────┐   │                                      │
│ │ Active Model: deepseek-r1      │   │ 📚 MODELS (Hermes)                   │
│ │ Memory: ▓▓▓▓▓░░░░░ 5/8 GB      │   │ ┌────────────────────────────────┐   │
│ │ Queue: ▓▓▓░░░░░░░ 12 tasks     │   │ Local (loaded):                 │   │
│ │ Mode: [ECO] BALANCED HIGH-PERF │   │ • mistral-7b [4.2GB] ✓          │   │
│ │                                │   │ • llama-13b [6.0GB] ✓           │   │
│ │ Next tasks:                    │   │ Registry (available):           │   │
│ │ 1. [⚡] shub: audio_track_03   │   │ • deepseek-r1 [7.0GB]           │   │
│ │    est. 2s                     │   │ • mixtral-8x7b [26GB]           │   │
│ │ 2. [⚙️] operator: validate     │   │ [↓ Download] [✕ Unload]         │   │
│ │    est. 5s                     │   │ └────────────────────────────────┘   │
│ │                                │   │                                      │
│ │ [🔄 Reload] [⚙️ Set Model]     │   │ 🔐 AUDIT (MCP)                      │
│ └────────────────────────────────┘   │ ┌────────────────────────────────┐   │
│                                      │ │ Executions: 1024                │   │
│ 📝 LOGS (Streaming)                  │ │ Violations: 3 (violations only) │   │
│ ┌────────────────────────────────┐   │ │ Avg time: 156ms                 │   │
│ │ [INFO]  Madre: plan_created    │   │ │ Security: ★★★★★ 98%           │   │
│ │ [WARN]  Switch: model_loading  │   │ │ Last exec: sha256-abc...        │   │
│ │ [INFO]  Hermes: download_ok    │   │ │ [🔍 Details] [📥 Export]       │   │
│ │ [DEBUG] Spawner: hija_ttl=300  │   │ │ [⚠️ Violations]                 │   │
│ │ [ERROR] MCP: forbidden_import   │   │ └────────────────────────────────┘   │
│ └────────────────────────────────┘   │                                      │
│ [🔍 Filter] [📥 Export]              │ 🐜 TASKS (Hormiguero)                │
│                                      │ ┌────────────────────────────────┐   │
└──────────────────────────────────────┼──────────────────────────────────────┤
│ 🗺️ MINIMAPA (Sistema)                │ Pending: 5 | Running: 3 | Done: 127 │
│ ┌──────────────────────────────────┐ │ [validation] [processing] [done]    │
│ │ ┌─────────┬─────────┬─────────┐  │ │ Reina Classification: enabled       │
│ │ │ Tentác. │ Madre   │ Hormig. │  │ │ Last activity: 2 minutes ago        │
│ │ │ 🟢      │ 🟢      │ 🟢      │  │ │ [↑ Priority] [View Timeline]        │
│ │ ├─────────┼─────────┼─────────┤  │ └────────────────────────────────────┘
│ │ │ Switch  │ Hermes  │ Shub    │  │
│ │ │ 🟢      │ 🟢      │ 🟢      │  │
│ │ ├─────────┼─────────┼─────────┤  │
│ │ │ Spawner │ MCP     │ OperatrI │  │
│ │ │ 🟢      │ 🟡      │ 🟢      │  │
│ │ └─────────┴─────────┴─────────┘  │
│ │ 🟢=ok 🟡=slow 🔴=down            │
│ └──────────────────────────────────┘
│ [💾 Save Layout] [📂 Load Preset] [🌙 Toggle Dark]
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔌 DIAGRAMA 8: WEBSOCKET CHANNEL HIERARCHY

```
WebSocket (/ws)
│
├── system
│   ├── status_update         {modules_health, timestamp}
│   ├── error                 {module, error_msg}
│   └── shutdown              {}
│
├── operator
│   ├── intent_parsed         {intent_type, confidence}
│   ├── job_queued            {job_id, intent}
│   └── job_status            {job_id, status}
│
├── madre
│   ├── plan_created          {plan_id, prompt, feedback}
│   ├── plan_updated          {plan_id, status}
│   ├── delegation_sent        {plan_id, target, action}
│   └── plan_completed        {plan_id, result}
│
├── switch
│   ├── task_queued           {task_id, priority, queue_size}
│   ├── model_switched        {model_name, memory_mb}
│   ├── model_preloading      {model_name, progress}
│   └── response_ready        {task_id, reply}
│
├── spawner
│   ├── spawn_created         {spawn_id, pid, cmd}
│   ├── spawn_status          {spawn_id, status, cpu, memory}
│   ├── spawn_output          {spawn_id, stream_type, data}
│   └── spawn_completed       {spawn_id, exit_code}
│
├── hermes
│   ├── model_download_start  {model_name, size_gb}
│   ├── model_download_progress {model_name, progress_pct}
│   ├── model_loaded          {model_name, memory_mb}
│   └── cli_command_executed  {cmd, result}
│
├── mcp
│   ├── sandbox_exec          {exec_id, code_hash, result}
│   ├── violation_detected    {exec_id, violation_type}
│   └── audit_log_entry       {audit_id, details}
│
└── hormiguero
    ├── task_created          {task_id, classification}
    ├── task_prioritized      {task_id, priority}
    ├── task_completed        {task_id, result}
    └── queen_decision        {task_id, classification_reason}
```

---

## 📊 DIAGRAMA 9: ESTADO DE INTEGRACIÓN POR MÓDULO

```mermaid
graph TB
    Op["Operator"]
    
    Op -->|✅ Implementado| TL["Tentáculo Link"]
    Op -->|✅ Implementado| Switch["Switch"]
    Op -->|✅ Implementado| Shub["Shub"]
    Op -->|✅ Implementado| Hermes["Hermes"]
    Op -->|✅ Implementado| Manifest["Manifestator"]
    
    Op -->|⚠️ Parcial| MCP["MCP<br/>(auditoría sin exponer)"]
    Op -->|❌ No integrado| Madre["Madre<br/>(planes ocultos)"]
    Op -->|❌ No integrado| Spawner["Spawner<br/>(hijas invisibles)"]
    Op -->|❌ No integrado| Hormiguero["Hormiguero<br/>(tareas sin ui)"]
    
    style Op fill:#4CAF50,stroke:#2E7D32,color:#fff
    style TL fill:#2196F3
    style Switch fill:#2196F3
    style Shub fill:#2196F3
    style Hermes fill:#2196F3
    style Manifest fill:#2196F3
    style MCP fill:#FFC107
    style Madre fill:#FF5722
    style Spawner fill:#FF5722
    style Hormiguero fill:#FF5722
```

---

## 🎯 CONCLUSIÓN DEL DIAGRAMA

La arquitectura actual es **funcional pero esquelética**. Los diagramas muestran:

1. **Tier 1 (Crítico)**: Falta integración Madre, Spawner, visualización de cola
2. **Tier 2 (Mayor)**: Falta paneles Hermes, MCP, Hormiguero
3. **Tier 3 (Mejora)**: Falta UX avanzada (collapsibles, minimapa, dark mode)

**Próximo paso**: Implementar según roadmap en `OPERATOR_AUDIT_v6_4.md`.

