CONTRATO DE AGENTES VX11 (resumen)
- NO preguntar salvo acciones destructivas reales (rm, rmdir, mover fuera de docs/audit, tocar tokens/secrets, git reset/clean/push, docker compose up/down).
- Antes de actuar: consultar y validar la fuente de verdad:
  - docs/audit/DB_MAP_v7_FINAL.md
  - docs/audit/DB_SCHEMA_v7_FINAL.json
- Evidencia obligatoria: todo output relevante se escribe en docs/audit/.
- Forense: forensic/crashes NUNCA se borra; si es necesario, se ARCHIVA en docs/audit/archived_forensic/.

**Cleanup Contract Addendum**

- Antes de mover o archivar archivos a `attic/` o ubicaciones de backup: cargar `docs/audit/CLEANUP_EXCLUDES_CORE.txt` y aplicar hard-exclude. Si un path CORE aparece en la lista de candidatos => ABORTA y reporta en `docs/audit/`.
- Nunca mover o eliminar archivos listados en `docs/audit/CLEANUP_EXCLUDES_CORE.txt` sin autorización explícita y registro de evidencia en `docs/audit/`.

---

## Tools Location (Active - 2026-01-02)

All copilot tools consolidated in `tools/` folder:

- **`tools/deepseek_r1.py`**: DeepSeek R1 reasoning engine wrapper (OpenAI-compatible)
- **`tools/vx11_status.py`**: System status generator (markdown/JSON output)
- **`tools/audit_bundle.py`**: Audit evidence bundler (ZIP compression)
- **`tools/copilot_reasoning.py`**: Advanced reasoning engine for complex tasks (2026-01-02: moved from .github/)

**Note**: Legacy backups stored in `docs/audit/archived_github_backups/20260102_cleanup/` for audit trail.

