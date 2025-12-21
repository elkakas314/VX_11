# Operator Frontend v7.0

Frontend (web UI) del Operator.

## Docker (compose)

- **Puerto:** 8020
- **Health:** `GET http://127.0.0.1:8020/` (root)

## Rol

- UI para interactuar con el backend de Operator.

## Arranque rápido (stack local)
```
docker compose up -d operator-backend operator-frontend
curl -fsS http://localhost:8020/
```
