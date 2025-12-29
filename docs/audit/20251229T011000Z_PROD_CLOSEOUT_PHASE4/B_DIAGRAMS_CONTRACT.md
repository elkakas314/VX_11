# VX11 — DIAGRAMAS CONTRATO (B) — ARQUITECTURA PRODUCCIÓN

---

## DIAGRAMA 1: Architecture Global (solo_madre policy)

```mermaid
graph TB
    User["👤 User (Browser)"]
    UI["🖥️ Operator UI<br/>operator/frontend<br/>PORT: 5173 (dev) | /operator/ui (prod)"]
    Proxy["🔗 Tentaculo Link<br/>Proxy + Gateway<br/>PORT: 8000"]
    Madre["👑 Madre<br/>Orchestration<br/>PORT: 8001"]
    Redis["🔴 Redis<br/>Cache/PubSub<br/>PORT: 6379"]
    DB["💾 SQLite<br/>data/runtime/vx11.db"]
    
    Switch["🔄 Switch<br/>(VENTANA TEMPORAL)<br/>PORT: 8002"]
    LocalLLM["💬 Local LLM<br/>Fallback<br/>(degraded)"]
    
    User -->|HTTP/WebSocket| UI
    UI -->|API calls| Proxy
    Proxy -->|relay| Madre
    Proxy -->|fallback| LocalLLM
    Madre -->|manage| Switch
    Madre <-->|state| Redis
    Madre <-->|audit| DB
    
    style Proxy fill:#0f0,stroke:#000,stroke-width:3px
    style Madre fill:#0f0,stroke:#000,stroke-width:2px
    style Redis fill:#0f0
    style Switch fill:#ff0,stroke:#f00,stroke-width:2px
    style LocalLLM fill:#0f0
```

---

## DIAGRAMA 2: Request Flow (Chat Endpoint)

```mermaid
sequenceDiagram
    participant UI as Operator UI
    participant TL as Tentaculo Link<br/>:8000
    participant M as Madre<br/>:8001
    participant SW as Switch<br/>:8002
    participant LLMF as LLM<br/>Fallback

    UI->>TL: POST /operator/api/chat<br/>(x-vx11-token header)
    TL->>TL: validate token + size
    TL->>M: check window?
    
    alt window_open (service=switch)
        M->>SW: route_to_switch
        SW-->>M: response (200)
        M-->>TL: {"route_taken":"switch"}
    else window_closed (solo_madre)
        M->>LLMF: degraded_fallback
        LLMF-->>M: response (200)
        M-->>TL: {"route_taken":"local_llm_degraded","degraded":true}
    end
    
    TL-->>UI: HTTP 200<br/>{"message_id","response","degraded"}
```

---

## DIAGRAMA 3: Single Entrypoint (Invariante A)

```mermaid
graph LR
    Internet["🌐 Internet<br/>(Clients)"]
    
    Internet -->|8000| TL["✅ SOLO Entrada<br/>Tentaculo Link<br/>:8000"]
    
    TL -->|forbidden| OB["❌ PROHIBIDO<br/>Operator Backend<br/>:8003"]
    TL -->|forbidden| SW["❌ PROHIBIDO<br/>Switch<br/>:8002"]
    TL -->|forbidden| M["❌ PROHIBIDO<br/>Madre (direct)<br/>:8001"]
    
    TL -->|allowed| Cache["✅ Internal:<br/>Redis<br/>:6379"]
    TL -->|allowed| BD["✅ Internal:<br/>SQLite"]
    
    style TL fill:#0f0,stroke:#000,stroke-width:3px
    style OB fill:#f00
    style SW fill:#f00
    style M fill:#f00
    style Cache fill:#0f0
    style BD fill:#0f0
```

---

## DIAGRAMA 4: Database Schema (71 tablas, integridad OK)

```mermaid
graph TB
    Core["📋 CORE TABLES<br/>—<br/>operator_message<br/>operator_session<br/>operator_tool_call<br/>—<br/>madre_policies<br/>madre_actions"]
    
    Audit["📊 AUDIT TABLES<br/>—<br/>audit_logs<br/>copilot_actions_log<br/>routing_events<br/>—<br/>power_events<br/>(ventanas)"]
    
    Domain["🔧 DOMAIN TABLES<br/>—<br/>incidents (1.1M rows)<br/>hijas_runtime<br/>tasks<br/>task_queue<br/>—<br/>canonical_*"]
    
    Utils["⚙️ UTILITY TABLES<br/>—<br/>module_health<br/>module_status<br/>system_state<br/>—<br/>models_local<br/>cli_registry"]
    
    DB["💾 SQLite vx11.db<br/>591 MB<br/>integrity=OK<br/>PRAGMA checks: 3/3 PASS"]
    
    Core --> DB
    Audit --> DB
    Domain --> DB
    Utils --> DB
    
    style DB fill:#0f0,stroke:#000,stroke-width:3px
```

---

## DIAGRAMA 5: Power Windows (Ventana Temporal)

```mermaid
graph LR
    Req["📥 Request<br/>/madre/power/window/open"]
    
    Req -->|validate| Policy{"Policy<br/>Check"}
    
    Policy -->|OK| Allowlist{"Allowlist<br/>Check"}
    Allowlist -->|✅ switch| Open["🟢 WINDOW OPEN<br/>deadline=now+TTL"]
    Allowlist -->|❌ invalid| Reject["❌ 422<br/>Rejected"]
    
    Open -->|docker compose start| Start["Start Services"]
    Start -->|TTL running| Monitor["⏱️ Monitor<br/>TTL expired?"]
    Monitor -->|YES| Close["🔴 AUTO CLOSE<br/>docker compose stop"]
    Monitor -->|NO| Monitor
    
    Close -->|stored| Events["📝 power_events<br/>log"]
    
    style Open fill:#0f0,stroke:#000,stroke-width:2px
    style Close fill:#f00,stroke:#000,stroke-width:2px
    style Reject fill:#f00
```

---

## DIAGRAMA 6: Invariantes (NO NEGOCIABLES)

```mermaid
graph TB
    I["INVARIANTES VX11<br/>(Non-negotiable Rails)"]
    
    I --> IA["A) Single Entrypoint<br/>tentaculo_link:8000 ONLY<br/>✅ Bypass prohibited"]
    I --> IB["B) Runtime solo_madre<br/>Default OFF, ventanas ON<br/>✅ Policy enforced"]
    I --> IC["C) Frontend Relativo<br/>No hardcodes<br/>✅ BASE_URL=''"]
    I --> ID["D) Chat Runtime<br/>Switch+CLI+fallback<br/>✅ Degraded always 200"]
    I --> IE["E) DeepSeek Construcción<br/>NO runtime dependency<br/>✅ Feature flag OFF"]
    I --> IF["F) Zero Secrets<br/>No tokens in repo<br/>✅ Secret scan clean"]
    I --> IG["G) Feature Flags OFF<br/>No auto-execute<br/>✅ Conservative default"]
    
    style I fill:#fff,stroke:#000,stroke-width:3px
    style IA fill:#0f0,stroke:#000
    style IB fill:#0f0,stroke:#000
    style IC fill:#0f0,stroke:#000
    style ID fill:#0f0,stroke:#000
    style IE fill:#0f0,stroke:#000
    style IF fill:#0f0,stroke:#000
    style IG fill:#0f0,stroke:#000
```

---

## DIAGRAMA 7: Ports Mapeados (solo_madre)

```
┌─────────────────────────────────────┐
│  VX11 SERVICIOS (solo_madre policy) │
├─────────────────────────────────────┤
│ ✅ Tentaculo Link   :8000 (UP)      │
│ ✅ Madre            :8001 (UP)      │
│ ✅ Redis            :6379 (UP)      │
│ ❌ Switch           :8002 (OFF)     │
│ ❌ Operator Backend :8003 (OFF)     │
│ ❌ Operator UI Dev  :5173 (OFF)     │
│ ❌ Hermes           :8004 (OFF)     │
│ ❌ Shubniggurath    :8005 (OFF)     │
└─────────────────────────────────────┘

Nota: Servicios OFF arrancan SOLO en ventanas temporales
```

---

## CONTRATO (Verificaciones Obligatorias)

1. **Arquitectura**: Single entrypoint ✅ (tentaculo only)
2. **Routing**: Chat siempre 200 (degraded fallback) ✅
3. **DB**: Integridad 3/3 PRAGMA checks ✅
4. **Seguridad**: 0 secrets + feature flags OFF ✅
5. **Ventanas**: open/close/TTL funcional ✅
6. **Tests**: 10/10 HTTP 200, degraded flag verificado ✅

---

**Generado**: 2025-12-29T01:10:00Z  
**Status**: ✅ DIAGRAMS CONTRACTE VERIFIED
