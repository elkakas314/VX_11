# Deployment: Tentáculo Link (Gateway VX11 v7.1)

**Versión:** 7.1 | **Módulo:** tentaculo_link (Puerto 8000)  
**Status:** AUTO-GENERATED STUB (safe)

## Descripción

Tentáculo Link es el **frontdoor único** del sistema VX11. Actúa como:
- Router HTTP central (mapea intents a módulos)
- Circuit breaker resiliente (protege contra cascadas)
- Control de autenticación (header `X-VX11-Token`)
- Agregador de estado (`/vx11/status`)

## Puertos

| Módulo | Puerto | Rol |
|--------|--------|-----|
| Tentáculo Link (gateway) | 8000 | HTTP frontdoor |
| Madre | 8001 | Orquestación |
| Switch | 8002 | Router IA |
| Hermes | 8003 | CLI execution |
| Hormiguero | 8004 | Paralelización |
| Manifestator | 8005 | Auditoría + patches |
| MCP | 8006 | Conversacional |
| Shub Niggurath | 8007 | Procesamiento avanzado |
| Spawner | 8008 | Procesos efímeros |
| Operator Backend | 8011 | Chat + session |
| Operator Frontend | 8020 | React UI (Vite) |

## Configuración

Ver: `config/settings.py` para URLs, timeouts, tokens.

## Health Checks

```bash
# Gateway
curl http://127.0.0.1:8000/health

# Todos los módulos
for port in {8000..8008} 8011; do
  curl http://127.0.0.1:$port/health
done
```

## Documentación Completa

Ver:
- `docs/ARCHITECTURE.md` — Visión general
- `docs/API_REFERENCE.md` — Endpoints
- `.github/copilot-instructions.md` — Instrucciones canónicas
