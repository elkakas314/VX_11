# VX11 Operator Agent Examples — 7 Escenarios Reales

**Versión:** 7.1 | **Fecha:** 2025-12-14  
**Objetivo:** Demonstrar cómo usar los 3 agentes en situaciones reales

---

## Scenario 1: Morning System Check (Lite, FREE)

### Situación
Es lunes 9:00 AM. Quieres verificar que VX11 está saludable antes de trabajar.

### Comando
```
@vx11-operator-lite status
```

### Ejecución (2s)

```
Checking system health...

Gateway (8000):       ✓ Responding
Operator API (8011):  ✓ Responding  
Operator UI (8020):   ✓ Responding
Database:             ✓ Connected (vx11.db, 2.5MB)
Last autosync:        2025-12-14 06:00 UTC (3h ago)
Drift status:         ✓ NO CRITICAL ISSUES
Incidents pending:    0

✅ System HEALTHY
```

### Resultado
- Tiempo: 2 segundos
- Costo: $0 (binary check)
- Acción siguiente: Proceed to work OR check drift if concerned

---

## Scenario 2: Detect and Fix Drift (Operator, $0.50)

### Situación
Un PR fue mergeado hace 2 horas con cambios en docs. Quieres asegurar que no hay drift.

### Step 1: Audit (Inspector, $0.10)

```
@vx11-inspector detect drift
```

### Ejecución (10s)

```
Scanning repository for drift...

Files analyzed: 2,341
Baseline comparison: OK

Issues found:
  ❌ STALE: docs/API_REFERENCE.md (last edited: 2025-12-05, 9 days ago)
  ❌ UNUSED: docs/legacy/OLD_ARCHITECTURE_v5.md (no references)
  ❌ ORPHAN: logs/pytest_phase5.txt (>7 days old)

Severity: LOW

Recommendations:
  1. Update API_REFERENCE.md timestamp
  2. Archive OLD_ARCHITECTURE_v5.md to docs/legacy/
  3. Clean old logs
```

### Step 2: Fix (Operator, $0.40)

```
@vx11-operator fix drift
```

### Ejecución (1m)

```
Fixing detected drift...

Step 1: Update stale docs
  - docs/API_REFERENCE.md → timestamp updated
  - Validating links... ✓ OK

Step 2: Archive unused files
  - docs/legacy/OLD_ARCHITECTURE_v5.md → archived to docs/legacy/
  - No broken references

Step 3: Clean old logs
  - Removed 5 logs >7 days old
  - Freed 50MB

Step 4: Validate
  - Python syntax: ✓ OK
  - Imports: ✓ No violations
  - Tests: ✓ 45/45 passed
  - Secrets: ✓ None detected

Step 5: Autosync check
  - Safe to autosync: YES
  - Committing changes...
  - ✅ Committed to main
```

### Resultado
- Tiempo: 70 segundos
- Costo: $0.50
- Cambios: 3 files updated, 50MB freed
- Autosync: Automatic (validated + safe)

---

## Scenario 3: Security Incident (Inspector, $0.50)

### Situación
Un desarrollador accidentalmente commiteó `.env` con secrets. GitHub Actions detectó. Necesitas investigar.

### Comando
```
@vx11-inspector audit security
```

### Ejecución (10s)

```
Running security audit...

Scanning tracked files for secrets...

FINDINGS:
  ❌ CRITICAL: .env tracked in git
     - Contains: DEEPSEEK_API_KEY, DATABASE_PASSWORD
     - Tracked since: 2025-12-14 08:15 UTC
     - Accessible to: Public repo viewers

  ❌ HIGH: tokens.env NOT in .gitignore
     - Should be excluded, currently tracked
     - Contains: VX11_TOKEN, API_TOKENS

  ✓ Config files: OK
     - settings.py has NO hardcoded secrets
     - deepseek.py uses env vars (correct)

SEVERITY: CRITICAL (secrets exposed)

RECOMMENDATIONS:
  1. Rotate all exposed tokens immediately
  2. Remove .env from git history: 
     git filter-branch --tree-filter 'rm -f .env' -- --all
  3. Add to .gitignore: *.env, *.env.local, tokens.env
  4. Force push (after rotation)
  5. Audit CloudFormation, IAM roles for lateral movement
```

### Report Generated
```
docs/audit/AUDIT_SECURITY_20251214T093000Z.md (full forensic report)
```

### Next Steps
```
@vx11-operator fix drift
  (Will remove .env from tracking, update .gitignore, validate)
```

### Resultado
- Tiempo: 10 segundos
- Costo: $0.50
- Acción: Manual token rotation (operator can't do this)
- Followup: @vx11-operator fix drift para cleanup automático

---

## Scenario 4: Import Violation (Operator+DeepSeek, $1.00)

### Situación
Test suite falla con `from madre import get_session` en `switch/main.py`. Violación de HTTP-only pattern.

### Step 1: Analyze (Operator, $0.50)

```
@vx11-operator audit imports
```

### Ejecución (15s)

```
Deep import analysis...

VIOLATION DETECTED:
  File: switch/main.py:45
  Import: from madre import get_session
  Pattern: Cross-module direct import
  Severity: CRITICAL
  
  Rule violated: HTTP-only inter-module communication
  
Analysis:
  - madre.get_session is used for: DB session initialization
  - Current pattern: DIRECT function call
  - Canonical pattern: HTTP GET /madre/session endpoint
  
Suggested refactoring:
  Before: from madre import get_session
  After:  async def get_madre_session():
            response = await client.get("http://madre:8001/session")
            return response.json()

Test impact: Would fix test failures in switch/test_integration.py
```

### Step 2: Fix (Operator, $0.50)

```
@vx11-operator fix drift
```

### Ejecución (2m)

```
Auto-refactoring...

Detecting: Cross-module import in switch/main.py:45

Refactoring pattern:
  Step 1: Create HTTP wrapper function
  Step 2: Replace imports with HTTP call
  Step 3: Update dependent code
  Step 4: Run tests

Changes:
  - switch/main.py:45 → Removed "from madre import"
  - switch/main.py:120 → Added HTTP wrapper
  - switch/client.py:NEW → New HTTP async function
  
Validation:
  - Python syntax: ✓ OK
  - Imports: ✓ No violations
  - Tests: ✓ 45/45 now pass
  - Secrets: ✓ None

Autosync: YES (safe refactoring)
  ✅ Committed as: "refactor: switch imports to HTTP-only (closes #145)"
```

### Resultado
- Tiempo: 135 segundos
- Costo: $1.00 (DeepSeek reasoning)
- Tests fixed: YES
- Autosync: Automatic

---

## Scenario 5: Task Execution (Operator, $0.10-$1.00)

### Situación
Necesitas indexar todos los modelos HuggingFace disponibles y guardar en BD. Es tarea async que dura 5-10 min.

### Comando
```
@vx11-operator run task: index all huggingface models and store in db
```

### Ejecución (5-10m)

```
Creating task and spawning workers...

Task created:
  ID: task-a1b2c3d4e5f6
  Intent: index_huggingface_models
  Priority: 5
  Status: PENDING

Delegating to Madre...
  Madre received task
  Spawning: 1 main worker + 4 parallel sub-workers
  Sub-workers assigned:
    - hija-0: Scan HF repo indexes (models A-F)
    - hija-1: Scan HF repo indexes (models G-M)
    - hija-2: Scan HF repo indexes (models N-S)
    - hija-3: Scan HF repo indexes (models T-Z)

Monitoring progress:
  [████░░░░░░] 40% (5 min elapsed)
  [██████░░░░] 60% (7 min elapsed)
  [████████░░] 80% (9 min elapsed)
  [██████████] 100% (10 min elapsed, 45 models indexed)

Task completed:
  Status: SUCCESS
  Models indexed: 45
  New models: 12
  Updated models: 33
  Storage: BD + cache/models/
  Duration: 10min 23s

Results saved to:
  - data/runtime/vx11.db (models_registry table)
  - logs/task_a1b2c3d4e5f6.log

✅ Task completed successfully
```

### Resultado
- Tiempo: 10 minutos
- Costo: $0.50 (lightweight task)
- Models: 45 indexed
- Autosync: N/A (metadata only)

---

## Scenario 6: Full Validation Before Release (Operator, $0.50)

### Situación
Tienes cambios listos. Antes de mergear a main, quieres validación 100%.

### Comando
```
@vx11-operator validate
```

### Ejecución (30s)

```
Running full validation suite...

✓ Python syntax (compileall)
  tentaculo_link/: OK
  operator_backend/: OK
  config/: OK
  No syntax errors

✓ Docker configuration
  docker-compose.yml: Valid
  docker-compose.shub.yml: Valid
  All ports available (8000-8020)

✓ Imports validation
  Cross-module imports: 0 violations ✓
  Import cycles: None detected ✓
  Dead imports: None ✓

✓ Security scan
  Secrets: None detected ✓
  .gitignore compliance: ✓
  Tracked sensitive files: None ✓

✓ Frontend type checking
  TypeScript: 0 errors ✓
  React components: All typed ✓

✓ Test suite
  pytest: 45/45 PASSED ✓
  Coverage: 78% (acceptable)

VALIDATION RESULT: ✅ ALL CHECKS PASSED

Safe to merge. Autosync: ENABLED
```

### Resultado
- Tiempo: 30 segundos
- Costo: $0.50
- Status: Ready for merge
- Risk level: LOW

---

## Scenario 7: Cleanup & Maintenance (Lite, FREE)

### Situación
Fin de mes. Quieres limpiar archivos viejos, liberar espacio, archivar logs.

### Comando
```
@vx11-operator-lite cleanup
```

### Ejecución (30s)

```
Running cleanup...

Cleaning old logs:
  Removed: logs/pytest_phase1.txt (89 days old)
  Removed: logs/pytest_phase2.txt (72 days old)
  Freed: 120MB

Archiving crash dumps:
  Archived: 45 crash dumps > 30 days → forensic/archive/2025-11-14.tar.gz
  Kept: 3 recent crashes for debugging
  Freed: 250MB

Rotating snapshots:
  Removed: snapshot_20251101.tar.gz (too old)
  Kept: 5 most recent snapshots
  Freed: 500MB

Pruning BD:
  Cleaned: 1,200 old incident records
  Cleaned: 850 old task records
  DB size: 2.5MB → 1.8MB (freed 700MB metadata)

Total freed: 1.57GB

✅ Cleanup complete
```

### Resultado
- Tiempo: 30 segundos
- Costo: FREE
- Disk freed: 1.57GB
- Maintenance: Complete

---

## Quick Decision Tree

```
┌─ Morning check?
│  └─→ @vx11-operator-lite status (FREE, 2s)
│
├─ Need autosync?
│  ├─ Check first: @vx11-inspector detect drift ($0.10, 10s)
│  └─ If safe: @vx11-operator fix drift ($0.40, 1m)
│
├─ Security audit?
│  └─→ @vx11-inspector audit security ($0.05, 5s)
│
├─ Complex task?
│  ├─ Simple: @vx11-operator-lite cleanup (FREE, 30s)
│  └─ Heavy: @vx11-operator run task: ... ($1.00+, variable)
│
├─ Import problem?
│  └─→ @vx11-operator audit imports + fix drift ($1.00, 2m)
│
├─ Ready to release?
│  └─→ @vx11-operator validate ($0.50, 30s)
│
└─ Stuck?
   └─→ @vx11-operator-lite use deepseek: question ($0.50+, 30s)
```

---

**VX11 Operator Examples v7.1** — Scenarios, costs, durations, outputs.

