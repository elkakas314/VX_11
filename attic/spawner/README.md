# Spawner v6.3

Hijas efímeras con autoconsciencia y control P&P.

## Endpoints
- `POST /spawn` crea hija con TTL, prioridad y contexto.
- `POST /spawn/kill/{id}` mata hija.
- `GET /spawn/status/{id}` estado.
- `GET /spawn/list` lista hijas activas.
- `POST /spawn/cleanup` limpia finalizadas.
- `GET /health` healthcheck.

## Características
- Persistencia en BD (`hijas_runtime`) con nacimiento/muerte, TTL, propósito y módulo creador.
- Watchdog de TTL y heartbeat cada 5s.
- Límite de hijas activas (`SPAWNER_MAX_ACTIVE`, por defecto 5).
- Sandbox: cwd por defecto `/app/sandbox`, comandos permitidos listados en `ALLOWED_COMMANDS`.
- Eventos a Tentáculo Link vía `/events/ingest`.

## Docker
```
docker build -f spawner/Dockerfile -t vx11-spawner:latest .
docker run -p 8008:8008 vx11-spawner:latest
```
