# 02_AUDIT_FINDINGS

Lo que hay:
- Madre service uses `madre.main:app` (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_madre_dockerfile.txt`).
- `madre.main` defines `/power/status`, `/power/idle_min`, `/power/regen_dbmap`, `/power/ritual` with plan/apply pattern via `power_saver` (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_madre_main_power_block.txt`).
- `madre.main` attempts to replace `app` with `madre.main_legacy:app` for back-compat (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_madre_main_power_block.txt`).
- `madre.main_legacy` exposes `/madre/power/on|off|status|auto-decide` and `/madre/power/db_retention` (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_madre_main_legacy_power_block.txt`).
- `madre.main_legacy` uses Docker SDK to start/stop containers by name (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_madre_docker_refs.txt`).
- Hermes service in compose points to `switch/hermes` (`docker-compose.override.yml` + `switch/hermes/Dockerfile`) (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_compose_hermes_block.txt`, `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_compose_override_head.txt`).
- Canonical Hermes code appears in `switch/hermes/main.py` with endpoints `/health`, `/hermes/available`, `/hermes/exec`, `/hermes/job`, `/waveform` and DB usage via `ModelsLocal` (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_hermes_entrypoints_content.txt`).
- Other hermes directories are non-code: `forensic/hermes` logs, `docs/archive/hermes` docs, `models/hermes` data (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_hermes_dir_file_lists.txt`).
- Switch integrates Hermes for CLI registry/selection (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_switch_main.py.txt`).
- Tentaculo Link re-exports `main_v7.py`, but `main_v7.py` appears mostly empty and has no FastAPI markers found (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_tentaculo_main_v7_fastapi.txt`).
- Schema tables relevant to Madre/Hermes exist: `models_local`, `local_models_v2`, `model_registry`, `model_usage_stats`, `hermes_ingest`, `system_events`, `audit_logs`, `module_status` (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_schema_tables_relevant.txt`).

Lo que falta (vs objetivo A/B):
- Madre lacks a dedicated per-service power manager with allowlist sourced from compose and explicit PLAN/APPLY model + triple lock on apply=true.
- Madre power endpoints in `main_legacy` perform direct on/off without PLAN-only default and without evidence under `docs/audit/`.
- Madre uses `subprocess` with `shell=True` in `/power/status`, which violates hard prohibition (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_madre_main_power_block.txt`).
- Hermes lacks a documented 3-tier discovery pipeline with PLAN/APPLY and explicit non-routing guarantee; currently has minimal endpoints and some pruning logic that deletes files (`p.unlink()`).
- No canonical top-level `hermes/` module directory, which conflicts with structural expectations from canon.
- No evidence of power-manager triple lock (header key + token TTL + confirm string) in Madre.

Riesgos:
- Existing `power_saver` and `main_legacy` paths can stop services or interact with Docker without plan-only guardrails and without explicit allowlist (see `docs/audit/madre_power_manager_plus_hermes_20251219T020423Z/02_madre_docker_refs.txt`).
- `madre.main` contains `shell=True` usage (policy violation) and uses `grep` of repo processes; will need surgical replacement with safe subprocess args.
- Hermes code is located under `switch/hermes`, while other hermes directories exist; ambiguity risks import confusion and duplication checks.
- Tentaculo Link `main_v7.py` appears empty; gateway health/route coverage may be incomplete if this is the loaded app.
- Hermes pruning removes model files without explicit audit trail or plan/apply pattern; could conflict with evidence rules.
