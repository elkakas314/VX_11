# GitHub Workflows — Path-Specific Instructions

**Scope:** `.github/workflows/`

## Reglas YAML Workflow

### 1. Concurrency Policy
```yaml
concurrency:
  group: vx11-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```
- **Efecto:** Si nuevo run entra en mismo workflow + branch, cancela el anterior.
- **Por qué:** Evita múltiples CI/audits simultáneos que saturen recursos.

### 2. Permisos Mínimos (Least Privilege)
```yaml
permissions:
  contents: read          # ✅ Solo si necesitas leer repo
  pull-requests: read     # ✅ Si auditas PRs
  # NO: write, admin, etc. (a menos que sea necesario)
```

### 3. Artifacts (v4+)
```yaml
- uses: actions/upload-artifact@v4  # ✅ v4, no v3
  with:
    name: vx11-audit-report
    path: docs/audit/AUDIT_*.md
    retention-days: 30               # ✅ Limpiar automáticamente
```

### 4. Workflow Dispatch (Manual Trigger)
```yaml
on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Dry-run only (no apply)"
        required: false
        default: "true"
```
- Permite ejecución manual desde GitHub UI sin push.

### 5. Exclusiones Smart
```yaml
on:
  push:
    paths-ignore:
      - "docs/**"
      - "logs/**"
      - ".copilot-audit/**"
      - "*.md"
```
- **Evita** re-runs por cambios en docs o MD.

### 6. Separación: STATIC vs RUNTIME

**STATIC AUDIT** (GitHub runner, no docker local):
- Python compile check
- YAML validation
- Grep pattern searches
- Import analysis
- **Tiempo:** <2 min, sin recursos externos

**RUNTIME AUDIT** (Local Copilot, docker local Lenovo):
- `docker compose ps`
- HTTP health checks
- Drift detection (file hashing)
- BD queries
- **Tiempo:** 2–5 min, MAX 2 containers

### 7. Artifacts Export
```yaml
- run: python scripts/vx11_audit.py > audit_report.txt
- uses: actions/upload-artifact@v4
  with:
    name: audit-report-${{ github.run_id }}
    path: audit_report.txt
```
- Reports → GitHub UI → `docs/audit/` en commit local.

## Workflow Checklist

Antes de mergear un `.yml`:
- [ ] `concurrency` definido
- [ ] `permissions` mínimo
- [ ] `actions/upload-artifact@v4` (si hay artifacts)
- [ ] `workflow_dispatch` presente
- [ ] Paths-ignore correcto
- [ ] `continue-on-error: true` SOLO si apropiado
- [ ] YAML válido: `yamllint .github/workflows/nombre.yml`
- [ ] Sin hardcoded tokens/secrets

## Naming Convention

- `vx11-ci.yml` — Python compile, lint, tests (STATIC)
- `vx11-audit-static.yml` — Tree, imports, drift detection (STATIC)
- `vx11-audit-runtime.yml` — HTTP checks, DB validation (RUNTIME, local)
- `vx11-autosync.yml` — Auto-repairs, blocker check (GATED)

---

**Última actualización:** 2025-12-16  
**Policy:** Concurrency + Least Privilege + Artifact v4 + Dispatch
