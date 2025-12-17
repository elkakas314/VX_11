# TENTACULO_LINK Audit BEFORE - 2025-12-16

Resumen inicial de auditoría previa a cambios (FASE 0-2)

- Repo root: /home/elkakas314/vx11
- Branch creado: `tentaculo-link-prod-align-v7`
- Backup: `.backups/tentaculo_link/backup_20251216_034513`

Hallazgos iniciales:

- Archivo sensible detectado y movido a cuarentena:
  - `tokens.env` (contenía DEEPSEEK_API_KEY, HUGGINGFACE_TOKEN, OPENROUTER_API_KEY, GITHUB_TOKEN_CLASSIC) → movido a `tentaculo_link/_legacy/quarantine/DO_NOT_RUN/tokens.env`.
  - Se creó `tentaculo_link/_legacy/quarantine/DO_NOT_RUN/README_DO_NOT_RUN.md` explicando la cuarentena.
  - Se creó `tokens.env` redacted en repo root con placeholders.

- Directories creados en `tentaculo_link/_legacy/`:
  - `inbox/2025-12-16/`
  - `archive/`
  - `quarantine/DO_NOT_RUN/`
  - `notes/`

Archivos movidos a cuarentena (secrets redactados):

- `tokens.env` → `tentaculo_link/_legacy/quarantine/DO_NOT_RUN/tokens.env`
- `docs/VX11_v7_FINAL_PRODUCTION_READY.md` → `tentaculo_link/_legacy/quarantine/DO_NOT_RUN/VX11_v7_FINAL_PRODUCTION_READY.md`
- `docs/docsset/tokens` → `tentaculo_link/_legacy/quarantine/DO_NOT_RUN/docs_tokens`
- `scripts/secure/secure_tokens.env.master` → `tentaculo_link/_legacy/quarantine/DO_NOT_RUN/secure_tokens.env.master`

Se añadieron placeholders/redacted files en las ubicaciones originales para señalizar la remoción.

- Runtime status (desde `VX11_STATUS_REPORT.md`): todos los servicios OK excepto `shubniggurath` → BROKEN.

Acciones siguientes planificadas:
- Auditoría profunda del módulo `tentaculo_link` (estructura, endpoints, routes, clients).
- Crear MOVE_PLAN en `tentaculo_link/_legacy/notes/MOVE_PLAN_2025-12-16.md` cuando se muevan archivos legacy.
- Implementar gateway thin en `tentaculo_link/main.py` + subpackages `api/`, `core/`, `db/`, `config/`, `adapters/` (mantener bajo consumo).

Notas de seguridad:
- No se debe comprometer más los secrets. Quarantine contiene los originales y está listado en `.gitignore`.
