# REPO LAYOUT CANÓNICO (VX11)

Este documento declara las decisiones canónicas para el layout del repositorio VX11. No ejecutar cambios; este archivo es precondición para la limpieza.

Decisiones canónicas (2025-12-14):

- Backend Operator (CANÓNICO): `operator_backend/backend/`
- Frontend Operator (PRODUCCIÓN - CANÓNICO): `operator_backend/frontend/`
- Frontend Operator (SANDBOX/DEV): `operator/` (uso local para desarrollo; NO desplegar en producción sin validación)
- Módulos VX11 core: `tentaculo_link/`, `madre/`, `switch/`, `hermes/`, `hormiguero/`, `manifestator/`, `mcp/`, `shubniggurath/`, `spawner/` (NO tocar)
- Runtime data y modelos: `data/` (volumen compartido)
- Artifacts de build: `build/`, `operator/dist/`, `operator_backend/frontend/dist/` — se consideran artefactos reproducibles y no deben versionarse
- Auditorías generadas por Copilot: `.copilot-audit/` (revisar y mover a `docs/audit/` si se aprueba)

Estados y roles:

- `canonical` = Fuente de verdad para CI/CD y despliegue en Docker
- `sandbox/dev` = Experimentos y desarrollo rápido; puede contener divergencias
- `runtime` = Carpetas usadas en tiempo de ejecución (data, models, logs)
- `archive` = Documentos históricos, snapshots de auditoría antiguos

Decisión explícita sobre `operator/` (obligatoria en Fase 0):
- `operator/` será tratado como **SANDBOX/DEV** por defecto. No se eliminará ahora. Una decisión futura podrá marcarlo para consolidación o eliminación pero eso requerirá PR separado, tests y backup.

Quién autoriza limpieza

- El mantenedor del repositorio o equipo de arquitectura (owner) debe aprobar cualquier acción de borrado o movimiento. Este archivo es la base para la limpieza.

---

Fecha: 2025-12-14
Autorización: DOCUMENTO PREPARADO POR COPILOT — requiere revisión humana y firma explícita antes de ejecutar acciones.
