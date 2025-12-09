# Madre v6.3

Orquestador tentacular con scheduler y autoconsciencia global.

## Funciones clave
- Scheduler que refresca estado del sistema (CPU, memoria, cola de switch, hijos activos) cada 5s.
- Actualiza `system_state` en BD y registra decisiones en `scheduler_history`.
- Envía eventos a Tentáculo Link (`/events/ingest`) con `system_state_update`.
- Integra con spawner para crear/terminar hijas; con switch para cola y modelos.

## Endpoints
- `GET /health`
- `POST /control`
- Métricas: `/metrics/cpu`, `/metrics/memory`, `/metrics/queue`, `/metrics/throughput`
- HIJAS: `/madre/hija/{id}`, `/madre/hijas`

## Docker
```
docker build -f madre/Dockerfile -t vx11-madre:latest .
docker run -p 8001:8001 vx11-madre:latest
```
