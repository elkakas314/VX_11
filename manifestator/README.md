# Manifestator (VX11)

Este módulo está **desactivado/legacy** en VX11 v7 (aparece como servicio compose `manifestator` con profile `disabled`, por lo que no arranca por defecto).

Referencias canónicas:
- Contexto/puertos: `docs/VX11_CONTEXT.md`

## Docker (compose)

- **Servicio:** `manifestator` (profile: `disabled`)
- **Puerto:** 8005
- **Health:** `GET /health`

## Arranque (solo si necesitas legacy)
```
docker compose --profile disabled up -d manifestator
curl -fsS http://localhost:8005/health
docker compose logs --no-color --tail=200 manifestator
```

## Estado canónico
- CANONICALLY_DISABLED (legacy): el stack VX11 no depende de este módulo para producción.
