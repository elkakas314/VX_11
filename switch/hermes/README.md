# Hermes v6.3

Gestor de modelos locales ligeros (<2GB) y CLI externos para VX11.

## Funcionalidad
- Registro y listado de modelos en SQLite (`/app/data/hermes_models.db`).
- Categorías por tipo de tarea (Python, seguridad, audio, etc).
- Deprecación automática cuando excede 30 modelos.
- Registro y renovación placeholder de CLI externos.
- Healthcheck: `GET /health`.

## Endpoints
- `GET /health`
- `GET /hermes/list`
- `POST /hermes/register_model`
- `POST /hermes/search_models`
- `POST /hermes/sync`
- `POST /hermes/reindex`
- `GET /hermes/cli/list`
- `GET /hermes/cli/available`
- `POST /hermes/cli/register`
- `POST /hermes/cli/renew` (placeholder)

## Docker
```
docker build -f hermes/Dockerfile -t vx11-hermes:latest .
docker run -p 8003:8003 vx11-hermes:latest
```
