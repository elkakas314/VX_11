# CLEANUP REPORT cleanup_20251217T191923Z

## Moved to attic/
total 16
drwxrwxr-x  4 elkakas314 elkakas314 4096 dic 17 20:19 .
drwxr-xr-x 38 elkakas314 elkakas314 4096 dic 17 20:21 ..
drwxrwxr-x  6 elkakas314 elkakas314 4096 dic 16 11:06 operator_backend
drwxrwxr-x  4 elkakas314 elkakas314 4096 dic 16 11:21 operator_local

## docs/audit archived to docs/audit/archive/2025-12-17
total 12
drwxrwxr-x 3 elkakas314 elkakas314 4096 dic 17 20:20 .
drwxrwxr-x 4 elkakas314 elkakas314 4096 dic 17 20:20 ..
drwxrwxr-x 3 elkakas314 elkakas314 4096 dic 17 20:20 docs

## P0 Python check output
## P0 python check after operator archive
operator= /usr/lib/python3.10/operator.py
datetime_ok

## Docker compose validation
docker compose commands could not be executed in this environment (docker CLI lacks compose subcommand). See docs/audit/cleanup_20251217T191923Z/03_compose_config.txt for outputs.

## Git diff --stat (HEAD~3..HEAD)
 docker-compose.override.yml                        |  15 +++
 docs/CANONICAL_CORE.md                             |  20 ++++
 .../docs/audit}/AGENTS_SUITE_FINAL_SUMMARY.md      |   0
 .../audit}/AGENTS_SUITE_VALIDATION_20251214.md     |   0
 .../docs/audit}/AGENT_VX11_CONFIG_COMPLETION.md    |   0
 .../2025-12-17/docs/audit}/ARCHIVE_REFERENCES.md   |   0
 .../docs/audit}/BUILD_ARTIFACTS_INVENTORY.md       |   0
 .../audit}/CIERRE_CANONICO_TENTACULO_LINK_v7.md    |   0
 .../docs/audit}/COMPOSE_PORT_MAP_AFTER.md          |   0
 .../docs/audit}/COMPOSE_PORT_MAP_BEFORE.md         |   0
 .../2025-12-17/docs/audit}/COPILOT_BOOTSTRAP.md    |   0
 .../2025-12-17/docs/audit}/COPILOT_CONFIG_FINAL.md |   0
 .../docs/audit}/COPILOT_CONFIG_INVENTORY.md        |   0
 .../docs/audit}/COPILOT_CONFIG_REMOVALS.md         |   0
 .../2025-12-17/docs/audit}/DB_CONTRACT_REPORT.md   |   0
 .../2025-12-17/docs/audit}/DB_MAP_v7_META.txt      |   0
 .../2025-12-17/docs/audit}/DOCS_DRIFT_MAP.md       |   0
 .../docs/audit}/FASE0_STATUS_20251217T000000Z.md   |   0
 .../audit}/FASE1_VALIDATION_20251217T000000Z.md    |   0
 .../audit}/FASE2_PRE_SHUTDOWN_20251217T000000Z.md  |   0
 .../audit}/FASE3_VERIFICATION_20251217T000000Z.md  |   0
 .../docs/audit}/FINAL_TEST_RESULTS_P0_COMPLETE.txt |   0
 .../2025-12-17/docs/audit}/GFH_FINAL_SUMMARY.md    |   0
 .../EVIDENCE_INDEX.md                              |   0
 .../audit}/MADRE_VERIFICATION_2025-12-16/REPORT.md |   0
 .../raw/curl_madre_health.txt                      |   0
 .../raw/db_table_hits.txt                          |   0
 .../raw/delete_flow_hits.txt                       |   0
 .../raw/madre_routes_grep.txt                      |   0
 .../raw/openapi_and_paths_search.txt               |   0
 .../raw/parser_delete_mappings.txt                 |   0
 .../raw/parser_snippet.txt                         |   0
 .../raw/policy_and_suicide_checks.txt              |   0
 .../raw/policy_snippet.txt                         |   0
 .../raw/pytest_madre.txt                           |   0
 .../raw/runner_snippet.txt                         |   0
 .../raw/tree_madre.txt                             |   0
 .../docs/audit}/NODE_MODULES_INVENTORY.md          |   0
 .../audit}/PHASE0_COPILOT_CONTROLPLANE_REPORT.md   |   0
 .../2025-12-17/docs/audit}/PHASE2B_DECISIONS.md    |   0
 .../docs/audit}/PHASE2B_DOCUMENTATION_INDEX.md     |   0
 .../docs/audit}/PHASE2B_EXECUTION_PLAN.md          |   0
 .../docs/audit}/PHASE2B_FINAL_CLOSURE.md           |   0
 .../audit}/PHASE2B_ROADMAP_PLAYWRIGHT_MODELS.md    |   0
 .../2025-12-17/docs/audit}/PHASE2B_RUN_LOG.md      |   0
 .../docs/audit}/PHASE2_COMPLETE_PICTURE.md         |   0
 .../audit}/PHASE2_SWITCH_HERMES_P0_COMPLETION.md   |   0
 .../docs/audit}/PHASE3_CLI_CONCENTRATOR_FLUZO.md   |   0
 .../docs/audit}/PHASE3_CLOSURE_SUMMARY.md          |   0
 .../audit}/PHASE4_CLOSURE_TENTACULO_LINK_v7.md     |   0
 .../docs/audit}/PHASE4_COMPLETION_REPORT.md        |   0
 .../PHASEF_OPERATOR_CHAT_IMPLEMENTATION_REPORT.md  |   0
 .../audit}/PHASEG_TENTACULO_LINK_ROUTER_REPORT.md  |   0
 .../docs/audit}/PHASEH_OPERATOR_UI_TIER1_REPORT.md |   0
 .../docs/audit}/PLAN_A_F_COMPLETION_REPORT.md      |   0
 .../audit}/PRODUCTION_READINESS_CHECK_v7_FINAL.md  |   0
 .../docs/audit}/RUNTIME_PROCESS_AND_PORT_AUDIT.md  |   0
 .../docs/audit}/SECRETS_SCAN_2025-12-16.md         |   0
 .../SESSION_SUMMARY_TENTACULO_LINK_v7_PHASE4.md    |   0
 .../docs/audit}/SWITCH_HERMES_ACCEPTANCE.md        |   0
 .../docs/audit}/SWITCH_HERMES_ACCEPTANCE_DB.json   |   0
 .../docs/audit}/SWITCH_HERMES_PRODUCTION_READY.md  |   0
 .../docs/audit}/SWITCH_HERMES_REALITY.md           |   0
 .../2025-12-17/docs/audit}/SWITCH_HERMES_SMOKE.md  |   0
 .../TENTACULO_LINK_AUDIT_BEFORE_2025-12-16.md      |   0
 .../audit}/TENTACULO_LINK_PRODUCTION_ALIGNMENT.md  |   0
 .../docs/audit}/TENTACULO_LINK_STRUCTURAL_AUDIT.md |   0
 .../audit}/TEST_FAILS_SWITCH_HERMES_baseline.txt   |   0
 .../docs/audit}/TEST_RESULTS_P0_FINAL.txt          |   0
 .../2025-12-17/docs/audit}/TEST_RESULTS_P0_FIX.txt |   0
 .../docs/audit}/VX11_AGENT_BOOTSTRAP_REPORT.md     |   0
 .../audit}/VX11_AGENT_IMPLEMENTATION_REPORT.md     |   0
 .../2025-12-17/docs/audit}/VX11_API_DISCOVERY.md   |   0
 .../2025-12-17/docs/audit}/VX11_AUTOSYNC_REPORT.md |   0
 .../2025-12-17/docs/audit}/VX11_BUILD_ISSUES.md    |   0
 .../2025-12-17/docs/audit}/VX11_CANONICAL_AUDIT.md |   0
 .../VX11_COPILOT_ONBOARDING_AND_WORKFLOWS.md       |   0
 .../VX11_DIAGNOSTICS_AND_REPAIRS_20251215.md       |   0
 .../2025-12-17/docs/audit}/VX11_FINAL_REPORT.md    |   0
 .../2025-12-17/docs/audit}/VX11_PYTEST_FULL_RUN.md |   0
 .../docs/audit}/VX11_RUNTIME_TRUTH_REPORT.md       |   0
 .../docs/audit}/VX11_RUNTIME_VS_CANON.md           |   0
 .../2025-12-17/docs/audit}/VX11_STATUS_REPORT.md   |   0
 .../2025-12-17/docs/audit}/VX11_VALIDATE_REPORT.md |   0
 .../spill_home_root/OPERATOR_MODE_AUDIT.json       |   0
 .../spill_home_root/vx11-autosync-full.sh          |   0
 .../2025-12-16/spill_home_root/vx11-autosync.sh    |   0
 .../.github/agents/vx11_builder.agent.md           |   0
 .../copilot-agents/VX11-Inspector.prompt.md        |   0
 .../copilot-agents/VX11-Operator-Lite.prompt.md    |   0
 .../.github/copilot-agents/VX11-Operator.prompt.md |   0
 .../instructions/vx11_workflows.instructions.md    |   0
 .../.github/prompts/vx11_cleanup.prompt.md         |   0
 .../docs/audit}/archived_copilot/_moved_list.txt   |   0
 .../archived_copilot/scripts/vx11_bootstrap.sh     |   0
 .../sitecustomize.py.bak.20251217T144725Z          |   0
 .../sitecustomize.py.bak.20251217T155859Z          |   0
 ...s_CRASH_20251216T032116Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T032116Z_main.py |   0
 ...s_CRASH_20251216T032117Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T032117Z_main.py |   0
 ...s_CRASH_20251216T033751Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T033751Z_main.py |   0
 ...s_CRASH_20251216T033803Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T033803Z_main.py |   0
 ...s_CRASH_20251216T033804Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T033804Z_main.py |   0
 ...s_CRASH_20251216T034013Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T034013Z_main.py |   0
 ...s_CRASH_20251216T034024Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T034024Z_main.py |   0
 ...s_CRASH_20251216T034025Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T034025Z_main.py |   0
 ...s_CRASH_20251216T034026Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T034026Z_main.py |   0
 ...s_CRASH_20251216T231833Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T231833Z_main.py |   0
 ...s_CRASH_20251216T231834Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T231834Z_main.py |   0
 ...s_CRASH_20251216T233637Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T233637Z_main.py |   0
 ...s_CRASH_20251216T233644Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T233644Z_main.py |   0
 ...s_CRASH_20251216T233645Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251216T233645Z_main.py |   0
 ...s_CRASH_20251217T004334Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251217T004334Z_main.py |   0
 ...s_CRASH_20251217T004341Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251217T004341Z_main.py |   0
 ...s_CRASH_20251217T004342Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251217T004342Z_main.py |   0
 ...s_CRASH_20251217T004343Z_dsp_pipeline_trace.txt |   0
 ...forensic_crashes_CRASH_20251217T004343Z_main.py |   0
 .../dbmap/20251217T140330Z/DB_MAP_v7_FINAL.md      |   0
 .../dbmap/20251217T140330Z/DB_SCHEMA_v7_FINAL.json |   0
 .../audit}/cleanup_20251217T190153Z/TIMESTAMP.txt  |   0
 .../audit}/cleanup_20251217T190153Z/snapshot.txt   |   0
 .../cleanup_20251217T190237Z/pytest_canonic.txt    |   0
 .../raw/import_collisions_actions.txt              |   0
 .../cleanup_20251217T190237Z/raw_mv_commands.txt   |   0
 .../tests_classification.tsv                       |   0
 .../cleanup_20251217T190657Z/operator_ls.txt       |   0
 .../cleanup_20251217T190657Z/playwright_ls.txt     |   0
 .../archive_noncanonical_ls.txt                    |   0
 .../git_commit_playwright.txt                      |   0
 .../git_status_after_playwright_mv.txt             |   0
 .../cleanup_20251217T190902Z/playwright_git_mv.txt |   0
 .../archive_playwright_after_mv.txt                |   0
 .../cleanup_20251217T190943Z/playwright_fs_mv.txt  |   0
 .../playwright_move_record.txt                     |   0
 .../audit}/cleanup_20251217T191923Z/00_snapshot.md |   0
 .../copilot_archive/VX11-Inspector.prompt.md       |   0
 .../copilot_archive/VX11-Operator-Lite.prompt.md   |   0
 .../audit}/copilot_archive/VX11-Operator.prompt.md |   0
 .../docs/audit}/scan_20251217T172633Z/_meta.txt    |   0
 .../audit}/scan_20251217T172633Z/docker_audit.txt  |   0
 .../scan_20251217T172633Z/import_collisions.md     |   0
 .../audit}/scan_20251217T172633Z/import_map.json   |   0
 .../audit}/scan_20251217T172633Z/inventory.txt     |   0
 .../scan_20251217T172633Z/precheck_imports.txt     |   0
 .../01_after_operator_archive.status.txt           |   3 +
 .../01_commit_operator.txt                         | 101 +++++++++++++++++++++
 162 files changed, 139 insertions(+)
