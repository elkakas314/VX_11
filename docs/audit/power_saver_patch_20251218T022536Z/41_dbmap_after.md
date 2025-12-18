# VX11 Database Map (generated)

Generated at: 2025-12-18T02:29:35.074935Z

Database file: data/runtime/vx11.db

## Tables

### audit_logs — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - component (VARCHAR(64)) NOT NULL
  - level (VARCHAR(16))
  - message (TEXT) NOT NULL
  - created_at (DATETIME)

### chat_providers_stats — EMPTY (READY)

- Rows: 0
- Columns:
  - provider (TEXT) PK
  - success_count (INTEGER)
  - fail_count (INTEGER)
  - avg_latency_ms (REAL)

### cli_onboarding_state — EMPTY (READY)

- Module: hermes
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - provider_id (VARCHAR(128)) NOT NULL
  - state (VARCHAR(50))
  - notes (TEXT)
  - last_checked_at (DATETIME)
  - created_at (DATETIME)

### cli_providers — ACTIVE

- Module: hermes
- Rows: 1
- Columns:
  - id (INTEGER) PK NOT NULL
  - name (VARCHAR(100)) NOT NULL
  - base_url (VARCHAR(500))
  - api_key_env (VARCHAR(100)) NOT NULL
  - task_types (VARCHAR(255))
  - daily_limit_tokens (INTEGER)
  - monthly_limit_tokens (INTEGER)
  - tokens_used_today (INTEGER)
  - tokens_used_month (INTEGER)
  - reset_hour_utc (INTEGER)
  - enabled (BOOLEAN)
  - last_reset_at (DATETIME)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### cli_registry — EMPTY (READY)

- Module: hermes
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - name (VARCHAR(100)) NOT NULL
  - bin_path (VARCHAR(500))
  - available (BOOLEAN)
  - last_checked (DATETIME)
  - cli_type (VARCHAR(50)) NOT NULL
  - token_config_key (VARCHAR(100))
  - rate_limit_daily (INTEGER)
  - used_today (INTEGER)
  - notes (TEXT)
  - updated_at (DATETIME)

### cli_usage_stats — ACTIVE

- Module: hermes
- Rows: 146
- Columns:
  - id (INTEGER) PK NOT NULL
  - provider_id (VARCHAR(128)) NOT NULL
  - timestamp (DATETIME)
  - success (BOOLEAN)
  - latency_ms (INTEGER)
  - cost_estimated (FLOAT)
  - tokens_estimated (INTEGER)
  - error_class (VARCHAR(100))

### context — ACTIVE

- Rows: 6
- Columns:
  - id (INTEGER) PK NOT NULL
  - task_id (VARCHAR(36)) NOT NULL
  - key (VARCHAR(255)) NOT NULL
  - value (TEXT) NOT NULL
  - scope (VARCHAR(50))
  - created_at (DATETIME)
- Foreign keys:
  - task_id -> tasks.uuid (on_update=NO ACTION, on_delete=NO ACTION)

### copilot_actions_log — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK
  - session_id (TEXT)
  - timestamp (TIMESTAMP)
  - action (TEXT)
  - mode (TEXT)
  - files_touched (INTEGER)
  - git_commit (TEXT)
  - status (TEXT)
  - notes (TEXT)

### copilot_repo_map — ACTIVE

- Rows: 983
- Columns:
  - id (INTEGER) PK
  - path (TEXT)
  - file_hash (TEXT)
  - file_type (TEXT)
  - status (TEXT)
  - created_at (TIMESTAMP)
  - updated_at (TIMESTAMP)
  - content (TEXT)
  - meta_json (TEXT)

### copilot_runtime_services — ACTIVE

- Rows: 12
- Columns:
  - id (INTEGER) PK
  - service_name (TEXT)
  - host (TEXT)
  - port (INTEGER)
  - health_url (TEXT)
  - status (TEXT)
  - last_check (TIMESTAMP)
  - created_at (TIMESTAMP)
  - http_code (INTEGER)
  - latency_ms (INTEGER)
  - endpoint_ok (TEXT)
  - snippet (TEXT)
  - checked_at (TIMESTAMP)

### copilot_workflows_catalog — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK
  - workflow_file (TEXT)
  - workflow_name (TEXT)
  - triggers (TEXT)
  - jobs (TEXT)
  - created_at (TIMESTAMP)

### daughter_attempts — ACTIVE

- Rows: 127
- Columns:
  - id (INTEGER) PK NOT NULL
  - daughter_id (INTEGER) NOT NULL
  - attempt_number (INTEGER)
  - started_at (DATETIME)
  - finished_at (DATETIME)
  - status (VARCHAR(32))
  - error_message (VARCHAR(500))
  - tokens_used_cli (INTEGER)
  - tokens_used_local (INTEGER)
  - switch_model_used (VARCHAR(128))
  - cli_provider_used (VARCHAR(128))
  - created_at (DATETIME)
- Foreign keys:
  - daughter_id -> daughters.id (on_update=NO ACTION, on_delete=NO ACTION)

### daughter_tasks — ACTIVE

- Rows: 83
- Columns:
  - id (INTEGER) PK NOT NULL
  - intent_id (VARCHAR(36))
  - source (VARCHAR(64)) NOT NULL
  - priority (INTEGER)
  - status (VARCHAR(32))
  - task_type (VARCHAR(50)) NOT NULL
  - description (TEXT)
  - created_at (DATETIME)
  - updated_at (DATETIME)
  - finished_at (DATETIME)
  - max_retries (INTEGER)
  - current_retry (INTEGER)
  - metadata_json (TEXT)
  - plan_json (TEXT)

### daughters — ACTIVE

- Rows: 127
- Columns:
  - id (INTEGER) PK NOT NULL
  - task_id (INTEGER) NOT NULL
  - name (VARCHAR(128)) NOT NULL
  - purpose (TEXT)
  - tools_json (TEXT)
  - ttl_seconds (INTEGER)
  - started_at (DATETIME)
  - last_heartbeat_at (DATETIME)
  - ended_at (DATETIME)
  - status (VARCHAR(32))
  - mutation_level (INTEGER)
  - error_last (TEXT)
- Foreign keys:
  - task_id -> daughter_tasks.id (on_update=NO ACTION, on_delete=NO ACTION)

### drift_reports — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - module (VARCHAR(64)) NOT NULL
  - details (TEXT) NOT NULL
  - severity (VARCHAR(32))
  - timestamp (DATETIME)
  - resolved (BOOLEAN)

### engines — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - name (VARCHAR(128)) NOT NULL
  - engine_type (VARCHAR(32)) NOT NULL
  - domain (VARCHAR(64)) NOT NULL
  - endpoint (VARCHAR(256)) NOT NULL
  - version (VARCHAR(32))
  - quota_tokens_per_day (INTEGER)
  - quota_used_today (INTEGER)
  - quota_reset_at (DATETIME)
  - latency_ms (FLOAT)
  - cost_per_call (FLOAT)
  - enabled (BOOLEAN)
  - last_used (DATETIME)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### events — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - source (VARCHAR(64)) NOT NULL
  - event_type (VARCHAR(64)) NOT NULL
  - payload (TEXT)
  - created_at (DATETIME)

### feromona_events — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - type (VARCHAR(64)) NOT NULL
  - intensity (INTEGER)
  - module (VARCHAR(64)) NOT NULL
  - payload (TEXT)
  - timestamp (DATETIME)

### fluzo_signals — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - timestamp (DATETIME)
  - cpu_load_1m (FLOAT)
  - mem_pct (FLOAT)
  - on_ac (BOOLEAN)
  - battery_pct (INTEGER)
  - profile (VARCHAR(32))

### forensic_ledger — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - event (VARCHAR(255)) NOT NULL
  - payload (TEXT)
  - hash (VARCHAR(64)) NOT NULL
  - created_at (DATETIME)

### hermes_ingest — EMPTY (READY)

- Module: hermes
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - path (VARCHAR(512)) NOT NULL
  - size_bytes (INTEGER)
  - duration_sec (FLOAT)
  - status (VARCHAR(32))
  - created_at (DATETIME)

### hijas_runtime — ACTIVE

- Module: hormiguero
- Rows: 12
- Columns:
  - id (INTEGER) PK NOT NULL
  - name (VARCHAR(128)) NOT NULL
  - state (VARCHAR(32))
  - pid (INTEGER)
  - last_heartbeat (DATETIME)
  - meta_json (TEXT)
  - birth_context (TEXT)
  - death_context (TEXT)
  - intent_type (VARCHAR(64))
  - ttl (INTEGER)
  - killed_by (VARCHAR(128))
  - purpose (VARCHAR(256))
  - module_creator (VARCHAR(64))
  - born_at (DATETIME)
  - died_at (DATETIME)

### hijas_state — EMPTY (READY)

- Module: hormiguero
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - hija_id (VARCHAR(64)) NOT NULL
  - module (VARCHAR(64)) NOT NULL
  - status (VARCHAR(32))
  - cpu_usage (FLOAT)
  - ram_usage (FLOAT)
  - pid (INTEGER)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### hormiga_state — ACTIVE

- Rows: 8
- Columns:
  - id (INTEGER) PK NOT NULL
  - ant_id (VARCHAR(64)) NOT NULL
  - role (VARCHAR(32)) NOT NULL
  - status (VARCHAR(20))
  - last_scan_at (DATETIME)
  - mutation_level (INTEGER)
  - cpu_percent (FLOAT)
  - ram_percent (FLOAT)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### ia_decisions — ACTIVE

- Module: switch
- Rows: 10216
- Columns:
  - id (INTEGER) PK NOT NULL
  - prompt_hash (VARCHAR(64)) NOT NULL
  - provider (VARCHAR(50)) NOT NULL
  - task_type (VARCHAR(50))
  - prompt (TEXT) NOT NULL
  - response (TEXT)
  - latency_ms (INTEGER)
  - success (BOOLEAN)
  - confidence (FLOAT)
  - meta_json (TEXT)
  - created_at (DATETIME)

### incidents — ACTIVE

- Rows: 1123263
- Columns:
  - id (INTEGER) PK NOT NULL
  - ant_id (VARCHAR(64)) NOT NULL
  - incident_type (VARCHAR(64)) NOT NULL
  - severity (VARCHAR(20))
  - location (VARCHAR(255))
  - details (TEXT)
  - status (VARCHAR(20))
  - detected_at (DATETIME)
  - resolved_at (DATETIME)
  - queen_decision (VARCHAR(255))

### intents_log — ACTIVE

- Rows: 83
- Columns:
  - id (INTEGER) PK NOT NULL
  - source (VARCHAR(64)) NOT NULL
  - payload_json (TEXT) NOT NULL
  - created_at (DATETIME)
  - processed_by_madre_at (DATETIME)
  - result_status (VARCHAR(32))
  - notes (TEXT)

### local_models_v2 — EMPTY (READY)

- Module: hermes
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - name (VARCHAR(255)) NOT NULL
  - engine (VARCHAR(50)) NOT NULL
  - path (VARCHAR(512)) NOT NULL
  - size_bytes (INTEGER) NOT NULL
  - task_type (VARCHAR(50)) NOT NULL
  - max_context (INTEGER)
  - enabled (BOOLEAN)
  - last_used_at (DATETIME)
  - usage_count (INTEGER)
  - compatibility (VARCHAR(64))
  - meta_info (TEXT)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### madre_actions — ACTIVE

- Module: madre
- Rows: 49
- Columns:
  - id (INTEGER) PK NOT NULL
  - module (VARCHAR(64)) NOT NULL
  - action (VARCHAR(64)) NOT NULL
  - reason (VARCHAR(255))
  - created_at (DATETIME)

### madre_policies — ACTIVE

- Module: madre
- Rows: 10
- Columns:
  - id (INTEGER) PK NOT NULL
  - module (VARCHAR(64)) NOT NULL
  - error_threshold (INTEGER)
  - idle_seconds (INTEGER)
  - enable_autosuspend (BOOLEAN)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### model_registry — EMPTY (READY)

- Module: hermes
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - name (VARCHAR(255)) NOT NULL
  - path (VARCHAR(500)) NOT NULL
  - provider (VARCHAR(50)) NOT NULL
  - type (VARCHAR(50)) NOT NULL
  - size_bytes (INTEGER) NOT NULL
  - tags (TEXT)
  - last_used (DATETIME)
  - score (FLOAT)
  - available (BOOLEAN)
  - meta_json (TEXT)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### model_usage_stats — ACTIVE

- Module: hermes
- Rows: 10216
- Columns:
  - id (INTEGER) PK NOT NULL
  - model_or_cli_name (VARCHAR(255)) NOT NULL
  - kind (VARCHAR(20)) NOT NULL
  - task_type (VARCHAR(50)) NOT NULL
  - tokens_used (INTEGER)
  - latency_ms (INTEGER)
  - success (BOOLEAN)
  - error_message (VARCHAR(500))
  - user_id (VARCHAR(100))
  - created_at (DATETIME)

### models_local — ACTIVE

- Module: hermes
- Rows: 30
- Columns:
  - id (INTEGER) PK NOT NULL
  - name (VARCHAR(255)) NOT NULL
  - path (VARCHAR(512)) NOT NULL
  - size_mb (INTEGER)
  - hash (VARCHAR(128))
  - category (VARCHAR(64))
  - status (VARCHAR(32))
  - compatibility (VARCHAR(64))
  - downloaded_at (DATETIME)
  - updated_at (DATETIME)

### models_remote_cli — EMPTY (READY)

- Module: hermes
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - provider (VARCHAR(128)) NOT NULL
  - token (VARCHAR(256)) NOT NULL
  - limit_daily (INTEGER)
  - limit_weekly (INTEGER)
  - renew_at (DATETIME)
  - task_type (VARCHAR(64))
  - status (VARCHAR(32))
  - created_at (DATETIME)
  - updated_at (DATETIME)

### module_health — ACTIVE

- Rows: 1
- Columns:
  - id (INTEGER) PK NOT NULL
  - module (VARCHAR(50)) NOT NULL
  - status (VARCHAR(20))
  - last_ping (DATETIME)
  - error_count (INTEGER)
  - uptime_seconds (FLOAT)
  - updated_at (DATETIME)

### operator_browser_task — ACTIVE

- Module: operator
- Rows: 20
- Columns:
  - id (INTEGER) PK NOT NULL
  - session_id (VARCHAR(64)) NOT NULL
  - url (VARCHAR(500)) NOT NULL
  - status (VARCHAR(50))
  - snapshot_path (VARCHAR(255))
  - result (TEXT)
  - error (TEXT)
  - created_at (DATETIME)
  - executed_at (DATETIME)
- Foreign keys:
  - session_id -> operator_session.session_id (on_update=NO ACTION, on_delete=NO ACTION)

### operator_jobs — EMPTY (READY)

- Module: operator
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - job_id (VARCHAR(64)) NOT NULL
  - intent (VARCHAR(64)) NOT NULL
  - status (VARCHAR(32))
  - payload (TEXT)
  - result (TEXT)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### operator_message — ACTIVE

- Module: operator
- Rows: 74
- Columns:
  - id (INTEGER) PK NOT NULL
  - session_id (VARCHAR(64)) NOT NULL
  - role (VARCHAR(50)) NOT NULL
  - content (TEXT) NOT NULL
  - message_metadata (TEXT)
  - created_at (DATETIME)
- Foreign keys:
  - session_id -> operator_session.session_id (on_update=NO ACTION, on_delete=NO ACTION)

### operator_session — ACTIVE

- Module: operator
- Rows: 118
- Columns:
  - id (INTEGER) PK NOT NULL
  - session_id (VARCHAR(64)) NOT NULL
  - user_id (VARCHAR(64)) NOT NULL
  - source (VARCHAR(50)) NOT NULL
  - created_at (DATETIME)
  - updated_at (DATETIME)

### operator_switch_adjustment — ACTIVE

- Module: operator
- Rows: 20
- Columns:
  - id (INTEGER) PK NOT NULL
  - session_id (VARCHAR(64)) NOT NULL
  - message_id (INTEGER)
  - before_config (TEXT) NOT NULL
  - after_config (TEXT) NOT NULL
  - reason (TEXT) NOT NULL
  - applied (BOOLEAN)
  - created_at (DATETIME)
  - applied_at (DATETIME)
- Foreign keys:
  - message_id -> operator_message.id (on_update=NO ACTION, on_delete=NO ACTION)
  - session_id -> operator_session.session_id (on_update=NO ACTION, on_delete=NO ACTION)

### operator_tool_call — ACTIVE

- Module: operator
- Rows: 20
- Columns:
  - id (INTEGER) PK NOT NULL
  - message_id (INTEGER) NOT NULL
  - tool_name (VARCHAR(100)) NOT NULL
  - status (VARCHAR(50))
  - duration_ms (INTEGER)
  - result (TEXT)
  - error (TEXT)
  - created_at (DATETIME)
- Foreign keys:
  - message_id -> operator_message.id (on_update=NO ACTION, on_delete=NO ACTION)

### pheromone_log — ACTIVE

- Rows: 1122703
- Columns:
  - id (INTEGER) PK NOT NULL
  - pheromone_type (VARCHAR(64)) NOT NULL
  - intensity (INTEGER)
  - source_incident_ids (TEXT)
  - madre_intent_id (VARCHAR(64))
  - switch_consultation_id (VARCHAR(64))
  - payload (TEXT)
  - created_at (DATETIME)
  - executed_at (DATETIME)

### power_events — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - module (VARCHAR(64)) NOT NULL
  - action (VARCHAR(32)) NOT NULL
  - reason (VARCHAR(255))
  - cpu_usage (FLOAT)
  - ram_usage (FLOAT)
  - activity_score (FLOAT)
  - timestamp (DATETIME)

### reports — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - task_id (VARCHAR(36)) NOT NULL
  - report_type (VARCHAR(50)) NOT NULL
  - summary (TEXT)
  - details (TEXT)
  - metrics (TEXT)
  - created_at (DATETIME)
- Foreign keys:
  - task_id -> tasks.uuid (on_update=NO ACTION, on_delete=NO ACTION)

### routing_events — ACTIVE

- Rows: 41
- Columns:
  - id (INTEGER) PK NOT NULL
  - timestamp (DATETIME)
  - trace_id (VARCHAR(36)) NOT NULL
  - route_type (VARCHAR(50)) NOT NULL
  - provider_id (VARCHAR(128)) NOT NULL
  - score (FLOAT)
  - reasoning_short (VARCHAR(255))

### sandbox_exec — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - action (VARCHAR(128)) NOT NULL
  - status (VARCHAR(32))
  - duration_ms (FLOAT)
  - error (TEXT)
  - created_at (DATETIME)

### scheduler_history — ACTIVE

- Rows: 5225
- Columns:
  - id (INTEGER) PK NOT NULL
  - timestamp (DATETIME)
  - action (VARCHAR(64)) NOT NULL
  - reason (TEXT)
  - metrics (TEXT)

### shub_analysis — EMPTY (READY)

- Module: shubniggurath
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - track_id (INTEGER) NOT NULL
  - rms (FLOAT)
  - peak (FLOAT)
  - lufs (FLOAT)
  - noise_floor (FLOAT)
  - dynamic_range (FLOAT)
  - clipping (INTEGER)
  - notes (TEXT)
  - created_at (DATETIME)
- Foreign keys:
  - track_id -> shub_tracks.id (on_update=NO ACTION, on_delete=NO ACTION)

### shub_fx_chains — EMPTY (READY)

- Module: shubniggurath
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - track_id (INTEGER) NOT NULL
  - chain_name (VARCHAR(255)) NOT NULL
  - steps_json (TEXT) NOT NULL
  - created_at (DATETIME)
- Foreign keys:
  - track_id -> shub_tracks.id (on_update=NO ACTION, on_delete=NO ACTION)

### shub_presets — EMPTY (READY)

- Module: shubniggurath
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - fx_chain_id (INTEGER) NOT NULL
  - rpp_snippet (TEXT)
  - version (VARCHAR(32))
  - created_at (DATETIME)
- Foreign keys:
  - fx_chain_id -> shub_fx_chains.id (on_update=NO ACTION, on_delete=NO ACTION)

### shub_projects — EMPTY (READY)

- Module: shubniggurath
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - project_id (VARCHAR(64)) NOT NULL
  - name (VARCHAR(255)) NOT NULL
  - sample_rate (INTEGER)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### shub_tracks — EMPTY (READY)

- Module: shubniggurath
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - project_id (VARCHAR(64)) NOT NULL
  - name (VARCHAR(255)) NOT NULL
  - role (VARCHAR(64))
  - file_path (VARCHAR(512))
  - duration_sec (FLOAT)
  - created_at (DATETIME)
- Foreign keys:
  - project_id -> shub_projects.project_id (on_update=NO ACTION, on_delete=NO ACTION)

### spawns — ACTIVE

- Rows: 19
- Columns:
  - id (INTEGER) PK NOT NULL
  - uuid (VARCHAR(36)) NOT NULL
  - name (VARCHAR(255)) NOT NULL
  - cmd (VARCHAR(500)) NOT NULL
  - pid (INTEGER)
  - status (VARCHAR(20))
  - started_at (DATETIME)
  - ended_at (DATETIME)
  - exit_code (INTEGER)
  - stdout (TEXT)
  - stderr (TEXT)
  - parent_task_id (VARCHAR(36))
  - created_at (DATETIME)
- Foreign keys:
  - parent_task_id -> tasks.uuid (on_update=NO ACTION, on_delete=NO ACTION)

### switch_queue_v2 — ACTIVE

- Module: switch
- Rows: 10216
- Columns:
  - id (INTEGER) PK NOT NULL
  - source (VARCHAR(64)) NOT NULL
  - priority (INTEGER)
  - task_type (VARCHAR(50)) NOT NULL
  - payload_hash (VARCHAR(64)) NOT NULL
  - status (VARCHAR(32))
  - created_at (DATETIME)
  - started_at (DATETIME)
  - finished_at (DATETIME)
  - result_size (INTEGER)
  - error_message (VARCHAR(500))

### system_events — ACTIVE

- Rows: 12
- Columns:
  - id (INTEGER) PK NOT NULL
  - timestamp (DATETIME)
  - source (VARCHAR(64)) NOT NULL
  - event_type (VARCHAR(64)) NOT NULL
  - payload (TEXT)
  - severity (VARCHAR(16))

### system_state — ACTIVE

- Rows: 2
- Columns:
  - id (INTEGER) PK NOT NULL
  - key (VARCHAR(128)) NOT NULL
  - value (TEXT)
  - updated_at (DATETIME)
  - memory_pressure (FLOAT)
  - cpu_pressure (FLOAT)
  - switch_queue_level (FLOAT)
  - hermes_update_required (BOOLEAN)
  - shub_pipeline_state (VARCHAR(64))
  - operator_active (BOOLEAN)
  - system_load_score (FLOAT)
  - model_rotation_state (VARCHAR(128))
  - audio_pipeline_state (VARCHAR(128))
  - pending_tasks (INTEGER)
  - active_children (INTEGER)
  - last_operator_activity (DATETIME)
  - power_mode (VARCHAR(32))

### task_queue — ACTIVE

- Rows: 21
- Columns:
  - id (INTEGER) PK NOT NULL
  - source (VARCHAR(64)) NOT NULL
  - priority (INTEGER)
  - payload (TEXT) NOT NULL
  - status (VARCHAR(32))
  - enqueued_at (DATETIME)
  - dequeued_at (DATETIME)

### tasks — ACTIVE

- Rows: 20
- Columns:
  - id (INTEGER) PK NOT NULL
  - uuid (VARCHAR(36)) NOT NULL
  - name (VARCHAR(255)) NOT NULL
  - module (VARCHAR(50)) NOT NULL
  - action (VARCHAR(100)) NOT NULL
  - status (VARCHAR(20))
  - created_at (DATETIME)
  - updated_at (DATETIME)
  - result (TEXT)
  - error (TEXT)

### tokens_usage — EMPTY (READY)

- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - token_id (VARCHAR(256)) NOT NULL
  - used_at (DATETIME)
  - used_count (INTEGER)
  - source (VARCHAR(64))

