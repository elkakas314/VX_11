# VX11 Switch v6.3

Router de modelos con cola priorizada y rotación de modelos locales.

## Docker (compose)

- **Servicio:** `switch`
- **Puerto:** 8002
- **Health:** `GET /health`

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
- Carril lenguaje en `/switch/chat`: prioriza Copilot CLI si está usable.

## Resumen canon (simple)
- Carril conversación: `/switch/chat` usa Copilot CLI si está usable.
- Si falla, intenta otros CLIs habilitados.
- Si no hay CLI usable, usa modelo local 7B fijo (standby).
- Devuelve `engine_used`, `used_cli`, `fallback_reason`, `latency_ms`, `tokens_used` si aplica.
- Carril tareas: `/switch/task` + cola persistente.
- Mantiene 1 modelo activo + 1 caliente.
- Clasifica tema simple para evitar thrash.
- El 7B fijo no rota; solo se enciende/apaga.
- Flags: `VX11_MOCK_PROVIDERS`, `VX11_COPILOT_CLI_ENABLED`, `VX11_TESTING_MODE`.
- Ejemplo:
```
curl -s http://localhost:8002/switch/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"messages":[{"role":"user","content":"hola"}]}'
# {"engine_used":"copilot_cli","used_cli":true,"fallback_reason":null,"tokens_used":12}
```

## Docker
```
docker build -f switch/Dockerfile -t vx11-switch:latest .
docker run -p 8002:8002 vx11-switch:latest
```

## Arranque rápido (manual)
Opción A (uvicorn, modo mock sin red):
```
VX11_MOCK_PROVIDERS=1 uvicorn switch.main:app --host 0.0.0.0 --port 8002
curl -fsS http://localhost:8002/health
```

Opción B (compose existente):
```
docker compose up -d tentaculo_link switch
curl -fsS http://localhost:8002/health
```

Nota: `curl http://localhost:8002/...` falla con "connection refused" si Switch no
está levantado; no se inicia por defecto en modo VX11.

## Flags relevantes
- `VX11_COPILOT_CLI_ENABLED=1` habilita Copilot CLI (default: 1).
- `VX11_MOCK_PROVIDERS=1` fuerza mocks en CLIs para tests/manual.
- `VX11_TESTING_MODE=1` activa rutas seguras de testing.

## Notas de API
- `/switch/chat` usa el carril lenguaje por defecto. Para usar el routing SIL,
  enviar `metadata.language_lane=false`.
