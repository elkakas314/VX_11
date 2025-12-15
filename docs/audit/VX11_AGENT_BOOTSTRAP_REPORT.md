# VX11 Agent Bootstrap Report

**Generated:** 2025-12-15T09:46:11.000392Z  
**Repo:** /home/elkakas314/vx11  
**DB:** /home/elkakas314/vx11/data/runtime/vx11.db

## Canonical Paths

- ✓ Found: 9 files
- ✗ Missing: 0 files

- ✓ found: .github/copilot-instructions.md
- ✓ found: config/db_schema.py
- ✓ found: config/module_template.py
- ✓ found: config/settings.py
- ✓ found: config/tokens.py
- ✓ found: docker-compose.yml
- ✓ found: docs/ARCHITECTURE.md
- ✓ found: operator_backend/backend/main_v7.py
- ✓ found: tentaculo_link/main.py

## Runtime Services

| Service | Host | Port | Status |
|---------|------|------|--------|
| tentaculo_link | localhost | 8000 | 🟢 up |
| madre | localhost | 8001 | 🟢 up |
| switch | localhost | 8002 | 🟢 up |
| hermes | localhost | 8003 | 🔴 down |
| hormiguero | localhost | 8004 | 🔴 down |
| manifestator | localhost | 8005 | 🟢 up |
| mcp | localhost | 8006 | 🟢 up |
| shub | localhost | 8007 | 🔴 down |
| spawner | localhost | 8008 | 🟢 up |
| operator_backend | localhost | 8011 | 🟢 up |

## Database State

Tables: 86
- madre_tasks
- madre_ia_decisions
- madre_module_health
- madre_context
- madre_reports
- madre_spawns
- madre_model_registry
- madre_cli_registry
- madre_engines
- hermes_tasks
- hermes_ia_decisions
- hermes_module_health
- hermes_context
- hermes_reports
- hermes_spawns
- hermes_model_registry
- hermes_cli_registry
- hermes_engines
- hive_tasks
- hive_ia_decisions
- hive_module_health
- hive_context
- hive_reports
- hive_spawns
- hive_model_registry
- hive_cli_registry
- hive_engines
- tasks
- ia_decisions
- module_health
- model_registry
- cli_registry
- engines
- context
- reports
- spawns
- shub_projects
- operator_jobs
- hermes_ingest
- madre_policies
- madre_actions
- forensic_ledger
- shub_tracks
- shub_analysis
- shub_fx_chains
- shub_presets
- vx11_events
- queen_tasks
- ants
- models_local
- models_remote_cli
- tokens_usage
- task_queue
- events
- hijas_runtime
- system_state
- audit_logs
- sandbox_exec
- system_events
- scheduler_history
- power_events
- feromona_events
- hijas_state
- drift_reports
- cli_providers
- local_models_v2
- model_usage_stats
- switch_queue_v2
- daughter_tasks
- intents_log
- daughters
- daughter_attempts
- hormiga_state
- incidents
- pheromone_log
- operator_session
- operator_message
- operator_browser_task
- operator_tool_call
- operator_switch_adjustment
- chat_providers_stats
- copilot_repo_map
- sqlite_sequence
- copilot_runtime_services
- copilot_actions_log
- copilot_workflows_catalog
