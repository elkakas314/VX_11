# VX11 Database Schema Map

**Generated:** 2025-12-15T22:10:12.956601Z
**Database:** data/runtime/vx11.db
**Total Tables:** 50

**Database Size:** 0.3MB

## Table of Contents

1. [audit_logs](#audit_logs)
2. [cli_providers](#cli_providers)
3. [cli_registry](#cli_registry)
4. [context](#context)
5. [daughter_attempts](#daughter_attempts)
6. [daughter_tasks](#daughter_tasks)
7. [daughters](#daughters)
8. [drift_reports](#drift_reports)
9. [engines](#engines)
10. [events](#events)
11. [feromona_events](#feromona_events)
12. [forensic_ledger](#forensic_ledger)
13. [hermes_ingest](#hermes_ingest)
14. [hijas_runtime](#hijas_runtime)
15. [hijas_state](#hijas_state)
16. [hormiga_state](#hormiga_state)
17. [ia_decisions](#ia_decisions)
18. [incidents](#incidents)
19. [intents_log](#intents_log)
20. [local_models_v2](#local_models_v2)
21. [madre_actions](#madre_actions)
22. [madre_policies](#madre_policies)
23. [model_registry](#model_registry)
24. [model_usage_stats](#model_usage_stats)
25. [models_local](#models_local)
26. [models_remote_cli](#models_remote_cli)
27. [module_health](#module_health)
28. [operator_browser_task](#operator_browser_task)
29. [operator_jobs](#operator_jobs)
30. [operator_message](#operator_message)
31. [operator_session](#operator_session)
32. [operator_switch_adjustment](#operator_switch_adjustment)
33. [operator_tool_call](#operator_tool_call)
34. [pheromone_log](#pheromone_log)
35. [power_events](#power_events)
36. [reports](#reports)
37. [sandbox_exec](#sandbox_exec)
38. [scheduler_history](#scheduler_history)
39. [shub_analysis](#shub_analysis)
40. [shub_fx_chains](#shub_fx_chains)
41. [shub_presets](#shub_presets)
42. [shub_projects](#shub_projects)
43. [shub_tracks](#shub_tracks)
44. [spawns](#spawns)
45. [switch_queue_v2](#switch_queue_v2)
46. [system_events](#system_events)
47. [system_state](#system_state)
48. [task_queue](#task_queue)
49. [tasks](#tasks)
50. [tokens_usage](#tokens_usage)

---

## audit_logs

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `component` | VARCHAR(64) |  |  |  |
| 2 | `level` | VARCHAR(16) |  | ✓ |  |
| 3 | `message` | TEXT |  |  |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |

## cli_providers

**Rows:** 0

**Indices:** `sqlite_autoindex_cli_providers_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `name` | VARCHAR(100) |  |  |  |
| 2 | `base_url` | VARCHAR(500) |  | ✓ |  |
| 3 | `api_key_env` | VARCHAR(100) |  |  |  |
| 4 | `task_types` | VARCHAR(255) |  | ✓ |  |
| 5 | `daily_limit_tokens` | INTEGER |  | ✓ |  |
| 6 | `monthly_limit_tokens` | INTEGER |  | ✓ |  |
| 7 | `tokens_used_today` | INTEGER |  | ✓ |  |
| 8 | `tokens_used_month` | INTEGER |  | ✓ |  |
| 9 | `reset_hour_utc` | INTEGER |  | ✓ |  |
| 10 | `enabled` | BOOLEAN |  | ✓ |  |
| 11 | `last_reset_at` | DATETIME |  | ✓ |  |
| 12 | `created_at` | DATETIME |  | ✓ |  |
| 13 | `updated_at` | DATETIME |  | ✓ |  |

## cli_registry

**Rows:** 0

**Indices:** `sqlite_autoindex_cli_registry_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `name` | VARCHAR(100) |  |  |  |
| 2 | `bin_path` | VARCHAR(500) |  | ✓ |  |
| 3 | `available` | BOOLEAN |  | ✓ |  |
| 4 | `last_checked` | DATETIME |  | ✓ |  |
| 5 | `cli_type` | VARCHAR(50) |  |  |  |
| 6 | `token_config_key` | VARCHAR(100) |  | ✓ |  |
| 7 | `rate_limit_daily` | INTEGER |  | ✓ |  |
| 8 | `used_today` | INTEGER |  | ✓ |  |
| 9 | `notes` | TEXT |  | ✓ |  |
| 10 | `updated_at` | DATETIME |  | ✓ |  |

## context

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `task_id` | VARCHAR(36) |  |  |  |
| 2 | `key` | VARCHAR(255) |  |  |  |
| 3 | `value` | TEXT |  |  |  |
| 4 | `scope` | VARCHAR(50) |  | ✓ |  |
| 5 | `created_at` | DATETIME |  | ✓ |  |

## daughter_attempts

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `daughter_id` | INTEGER |  |  |  |
| 2 | `attempt_number` | INTEGER |  | ✓ |  |
| 3 | `started_at` | DATETIME |  | ✓ |  |
| 4 | `finished_at` | DATETIME |  | ✓ |  |
| 5 | `status` | VARCHAR(32) |  | ✓ |  |
| 6 | `error_message` | VARCHAR(500) |  | ✓ |  |
| 7 | `tokens_used_cli` | INTEGER |  | ✓ |  |
| 8 | `tokens_used_local` | INTEGER |  | ✓ |  |
| 9 | `switch_model_used` | VARCHAR(128) |  | ✓ |  |
| 10 | `cli_provider_used` | VARCHAR(128) |  | ✓ |  |
| 11 | `created_at` | DATETIME |  | ✓ |  |

## daughter_tasks

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `intent_id` | VARCHAR(36) |  | ✓ |  |
| 2 | `source` | VARCHAR(64) |  |  |  |
| 3 | `priority` | INTEGER |  | ✓ |  |
| 4 | `status` | VARCHAR(32) |  | ✓ |  |
| 5 | `task_type` | VARCHAR(50) |  |  |  |
| 6 | `description` | TEXT |  | ✓ |  |
| 7 | `created_at` | DATETIME |  | ✓ |  |
| 8 | `updated_at` | DATETIME |  | ✓ |  |
| 9 | `finished_at` | DATETIME |  | ✓ |  |
| 10 | `max_retries` | INTEGER |  | ✓ |  |
| 11 | `current_retry` | INTEGER |  | ✓ |  |
| 12 | `metadata_json` | TEXT |  | ✓ |  |
| 13 | `plan_json` | TEXT |  | ✓ |  |

## daughters

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `task_id` | INTEGER |  |  |  |
| 2 | `name` | VARCHAR(128) |  |  |  |
| 3 | `purpose` | TEXT |  | ✓ |  |
| 4 | `tools_json` | TEXT |  | ✓ |  |
| 5 | `ttl_seconds` | INTEGER |  | ✓ |  |
| 6 | `started_at` | DATETIME |  | ✓ |  |
| 7 | `last_heartbeat_at` | DATETIME |  | ✓ |  |
| 8 | `ended_at` | DATETIME |  | ✓ |  |
| 9 | `status` | VARCHAR(32) |  | ✓ |  |
| 10 | `mutation_level` | INTEGER |  | ✓ |  |
| 11 | `error_last` | TEXT |  | ✓ |  |

## drift_reports

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `module` | VARCHAR(64) |  |  |  |
| 2 | `details` | TEXT |  |  |  |
| 3 | `severity` | VARCHAR(32) |  | ✓ |  |
| 4 | `timestamp` | DATETIME |  | ✓ |  |
| 5 | `resolved` | BOOLEAN |  | ✓ |  |

## engines

**Rows:** 0

**Indices:** `sqlite_autoindex_engines_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `name` | VARCHAR(128) |  |  |  |
| 2 | `engine_type` | VARCHAR(32) |  |  |  |
| 3 | `domain` | VARCHAR(64) |  |  |  |
| 4 | `endpoint` | VARCHAR(256) |  |  |  |
| 5 | `version` | VARCHAR(32) |  | ✓ |  |
| 6 | `quota_tokens_per_day` | INTEGER |  | ✓ |  |
| 7 | `quota_used_today` | INTEGER |  | ✓ |  |
| 8 | `quota_reset_at` | DATETIME |  | ✓ |  |
| 9 | `latency_ms` | FLOAT |  | ✓ |  |
| 10 | `cost_per_call` | FLOAT |  | ✓ |  |
| 11 | `enabled` | BOOLEAN |  | ✓ |  |
| 12 | `last_used` | DATETIME |  | ✓ |  |
| 13 | `created_at` | DATETIME |  | ✓ |  |
| 14 | `updated_at` | DATETIME |  | ✓ |  |

## events

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `source` | VARCHAR(64) |  |  |  |
| 2 | `event_type` | VARCHAR(64) |  |  |  |
| 3 | `payload` | TEXT |  | ✓ |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |

## feromona_events

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `type` | VARCHAR(64) |  |  |  |
| 2 | `intensity` | INTEGER |  | ✓ |  |
| 3 | `module` | VARCHAR(64) |  |  |  |
| 4 | `payload` | TEXT |  | ✓ |  |
| 5 | `timestamp` | DATETIME |  | ✓ |  |

## forensic_ledger

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `event` | VARCHAR(255) |  |  |  |
| 2 | `payload` | TEXT |  | ✓ |  |
| 3 | `hash` | VARCHAR(64) |  |  |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |

## hermes_ingest

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `path` | VARCHAR(512) |  |  |  |
| 2 | `size_bytes` | INTEGER |  | ✓ |  |
| 3 | `duration_sec` | FLOAT |  | ✓ |  |
| 4 | `status` | VARCHAR(32) |  | ✓ |  |
| 5 | `created_at` | DATETIME |  | ✓ |  |

## hijas_runtime

**Rows:** 16

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `name` | VARCHAR(128) |  |  |  |
| 2 | `state` | VARCHAR(32) |  | ✓ |  |
| 3 | `pid` | INTEGER |  | ✓ |  |
| 4 | `last_heartbeat` | DATETIME |  | ✓ |  |
| 5 | `meta_json` | TEXT |  | ✓ |  |
| 6 | `birth_context` | TEXT |  | ✓ |  |
| 7 | `death_context` | TEXT |  | ✓ |  |
| 8 | `intent_type` | VARCHAR(64) |  | ✓ |  |
| 9 | `ttl` | INTEGER |  | ✓ |  |
| 10 | `killed_by` | VARCHAR(128) |  | ✓ |  |
| 11 | `purpose` | VARCHAR(256) |  | ✓ |  |
| 12 | `module_creator` | VARCHAR(64) |  | ✓ |  |
| 13 | `born_at` | DATETIME |  | ✓ |  |
| 14 | `died_at` | DATETIME |  | ✓ |  |

## hijas_state

**Rows:** 0

**Indices:** `sqlite_autoindex_hijas_state_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `hija_id` | VARCHAR(64) |  |  |  |
| 2 | `module` | VARCHAR(64) |  |  |  |
| 3 | `status` | VARCHAR(32) |  | ✓ |  |
| 4 | `cpu_usage` | FLOAT |  | ✓ |  |
| 5 | `ram_usage` | FLOAT |  | ✓ |  |
| 6 | `pid` | INTEGER |  | ✓ |  |
| 7 | `created_at` | DATETIME |  | ✓ |  |
| 8 | `updated_at` | DATETIME |  | ✓ |  |

## hormiga_state

**Rows:** 0

**Indices:** `sqlite_autoindex_hormiga_state_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `ant_id` | VARCHAR(64) |  |  |  |
| 2 | `role` | VARCHAR(32) |  |  |  |
| 3 | `status` | VARCHAR(20) |  | ✓ |  |
| 4 | `last_scan_at` | DATETIME |  | ✓ |  |
| 5 | `mutation_level` | INTEGER |  | ✓ |  |
| 6 | `cpu_percent` | FLOAT |  | ✓ |  |
| 7 | `ram_percent` | FLOAT |  | ✓ |  |
| 8 | `created_at` | DATETIME |  | ✓ |  |
| 9 | `updated_at` | DATETIME |  | ✓ |  |

## ia_decisions

**Rows:** 2

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `prompt_hash` | VARCHAR(64) |  |  |  |
| 2 | `provider` | VARCHAR(50) |  |  |  |
| 3 | `task_type` | VARCHAR(50) |  | ✓ |  |
| 4 | `prompt` | TEXT |  |  |  |
| 5 | `response` | TEXT |  | ✓ |  |
| 6 | `latency_ms` | INTEGER |  | ✓ |  |
| 7 | `success` | BOOLEAN |  | ✓ |  |
| 8 | `confidence` | FLOAT |  | ✓ |  |
| 9 | `meta_json` | TEXT |  | ✓ |  |
| 10 | `created_at` | DATETIME |  | ✓ |  |

## incidents

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `ant_id` | VARCHAR(64) |  |  |  |
| 2 | `incident_type` | VARCHAR(64) |  |  |  |
| 3 | `severity` | VARCHAR(20) |  | ✓ |  |
| 4 | `location` | VARCHAR(255) |  | ✓ |  |
| 5 | `details` | TEXT |  | ✓ |  |
| 6 | `status` | VARCHAR(20) |  | ✓ |  |
| 7 | `detected_at` | DATETIME |  | ✓ |  |
| 8 | `resolved_at` | DATETIME |  | ✓ |  |
| 9 | `queen_decision` | VARCHAR(255) |  | ✓ |  |

## intents_log

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `source` | VARCHAR(64) |  |  |  |
| 2 | `payload_json` | TEXT |  |  |  |
| 3 | `created_at` | DATETIME |  | ✓ |  |
| 4 | `processed_by_madre_at` | DATETIME |  | ✓ |  |
| 5 | `result_status` | VARCHAR(32) |  | ✓ |  |
| 6 | `notes` | TEXT |  | ✓ |  |

## local_models_v2

**Rows:** 2

**Indices:** `sqlite_autoindex_local_models_v2_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `name` | VARCHAR(255) |  |  |  |
| 2 | `engine` | VARCHAR(50) |  |  |  |
| 3 | `path` | VARCHAR(512) |  |  |  |
| 4 | `size_bytes` | INTEGER |  |  |  |
| 5 | `task_type` | VARCHAR(50) |  |  |  |
| 6 | `max_context` | INTEGER |  | ✓ |  |
| 7 | `enabled` | BOOLEAN |  | ✓ |  |
| 8 | `last_used_at` | DATETIME |  | ✓ |  |
| 9 | `usage_count` | INTEGER |  | ✓ |  |
| 10 | `compatibility` | VARCHAR(64) |  | ✓ |  |
| 11 | `meta_info` | TEXT |  | ✓ |  |
| 12 | `created_at` | DATETIME |  | ✓ |  |
| 13 | `updated_at` | DATETIME |  | ✓ |  |

## madre_actions

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `module` | VARCHAR(64) |  |  |  |
| 2 | `action` | VARCHAR(64) |  |  |  |
| 3 | `reason` | VARCHAR(255) |  | ✓ |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |

## madre_policies

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `module` | VARCHAR(64) |  |  |  |
| 2 | `error_threshold` | INTEGER |  | ✓ |  |
| 3 | `idle_seconds` | INTEGER |  | ✓ |  |
| 4 | `enable_autosuspend` | BOOLEAN |  | ✓ |  |
| 5 | `created_at` | DATETIME |  | ✓ |  |
| 6 | `updated_at` | DATETIME |  | ✓ |  |

## model_registry

**Rows:** 0

**Indices:** `sqlite_autoindex_model_registry_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `name` | VARCHAR(255) |  |  |  |
| 2 | `path` | VARCHAR(500) |  |  |  |
| 3 | `provider` | VARCHAR(50) |  |  |  |
| 4 | `type` | VARCHAR(50) |  |  |  |
| 5 | `size_bytes` | INTEGER |  |  |  |
| 6 | `tags` | TEXT |  | ✓ |  |
| 7 | `last_used` | DATETIME |  | ✓ |  |
| 8 | `score` | FLOAT |  | ✓ |  |
| 9 | `available` | BOOLEAN |  | ✓ |  |
| 10 | `meta_json` | TEXT |  | ✓ |  |
| 11 | `created_at` | DATETIME |  | ✓ |  |
| 12 | `updated_at` | DATETIME |  | ✓ |  |

## model_usage_stats

**Rows:** 2

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `model_or_cli_name` | VARCHAR(255) |  |  |  |
| 2 | `kind` | VARCHAR(20) |  |  |  |
| 3 | `task_type` | VARCHAR(50) |  |  |  |
| 4 | `tokens_used` | INTEGER |  | ✓ |  |
| 5 | `latency_ms` | INTEGER |  | ✓ |  |
| 6 | `success` | BOOLEAN |  | ✓ |  |
| 7 | `error_message` | VARCHAR(500) |  | ✓ |  |
| 8 | `user_id` | VARCHAR(100) |  | ✓ |  |
| 9 | `created_at` | DATETIME |  | ✓ |  |

## models_local

**Rows:** 30

**Indices:** `sqlite_autoindex_models_local_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `name` | VARCHAR(255) |  |  |  |
| 2 | `path` | VARCHAR(512) |  |  |  |
| 3 | `size_mb` | INTEGER |  | ✓ |  |
| 4 | `hash` | VARCHAR(128) |  | ✓ |  |
| 5 | `category` | VARCHAR(64) |  | ✓ |  |
| 6 | `status` | VARCHAR(32) |  | ✓ |  |
| 7 | `compatibility` | VARCHAR(64) |  | ✓ |  |
| 8 | `downloaded_at` | DATETIME |  | ✓ |  |
| 9 | `updated_at` | DATETIME |  | ✓ |  |

## models_remote_cli

**Rows:** 0

**Indices:** `sqlite_autoindex_models_remote_cli_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `provider` | VARCHAR(128) |  |  |  |
| 2 | `token` | VARCHAR(256) |  |  |  |
| 3 | `limit_daily` | INTEGER |  | ✓ |  |
| 4 | `limit_weekly` | INTEGER |  | ✓ |  |
| 5 | `renew_at` | DATETIME |  | ✓ |  |
| 6 | `task_type` | VARCHAR(64) |  | ✓ |  |
| 7 | `status` | VARCHAR(32) |  | ✓ |  |
| 8 | `created_at` | DATETIME |  | ✓ |  |
| 9 | `updated_at` | DATETIME |  | ✓ |  |

## module_health

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `module` | VARCHAR(50) |  |  |  |
| 2 | `status` | VARCHAR(20) |  | ✓ |  |
| 3 | `last_ping` | DATETIME |  | ✓ |  |
| 4 | `error_count` | INTEGER |  | ✓ |  |
| 5 | `uptime_seconds` | FLOAT |  | ✓ |  |
| 6 | `updated_at` | DATETIME |  | ✓ |  |

## operator_browser_task

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `session_id` | VARCHAR(64) |  |  |  |
| 2 | `url` | VARCHAR(500) |  |  |  |
| 3 | `status` | VARCHAR(50) |  | ✓ |  |
| 4 | `snapshot_path` | VARCHAR(255) |  | ✓ |  |
| 5 | `result` | TEXT |  | ✓ |  |
| 6 | `error` | TEXT |  | ✓ |  |
| 7 | `created_at` | DATETIME |  | ✓ |  |
| 8 | `executed_at` | DATETIME |  | ✓ |  |

## operator_jobs

**Rows:** 0

**Indices:** `sqlite_autoindex_operator_jobs_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `job_id` | VARCHAR(64) |  |  |  |
| 2 | `intent` | VARCHAR(64) |  |  |  |
| 3 | `status` | VARCHAR(32) |  | ✓ |  |
| 4 | `payload` | TEXT |  | ✓ |  |
| 5 | `result` | TEXT |  | ✓ |  |
| 6 | `created_at` | DATETIME |  | ✓ |  |
| 7 | `updated_at` | DATETIME |  | ✓ |  |

## operator_message

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `session_id` | VARCHAR(64) |  |  |  |
| 2 | `role` | VARCHAR(50) |  |  |  |
| 3 | `content` | TEXT |  |  |  |
| 4 | `message_metadata` | TEXT |  | ✓ |  |
| 5 | `created_at` | DATETIME |  | ✓ |  |

## operator_session

**Rows:** 11

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `session_id` | VARCHAR(64) |  |  |  |
| 2 | `user_id` | VARCHAR(64) |  |  |  |
| 3 | `source` | VARCHAR(50) |  |  |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |
| 5 | `updated_at` | DATETIME |  | ✓ |  |

## operator_switch_adjustment

**Rows:** 11

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `session_id` | VARCHAR(64) |  |  |  |
| 2 | `message_id` | INTEGER |  | ✓ |  |
| 3 | `before_config` | TEXT |  |  |  |
| 4 | `after_config` | TEXT |  |  |  |
| 5 | `reason` | TEXT |  |  |  |
| 6 | `applied` | BOOLEAN |  | ✓ |  |
| 7 | `created_at` | DATETIME |  | ✓ |  |
| 8 | `applied_at` | DATETIME |  | ✓ |  |

## operator_tool_call

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `message_id` | INTEGER |  |  |  |
| 2 | `tool_name` | VARCHAR(100) |  |  |  |
| 3 | `status` | VARCHAR(50) |  | ✓ |  |
| 4 | `duration_ms` | INTEGER |  | ✓ |  |
| 5 | `result` | TEXT |  | ✓ |  |
| 6 | `error` | TEXT |  | ✓ |  |
| 7 | `created_at` | DATETIME |  | ✓ |  |

## pheromone_log

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `pheromone_type` | VARCHAR(64) |  |  |  |
| 2 | `intensity` | INTEGER |  | ✓ |  |
| 3 | `source_incident_ids` | TEXT |  | ✓ |  |
| 4 | `madre_intent_id` | VARCHAR(64) |  | ✓ |  |
| 5 | `switch_consultation_id` | VARCHAR(64) |  | ✓ |  |
| 6 | `payload` | TEXT |  | ✓ |  |
| 7 | `created_at` | DATETIME |  | ✓ |  |
| 8 | `executed_at` | DATETIME |  | ✓ |  |

## power_events

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `module` | VARCHAR(64) |  |  |  |
| 2 | `action` | VARCHAR(32) |  |  |  |
| 3 | `reason` | VARCHAR(255) |  | ✓ |  |
| 4 | `cpu_usage` | FLOAT |  | ✓ |  |
| 5 | `ram_usage` | FLOAT |  | ✓ |  |
| 6 | `activity_score` | FLOAT |  | ✓ |  |
| 7 | `timestamp` | DATETIME |  | ✓ |  |

## reports

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `task_id` | VARCHAR(36) |  |  |  |
| 2 | `report_type` | VARCHAR(50) |  |  |  |
| 3 | `summary` | TEXT |  | ✓ |  |
| 4 | `details` | TEXT |  | ✓ |  |
| 5 | `metrics` | TEXT |  | ✓ |  |
| 6 | `created_at` | DATETIME |  | ✓ |  |

## sandbox_exec

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `action` | VARCHAR(128) |  |  |  |
| 2 | `status` | VARCHAR(32) |  | ✓ |  |
| 3 | `duration_ms` | FLOAT |  | ✓ |  |
| 4 | `error` | TEXT |  | ✓ |  |
| 5 | `created_at` | DATETIME |  | ✓ |  |

## scheduler_history

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `timestamp` | DATETIME |  | ✓ |  |
| 2 | `action` | VARCHAR(64) |  |  |  |
| 3 | `reason` | TEXT |  | ✓ |  |
| 4 | `metrics` | TEXT |  | ✓ |  |

## shub_analysis

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `track_id` | INTEGER |  |  |  |
| 2 | `rms` | FLOAT |  | ✓ |  |
| 3 | `peak` | FLOAT |  | ✓ |  |
| 4 | `lufs` | FLOAT |  | ✓ |  |
| 5 | `noise_floor` | FLOAT |  | ✓ |  |
| 6 | `dynamic_range` | FLOAT |  | ✓ |  |
| 7 | `clipping` | INTEGER |  | ✓ |  |
| 8 | `notes` | TEXT |  | ✓ |  |
| 9 | `created_at` | DATETIME |  | ✓ |  |

## shub_fx_chains

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `track_id` | INTEGER |  |  |  |
| 2 | `chain_name` | VARCHAR(255) |  |  |  |
| 3 | `steps_json` | TEXT |  |  |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |

## shub_presets

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `fx_chain_id` | INTEGER |  |  |  |
| 2 | `rpp_snippet` | TEXT |  | ✓ |  |
| 3 | `version` | VARCHAR(32) |  | ✓ |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |

## shub_projects

**Rows:** 0

**Indices:** `sqlite_autoindex_shub_projects_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `project_id` | VARCHAR(64) |  |  |  |
| 2 | `name` | VARCHAR(255) |  |  |  |
| 3 | `sample_rate` | INTEGER |  | ✓ |  |
| 4 | `created_at` | DATETIME |  | ✓ |  |
| 5 | `updated_at` | DATETIME |  | ✓ |  |

## shub_tracks

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `project_id` | VARCHAR(64) |  |  |  |
| 2 | `name` | VARCHAR(255) |  |  |  |
| 3 | `role` | VARCHAR(64) |  | ✓ |  |
| 4 | `file_path` | VARCHAR(512) |  | ✓ |  |
| 5 | `duration_sec` | FLOAT |  | ✓ |  |
| 6 | `created_at` | DATETIME |  | ✓ |  |

## spawns

**Rows:** 0

**Indices:** `sqlite_autoindex_spawns_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `uuid` | VARCHAR(36) |  |  |  |
| 2 | `name` | VARCHAR(255) |  |  |  |
| 3 | `cmd` | VARCHAR(500) |  |  |  |
| 4 | `pid` | INTEGER |  | ✓ |  |
| 5 | `status` | VARCHAR(20) |  | ✓ |  |
| 6 | `started_at` | DATETIME |  | ✓ |  |
| 7 | `ended_at` | DATETIME |  | ✓ |  |
| 8 | `exit_code` | INTEGER |  | ✓ |  |
| 9 | `stdout` | TEXT |  | ✓ |  |
| 10 | `stderr` | TEXT |  | ✓ |  |
| 11 | `parent_task_id` | VARCHAR(36) |  | ✓ |  |
| 12 | `created_at` | DATETIME |  | ✓ |  |

## switch_queue_v2

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `source` | VARCHAR(64) |  |  |  |
| 2 | `priority` | INTEGER |  | ✓ |  |
| 3 | `task_type` | VARCHAR(50) |  |  |  |
| 4 | `payload_hash` | VARCHAR(64) |  |  |  |
| 5 | `status` | VARCHAR(32) |  | ✓ |  |
| 6 | `created_at` | DATETIME |  | ✓ |  |
| 7 | `started_at` | DATETIME |  | ✓ |  |
| 8 | `finished_at` | DATETIME |  | ✓ |  |
| 9 | `result_size` | INTEGER |  | ✓ |  |
| 10 | `error_message` | VARCHAR(500) |  | ✓ |  |

## system_events

**Rows:** 16

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `timestamp` | DATETIME |  | ✓ |  |
| 2 | `source` | VARCHAR(64) |  |  |  |
| 3 | `event_type` | VARCHAR(64) |  |  |  |
| 4 | `payload` | TEXT |  | ✓ |  |
| 5 | `severity` | VARCHAR(16) |  | ✓ |  |

## system_state

**Rows:** 0

**Indices:** `sqlite_autoindex_system_state_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `key` | VARCHAR(128) |  |  |  |
| 2 | `value` | TEXT |  | ✓ |  |
| 3 | `updated_at` | DATETIME |  | ✓ |  |
| 4 | `memory_pressure` | FLOAT |  | ✓ |  |
| 5 | `cpu_pressure` | FLOAT |  | ✓ |  |
| 6 | `switch_queue_level` | FLOAT |  | ✓ |  |
| 7 | `hermes_update_required` | BOOLEAN |  | ✓ |  |
| 8 | `shub_pipeline_state` | VARCHAR(64) |  | ✓ |  |
| 9 | `operator_active` | BOOLEAN |  | ✓ |  |
| 10 | `system_load_score` | FLOAT |  | ✓ |  |
| 11 | `model_rotation_state` | VARCHAR(128) |  | ✓ |  |
| 12 | `audio_pipeline_state` | VARCHAR(128) |  | ✓ |  |
| 13 | `pending_tasks` | INTEGER |  | ✓ |  |
| 14 | `active_children` | INTEGER |  | ✓ |  |
| 15 | `last_operator_activity` | DATETIME |  | ✓ |  |
| 16 | `power_mode` | VARCHAR(32) |  | ✓ |  |

## task_queue

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `source` | VARCHAR(64) |  |  |  |
| 2 | `priority` | INTEGER |  | ✓ |  |
| 3 | `payload` | TEXT |  |  |  |
| 4 | `status` | VARCHAR(32) |  | ✓ |  |
| 5 | `enqueued_at` | DATETIME |  | ✓ |  |
| 6 | `dequeued_at` | DATETIME |  | ✓ |  |

## tasks

**Rows:** 0

**Indices:** `sqlite_autoindex_tasks_1`

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `uuid` | VARCHAR(36) |  |  |  |
| 2 | `name` | VARCHAR(255) |  |  |  |
| 3 | `module` | VARCHAR(50) |  |  |  |
| 4 | `action` | VARCHAR(100) |  |  |  |
| 5 | `status` | VARCHAR(20) |  | ✓ |  |
| 6 | `created_at` | DATETIME |  | ✓ |  |
| 7 | `updated_at` | DATETIME |  | ✓ |  |
| 8 | `result` | TEXT |  | ✓ |  |
| 9 | `error` | TEXT |  | ✓ |  |

## tokens_usage

**Rows:** 0

### Columns

| # | Name | Type | PK | Nullable | Default |
|---|------|------|----|---------|---------|
| 0 | `id` | INTEGER | ✓ |  |  |
| 1 | `token_id` | VARCHAR(256) |  |  |  |
| 2 | `used_at` | DATETIME |  | ✓ |  |
| 3 | `used_count` | INTEGER |  | ✓ |  |
| 4 | `source` | VARCHAR(64) |  | ✓ |  |

---

## Summary Statistics

- **Total Tables:** 50
- **Total Rows:** 90
- **Database Size:** 0.3MB
