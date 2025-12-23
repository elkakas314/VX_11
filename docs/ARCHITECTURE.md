# VX11 Architecture
**Status:** Índice/Bridge Document | **Generated:** 2025-12-22T02:35:00Z

---

## 📚 Overview

VX11 es un orquestador de IA descentralizado con autonomía escalable. Esta página actúa como **índice centralizado** que apunta a documentación arquitectónica distribuida en el repositorio.

Para **mapeo exhaustivo de componentes**, consulta los documentos canónicos listados abajo.

---

## 🏛️ Documentación Arquitectónica Canónica

### Core Structure
- **[CANONICAL_CORE.md](CANONICAL_CORE.md)** — Core modules: madre, tentaculo_link, switch, mcp, spawner
- **[MODULES_INDEX.md](MODULES_INDEX.md)** — Índice completo de módulos y responsabilidades

### Runtime & Flows
- **[CANONICAL_RUNTIME_POLICY_VX11.json](CANONICAL_RUNTIME_POLICY_VX11.json)** — Políticas de ejecución, perfiles, modos
- **[CANONICAL_FLOWS_VX11.json](CANONICAL_FLOWS_VX11.json)** — Workflows canónicos (chat, control, orchestration)
- **[CANONICAL_SEMANTIC_VX11.json](CANONICAL_SEMANTIC_VX11.json)** — Semántica de decisiones, autonomy rules

### Database & State
- **[DB_MAP_v7_FINAL.md](../audit/DB_MAP_v7_FINAL.md)** — Mapeo de tablas SQLite, relaciones
- **[DB_SCHEMA_v7_FINAL.json](../audit/DB_SCHEMA_v7_FINAL.json)** — Schema completo: DDL, constraints, índices

### Filesystem & Deployment
- **[CANONICAL_TARGET_FS_VX11.json](CANONICAL_TARGET_FS_VX11.json)** — Estructura esperada del FS (allowed_roots, ignore_globs)
- **[CANONICAL_FS_VX11.json](CANONICAL_FS_VX11.json)** — Snapshot actual del FS
- **[docker-compose.yml](../docker-compose.yml)** — Servicios, puertos, healthchecks (código fuente)

### Master & Metrics
- **[CANONICAL_MASTER_VX11.json](CANONICAL_MASTER_VX11.json)** — Master registry: versioning, module assignments
- **[PERCENTAGES.json](../audit/PERCENTAGES.json)** — Métricas de orden/estabilidad/coherencia
- **[SCORECARD.json](../audit/SCORECARD.json)** — Estado global post-verificación

---

## 🔄 Relaciones entre Componentes

```
┌─────────────────────────────────────────────────────┐
│  Operator (Frontend/Backend) — User Interface       │
└────────────────────┬────────────────────────────────┘
                     │ (REST/WebSocket)
                     ▼
┌─────────────────────────────────────────────────────┐
│  TENTACULO_LINK (8000) — Gateway/Frontdoor         │
│  ├─ Route to: madre, switch, hermes, etc.          │
│  └─ Auth: token validation                          │
└────────────────────┬────────────────────────────────┘
          ┌──────────┼──────────┬───────────┬──────────┐
          ▼          ▼          ▼           ▼          ▼
    ┌──────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐ ┌────────┐
    │ MADRE    │ │ SWITCH   │ │ HERMES │ │HORMIGUERO│ │SPAWNER │
    │ (8001)   │ │ (8002)   │ │(8003)  │ │ (8004)   │ │ (8008) │
    │Orchestr. │ │Routing   │ │CLI/    │ │Parallel. │ │Ephemer.│
    │          │ │Adaptive  │ │Bridge  │ │ Ants     │ │Exec    │
    └─┬────────┘ └──────────┘ └───┬────┘ └─────────┘ └────┬───┘
      │                            │                      │
      └────────────────┬───────────┴──────────────────────┘
                       ▼
            ┌──────────────────────┐
            │ SWITCH/HERMES (Real) │ ← Canonical hermes
            │ (dockerfile, models) │
            └──────────────────────┘

┌─────────────────────────────────────────────────────┐
│ DB: data/runtime/vx11.db (SQLite)                  │
│ ├─ Core tables: module_status, tasks, spawns, etc. │
│ ├─ Logs: pheromone_log, routing_events, etc.      │
│ └─ Metadata: manifests, intents, decisions        │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 How to Navigate

### For New Contributors
1. Start with **[CANONICAL_CORE.md](CANONICAL_CORE.md)** to understand core modules
2. Read **[CANONICAL_FLOWS_VX11.json](CANONICAL_FLOWS_VX11.json)** to see workflows
3. Explore **[docker-compose.yml](../docker-compose.yml)** for service orchestration

### For Operators/DevOps
1. Check **[CANONICAL_RUNTIME_POLICY_VX11.json](CANONICAL_RUNTIME_POLICY_VX11.json)** for runtime modes
2. Review **[DB_MAP_v7_FINAL.md](../audit/DB_MAP_v7_FINAL.md)** for data model
3. Monitor **[PERCENTAGES.json](../audit/PERCENTAGES.json)** for health metrics

### For Architects
1. Consult **[CANONICAL_MASTER_VX11.json](CANONICAL_MASTER_VX11.json)** for module versioning
2. Review **[CANONICAL_SEMANTIC_VX11.json](CANONICAL_SEMANTIC_VX11.json)** for decision semantics
3. Check **[CANONICAL_TARGET_FS_VX11.json](CANONICAL_TARGET_FS_VX11.json)** for structural invariants

---

## 📋 Key Files by Purpose

| Purpose | File | Location |
|---------|------|----------|
| **Module Map** | CANONICAL_CORE.md | docs/ |
| **Workflow Definitions** | CANONICAL_FLOWS_VX11.json | docs/ |
| **Database Schema** | DB_SCHEMA_v7_FINAL.json | docs/audit/ |
| **Service Config** | docker-compose.yml | root |
| **Filesystem Rules** | CANONICAL_TARGET_FS_VX11.json | docs/ |
| **Metrics/Health** | PERCENTAGES.json | docs/audit/ |
| **Runtime Modes** | CANONICAL_RUNTIME_POLICY_VX11.json | docs/ |
| **Autonomy Rules** | CANONICAL_SEMANTIC_VX11.json | docs/ |

---

## ⚠️ Important Notes

- **Hermes Canonical:** Always at `switch/hermes/`, never root `./hermes/`
- **Core Mode:** Default behavior: madre, tentaculo_link, switch, hermes, hormiguero, spawner, mcp (7 services)
- **Profiles:** manifestator, shubniggurath, operator exist but may be disabled by default
- **DB Location:** Always `data/runtime/vx11.db` (SQLite, single source of truth)
- **Changes:** All architecture changes must maintain canonical invariants (see CANONICAL_TARGET_FS_VX11.json)

---

## 🔗 Quick Links

- [README.md](../README.md) — Project overview & getting started
- [VX11_CONTEXT.md](../VX11_CONTEXT.md) — Runtime context & service endpoints
- [AGENTS.md](../.github/AGENTS.md) — Agent contract & rules
- [docs/audit/](../audit/) — Maintenance logs & evidencia

---

**Last Updated:** 2025-12-22  
**Canonical Version:** v7  
**Status:** ✅ MAINTAINED
