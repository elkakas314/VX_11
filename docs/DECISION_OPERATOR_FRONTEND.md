# DECISIÓN: operator/ (SANDBOX vs FUSIÓN)

Contexto

Existen dos frontends:
- `operator/` (dev sandbox)
- `operator_backend/frontend/` (production build used by docker-compose)

Decisión tomada (Fase 0 - 2025-12-14):

- `operator/` será etiquetado y tratado como **SANDBOX/DEV**.
- `operator_backend/frontend/` se mantiene como **FRONTEND CANÓNICO (PRODUCCIÓN)**.

Motivación

- `operator_backend/frontend` ya forma parte del pipeline de despliegue (`docker-compose.yml` references it) y dispone de `Dockerfile` y `nginx.conf` para producción.
- Mantener `operator/` como sandbox permite a desarrolladores iterar sin afectar despliegue.

Condiciones para futura fusión/eliminación

- Se requiere PR de consolidación con: tests, build reproducible, y respaldo.
- La fusión sólo se ejecutará después de: revisión humana, CI verde, y aprobación de owner.

---
Fecha: 2025-12-14
