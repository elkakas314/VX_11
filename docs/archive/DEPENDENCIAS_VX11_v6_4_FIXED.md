# VX11 v6.4 – Dependencias y Dockerfiles Corregidos (IA aislada en Switch)

## Cambios realizados
- Se consolidaron requisitos mínimos sin IA en `requirements.txt` y `requirements_minimal.txt`; tentáculo usa `requirements_tentaculo.txt`; Switch mantiene IA en `requirements_switch.txt` únicamente.
- Dockerfiles revisados: tentaculo_link, madre, switch, hermes, spawner, hormiguero, mcp, operator/backend, manifestator (disabled), shub (disabled), operator/frontend. Ninguno copia el requirements global por error.
- Shub y Manifestator permanecen deshabilitados (comentario y sin healthcheck); no instalan IA.
- Healthchecks estandarizados en servicios activos con curl sin token.

## Módulos que instalaban IA accidentalmente (estado previo)
- Antes: cualquier Dockerfile que usara `requirements.txt` global arrastraba torch/transformers. Ahora solo Switch instala IA por diseño; los demás usan requirements mínimos.

## Requisitos finales por módulo
- Global mínimo (no IA): `requirements.txt` / `requirements_minimal.txt`.
- Tentáculo: `requirements_tentaculo.txt` (FastAPI/httpx/websockets/pydantic).
- Switch: `requirements_switch.txt` (FastAPI + IA ligera: transformers/huggingface-hub; sin torch GPU).
- Hermes/MCP/Madre/Spawner/Hormiguero/Operator-backend/Manifestator/Shub: `requirements_minimal.txt`.
- Operator-frontend: stack Node (package.json), sin IA.

## Dockerfiles (resumen)
- Usan Python 3.11-slim (servicios backend), npm/nginx para frontend.
- Limpieza apt y eliminación de `__pycache__` en runtime.
- Rutas creadas: `/app/logs /app/data /app/models /app/sandbox`.
- `ENV ULTRA_LOW_MEMORY=true` y `PYTHONUNBUFFERED=1` en backend activos.
- Healthcheck estandarizado `curl -fsS http://localhost:PORT/health`.

## Checklist post-corrección
- [x] IA confinada a Switch.
- [x] Shub y Manifestator deshabilitados.
- [x] Ningún Dockerfile instala requirements global por error.
- [x] Requirements mínimos definidos por módulo.
- [x] Healthchecks sin autenticación.

## Comandos para build/arranque
```bash
docker-compose build
docker-compose up -d
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```
