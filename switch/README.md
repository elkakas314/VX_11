# VX11 Switch v6.3

Router de modelos con cola priorizada y rotación de modelos locales.

## Endpoints
- `GET /health`
- `POST /switch/route-v5`
- `GET /switch/queue/status`
- `GET /switch/queue/next`
- `POST /switch/admin/preload_model`
- `POST /switch/admin/set_default_model`
- `GET /switch/models/available`

## Características
- Cola FIFO priorizada (shub > operator/tentaculo_link > madre > hijas > default).
- Modelo activo + modelo precalentado.
- Hasta 30 modelos locales registrados.
- Integración con Hermes para CLI (enrutado opcional).

## Docker
```
docker build -f switch/Dockerfile -t vx11-switch:latest .
docker run -p 8002:8002 vx11-switch:latest
```
