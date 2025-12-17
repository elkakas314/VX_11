# Secret Scan Report — 2025-12-16

**Scope**: Full repo excluding `.backups/`, `tentaculo_link/_legacy/quarantine/`, `tentaculo_link/_legacy/archive/`, `.git/`, `.venv/`, `__pycache__/`.

## Findings

| Archivo | Patrón | Contenido | Acción |
|---------|--------|----------|--------|
| `tokens.env.master` | `DEEPSEEK_API_KEY`, `HUGGINGFACE_API_KEY` | Master token vars (template) | Movido a `tentaculo_link/_legacy/quarantine/DO_NOT_RUN/tokens.env.master_quarantine` |
| `tokens.env.sample` | Placeholders solo | `TU_DEEPSEEK_API_KEY_AQUI` (template) | OK — es sample, contiene solo placeholders |
| `tokens.env` | NO EXISTE en raíz (redacted por quarantine anterior) | — | OK — estaba en quarantine |
| Múltiples `.py`, `.md` archivos | Referencias a `DEEPSEEK_API_KEY=` | Références de código (no valores reales) | OK — son referencias, no secretos |

## Status

✅ **LIMPIO**: No hay secretos reales expuestos fuera de quarantine.

- `tokens.env.master` → quarantine (2025-12-16T15:30Z)
- Placeholder redacted en lugar del original
- `.gitignore` ya incluye `.backups/`, quarantine paths

## Próximos pasos

- CI/CD debe validar:
  - `tokens.env*` no se trackea (excl. `.sample`)
  - Secrets no se pushean a origin
  - Quarantine path no se pushea
