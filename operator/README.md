# Operator (VX11)

`operator-backend` expone la API del dashboard (compose: `8011`) y `operator-frontend` sirve la UI (compose: `8020`).

Puntos canónicos:
- Contexto operativo global: `docs/VX11_CONTEXT.md`
- Health: `GET http://localhost:8011/health`
- UI: `http://localhost:8020/`

## Arranque rápido (stack local)
Dependencias: `tentaculo_link` y `switch` (el backend depende de ambos).
```
docker compose up -d tentaculo_link switch operator-backend operator-frontend
curl -fsS http://localhost:8011/health
curl -fsS http://localhost:8020/
```
