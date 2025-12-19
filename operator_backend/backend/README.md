# Operator Backend v7.0

API backend para Operator (UI/automation).

## Docker (compose)

- **Puerto:** 8011
- **Health:** `GET /health`
- **Volúmenes:** `./data` → `/app/data` (incluye `data/runtime/vx11.db`)

## Rol

- Expone endpoints para sesiones/mensajes/tareas del operador.
- Opera sobre la BD unificada `vx11.db`.

