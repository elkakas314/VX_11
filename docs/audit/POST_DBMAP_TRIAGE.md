# POST DBMAP TRIAGE

Generated at: $(date -u --rfc-3339=seconds)

## Git status
## main
 M .github/workflows/ci.yml
 M .gitignore
 M config/container_state.py
 M config/db_schema.py
 M conftest.py
 M docs/audit/COPILOT_BOOTSTRAP.md
 M docs/audit/DBMAP_MAINTENANCE.md
 M docs/audit/DB_MAP_v7_FINAL.md
 M docs/audit/DB_SCHEMA_v7_FINAL.json
 M docs/audit/VX11_AGENT_BOOTSTRAP_REPORT.md
 M docs/audit/VX11_VALIDATE_REPORT.md
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
?? docs/audit/COPILOT_CONFIG_INVENTORY.md
?? docs/audit/COPILOT_CONFIG_REMOVALS.md
?? docs/audit/FASE0_STATUS_20251217T000000Z.md
?? docs/audit/FASE1_VALIDATION_20251217T000000Z.md
?? docs/audit/FASE2_PRE_SHUTDOWN_20251217T000000Z.md
?? docs/audit/FASE3_VERIFICATION_20251217T000000Z.md
?? docs/audit/POST_DBMAP_TRIAGE.md
?? docs/audit/VX11_AUTOSYNC_REPORT.md
?? docs/audit/VX11_FINAL_REPORT.md
?? docs/audit/VX11_PYTEST_FULL_RUN.md
?? docs/audit/archive/
?? docs/audit/archived_copilot/
?? docs/audit/archived_forensic/
?? scripts/vx11_bootstrap.sh
?? sitecustomize.py.bak.20251217T144725Z
?? sitecustomize.py.bak.20251217T155859Z

## Last commit (git log -1)
commit 4376d58fda92086bd4bc4503314832df5832ae4e
Author:     VX11 Deep Surgeon <vx11@deep-surgeon.dev>
AuthorDate: Wed Dec 17 15:05:46 2025 +0100
Commit:     VX11 Deep Surgeon <vx11@deep-surgeon.dev>
CommitDate: Wed Dec 17 15:05:46 2025 +0100

    chore(audit): regenerate DB_SCHEMA and DB_MAP; backup and maintenance report (non-destructive) [skip ci]

## Git diff --name-status (against HEAD)
M	.github/workflows/ci.yml
M	.gitignore
M	config/container_state.py
M	config/db_schema.py
M	conftest.py
M	docs/audit/COPILOT_BOOTSTRAP.md
M	docs/audit/DBMAP_MAINTENANCE.md
M	docs/audit/DB_MAP_v7_FINAL.md
M	docs/audit/DB_SCHEMA_v7_FINAL.json
M	docs/audit/VX11_AGENT_BOOTSTRAP_REPORT.md
M	docs/audit/VX11_VALIDATE_REPORT.md
M	hormiguero/main_v7.py
M	madre/main.py
M	mcp/main.py
M	mcp/tools_wrapper.py
M	operator_backend/backend/browser.py
M	pytest.ini
M	shubniggurath/core/__init__.py
M	shubniggurath/core/audio_batch_engine.py
M	sitecustomize.py
M	vx11.code-workspace

## Untracked files (git ls-files --others --exclude-standard)
.github/agents/vx11_builder.agent.md
.github/instructions/vx11_workflows.instructions.md
.github/prompts/vx11_cleanup.prompt.md
docs/audit/COPILOT_CONFIG_INVENTORY.md
docs/audit/COPILOT_CONFIG_REMOVALS.md
docs/audit/FASE0_STATUS_20251217T000000Z.md
docs/audit/FASE1_VALIDATION_20251217T000000Z.md
docs/audit/FASE2_PRE_SHUTDOWN_20251217T000000Z.md
docs/audit/FASE3_VERIFICATION_20251217T000000Z.md
docs/audit/POST_DBMAP_TRIAGE.md
docs/audit/VX11_AUTOSYNC_REPORT.md
docs/audit/VX11_FINAL_REPORT.md
docs/audit/VX11_PYTEST_FULL_RUN.md
docs/audit/archive/2025-12-16/spill_home_root/OPERATOR_MODE_AUDIT.json
docs/audit/archive/2025-12-16/spill_home_root/vx11-autosync-full.sh
docs/audit/archive/2025-12-16/spill_home_root/vx11-autosync.sh
docs/audit/archived_copilot/.github/copilot-agents/VX11-Inspector.prompt.md
docs/audit/archived_copilot/.github/copilot-agents/VX11-Operator-Lite.prompt.md
docs/audit/archived_copilot/.github/copilot-agents/VX11-Operator.prompt.md
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032116Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032116Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032117Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032117Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033751Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033751Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033803Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033803Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033804Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033804Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034013Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034013Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034024Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034024Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034025Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034025Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034026Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034026Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231833Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231833Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231834Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231834Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233637Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233637Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233644Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233644Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233645Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233645Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004334Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004334Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004341Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004341Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004342Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004342Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004343Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004343Z_main.py
scripts/vx11_bootstrap.sh
sitecustomize.py.bak.20251217T144725Z
sitecustomize.py.bak.20251217T155859Z

## DB: copilot_repo_map count(*)
983

## Python quick import test
ok

## docker-compose ps (readonly)
       Name                      Command                  State                        Ports                  
--------------------------------------------------------------------------------------------------------------
vx11-hermes           python -m uvicorn switch.h ...   Up (healthy)   0.0.0.0:8003->8003/tcp,:::8003->8003/tcp
vx11-switch           python -m uvicorn switch.m ...   Up (healthy)   0.0.0.0:8002->8002/tcp,:::8002->8002/tcp
vx11-tentaculo-link   python -m uvicorn tentacul ...   Up (healthy)   0.0.0.0:8000->8000/tcp,:::8000->8000/tcp

## Health checks (curl 8000-8005)
-- port 8000 --
{"status":"ok","module":"tentaculo_link","version":"7.0"}-- port 8001 --
curl: (7) Failed to connect to 127.0.0.1 port 8001 after 0 ms: Connection refused
unavailable
-- port 8002 --
{"status":"ok","module":"switch","active_model":"general-7b","warm_model":"audio-engineering","queue_size":0}-- port 8003 --
{"status":"ok","module":"hermes"}-- port 8004 --
curl: (7) Failed to connect to 127.0.0.1 port 8004 after 0 ms: Connection refused
unavailable
-- port 8005 --
curl: (7) Failed to connect to 127.0.0.1 port 8005 after 0 ms: Connection refused
unavailable
commit 4376d58fda92086bd4bc4503314832df5832ae4e
Author:     VX11 Deep Surgeon <vx11@deep-surgeon.dev>
AuthorDate: Wed Dec 17 15:05:46 2025 +0100
Commit:     VX11 Deep Surgeon <vx11@deep-surgeon.dev>
CommitDate: Wed Dec 17 15:05:46 2025 +0100

    chore(audit): regenerate DB_SCHEMA and DB_MAP; backup and maintenance report (non-destructive) [skip ci]
M	.github/workflows/ci.yml
M	.gitignore
M	config/container_state.py
M	config/db_schema.py
M	conftest.py
M	docs/audit/COPILOT_BOOTSTRAP.md
M	docs/audit/DBMAP_MAINTENANCE.md
M	docs/audit/DB_MAP_v7_FINAL.md
M	docs/audit/DB_SCHEMA_v7_FINAL.json
M	docs/audit/VX11_AGENT_BOOTSTRAP_REPORT.md
M	docs/audit/VX11_VALIDATE_REPORT.md
M	hormiguero/main_v7.py
M	madre/main.py
M	mcp/main.py
M	mcp/tools_wrapper.py
M	operator_backend/backend/browser.py
M	pytest.ini
M	shubniggurath/core/__init__.py
M	shubniggurath/core/audio_batch_engine.py
M	sitecustomize.py
M	vx11.code-workspace
.github/agents/vx11_builder.agent.md
.github/instructions/vx11_workflows.instructions.md
.github/prompts/vx11_cleanup.prompt.md
docs/audit/COPILOT_CONFIG_INVENTORY.md
docs/audit/COPILOT_CONFIG_REMOVALS.md
docs/audit/FASE0_STATUS_20251217T000000Z.md
docs/audit/FASE1_VALIDATION_20251217T000000Z.md
docs/audit/FASE2_PRE_SHUTDOWN_20251217T000000Z.md
docs/audit/FASE3_VERIFICATION_20251217T000000Z.md
docs/audit/POST_DBMAP_TRIAGE.md
docs/audit/VX11_AUTOSYNC_REPORT.md
docs/audit/VX11_FINAL_REPORT.md
docs/audit/VX11_PYTEST_FULL_RUN.md
docs/audit/archive/2025-12-16/spill_home_root/OPERATOR_MODE_AUDIT.json
docs/audit/archive/2025-12-16/spill_home_root/vx11-autosync-full.sh
docs/audit/archive/2025-12-16/spill_home_root/vx11-autosync.sh
docs/audit/archived_copilot/.github/copilot-agents/VX11-Inspector.prompt.md
docs/audit/archived_copilot/.github/copilot-agents/VX11-Operator-Lite.prompt.md
docs/audit/archived_copilot/.github/copilot-agents/VX11-Operator.prompt.md
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032116Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032116Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032117Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T032117Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033751Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033751Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033803Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033803Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033804Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T033804Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034013Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034013Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034024Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034024Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034025Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034025Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034026Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T034026Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231833Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231833Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231834Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T231834Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233637Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233637Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233644Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233644Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233645Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251216T233645Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004334Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004334Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004341Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004341Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004342Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004342Z_main.py
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004343Z_dsp_pipeline_trace.txt
docs/audit/archived_forensic/forensic_crashes_CRASH_20251217T004343Z_main.py
scripts/vx11_bootstrap.sh
sitecustomize.py.bak.20251217T144725Z
sitecustomize.py.bak.20251217T155859Z
983
ok
       Name                      Command                  State                        Ports                  
--------------------------------------------------------------------------------------------------------------
vx11-hermes           python -m uvicorn switch.h ...   Up (healthy)   0.0.0.0:8003->8003/tcp,:::8003->8003/tcp
vx11-switch           python -m uvicorn switch.m ...   Up (healthy)   0.0.0.0:8002->8002/tcp,:::8002->8002/tcp
vx11-tentaculo-link   python -m uvicorn tentacul ...   Up (healthy)   0.0.0.0:8000->8000/tcp,:::8000->8000/tcp
-- port 8005 --
curl: (7) Failed to connect to 127.0.0.1 port 8005 after 0 ms: Connection refused
unavailable
-- port 8005 --
curl: (7) Failed to connect to 127.0.0.1 port 8005 after 0 ms: Connection refused
unavailable
-- port 8005 --
curl: (7) Failed to connect to 127.0.0.1 port 8005 after 0 ms: Connection refused
unavailable
-- port 8005 --
curl: (7) Failed to connect to 127.0.0.1 port 8005 after 0 ms: Connection refused
unavailable
-- port 8005 --
curl: (7) Failed to connect to 127.0.0.1 port 8005 after 0 ms: Connection refused
unavailable
-- port 8005 --
curl: (7) Failed to connect to 127.0.0.1 port 8005 after 0 ms: Connection refused
unavailable
