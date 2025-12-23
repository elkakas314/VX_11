# Hermes v6.3

Gestor de modelos locales ligeros (<2GB) y CLI externos para VX11.

## Docker (compose)

- **Servicio:** `hermes`
- **Puerto:** 8003
- **Health:** `GET /health`

## Funcionalidad
- Registro y listado de modelos en SQLite (`/app/data/hermes_models.db`).
- Categorías por tipo de tarea (Python, seguridad, audio, etc).
- Deprecación automática cuando excede 30 modelos.
- Registro y renovación placeholder de CLI externos.
- Healthcheck: `GET /health`.
- Descubrimiento local/catalogo/HF en `/hermes/discover` (web opcional).

## Resumen canon (simple)
- `/hermes/discover` propone candidatos HF <2.5GB.
- Registra metadata: `download_url`, `model_id`, tamaño y dominio.
- NO descarga nada por defecto.
- Solo descarga si `allow_download=true` y `VX11_HERMES_DOWNLOAD_ENABLED=1`.
- `allow_web=true` habilita búsqueda web (OFF por defecto).
- Playwright/MCP solo si `VX11_HERMES_PLAYWRIGHT_ENABLED=1`.
- Sin red por defecto; fallback determinista offline.
- Escribe evidencia en `docs/audit/hermes_discover_*/`.
- Flags clave: `VX11_MOCK_PROVIDERS`, `VX11_HERMES_DOWNLOAD_ENABLED`.
- Health simple en `/health` para smoke.
- OpenRouter: pendiente (no activo, sin consumo).

Ejemplo offline (sin descarga):
```
curl -s http://localhost:8003/hermes/discover \\
  -H 'Content-Type: application/json' \\
  -d '{"apply":true,"allow_web":false,"allow_download":false}'
```

## Endpoints
- `GET /health`
- `GET /hermes/list`
- `POST /hermes/register_model`
- `POST /hermes/search_models`
- `POST /hermes/sync`
- `POST /hermes/reindex`
- `POST /hermes/discover` (plan/apply, allow_web)
- `GET /hermes/cli/list`
- `GET /hermes/cli/available`
- `POST /hermes/cli/register`
- `POST /hermes/cli/renew` (placeholder)

## Arranque rápido (manual)
Opción A (uvicorn, modo mock sin red):
```
VX11_MOCK_PROVIDERS=1 uvicorn switch.hermes.main:app --host 0.0.0.0 --port 8003
curl -fsS http://localhost:8003/health
```

Opción B (compose existente):
```
docker compose up -d tentaculo_link hermes
curl -fsS http://localhost:8003/health
```

Nota: `curl http://localhost:8003/...` falla con "connection refused" si Hermes no
está levantado; no se inicia por defecto en modo VX11.

## Flags relevantes
- `VX11_HERMES_DOWNLOAD_ENABLED=1` permite descargas (default OFF).
- `VX11_HERMES_PLAYWRIGHT_ENABLED=1` habilita Playwright/MCP (default OFF).
- `VX11_MOCK_PROVIDERS=1` evita red en rutas de prueba.
