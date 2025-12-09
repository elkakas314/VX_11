# DSP
- Pipeline real con `audioop`/`wave`: peak, RMS, LUFS aproximado, rango dinámico.
- Detecciones: clipping (conteo de muestras > -1 dBFS), ruido de fondo (noise floor), DR bajo.
- Sugiere FX básicos: limiter, noise_gate, multiband_compressor según métricas.
- Función principal: `analyze_audio(path)` devuelve JSON con métricas e issues.
- Las métricas se persisten en BD `shub_analysis` y disparan cadenas FX en `shub_fx_chains`.
