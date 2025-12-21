# SHUB-NIGGURATH — Estado v7.1

## Resumen
- Módulo presente en `shubniggurath/` con subcarpetas: `core/`, `dsp/`, `ops/`, `pipelines/`, `routes/`, `workspace/` (tmp, cache), `docs/`, `tests/`.
- API mínima montada desde `shubniggurath/main.py` via `routes/main.py`:
  - `GET /shub/health`
  - `POST /shub/analyze`
  - `POST /shub/mix`
  - `POST /shub/event-ready`
- Dependencia de inferencia: usa Switch/Hermes vía HTTP (`route-v5`, `event-ready`), no carga modelos locales pesados.
- Estado operativo: **inactivo** por defecto (sin servicio en docker-compose). Listo para invocación on-demand (REAPER o llamadas directas).

## Compatibilidad VX11
- Tokens: respeta `settings.token_header` y `settings.api_token` (o `VX11_GATEWAY_TOKEN` si se expone).
- Puertos y rutas: no modifica `docker-compose.yml`; se integra cuando se monte el servicio.
- Imports internos validados: `core` → `pipelines` → `dsp/ops`; sin imports cruzados a otros módulos VX11.

## Uso recomendado
1. Arrancar Switch/Hermes/Spawner antes de llamar a `/shub/*`.
2. Para REAPER/CLI, usar `/shub/event-ready` como handshake.
3. No habilitar contenedor Shub hasta que se apruebe la puesta en marcha (revisar recursos).

## Tests
- `shubniggurath/tests/` cubre engine, pipelines y bridge mínimo.
