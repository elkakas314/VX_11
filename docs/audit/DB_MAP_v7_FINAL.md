# VX11 Database Map (v7 Post-Phase 3)

**Generated**: 2025-12-16T00:03:23.597354Z

---

## Summary

- Total Tables: 54
- Database Integrity: ok

---

### audit_logs
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| component | VARCHAR(64) |  | ✓ |
| level | VARCHAR(16) |  |  |
| message | TEXT |  | ✓ |
| created_at | DATETIME |  |  |

### cli_onboarding_state
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | switch |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| provider_id | VARCHAR(128) |  | ✓ |
| state | VARCHAR(50) |  |  |
| notes | TEXT |  |  |
| last_checked_at | DATETIME |  |  |
| created_at | DATETIME |  |  |

### cli_providers
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | switch |
| Filas | 0 |
| Columnas | 14 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| name | VARCHAR(100) |  | ✓ |
| base_url | VARCHAR(500) |  |  |
| api_key_env | VARCHAR(100) |  | ✓ |
| task_types | VARCHAR(255) |  |  |
| daily_limit_tokens | INTEGER |  |  |
| monthly_limit_tokens | INTEGER |  |  |
| tokens_used_today | INTEGER |  |  |
| tokens_used_month | INTEGER |  |  |
| reset_hour_utc | INTEGER |  |  |
| enabled | BOOLEAN |  |  |
| last_reset_at | DATETIME |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### cli_registry
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | hermes |
| Filas | 0 |
| Columnas | 11 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| name | VARCHAR(100) |  | ✓ |
| bin_path | VARCHAR(500) |  |  |
| available | BOOLEAN |  |  |
| last_checked | DATETIME |  |  |
| cli_type | VARCHAR(50) |  | ✓ |
| token_config_key | VARCHAR(100) |  |  |
| rate_limit_daily | INTEGER |  |  |
| used_today | INTEGER |  |  |
| notes | TEXT |  |  |
| updated_at | DATETIME |  |  |

### cli_usage_stats
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | switch |
| Filas | 1 |
| Columnas | 8 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| provider_id | VARCHAR(128) |  | ✓ |
| timestamp | DATETIME |  |  |
| success | BOOLEAN |  |  |
| latency_ms | INTEGER |  |  |
| cost_estimated | FLOAT |  |  |
| tokens_estimated | INTEGER |  |  |
| error_class | VARCHAR(100) |  |  |

### context
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | madre |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| task_id | VARCHAR(36) |  | ✓ |
| key | VARCHAR(255) |  | ✓ |
| value | TEXT |  | ✓ |
| scope | VARCHAR(50) |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- task_id → tasks.uuid

### daughter_attempts
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | madre |
| Filas | 0 |
| Columnas | 12 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| daughter_id | INTEGER |  | ✓ |
| attempt_number | INTEGER |  |  |
| started_at | DATETIME |  |  |
| finished_at | DATETIME |  |  |
| status | VARCHAR(32) |  |  |
| error_message | VARCHAR(500) |  |  |
| tokens_used_cli | INTEGER |  |  |
| tokens_used_local | INTEGER |  |  |
| switch_model_used | VARCHAR(128) |  |  |
| cli_provider_used | VARCHAR(128) |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- daughter_id → daughters.id

### daughter_tasks
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | madre |
| Filas | 0 |
| Columnas | 14 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| intent_id | VARCHAR(36) |  |  |
| source | VARCHAR(64) |  | ✓ |
| priority | INTEGER |  |  |
| status | VARCHAR(32) |  |  |
| task_type | VARCHAR(50) |  | ✓ |
| description | TEXT |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |
| finished_at | DATETIME |  |  |
| max_retries | INTEGER |  |  |
| current_retry | INTEGER |  |  |
| metadata_json | TEXT |  |  |
| plan_json | TEXT |  |  |

### daughters
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | madre |
| Filas | 0 |
| Columnas | 12 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| task_id | INTEGER |  | ✓ |
| name | VARCHAR(128) |  | ✓ |
| purpose | TEXT |  |  |
| tools_json | TEXT |  |  |
| ttl_seconds | INTEGER |  |  |
| started_at | DATETIME |  |  |
| last_heartbeat_at | DATETIME |  |  |
| ended_at | DATETIME |  |  |
| status | VARCHAR(32) |  |  |
| mutation_level | INTEGER |  |  |
| error_last | TEXT |  |  |

**Foreign Keys:**

- task_id → daughter_tasks.id

### drift_reports
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| module | VARCHAR(64) |  | ✓ |
| details | TEXT |  | ✓ |
| severity | VARCHAR(32) |  |  |
| timestamp | DATETIME |  |  |
| resolved | BOOLEAN |  |  |

### engines
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | switch |
| Filas | 0 |
| Columnas | 15 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| name | VARCHAR(128) |  | ✓ |
| engine_type | VARCHAR(32) |  | ✓ |
| domain | VARCHAR(64) |  | ✓ |
| endpoint | VARCHAR(256) |  | ✓ |
| version | VARCHAR(32) |  |  |
| quota_tokens_per_day | INTEGER |  |  |
| quota_used_today | INTEGER |  |  |
| quota_reset_at | DATETIME |  |  |
| latency_ms | FLOAT |  |  |
| cost_per_call | FLOAT |  |  |
| enabled | BOOLEAN |  |  |
| last_used | DATETIME |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### events
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| source | VARCHAR(64) |  | ✓ |
| event_type | VARCHAR(64) |  | ✓ |
| payload | TEXT |  |  |
| created_at | DATETIME |  |  |

### feromona_events
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| type | VARCHAR(64) |  | ✓ |
| intensity | INTEGER |  |  |
| module | VARCHAR(64) |  | ✓ |
| payload | TEXT |  |  |
| timestamp | DATETIME |  |  |

### fluzo_signals
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | switch |
| Filas | 0 |
| Columnas | 7 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| timestamp | DATETIME |  |  |
| cpu_load_1m | FLOAT |  |  |
| mem_pct | FLOAT |  |  |
| on_ac | BOOLEAN |  |  |
| battery_pct | INTEGER |  |  |
| profile | VARCHAR(32) |  |  |

### forensic_ledger
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| event | VARCHAR(255) |  | ✓ |
| payload | TEXT |  |  |
| hash | VARCHAR(64) |  | ✓ |
| created_at | DATETIME |  |  |

### hermes_ingest
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| path | VARCHAR(512) |  | ✓ |
| size_bytes | INTEGER |  |  |
| duration_sec | FLOAT |  |  |
| status | VARCHAR(32) |  |  |
| created_at | DATETIME |  |  |

### hijas_runtime
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | unknown |
| Filas | 21 |
| Columnas | 15 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| name | VARCHAR(128) |  | ✓ |
| state | VARCHAR(32) |  |  |
| pid | INTEGER |  |  |
| last_heartbeat | DATETIME |  |  |
| meta_json | TEXT |  |  |
| birth_context | TEXT |  |  |
| death_context | TEXT |  |  |
| intent_type | VARCHAR(64) |  |  |
| ttl | INTEGER |  |  |
| killed_by | VARCHAR(128) |  |  |
| purpose | VARCHAR(256) |  |  |
| module_creator | VARCHAR(64) |  |  |
| born_at | DATETIME |  |  |
| died_at | DATETIME |  |  |

### hijas_state
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 9 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| hija_id | VARCHAR(64) |  | ✓ |
| module | VARCHAR(64) |  | ✓ |
| status | VARCHAR(32) |  |  |
| cpu_usage | FLOAT |  |  |
| ram_usage | FLOAT |  |  |
| pid | INTEGER |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### hormiga_state
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | hormiguero |
| Filas | 0 |
| Columnas | 10 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| ant_id | VARCHAR(64) |  | ✓ |
| role | VARCHAR(32) |  | ✓ |
| status | VARCHAR(20) |  |  |
| last_scan_at | DATETIME |  |  |
| mutation_level | INTEGER |  |  |
| cpu_percent | FLOAT |  |  |
| ram_percent | FLOAT |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### ia_decisions
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | switch |
| Filas | 2 |
| Columnas | 11 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| prompt_hash | VARCHAR(64) |  | ✓ |
| provider | VARCHAR(50) |  | ✓ |
| task_type | VARCHAR(50) |  |  |
| prompt | TEXT |  | ✓ |
| response | TEXT |  |  |
| latency_ms | INTEGER |  |  |
| success | BOOLEAN |  |  |
| confidence | FLOAT |  |  |
| meta_json | TEXT |  |  |
| created_at | DATETIME |  |  |

### incidents
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | hormiguero |
| Filas | 0 |
| Columnas | 10 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| ant_id | VARCHAR(64) |  | ✓ |
| incident_type | VARCHAR(64) |  | ✓ |
| severity | VARCHAR(20) |  |  |
| location | VARCHAR(255) |  |  |
| details | TEXT |  |  |
| status | VARCHAR(20) |  |  |
| detected_at | DATETIME |  |  |
| resolved_at | DATETIME |  |  |
| queen_decision | VARCHAR(255) |  |  |

### intents_log
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 7 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| source | VARCHAR(64) |  | ✓ |
| payload_json | TEXT |  | ✓ |
| created_at | DATETIME |  |  |
| processed_by_madre_at | DATETIME |  |  |
| result_status | VARCHAR(32) |  |  |
| notes | TEXT |  |  |

### local_models_v2
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | hermes |
| Filas | 2 |
| Columnas | 14 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| name | VARCHAR(255) |  | ✓ |
| engine | VARCHAR(50) |  | ✓ |
| path | VARCHAR(512) |  | ✓ |
| size_bytes | INTEGER |  | ✓ |
| task_type | VARCHAR(50) |  | ✓ |
| max_context | INTEGER |  |  |
| enabled | BOOLEAN |  |  |
| last_used_at | DATETIME |  |  |
| usage_count | INTEGER |  |  |
| compatibility | VARCHAR(64) |  |  |
| meta_info | TEXT |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### madre_actions
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| module | VARCHAR(64) |  | ✓ |
| action | VARCHAR(64) |  | ✓ |
| reason | VARCHAR(255) |  |  |
| created_at | DATETIME |  |  |

### madre_policies
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 7 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| module | VARCHAR(64) |  | ✓ |
| error_threshold | INTEGER |  |  |
| idle_seconds | INTEGER |  |  |
| enable_autosuspend | BOOLEAN |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### model_registry
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | hermes |
| Filas | 0 |
| Columnas | 13 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| name | VARCHAR(255) |  | ✓ |
| path | VARCHAR(500) |  | ✓ |
| provider | VARCHAR(50) |  | ✓ |
| type | VARCHAR(50) |  | ✓ |
| size_bytes | INTEGER |  | ✓ |
| tags | TEXT |  |  |
| last_used | DATETIME |  |  |
| score | FLOAT |  |  |
| available | BOOLEAN |  |  |
| meta_json | TEXT |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### model_usage_stats
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | switch |
| Filas | 2 |
| Columnas | 10 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| model_or_cli_name | VARCHAR(255) |  | ✓ |
| kind | VARCHAR(20) |  | ✓ |
| task_type | VARCHAR(50) |  | ✓ |
| tokens_used | INTEGER |  |  |
| latency_ms | INTEGER |  |  |
| success | BOOLEAN |  |  |
| error_message | VARCHAR(500) |  |  |
| user_id | VARCHAR(100) |  |  |
| created_at | DATETIME |  |  |

### models_local
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | unknown |
| Filas | 30 |
| Columnas | 10 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| name | VARCHAR(255) |  | ✓ |
| path | VARCHAR(512) |  | ✓ |
| size_mb | INTEGER |  |  |
| hash | VARCHAR(128) |  |  |
| category | VARCHAR(64) |  |  |
| status | VARCHAR(32) |  |  |
| compatibility | VARCHAR(64) |  |  |
| downloaded_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### models_remote_cli
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 10 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| provider | VARCHAR(128) |  | ✓ |
| token | VARCHAR(256) |  | ✓ |
| limit_daily | INTEGER |  |  |
| limit_weekly | INTEGER |  |  |
| renew_at | DATETIME |  |  |
| task_type | VARCHAR(64) |  |  |
| status | VARCHAR(32) |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### module_health
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | switch |
| Filas | 0 |
| Columnas | 7 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| module | VARCHAR(50) |  | ✓ |
| status | VARCHAR(20) |  |  |
| last_ping | DATETIME |  |  |
| error_count | INTEGER |  |  |
| uptime_seconds | FLOAT |  |  |
| updated_at | DATETIME |  |  |

### operator_browser_task
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | operator |
| Filas | 0 |
| Columnas | 9 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| session_id | VARCHAR(64) |  | ✓ |
| url | VARCHAR(500) |  | ✓ |
| status | VARCHAR(50) |  |  |
| snapshot_path | VARCHAR(255) |  |  |
| result | TEXT |  |  |
| error | TEXT |  |  |
| created_at | DATETIME |  |  |
| executed_at | DATETIME |  |  |

**Foreign Keys:**

- session_id → operator_session.session_id

### operator_jobs
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 8 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| job_id | VARCHAR(64) |  | ✓ |
| intent | VARCHAR(64) |  | ✓ |
| status | VARCHAR(32) |  |  |
| payload | TEXT |  |  |
| result | TEXT |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### operator_message
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | operator |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| session_id | VARCHAR(64) |  | ✓ |
| role | VARCHAR(50) |  | ✓ |
| content | TEXT |  | ✓ |
| message_metadata | TEXT |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- session_id → operator_session.session_id

### operator_session
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | operator |
| Filas | 16 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| session_id | VARCHAR(64) |  | ✓ |
| user_id | VARCHAR(64) |  | ✓ |
| source | VARCHAR(50) |  | ✓ |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### operator_switch_adjustment
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | unknown |
| Filas | 16 |
| Columnas | 9 |
| Foreign Keys | 2 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| session_id | VARCHAR(64) |  | ✓ |
| message_id | INTEGER |  |  |
| before_config | TEXT |  | ✓ |
| after_config | TEXT |  | ✓ |
| reason | TEXT |  | ✓ |
| applied | BOOLEAN |  |  |
| created_at | DATETIME |  |  |
| applied_at | DATETIME |  |  |

**Foreign Keys:**

- message_id → operator_message.id
- session_id → operator_session.session_id

### operator_tool_call
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | operator |
| Filas | 0 |
| Columnas | 8 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| message_id | INTEGER |  | ✓ |
| tool_name | VARCHAR(100) |  | ✓ |
| status | VARCHAR(50) |  |  |
| duration_ms | INTEGER |  |  |
| result | TEXT |  |  |
| error | TEXT |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- message_id → operator_message.id

### pheromone_log
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 9 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| pheromone_type | VARCHAR(64) |  | ✓ |
| intensity | INTEGER |  |  |
| source_incident_ids | TEXT |  |  |
| madre_intent_id | VARCHAR(64) |  |  |
| switch_consultation_id | VARCHAR(64) |  |  |
| payload | TEXT |  |  |
| created_at | DATETIME |  |  |
| executed_at | DATETIME |  |  |

### power_events
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 8 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| module | VARCHAR(64) |  | ✓ |
| action | VARCHAR(32) |  | ✓ |
| reason | VARCHAR(255) |  |  |
| cpu_usage | FLOAT |  |  |
| ram_usage | FLOAT |  |  |
| activity_score | FLOAT |  |  |
| timestamp | DATETIME |  |  |

### reports
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | madre |
| Filas | 0 |
| Columnas | 7 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| task_id | VARCHAR(36) |  | ✓ |
| report_type | VARCHAR(50) |  | ✓ |
| summary | TEXT |  |  |
| details | TEXT |  |  |
| metrics | TEXT |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- task_id → tasks.uuid

### routing_events
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | switch |
| Filas | 1 |
| Columnas | 7 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| timestamp | DATETIME |  |  |
| trace_id | VARCHAR(36) |  | ✓ |
| route_type | VARCHAR(50) |  | ✓ |
| provider_id | VARCHAR(128) |  | ✓ |
| score | FLOAT |  |  |
| reasoning_short | VARCHAR(255) |  |  |

### sandbox_exec
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| action | VARCHAR(128) |  | ✓ |
| status | VARCHAR(32) |  |  |
| duration_ms | FLOAT |  |  |
| error | TEXT |  |  |
| created_at | DATETIME |  |  |

### scheduler_history
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| timestamp | DATETIME |  |  |
| action | VARCHAR(64) |  | ✓ |
| reason | TEXT |  |  |
| metrics | TEXT |  |  |

### shub_analysis
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | shub |
| Filas | 0 |
| Columnas | 10 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| track_id | INTEGER |  | ✓ |
| rms | FLOAT |  |  |
| peak | FLOAT |  |  |
| lufs | FLOAT |  |  |
| noise_floor | FLOAT |  |  |
| dynamic_range | FLOAT |  |  |
| clipping | INTEGER |  |  |
| notes | TEXT |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- track_id → shub_tracks.id

### shub_fx_chains
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| track_id | INTEGER |  | ✓ |
| chain_name | VARCHAR(255) |  | ✓ |
| steps_json | TEXT |  | ✓ |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- track_id → shub_tracks.id

### shub_presets
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| fx_chain_id | INTEGER |  | ✓ |
| rpp_snippet | TEXT |  |  |
| version | VARCHAR(32) |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- fx_chain_id → shub_fx_chains.id

### shub_projects
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | shub |
| Filas | 0 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| project_id | VARCHAR(64) |  | ✓ |
| name | VARCHAR(255) |  | ✓ |
| sample_rate | INTEGER |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |

### shub_tracks
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | shub |
| Filas | 0 |
| Columnas | 7 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| project_id | VARCHAR(64) |  | ✓ |
| name | VARCHAR(255) |  | ✓ |
| role | VARCHAR(64) |  |  |
| file_path | VARCHAR(512) |  |  |
| duration_sec | FLOAT |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- project_id → shub_projects.project_id

### spawns
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | madre |
| Filas | 0 |
| Columnas | 13 |
| Foreign Keys | 1 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| uuid | VARCHAR(36) |  | ✓ |
| name | VARCHAR(255) |  | ✓ |
| cmd | VARCHAR(500) |  | ✓ |
| pid | INTEGER |  |  |
| status | VARCHAR(20) |  |  |
| started_at | DATETIME |  |  |
| ended_at | DATETIME |  |  |
| exit_code | INTEGER |  |  |
| stdout | TEXT |  |  |
| stderr | TEXT |  |  |
| parent_task_id | VARCHAR(36) |  |  |
| created_at | DATETIME |  |  |

**Foreign Keys:**

- parent_task_id → tasks.uuid

### switch_queue_v2
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | switch |
| Filas | 0 |
| Columnas | 11 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| source | VARCHAR(64) |  | ✓ |
| priority | INTEGER |  |  |
| task_type | VARCHAR(50) |  | ✓ |
| payload_hash | VARCHAR(64) |  | ✓ |
| status | VARCHAR(32) |  |  |
| created_at | DATETIME |  |  |
| started_at | DATETIME |  |  |
| finished_at | DATETIME |  |  |
| result_size | INTEGER |  |  |
| error_message | VARCHAR(500) |  |  |

### system_events
| Atributo | Valor |
|----------|-------|
| Estado | ACTIVE |
| Módulo | unknown |
| Filas | 21 |
| Columnas | 6 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| timestamp | DATETIME |  |  |
| source | VARCHAR(64) |  | ✓ |
| event_type | VARCHAR(64) |  | ✓ |
| payload | TEXT |  |  |
| severity | VARCHAR(16) |  |  |

### system_state
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 17 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| key | VARCHAR(128) |  | ✓ |
| value | TEXT |  |  |
| updated_at | DATETIME |  |  |
| memory_pressure | FLOAT |  |  |
| cpu_pressure | FLOAT |  |  |
| switch_queue_level | FLOAT |  |  |
| hermes_update_required | BOOLEAN |  |  |
| shub_pipeline_state | VARCHAR(64) |  |  |
| operator_active | BOOLEAN |  |  |
| system_load_score | FLOAT |  |  |
| model_rotation_state | VARCHAR(128) |  |  |
| audio_pipeline_state | VARCHAR(128) |  |  |
| pending_tasks | INTEGER |  |  |
| active_children | INTEGER |  |  |
| last_operator_activity | DATETIME |  |  |
| power_mode | VARCHAR(32) |  |  |

### task_queue
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 7 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| source | VARCHAR(64) |  | ✓ |
| priority | INTEGER |  |  |
| payload | TEXT |  | ✓ |
| status | VARCHAR(32) |  |  |
| enqueued_at | DATETIME |  |  |
| dequeued_at | DATETIME |  |  |

### tasks
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | madre |
| Filas | 0 |
| Columnas | 10 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| uuid | VARCHAR(36) |  | ✓ |
| name | VARCHAR(255) |  | ✓ |
| module | VARCHAR(50) |  | ✓ |
| action | VARCHAR(100) |  | ✓ |
| status | VARCHAR(20) |  |  |
| created_at | DATETIME |  |  |
| updated_at | DATETIME |  |  |
| result | TEXT |  |  |
| error | TEXT |  |  |

### tokens_usage
| Atributo | Valor |
|----------|-------|
| Estado | EMPTY (READY) |
| Módulo | unknown |
| Filas | 0 |
| Columnas | 5 |
| Foreign Keys | 0 |

**Columnas:**

| Nombre | Tipo | PK | NOT NULL |
|--------|------|----|---------|
| id | INTEGER | ✓ | ✓ |
| token_id | VARCHAR(256) |  | ✓ |
| used_at | DATETIME |  |  |
| used_count | INTEGER |  |  |
| source | VARCHAR(64) |  |  |

