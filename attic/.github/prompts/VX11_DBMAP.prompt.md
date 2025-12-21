# VX11 Database Map (DBMAP)

Quick reference for BD schema and how to query.

## BD Location
- **Primary:** `/data/runtime/vx11.db` (SQLite)
- **Type:** Single-writer pattern, all tables unified
- **Backup:** `/data/backups/` (automated snapshots)

## Main Tables (Quick Reference)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tasks` | Madre tasks, status tracking | `uuid`, `name`, `status`, `created_at` |
| `ia_decisions` | Switch routing decisions | `prompt_hash`, `provider`, `confidence`, `latency_ms` |
| `model_registry` | Local models (HF, GGUF, etc.) | `name`, `path`, `size_bytes`, `available` |
| `cli_registry` | CLI tools discovered | `name`, `bin_path`, `available` |
| `operator_session` | Chat sessions | `session_id`, `user_id`, `created_at` |
| `operator_message` | Chat messages | `session_id`, `role`, `content` |
| `module_health` | Module status snapshots | `module`, `status`, `last_ping` |
| `hijas_runtime` | Ephemeral tasks (Madre spawns) | `name`, `state`, `ttl`, `born_at` |
| `drift_reports` | Audits findings | `module`, `details`, `severity`, `timestamp` |

## Connect & Query

```python
from config.db_schema import get_session, Task, OperatorSession

# Get session (unified vx11.db)
db = get_session("vx11")

try:
    # Example: List recent tasks
    tasks = db.query(Task).filter(Task.status == "pending").all()
    for t in tasks:
        print(f"{t.uuid}: {t.name} ({t.status})")
    
    # Example: List sessions
    sessions = db.query(OperatorSession).all()
    for s in sessions:
        print(f"Session {s.session_id}: {len(s.messages)} messages")

finally:
    db.close()
```

## Useful Queries

### Recent Errors
```python
from config.db_schema import Task
# Tasks with errors
errors = db.query(Task).filter(Task.status == "failed").limit(5).all()
for t in errors:
    print(f"ERROR: {t.name} - {t.error}")
```

### Model Performance
```python
from config.db_schema import IADecision
# Check Switch decision latencies (avg response time)
decisions = db.query(IADecision).all()
avg_latency = sum(d.latency_ms or 0 for d in decisions) / len(decisions) if decisions else 0
print(f"Avg Switch latency: {avg_latency}ms")
```

### Module Health Timeline
```python
from config.db_schema import ModuleHealth
health_history = db.query(ModuleHealth).order_by(ModuleHealth.updated_at.desc()).limit(20).all()
for h in health_history:
    print(f"{h.module}: {h.status} ({h.last_ping})")
```

## Maintenance

### Cleanup Old Records (>30 days)
```python
from datetime import datetime, timedelta
from config.db_schema import Task, ForensicLedger

cutoff = datetime.utcnow() - timedelta(days=30)

# Count old tasks
old_count = db.query(Task).filter(Task.created_at < cutoff).count()
print(f"Tasks >30d: {old_count}")

# Archive to file instead of deleting (compliance)
# See config/forensics.py -> ttl_cleanup()
```

### DB Integrity Check
```bash
# From shell
sqlite3 /home/elkakas314/vx11/data/runtime/vx11.db "PRAGMA integrity_check;"
# Should output: "ok"
```

## Performance Tips
- ✅ Use `.filter(Column == value).first()` for single lookups (fast)
- ✅ Use `.all()` only for <1000 rows
- ❌ Avoid `SELECT *` without `.limit()`
- ❌ Never leave sessions open (always `db.close()`)

## Schema Diagram (Text)
```
Madre (8001)
  ├─ creates Task → stored in DB
  ├─ delegates to Switch (8002)
  └─ records IADecision
       ├─ provider (local, CLI, remote)
       ├─ latency_ms
       └─ confidence score

Operator (8011)
  ├─ creates OperatorSession
  ├─ appends OperatorMessage (role: user|assistant|tool)
  └─ tracks OperatorToolCall (tool outcomes)
```

---

**Last Update:** 2025-12-16  
**Schema Version:** v7.0 (unified vx11.db)
