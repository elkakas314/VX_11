# Copilot Instructions for VX11

## CONTEXT BOOTSTRAP (MANDATORY ON EVERY @vx11 TRIGGER)
- Validar docker-compose.full-test.yml y health de todos los servicios

Before executing ANY @vx11 command, read in order:
1. docs/audit/CLEANUP_EXCLUDES_CORE.txt (CORE protection list)
2. docs/audit/DB_SCHEMA_v7_FINAL.json (current DB structure)
3. docs/audit/DB_MAP_v7_FINAL.md (table mapping + meta)
4. docs/canon/ (active specs: CANONICAL_SHUB_VX11.json + others)
5. forensic/ (latest crash patterns / incident summary)
6. docs/audit/ (latest OUTDIR timestamp + SCORECARD.json)

**If any file missing**: DO NOT ASSUME - report "BOOTSTRAP INCOMPLETE: <file> not found"

---

## @vx11 status OUTPUT CONTRACT (FIXED FORMAT)

Every `@vx11 status` invocation MUST return:
- **Git**: branch, HEAD commit, remoto (vx_11_remote), working tree status
- **Docker**: servicios up/down + health check results (9 puertos estándar: 8000-8008, 8011)
- **Canon**: JSON validation hash (docs/canon/) + last update timestamp
- **DB**: size, integrity_check result, quick_check result, foreign_key_check result
- **Mapas**: timestamp + existence check (DB_SCHEMA_v7_FINAL.json, DB_MAP_v7_FINAL.md, DB_MAP_v7_META.txt)
- **Percentages** (if SCORECARD.json exists): Orden_fs_pct, Coherencia_routing_pct, Automatizacion_pct, Autonomia_pct, Global_ponderado_pct
- **Blockers**: if any metric/file missing, report EXACTLY: "BLOCKED: <resource> not found at <path> (expected from: <source>)"

---

Instrucciones globales:
- El proyecto es VX11 (profile full-test: madre, tentaculo_link, switch, operator-backend, operator-frontend, spawner).
- No preguntar por contexto; esta en los ficheros.
- Lee estas fuentes de contexto sin pedirlas:
  - VX11_CONTEXT.md
  - docs/audit/DB_MAP_v7_FINAL.md
  - docs/audit/DB_SCHEMA_v7_FINAL.json
  - .github/agents/vx11.agent.md (ÚNICO archivo activo de agente; legacy archivado en docs/audit/archived_agents/)
- Madre v7 es el default; usar `VX11_USE_LEGACY_APP=1` solo para compatibilidad puntual de tests.
- Spawner debe cumplir contrato avanzado y registrar en BD (spawns + daughter_*).
- Despues de CADA tarea/cambio: ejecutar mantenimiento post-task y dejar evidencia en docs/audit/<TS>/ sin pedir permiso.
- Flujo obligatorio:
  1) Auditoria primero (structure/flow/db/rutas) con evidencia.
  2) Cambios mínimos y canónicos (no atajos).
  3) Al final SIEMPRE: `POST /madre/power/maintenance/post_task` (o equivalente local si no está disponible), regenerar DB_MAP/SCHEMA/SCORECARD, actualizar PERCENTAGES.json y dejar evidencia.
- La estabilidad en PERCENTAGES usa gate de integrity_check + healthchecks core + tests P0 + coherencia de contratos.
- No crear scripts nuevos si ya existe algo equivalente en scripts/.
- No crear FINAL_v2; se actualizan los FINAL canonicos.
- No crear carpetas de modulos nuevas.
- No pedir confirmacion salvo acciones destructivas reales (rm, rmdir, mover fuera de docs/audit, tocar tokens/secrets, git reset/clean/push, docker compose up/down).
- Si se toca BD/estructura: ejecutar comandos canonicos + actualizar SCORECARD.json:
  - sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" "PRAGMA quick_check;"
  - sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000;" "PRAGMA integrity_check;"
  - sqlite3 data/runtime/vx11.db -cmd "PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON;" "PRAGMA foreign_key_check;"
  - PYTHONPATH=. python3 -m scripts.generate_db_map_from_db data/runtime/vx11.db
  - python3 scripts/audit_counts.py data/runtime/vx11.db > docs/audit/<TS>/counts.json
  - Actualizar docs/audit/SCORECARD.json
  - Rotar data/backups: conservar 2 mas nuevos, mover resto a data/backups/archived (respetar docs/audit/CLEANUP_EXCLUDES_CORE.txt).
- Servicios systemd vx11-*: si hay auto-respawn de no-Madre, detener/deshabilitar con evidencia; si falta sudo, registrar bloqueo.
- Si post_task se ejecuta en contenedor y /app/docs/audit no esta montado, copiar evidencias al host.

---

## POWER CONTROL COMMANDS (container-level only, docker compose)

### NEW: `@vx11 solo_madre`
- **Action**: Apply SOLO_MADRE policy (stop all services except madre)
- **Execution**: POST /madre/power/policy/solo_madre/apply
- **Result**: docker ps shows ONLY vx11-madre running
- **Evidence**: docs/audit/madre_power_solo_madre_*/ with pre/post snapshots
- **Use case**: Hardened mode, reduce resource usage, emergencies

### NEW: `@vx11 power start <module>`
- **Action**: Start a specific service container (docker compose up -d)
- **Module list**: tentaculo_link, switch, hermes, hormiguero, mcp, spawner, shubniggurath, manifestator, operator-backend, operator-frontend
- **Guardrail**: VX11_ALLOW_SERVICE_CONTROL=1 (enabled in docker-compose.yml)
- **Evidence**: docs/audit/madre_power_start_<module>_*/
- **Format**: `/madre/power/service/start {"service":"switch"}`

### NEW: `@vx11 power stop <module>`
- **Action**: Stop a specific service container (docker compose stop)
- **Module list**: same as above (cannot stop madre from this endpoint)
- **Guardrail**: Same as start
- **Evidence**: docs/audit/madre_power_stop_<module>_*/
- **Format**: `/madre/power/service/stop {"service":"switch"}`

### NEW: `@vx11 power status`
- **Action**: Show current container state (docker compose ps)
- **Format**: GET /madre/power/status
- **Returns**: List of running services with health status

### NEW: `@vx11 power policy check`
- **Action**: Check if SOLO_MADRE policy is active
- **Format**: GET /madre/power/policy/solo_madre/status
- **Returns**: {"policy_active": true|false, "running_services": [...]}

---

## POWER CONTROL RAILS (NON-NEGOTIABLE)

1. **Container-level ONLY**: Use `docker compose`, NEVER `docker exec` or `kill` or process-level signals
2. **No arbitrary commands**: Power manager has allowlist of services from docker-compose.yml
3. **Evidence mandatory**: Every action logs to docs/audit/ with timestamps, pre/post snapshots, DB records
4. **No service restart loops**: If a service fails to start, report and do NOT retry automatically (human decision)
5. **Madre is protected**: Cannot be stopped via power endpoints (manual only if needed, with explicit git reset)
6. **Audit trail**: All power actions go to forensic/madre/ + SQLite copilot_actions_log (if exists) + OUTDIR

---

## POWER CONTROL EXAMPLES

```bash
# Check current state
curl -s http://localhost:8001/madre/power/status

# Apply SOLO_MADRE policy (stop all except madre)
curl -X POST http://localhost:8001/madre/power/policy/solo_madre/apply

# Check if solo_madre is active
curl -s http://localhost:8001/madre/power/policy/solo_madre/status

# Start switch service
curl -X POST http://localhost:8001/madre/power/service/start \
  -H "Content-Type: application/json" \
  -d '{"service":"switch"}'

# Stop switch service
curl -X POST http://localhost:8001/madre/power/service/stop \
  -H "Content-Type: application/json" \
  -d '{"service":"switch"}'

# Named modes (low_power, operative_core, full)
curl -X POST http://localhost:8001/madre/power/mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"low_power", "apply":true}'
```

---

## MODELOS & COSTE OPTIMIZATION

### Preferencias de Modelo (en orden)
1. **DeepSeek R1** (si disponible) — Reasoning complejo, debugging, análisis
2. **GPT-5 mini** — Respuestas compactas, código rápido, ejecución
3. **GPT-4.1** — Fallback, análisis arquitectónico

### Anti-Patterns (PROHIBIDOS)
- ❌ Sobre-planificación (no hacer listas de 20 pasos)
- ❌ Preguntar antes de actuar (salvo destructivo/ambiguo)
- ❌ Refactoring paralelo (cambio = una cosa)
- ❌ Limpieza "mientras estamos"
- ❌ Secretos en código (siempre env vars)

### Regla de Oro
**Ejecutar → Verificar → Corregir** (no planificar → esperar → ejecutar)

---

## DeepSeek R1 DEFAULT RULE (SIN PEDIRLO)

### ¿CUÁNDO usar DeepSeek R1 (siempre que sea posible)?
- Razonamiento = "explicar por qué"
- Debugging = "encontrar qué está mal"
- Análisis = "evaluar impacto"
- Código = "implementar, refactor, testing"
- Decisiones = "árbol de opciones, trade-offs"

### ¿CÓMO usarlo?
- **Si disponible**: Endpoint VX11 `/operator/api/assist/deepseek_r1`
  ```bash
  curl -X POST http://localhost:8000/operator/api/assist/deepseek_r1 \
    -H "X-VX11-Token: vx11-local-token" \
    -H "Content-Type: application/json" \
    -d '{"purpose":"debug","prompt":"...","temperature":1.0}'
  ```
- **CLI/SDK**: Pasar `--model deepseek-r1` o `model="deepseek-r1"` a llamada LLM

### ¿DEGRADACIÓN?
- Si DeepSeek R1 NO está disponible → fallback a GPT-5 mini/GPT-4.1
- **REGISTRAR**: Log en docs/audit/$TS/model_usage.json:
  ```json
  {
    "timestamp": "20251230T221000Z",
    "attempted_model": "deepseek-r1",
    "fallback_used": "gpt-4.1",
    "reason": "endpoint_unavailable",
    "task": "<task_name>"
  }
  ```
- Marcar degradation en SCORECARD.json

### Metadata Obligatoria (respuestas DeepSeek R1)
```json
{
  "provider_used": "deepseek",
  "model_used": "r1",
  "trace_id": "<uuid>",
  "temperature": 1.0,
  "reasoning_tokens": 1234,
  "total_tokens": 5678
}
```

---

## DEEPSEEK R1 REASONING ORACLE (COPILOT-INTERNAL)

**Location**: `.github/deepseek_r1_reasoning.py`  
**Purpose**: Structured planning for complex VX11 tasks  
**Access**: Copilot ONLY (not for direct human invocation)  
**Audit**: `docs/audit/r1/` (auto-logged, gitignored)

### When to invoke DeepSeek R1 (MANDATORY)
- ✅ Branch merges / consolidation decisions
- ✅ Architecture or contract changes (Switch routing, Operator wiring, tentaculo_link constraints)
- ✅ Failing tests requiring diagnosis
- ✅ Changes to `.github/*`, security workflows, or canonical docs
- ✅ Complex refactors or multi-step system redesigns

### Copilot invocation (automatic)
```python
# Pseudo-code (executed internally when MANDATORY trigger detected)
plan = execute_deepseek_reasoning(
    objective="<task_name>",
    context="VX11 invariants + constraints",
    task="<specific_task_description>"
)
# Returns: {"tasks": [...], "risks": [...], "tests_to_run": [...], "rollback_plan": [...], ...}
```

### Rails (Safety guardrails enforced automatically)
- **Invariants**: solo_madre runtime, tentaculo_link entrypoint, SQLite BD, forense immutable
- **Protected paths**: Never touch `docs/audit/**`, `forensic/**`, `docs/canon/**`, `tokens.env*`
- **Atomicity**: Each task single-purpose, clear commit message
- **Rollback**: Every plan includes emergency recovery
- **Testing**: All plans specify tests before production
- **Audit**: All reasoning logged with timestamp + violations tracked

### Output contract (JSON format)
```json
{
  "tasks": [{"id": "T1", "description": "...", "commands": [...], "done_when": "..."}],
  "risks": [{"risk": "...", "severity": "low|med|high", "mitigation": "..."}],
  "tests_to_run": ["..."],
  "rollback_plan": ["..."],
  "protected_resources_checked": true,
  "invariants_preserved": true,
  "definition_of_done": ["..."],
  "reasoning": "explanation of decisions"
}
```

### Safety verification (automatic)
- Verify no protected paths touched
- Verify invariants preserved
- Verify rollback plan exists
- Verify tests specified
- Track and report any violations

---

## GIT DISCIPLINE (NON-NEGOTIABLE)

- **Remote**: vx_11_remote ONLY (never 'origin' if not exists; always verify with `git remote -v`)
- **Push**: atomic commits with VX11-style messages ("vx11: <module>: <action> + details")
- **Force push**: NEVER except explicit rollback (git reset --hard <commit> && git push vx_11_remote main --force), MUST document in OUTDIR
- **Branches**: work on main locally; if integration branch exists, use PR workflow
- **Evidence**: EVERY commit leaves docs/audit/<TS>/ audit trail (commit hash, files changed, reasoning)

---

## LOW QUESTIONS POLICY (ASSUME WHEN POSSIBLE)

Only ask user if:
- **Destructive action**: rm, DELETE, git reset, docker compose down
- **Ambiguous input**: multiple valid interpretations (ask which one)
- **External decision**: requires human judgment not in context (e.g., which service to prioritize?)

DO NOT ask for:
- Clarification if context is clear (re-read, don't re-ask)
- Permission after stating analysis (state action + execute, evidence in OUTDIR)
- Confirmation of obvious next steps

All decisions MUST be auditable (evidence in OUTDIR timestamp directory).

---

## POST-TASK AUTOMATION (AFTER EVERY SIGNIFICANT CHANGE)

After completing @vx11 task:

1. **Execute**: `curl -s -X POST http://localhost:8001/madre/power/maintenance/post_task -H "Content-Type: application/json" -d '{"reason":"<task_summary>"}'`
2. **Capture**: output → docs/audit/<TS>/post_task_result.json
3. **Regenerate**: `PYTHONPATH=. python3 -m scripts.generate_db_map_from_db data/runtime/vx11.db`
4. **Verify DB**: `sqlite3 data/runtime/vx11.db "PRAGMA integrity_check;"` (should return "ok")
5. **Copy if container**: if post_task runs in Docker, copy docs/audit/<TS>/ to host
6. **Commit atomic**: "vx11: <task> + post-task maintenance + DB regeneration"
7. **Push**: vx_11_remote/main (NO force)

---

## DB MAINTENANCE AUTOMATION RULES

| Scenario | Action |
|----------|--------|
| Destructive (DELETE, rm, schema alter) | ALWAYS: PRAGMA checks + regenerate DB maps + post_task + atomic commit |
| Regular changes (edit code/config, 10+ edits) | Post-task recommended (or at end of session) |
| @vx11 status query | PRAGMA quick_check + integrity_check (read-only, no side-effects) |
| Periodic maintenance | Daily trigger via @vx11 maintenance (manual or cron) |

---

## .github Structure (Clean State 2026-01-02)

```
.github/
├── copilot-instructions.md              # This file (canonical rails)
├── instructions/vx11_global.instructions.md
├── workflows/ (4 CI workflows)
│   ├── vx11-e2e.yml
│   ├── operator-e2e-hardening.yml
│   ├── p11-secret-scan.yml
│   └── vx11-audit-bundle.yml
└── (no backups, no duplicates, no legacy)
```

**Active Tools (tools/)**:
- `deepseek_r1.py`: Basic DeepSeek wrapper (OpenAI-compatible)
- `vx11_status.py`: Status generator (markdown/JSON)
- `audit_bundle.py`: ZIP bundler for audit evidence
- `copilot_reasoning.py`: Advanced reasoning engine for complex tasks

**Backups Moved To**: `docs/audit/archived_github_backups/20260102_cleanup/`

---

Copilot:
- Audita primero.
- Ejecuta despues.
- Registra evidencia siempre.
- No rompe VX11.
- No limpia nada sin orden.
 - Addendum: see `.github/copilot-instructions.vx11_addendum.md` for required bootstrap/status/git/post-task rules.
