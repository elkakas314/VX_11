# Operator v6.3
- Backend FastAPI (8011) con intents de audio, colas en memoria, health agregado y clientes a Shub/Hermes/Switch/Manifestator.
- Endpoints clave: `/intents/parse`, `/intents/execute`, `/jobs/{id}`, `/health/aggregate`, `/api/shub/run_mode_c`.
- UI (operator-frontend) incluye dashboard, chat, panel Shub (Modo C), panel Manifestator, health tiles, jobs.
- Token `X-VX11-TOKEN` requerido; bypass solo en pytest mediante settings.testing_mode.
