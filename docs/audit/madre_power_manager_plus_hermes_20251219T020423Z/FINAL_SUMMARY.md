# FINAL_SUMMARY

Por que Madre es la unica siempre ON:
- Madre concentra control de energia y orquesta start/stop/restart con allowlist y evidencia; el resto no autostarta docker.

Arranque bajo demanda:
- Servicios se inician/pausan via `/madre/power/service/{name}/start|stop|restart` con plan/apply y allowlist de compose o DB.

Garantias triple lock:
- `X-VX11-POWER-KEY` + `X-VX11-POWER-TOKEN` (TTL 60s) + confirm string requerido para apply=true.

Limitaciones:
- Sin permisos Docker: respuestas plan-only y evidencia en `plan_only_reason.txt`.
- `apply=true` puede fallar si docker/compose no disponible.

Scoreboard antes/despues (global):
- order_structure: 75.00 -> 76.67 (delta +1.67)
- stability: 100.00 -> 100.00 (delta +0.00)
- functionality: 68.33 -> 80.00 (delta +11.67)
- automation: 21.67 -> 31.67 (delta +10.00)
- autonomy: 63.33 -> 70.00 (delta +6.67)
- global_overall: 65.67 -> 71.67 (delta +6.00)
