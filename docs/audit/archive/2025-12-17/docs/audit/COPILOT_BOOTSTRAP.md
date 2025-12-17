# COPILOT_BOOTSTRAP
Generated: 2025-12-17T11:09:48Z
Repo: /home/elkakas314/vx11
Branch: main
Commit: 6907ede

DB MAP (FUENTE DE VERDAD):
- docs/audit/DB_MAP_v7_FINAL.md
DB SCHEMA (FUENTE DE VERDAD):
- docs/audit/DB_SCHEMA_v7_FINAL.json

Git status:
## main
 M .github/agents/vx11.agent.md
 D .github/copilot-agents/VX11-Inspector.prompt.md
 D .github/copilot-agents/VX11-Operator-Lite.prompt.md
 D .github/copilot-agents/VX11-Operator.prompt.md
 M .github/copilot-instructions.md
 M .github/workflows/ci.yml
 M AGENTS.md
 M config/container_state.py
 M config/db_schema.py
 M conftest.py
 M docs/audit/VX11_AGENT_BOOTSTRAP_REPORT.md
 M docs/audit/VX11_VALIDATE_REPORT.md
 D forensic/crashes/CRASH_20251216T032116Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T032116Z/main.py
 D forensic/crashes/CRASH_20251216T032117Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T032117Z/main.py
 D forensic/crashes/CRASH_20251216T033751Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T033751Z/main.py
 D forensic/crashes/CRASH_20251216T033803Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T033803Z/main.py
 D forensic/crashes/CRASH_20251216T033804Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T033804Z/main.py
 D forensic/crashes/CRASH_20251216T034013Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T034013Z/main.py
 D forensic/crashes/CRASH_20251216T034024Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T034024Z/main.py
 D forensic/crashes/CRASH_20251216T034025Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T034025Z/main.py
 D forensic/crashes/CRASH_20251216T034026Z/dsp_pipeline_trace.txt
 D forensic/crashes/CRASH_20251216T034026Z/main.py
 M hormiguero/main_v7.py
 M madre/main.py
 M mcp/main.py
 M mcp/tools_wrapper.py
 M operator_backend/backend/browser.py
 M pytest.ini
 M shubniggurath/core/__init__.py
 M shubniggurath/core/audio_batch_engine.py
 M sitecustomize.py
 M vx11.code-workspace
?? .github/agents/vx11_builder.agent.md
?? .github/instructions/vx11_workflows.instructions.md
?? .github/prompts/vx11_cleanup.prompt.md
?? docs/audit/COPILOT_BOOTSTRAP.md
?? docs/audit/COPILOT_CONFIG_INVENTORY.md
?? docs/audit/COPILOT_CONFIG_REMOVALS.md
?? docs/audit/ULTRA_AUDIT_2025-12-16/
?? docs/audit/VX11_AUTOSYNC_REPORT.md
?? docs/audit/VX11_FINAL_REPORT.md
?? docs/audit/VX11_PYTEST_FULL_RUN.md
?? docs/audit/archive/
?? docs/audit/archived_copilot/
?? forensic/crashes/CRASH_20251216T231833Z/
?? forensic/crashes/CRASH_20251216T231834Z/
?? forensic/crashes/CRASH_20251216T233637Z/
?? forensic/crashes/CRASH_20251216T233644Z/
?? forensic/crashes/CRASH_20251216T233645Z/
?? forensic/crashes/CRASH_20251217T004334Z/
?? forensic/crashes/CRASH_20251217T004341Z/
?? forensic/crashes/CRASH_20251217T004342Z/
?? forensic/crashes/CRASH_20251217T004343Z/
?? operator/
?? playwright/
?? scripts/vx11_bootstrap.sh

Reglas:
- No crear duplicados ni archivos final_v2.
- Forense: forensic/crashes NUNCA borrar.


## DBMAP maintenance (recent)

- scanned_at: 2025-12-17T14:03:00Z
- database_path: data/runtime/vx11.db
- database_sha256: 0a8a2599e79044ec2e1cd02d25f5e546b85692d6697c998c38450cea8df4f4c8
- copilot_repo_map_rows: 11
- map_file: docs/audit/DB_MAP_v7_FINAL.md
- schema_file: docs/audit/DB_SCHEMA_v7_FINAL.json
- backups_dir: docs/audit/backups/dbmap/

Actions:
- Created timestamped backup copy of DB_MAP and DB_SCHEMA
- Regenerated DB_SCHEMA and DB_MAP from live sqlite and persisted artifacts under docs/audit/
