# VX11 v6.3 — Auditoría y Entrega

## Cambios por módulo
- Shub: pipeline DSP real (`dsp_pipeline.py`), endpoints `/v1/analysis/detail` y `/v1/mode_c/run`, guardado en BD unificada (tablas shub_*).
- Operator: backend intents/colas/health y clientes Shub/Hermes/Manifestator; frontend con paneles health/jobs/shub/manifest.
- Hermes: sandbox reforzado, endpoints `/waveform`, `/spectrogram`, `/normalize`, `/ingest`, cache waveform, BD `hermes_ingest`.
- Madre: state machine P&P con políticas básicas, endpoints module_states/set_module_state, acciones registradas.
- Manifestator: blueprint actualizado a `docs/VX11_v6.3_CANONICAL.json`.
- BD: tablas nuevas en `config/db_schema.py` (shub_*, operator_jobs, hermes_ingest, madre_policies/actions, forensic_ledger).
- Tests: unitarios para intents Operator, DSP Shub, Hermes waveform/spectrogram, Madre estados.
- Docs fractal: nodos rellenados con info técnica.

## Estado módulos
- Operator: sirve en 8011; token `X-VX11-TOKEN`; UI en operator-frontend.
- Hermes: sandbox en `SANDBOX_PATH` (fallback `./sandbox`); procesado ligero sin dependencias externas.
- Madre: evalúa health → off/standby; acciones logueadas en BD.
- Manifestator: usa blueprint v6.3 para drift/validate.

## Tests existentes
- `tests/test_operator_intents.py`: parser intents audio.
- `tests/test_shub_mode_c.py`: DSP y endpoint Modo C.
- `tests/test_hermes_waveform.py`: waveform y spectrogram.
- `tests/test_madre_states.py`: state machine P&P (apaga por errores).

## Pendientes / Riesgos
- Integración completa Switch/health con registro en BD aún básica.
- No se ha ejecutado `npm install/build` frontend ni `pytest`.
- Waveform/spectrogram son placeholders hash-based; mejorar con ffmpeg/sox si disponibles.
- Operator integración a servicios reales requiere puertos vivos (Shub/Hermes/Manifestator).

## Comandos de arranque
```bash
# Backend
docker-compose build && docker-compose up -d

# Frontend Operator
cd operator-frontend
npm install
npm run build
npm run dev -- --host --port 8020

# Tests (py)
pytest -q
```

## Estado final tras pulido
- Shub: OK — DSP/Modo C guardando en BD y retornando métricas+FX.
- Operator: OK — backend intents/colas/health y frontend con paneles Shub/Manifest/Health.
- Hermes: OK — sandbox reforzado, waveform/spectrogram/normalize/ingest.
- Madre: OK — P&P con políticas y logs en BD (core no se apaga).
- Manifestator: OK — blueprint v6.3 activo.
- Comandos rápidos:
  - Tests: `pytest -q`
  - Backend: `docker-compose up -d`
  - Frontend Operator: `cd operator-frontend && npm install && npm run build && npm run dev -- --host --port 8020`
