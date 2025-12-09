# Operator Chat v7.0

Flujo reforzado Operator → Switch → Hermes para modos `mezcla` y `sistema`.

## Entradas
- `POST /intent` con `intent_type=chat|mixing|system`, `data.message`, `metadata` opcional.
- `POST /intent/chat` atajo directo para chat/mix.

## Enriquecimiento automático
- El parser detecta palabras clave de mezcla (`mezcla`, `mix`, `voz`, `paneo`, `reson`) y genera `metadata.mode=mix` con `metadata.mix_ops` (acciones sugeridas para el mezclador).
- Palabras clave de estado (`sistema`, `status`, `estado`) fijan `metadata.mode=system`.
- Otros intents se mantienen, pero siempre se envía `source=operator` hacia Switch.

## Endpoints UI (Operator backend)
- `GET /ui/status`: retorna los estados agregados desde Tentáculo Link (`/vx11/health-aggregate`).
- `GET /ui/events`: últimos eventos en memoria (intents/chat y errores básicos).

## Enrutamiento
- Chats y mezclas se envían directo a `Switch /switch/route-v5` con `prompt` y `metadata`.
- Los intent genéricos siguen pasando por Tentáculo Link (`/events/ingest`), conservando `metadata`.

## Uso recomendado
```bash
curl -H "X-VX11-Token: vx11-local-token" \
  -X POST http://127.0.0.1:8011/intent \
  -d '{"intent_type":"chat","target":"switch","data":{"message":"mezcla la voz y quita resonancias"}}'
```
- `metadata.mix_ops` llegará a Switch para priorizar modelos de mezcla y despachar hacia Hermes/Shub según corresponda.

## Validación rápida
- `curl -H "X-VX11-Token: vx11-local-token" http://127.0.0.1:8011/health`
- `pytest tests/test_operator_switch_hermes_flow.py`
