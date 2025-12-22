# VX11 Database Map (generated)

Generated at: 2025-12-22T04:56:36.912761Z

Database file: data/runtime/vx11.db

## Tables

### audit_logs — EMPTY (READY)

- Module: madre
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - component (VARCHAR(64)) NOT NULL
  - level (VARCHAR(16))
  - message (TEXT) NOT NULL
  - created_at (DATETIME)

### canonical_docs — ACTIVE

- Rows: 6
- Columns:
  - doc_type (TEXT) PK
  - version (TEXT)
  - sha256 (TEXT)
  - content_json (TEXT)
  - source_path (TEXT)
  - created_at_utc (TEXT)
  - git_head (TEXT)

### canonical_docs_legacy_20251220T212937Z — LEGACY - preserved

- Rows: 12
- Columns:
  - canonical_version (TEXT) PK
  - doc_path (TEXT) PK
  - sha256 (TEXT)
  - size_bytes (INTEGER)
  - created_at_utc (TEXT)
  - doc_type (TEXT)
  - version (TEXT)
  - json (TEXT)
  - source_path (TEXT)
  - content_json (TEXT)
  - git_head (TEXT)

### canonical_kv — ACTIVE

- Rows: 18
- Columns:
  - key (TEXT) PK
  - value (TEXT)
  - updated_at_utc (TEXT)

### canonical_registry — ACTIVE

- Rows: 1
- Columns:
  - canonical_version (TEXT) PK
  - git_commit (TEXT)
  - git_branch (TEXT)
  - master_path (TEXT)
  - master_sha256 (TEXT)
  - created_at_utc (TEXT)

### canonical_runs — ACTIVE

- Rows: 8
- Columns:
  - run_id (TEXT) PK
  - canonical_version (TEXT)
  - outdir (TEXT)
  - started_at_utc (TEXT)
  - ended_at_utc (TEXT)
  - coverage_pct (REAL)
  - global_parcial_pct (REAL)
  - global_ponderado_pct (REAL)
  - metrics_json (TEXT)
  - git_head (TEXT)
  - results_json (TEXT)
  - finished_at_utc (TEXT)
  - percentages_json (TEXT)

### chat_providers_stats — ACTIVE

- Module: switch
- Rows: 1
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
- Rows: 287
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

- Module: madre
- Rows: 12
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

- Module: mcp
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

- Module: mcp
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

- Module: madre
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

- Module: mcp
- Rows: 0
- Columns:
  - id (INTEGER) PK
  - workflow_file (TEXT)
  - workflow_name (TEXT)
  - triggers (TEXT)
  - jobs (TEXT)
  - created_at (TIMESTAMP)

### daughter_attempts — ACTIVE

- Module: spawner
- Rows: 151
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

- Module: spawner
- Rows: 101
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

- Module: spawner
- Rows: 151
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

- Module: manifestator
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - module (VARCHAR(64)) NOT NULL
  - details (TEXT) NOT NULL
  - severity (VARCHAR(32))
  - timestamp (DATETIME)
  - resolved (BOOLEAN)

### engines — EMPTY (READY)

- Module: switch
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

- Module: tentaculo_link
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - source (VARCHAR(64)) NOT NULL
  - event_type (VARCHAR(64)) NOT NULL
  - payload (TEXT)
  - created_at (DATETIME)

### feromona_events — EMPTY (READY)

- Module: hormiguero
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - type (VARCHAR(64)) NOT NULL
  - intensity (INTEGER)
  - module (VARCHAR(64)) NOT NULL
  - payload (TEXT)
  - timestamp (DATETIME)
  - kind (TEXT)
  - scope (TEXT)
  - payload_json (TEXT)
  - source (TEXT)
  - created_at (DATETIME)

### fluzo_signals — EMPTY (READY)

- Module: switch
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

- Module: mcp
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
- Rows: 26
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

### hijas_state — ACTIVE

- Module: hormiguero
- Rows: 14
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

- Module: hormiguero
- Rows: 11
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
  - hormiga_id (TEXT)
  - name (TEXT)
  - enabled (INTEGER)
  - aggression_level (INTEGER)
  - scan_interval_sec (INTEGER)
  - last_ok_at (DATETIME)
  - last_error_at (DATETIME)
  - last_error (TEXT)
  - stats_json (TEXT)

### ia_decisions — ACTIVE

- Module: switch
- Rows: 10217
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

- Module: hormiguero
- Rows: 1126461
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
  - incident_id (TEXT)
  - kind (TEXT)
  - title (TEXT)
  - description (TEXT)
  - evidence_json (TEXT)
  - source (TEXT)
  - first_seen_at (DATETIME)
  - last_seen_at (DATETIME)
  - correlation_id (TEXT)
  - tags (TEXT)
  - suggested_actions_json (TEXT)
  - execution_plan_json (TEXT)
  - created_at (DATETIME)
  - updated_at (DATETIME)

### intents_log — ACTIVE

- Module: madre
- Rows: 102
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
- Rows: 52
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
- Rows: 10217
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

- Module: madre
- Rows: 1
- Columns:
  - id (INTEGER) PK NOT NULL
  - module (VARCHAR(50)) NOT NULL
  - status (VARCHAR(20))
  - last_ping (DATETIME)
  - error_count (INTEGER)
  - uptime_seconds (FLOAT)
  - updated_at (DATETIME)

### module_status — ACTIVE

- Module: madre
- Rows: 11
- Columns:
  - module_name (TEXT) PK
  - service_name (TEXT)
  - port (INTEGER)
  - health_url (TEXT)
  - status (TEXT) NOT NULL
  - checked_at_utc (TEXT) NOT NULL
  - notes (TEXT)
  - report_path (TEXT)

### operator_browser_task — ACTIVE

- Module: operator
- Rows: 43
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
- Rows: 120
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
- Rows: 123
- Columns:
  - id (INTEGER) PK NOT NULL
  - session_id (VARCHAR(64)) NOT NULL
  - user_id (VARCHAR(64)) NOT NULL
  - source (VARCHAR(50)) NOT NULL
  - created_at (DATETIME)
  - updated_at (DATETIME)

### operator_switch_adjustment — ACTIVE

- Module: operator
- Rows: 43
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
- Rows: 43
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

- Module: hormiguero
- Rows: 1125692
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
  - pheromone_id (TEXT)
  - incident_id (TEXT)
  - action_kind (TEXT)
  - action_payload_json (TEXT)
  - requested_by (TEXT)
  - approved_by (TEXT)
  - status (TEXT)
  - result_json (TEXT)
  - updated_at (DATETIME)

### power_events — EMPTY (READY)

- Module: madre
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

- Module: madre
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

- Module: switch
- Rows: 67
- Columns:
  - id (INTEGER) PK NOT NULL
  - timestamp (DATETIME)
  - trace_id (VARCHAR(36)) NOT NULL
  - route_type (VARCHAR(50)) NOT NULL
  - provider_id (VARCHAR(128)) NOT NULL
  - score (FLOAT)
  - reasoning_short (VARCHAR(255))

### sandbox_exec — EMPTY (READY)

- Module: mcp
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - action (VARCHAR(128)) NOT NULL
  - status (VARCHAR(32))
  - duration_ms (FLOAT)
  - error (TEXT)
  - created_at (DATETIME)

### scheduler_history — ACTIVE

- Module: madre
- Rows: 46277
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

- Module: spawner
- Rows: 39
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
- Rows: 10217
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

- Module: madre
- Rows: 12
- Columns:
  - id (INTEGER) PK NOT NULL
  - timestamp (DATETIME)
  - source (VARCHAR(64)) NOT NULL
  - event_type (VARCHAR(64)) NOT NULL
  - payload (TEXT)
  - severity (VARCHAR(16))

### system_state — ACTIVE

- Module: madre
- Rows: 6
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

- Module: madre
- Rows: 91
- Columns:
  - id (INTEGER) PK NOT NULL
  - source (VARCHAR(64)) NOT NULL
  - priority (INTEGER)
  - payload (TEXT) NOT NULL
  - status (VARCHAR(32))
  - enqueued_at (DATETIME)
  - dequeued_at (DATETIME)
  - result (TEXT)
  - updated_at (DATETIME)

### tasks — ACTIVE

- Module: madre
- Rows: 23
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

- Module: switch
- Rows: 0
- Columns:
  - id (INTEGER) PK NOT NULL
  - token_id (VARCHAR(256)) NOT NULL
  - used_at (DATETIME)
  - used_count (INTEGER)
  - source (VARCHAR(64))

