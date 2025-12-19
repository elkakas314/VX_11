# Hormiguero VX11 (v7)

Rol: vigilancia + ejecucion minima ultra low-power.

## Arquitectura
- Reina: orquesta scans, agrega hallazgos, consulta Switch antes de feromonas.
- Hormigas: escanean y reportan; sin feromonas.

## API
- GET /health
- GET /hormiguero/status
- POST /hormiguero/scan/once
- GET /hormiguero/incidents
- GET /hormiguero/pheromones
- POST /hormiguero/actions/preview
- POST /hormiguero/actions/apply

## Guardrails
- `HORMIGUERO_ACTIONS_ENABLED=0` por defecto.
- Apply requiere aprobacion en DB (pheromone_log) y correlation_id.

## DB
Usa `data/runtime/vx11.db` y asegura tablas/columnas requeridas para:
`hormiga_state`, `incidents`, `pheromone_log`, `feromona_events`.
