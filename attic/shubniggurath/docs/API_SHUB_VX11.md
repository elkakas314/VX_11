# API SHUB VX11 (mínima)

## Autenticación
Usa `X-VX11-Token` (o `settings.token_header`) con token de VX11. No expone CORS amplio; monta el router dentro de la app FastAPI existente.

## Endpoints
### GET /shub/health
Devuelve estado del módulo, pipelines y puertos configurados.

### POST /shub/analyze
Body:
```json
{
  "audio": [0.1, -0.2, ...],
  "sample_rate": 48000,
  "metadata": {"style": "rock"}
}
```
Respuesta: análisis heurístico, issues detectados y headline para Switch.

### POST /shub/mix
Body:
```json
{
  "stems": {"vox": [...], "drums": [...]},
  "metadata": {"target": "demo"}
}
```
Respuesta: mezcla promedio, roles detectados, makeup gain sugerido.

### POST /shub/event-ready
Propaga evento de disponibilidad a Hermes/Spawner (best-effort).

## Integración VX11
- Madre planifica pipeline de audio y llama a estos endpoints.
- Switch recibe hints mediante `_send_switch_hint` (route-v5).
- Hermes/Spawner notificados via HTTP si están levantados.
