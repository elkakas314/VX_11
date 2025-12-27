# VX11 Audit Index & Navigation

**Generated**: 2025-12-27T01:21:19Z
**Purpose**: Single source of truth for audit directory structure and how to find recent audits

## Latest 10 OUTDIRs (Most Recent)

| # | Directory | Date | Focus |
|---|-----------|------|-------|
| 1 | [vx11_prompt1_bootstrap_20251227T012119Z](vx11_prompt1_bootstrap_20251227T012119Z) | 2025-12-27 01:21 | 🔍 **THIS AUDIT**: Bootstrap + Deep audit + specs |
| 2 | [vx11_status_fix_20251226T015000Z](vx11_status_fix_20251226T015000Z) | 2025-12-26 01:50 | Status endpoint fixes |
| 3 | vx11_stabilize_20251225T020359Z | 2025-12-25 02:03 | Stability validation |
| 4 | vx11_stability_20251225T045420Z | 2025-12-25 04:54 | Health checks |
| 5 | vx11_stability_20251225T045413Z | 2025-12-25 04:54 | Health checks |
| 6 | vx11_stability_20251225T045412Z | 2025-12-25 04:54 | Health checks |
| 7 | vx11_stability_20251225T045217Z | 2025-12-25 04:52 | Smoke tests |
| 8 | vx11_stability_20251225T045209Z | 2025-12-25 04:52 | Smoke tests |
| 9 | vx11_stability_20251225T044847Z | 2025-12-25 04:48 | Startup tests |
| 10 | vx11_stability_20251225T044839Z | 2025-12-25 04:48 | Startup tests |

## This Audit (PROMPT 1) — Key Files

**Location**: `docs/audit/vx11_prompt1_bootstrap_20251227T012119Z/`

### Deliverables Generated
1. **AGENT_EFFECTIVE_CONFIG.md** — Configuration snapshot (instructions, tools, policies)
2. **GIT_SNAPSHOT.md** — Git state (branch, commits, diffs)
3. **DOCKER_SNAPSHOT.md** — Docker services (running containers, compose config)
4. **HEALTH_OPENAPI.md** — Health checks + OpenAPI schema inspection
5. **DB_STATUS.md** — Database integrity + table counts + schema
6. **CANON_STATUS.md** — Canonical specs validation + hash
7. **REPORT_GAPS.md** — P0/P1/P2 technical gaps
8. **OPERATOR_SPEC_SUMMARY.md** — Operator backend + local specs
9. **SHUB_SPEC_SUMMARY.md** — Shubniggurath AI engine specs
10. **SPEC_FILES_FOUND.txt** — Spec file locations
11. **NEXT_STEPS.md** — PROMPT 2 readiness + action plan
12. **AUDIT_CLEANUP_POLICY.md** — Retention + archiving policy

### Quick Reference
- 🔴 **P0 Blockers**: 3 items (see REPORT_GAPS.md)
- 🟡 **P1 High**: 3 items (architectural decisions needed)
- 🟠 **P2 Medium**: 3 items (nice-to-have cleanup)

---

## Archived OUTDIRs (To Be Moved)

**Location**: `docs/audit/_archive/2025-12/` (after archiving)

122 additional stability audits + 6 legacy audit dirs ready for compression.

**How to restore**:
```bash
# Extract a specific archived audit
tar xzf docs/audit/_archive/2025-12/vx11_stability_XXXXXXXX.tar.gz -C docs/audit/

# Or list contents before extracting
tar tzf docs/audit/_archive/2025-12/vx11_stability_batch_1.tar.gz | head -20
```

---

## Core Audit Files (Permanent)

These files are NEVER archived:
- **DB_SCHEMA_v7_FINAL.json** — Current DB schema reference
- **DB_MAP_v7_FINAL.md** — Table mapping + relationships
- **DB_MAP_v7_META.txt** — Metadata + integrity status
- **SCORECARD.json** — Current metrics snapshot
- **CLEANUP_EXCLUDES_CORE.txt** — Protected file list
- **INDICE_GLOBAL.md** — This file (navigation)

---

## How to Find Audits by Task

### By Date
```bash
ls -lht docs/audit/vx11_*/ | head -10
```

### By Name Pattern
```bash
# Bootstrap audits
ls docs/audit/vx11_prompt1_bootstrap_*/

# Stability audits
ls docs/audit/vx11_stability_*/

# Codex runs
ls docs/audit/vx11_codex_run_*/

# Full audits
ls docs/audit/VX11_FULL_AUDIT_*/

# Local ready audits
ls docs/audit/VX11_LOCAL_READY_*/
```

### By Size
```bash
du -sh docs/audit/vx11_* | sort -hr | head -20
```

---

## Audit Metadata

| Property | Value |
|----------|-------|
| **Total OUTDIRs** | 132+ (including archived) |
| **Current size** | 2.8 GB |
| **Live OUTDIRs** | 10 (top recent) |
| **Archived (planned)** | 122+ (to compress) |
| **Target size** | ~1 GB (after archive) |
| **Forensic dirs** | 10+ (NEVER deleted) |
| **Last cleanup** | 2025-12-27T01:21:19Z (this audit) |

---

## Next Audit (PROMPT 2)

**Expected**: 2025-12-27 ~10:00-12:00Z (after PROMPT 1 implementation)
**Scope**: Operator end-to-end wiring + docker-compose integration
**Outdir**: `docs/audit/vx11_prompt2_operator_e2e_<TS>Z/`

---

**Maintained by**: @vx11 AGENT
**Last Updated**: 2025-12-27T01:21:19Z
**Policy**: See AUDIT_CLEANUP_POLICY.md for retention rules
