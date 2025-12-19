# Spawner v6.7

Ejecutor de procesos efímeros (hijas) solicitado por Madre/Hormiguero.

## Docker (compose)

- **Puerto:** 8008
- **Health:** `GET /health`
- **Volúmenes:** `./build/artifacts/sandbox` → `/app/sandbox`, `./data/runtime` → `/app/data/runtime`

## Rol

- Recibe solicitudes de spawn (por HTTP) y ejecuta comandos/plantillas controladas.
- Mantiene el runtime lo más liviano posible (modo ULTRA_LOW_MEMORY).

