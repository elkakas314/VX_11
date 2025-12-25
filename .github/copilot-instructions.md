# Copilot Instructions for VX11

## CONTEXT BOOTSTRAP (MANDATORY ON EVERY @vx11 TRIGGER)

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
- El proyecto es VX11.
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

Copilot:
- Audita primero.
- Ejecuta despues.
- Registra evidencia siempre.
- No rompe VX11.
- No limpia nada sin orden.
 - Addendum: see `.github/copilot-instructions.vx11_addendum.md` for required bootstrap/status/git/post-task rules.
