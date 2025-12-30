# OPERATOR + SPAWNER CLOSURE — 20251230_185256

## FASE 0 — AUDITORÍA (API actual)
- Spawner expone endpoints en `spawner/main.py`:
  - `GET /health`
  - `GET /process/{daughter_id}`
  - `GET /process/uuid/{spawn_uuid}`
  - `DELETE /kill/{daughter_id}`
  - `POST /spawn`
  - `POST /spawner/create`
  - `POST /spawner/spawn`
- Invocación actual vía Madre:
  - Madre legacy incluye `/madre/daughter/spawn` y delega al spawner.
  - Madre v7 usa delegación a spawner en tareas de hijas (helpers y runner).
- Tentaculo_link ya define cliente/ruta a spawner (clients + route table).

Evidencia: `docs/audit/OPERATOR_SPAWNER_PHASE0_COMMANDS_20251230_185256.txt`

## FASE 1 — BACKEND (Operator + Events)
- Operator backend añadió endpoints:
  - `GET /operator/api/spawner/status`
  - `GET /operator/api/spawner/runs`
  - `POST /operator/api/spawner/submit` (rate-limited, Madre-gated vía tentaculo_link).
- tentaculo_link añadió router `routes/spawner.py`:
  - `GET /api/spawner/status` (read-only + policy window)
  - `GET /api/spawner/runs` (read-only + resumen logs)
  - `POST /api/spawner/submit` (bloqueado en `solo_madre`, siempre pasa por Madre vía `/madre/intent`).
- Eventos de spawn (`created/running/done/error`) integrados en `spawner/main.py` usando `operator_events` cuando `VX11_EVENTS_ENABLED=true`.

## FASE 2 — FRONTEND (Operator UI)
- Nuevo tab **Spawner** con modo observación (runs, estado, logs resumidos).
- Modo acción presente, deshabilitado cuando `solo_madre` (explica cómo habilitar ventana temporal via Madre).
- Estética oscura consistente.

Screenshot: `browser:/tmp/codex_browser_invocations/4464d7dca06a9e85/artifacts/artifacts/spawner-view.png`

## FASE 3 — tentaculo_link
- Rutas/proxy añadidas para spawner bajo `/operator/api/*` sin exposición directa del spawner.

## FASE 4 — TESTS + CIERRE
- Tests backend y smoke e2e (compose.full-test): **NO ejecutados en este entorno**.
  - Razón: no se ejecutó docker compose en este ciclo.

Evidencia adicional:
- `docs/audit/OPERATOR_SPAWNER_DEVSERVER_20251230_185256.txt`

