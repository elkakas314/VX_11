# VX11 v7.x – Flujos Shub / Switch / Hermes / Hijas

## Prioridades y colas (Switch)
- Cola priorizada: `shub` > `operator` > `madre` > resto.
- `ModelPool` mantiene doble buffer: `active` + `warm`; rota por categoría (audio/general) y solo modelos <2GB.
- Fallback a CLI cuando: `mode/cli` explícito, tarea `cli_only`, cola saturada con `allow_cli_fallback`, o sin modelo adecuado.

## Hermes como registro
- Registra modelos locales con `task_type`, `size_mb` y categoría; rechaza >2GB.
- Endpoints: `/hermes/models/best` devuelve candidatos <2GB por tarea; `/hermes/cli/candidates` lista CLIs por tipo.
- Discovery/renovación sigue en modo stub; Hermes no decide, solo lista recursos.

## Flujo Shub → Madre → Spawner → Hijas → Hormiguero
1) Shub recibe petición (analyze/mix/master/diagnose) y valida.
2) Madre expone `/madre/shub/task`: registra intent `shub_task`, despacha a Spawner.
3) Spawner crea hija efímera con `module=shub`, TTL y contexto (rutas/params).
4) Hijas invocan Shub vía HTTP (8007) o bridge stub; Hormiguero puede monitorear vía `/hormiguero/monitor/shub`.
5) Tentáculo agrega health-aggregate usando hostnames; Shub expone `/shub/health` y métricas stub.

## Tokens y seguridad
- Token canónico: `vx11-local-token` (API_TOKEN y VX11_* en todos los servicios).
- Endpoints de health/metrics permiten acceso sin token solo para liveness; resto exige header `X-VX11-Token`.

## Notas de operación
- No se tocaron puertos ni nombres de servicios.
- Cambios son incrementales y compatibles con tests existentes.
- Próximas fases: enriquecer selección de modelos/CLI y conectar Shub con pipelines reales de audio.
