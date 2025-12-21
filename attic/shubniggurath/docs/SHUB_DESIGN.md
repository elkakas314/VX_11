# Shub-Niggurath VX11 Audio Module (Design Snapshot)

## Objetivo
Servicio de análisis/mix ligero que delega inferencia pesada al Switch/Hermes y expone una API REST mínima para VX11. No usa IA local ni DSP pesado; solo heurísticas básicas.

## Componentes
- `core/engine.py`: orquestador central, envía hints a Switch/Hermes/Spawner y ejecuta pipelines.
- `core/registry.py`: factoría singleton.
- `dsp/*`: utilidades simples (normalizado, segmentación, estimación de balance espectral).
- `ops/*`: operaciones de mezcla, compresión heurística, diagnóstico y stems.
- `pipelines/audio_analyzer.py`: pipeline de análisis + diagnóstico.
- `pipelines/mix_pipeline.py`: mezcla de stems + ganancia sugerida.
- `pipelines/reaper_pipeline.py`: descriptor RPP mínimo (sin escribir disco).
- `routes/main.py`: router FastAPI con `/shub/*`.

## Flujo VX11
1) Madre planifica tarea de audio y llama a `/shub/analyze` o `/shub/mix`.
2) Shub analiza (heurístico), devuelve resumen y issues.
3) Shub envía hint opcional a Switch (`/switch/route-v5`) para elegir modelo IA.
4) Hermes/Spawner reciben `event-ready` si procede.
5) Hormiguero puede leer métricas vía Madre (no hay imports cruzados).

## Tokens/Seguridad
- Usa `settings.token_header` y tokens de config/tokens/env si existen.
- No abre CORS adicional; depende de app madre para incluir el router con auth.

## Rutas
- `GET /shub/health`
- `POST /shub/analyze`
- `POST /shub/mix`
- `POST /shub/event-ready`

## Limitaciones intencionales
- Sin FFT ni ML local.
- Sin escritura en disco (solo workspace/cache/tmp).
- Sin llamadas directas entre módulos fuera de HTTP.
