# VX11 Agent Bootstrap Report

**Generated:** 2025-12-16T19:37:45.978476Z  
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
| shubniggurath | localhost | 8007 | 🔴 BROKEN |
| operator | localhost | 8011 | 🔴 OK |
| tentaculo_link | localhost | 8000 | 🔴 down |
| madre | localhost | 8001 | 🔴 down |
| switch | localhost | 8002 | 🔴 down |
| hermes | localhost | 8003 | 🔴 down |
| hormiguero | localhost | 8004 | 🔴 down |
| manifestator | localhost | 8005 | 🔴 down |
| mcp | localhost | 8006 | 🔴 down |
| shub | localhost | 8007 | 🔴 down |
| spawner | localhost | 8008 | 🔴 down |
| operator_backend | localhost | 8011 | 🔴 down |

## Database State

Tables: 60
- tasks
- ia_decisions
- module_health
- model_registry
- cli_registry
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
- engines
- shub_projects
- operator_jobs
- hermes_ingest
- madre_policies
- madre_actions
- forensic_ledger
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
- hormiga_state
- incidents
- pheromone_log
- operator_session
- cli_usage_stats
- cli_onboarding_state
- fluzo_signals
- routing_events
- context
- reports
- spawns
- shub_tracks
- daughters
- operator_message
- operator_browser_task
- shub_analysis
- shub_fx_chains
- daughter_attempts
- operator_tool_call
- operator_switch_adjustment
- shub_presets
- copilot_repo_map
- sqlite_sequence
- copilot_runtime_services
- copilot_actions_log
- copilot_workflows_catalog
- chat_providers_stats
