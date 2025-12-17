# Documentation & Audit Path — Instructions

**Scope:** `docs/`, `docs/audit/`, `.copilot-audit/`

## Reports y Auditorías

### Ubicación de Reports
- **Active Audits**: `docs/audit/AUDIT_*.md` (timestamped)
- **Archived**: `docs/audit/archive/YYYY-MM-DD/` (si se archivan)
- **Phase Reports**: `docs/audit/PHASE{N}_*.md`
- **Enforcement**: `docs/audit/DRIFT_LATEST.md`, `docs/audit/AGENT_STATE_CURRENT.md`

### Qué Documentar en Reports
1. **Timestamp UTC** (ISO 8601)
2. **Módulos auditados** (lista + estado)
3. **Drift detectado** (si aplica)
4. **Comandos ejecutados** (curl, docker, python)
5. **Resultados finales** (OK/BROKEN/ACTION NEEDED)
6. **Próximos pasos** (recomendaciones)

### Secciones Estándar en Reportes
```markdown
# AUDIT: [Name] — [Date]

## Estado Actual
- Tentáculo Link: [OK|BROKEN]
- Madre: [OK|BROKEN]
- ...

## Cambios Detectados
- [lista de diffs o modificaciones]

## Recomendaciones
1. [acción 1]
2. [acción 2]

## Comandos Usados
\`\`\`bash
curl -s http://127.0.0.1:8000/health
...
\`\`\`

## Metadata
- **Runner:** GitHub Actions / Local Copilot
- **Duration:** X segundos
- **Artifacts:** [links]
```

### Prohibido en Docs
- ❌ Tokens o credenciales
- ❌ Full dumps de logs (use head/tail)
- ❌ Arquitectivos temporales (*.tmp, *.bak)
- ❌ Cambios sin timestamp o metadata

### Limpiar Docs Antiguos
- Cada 30 días: revisar `docs/audit/` y archivar reports >30d en `docs/audit/archive/`
- Si recurso >5MB: comprimir con `tar.gz`
- Mantener últimos 10 reports activos

## Guía de Auditorías

### Auditoría Estática (sin containers)
- Python: `python -m py_compile`
- YAML: `yamllint .github/workflows/`
- Imports: `grep -r "^import\|^from" {modulo}`
- **Tiempo:** <1 min, recursos mínimos

### Auditoría Runtime (containers ON)
- **MAX 2 containers** activos durante audit
- Health: `curl -s http://localhost:PORT/health`
- Drift: comparar archivos contra baseline
- **Tiempo:** 2–5 min
- Guardar logs en `forensic/{modulo}/logs/YYYY-MM-DD.log`

### Drift Detection
```bash
# Computar hashes actuales
find tentaculo_link -type f -name "*.py" | xargs sha256sum > current.hashes

# Comparar con baseline
diff baseline.hashes current.hashes > drift.txt
```

---

**Última actualización:** 2025-12-16  
**Policy:** Low-power audits, timestamped reports, archived >30d
