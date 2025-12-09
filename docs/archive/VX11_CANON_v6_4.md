# VX11 v6.4 – Canonización Operativa

Estado reconstruido según auditoría forense v6.3 y memoria canónica (MADRE, SWITCH, HERMES, SPAWNER, MCP, HORMIGUERO).

## Núcleo y Flujos
- **Tentáculo Link**: frontdoor IO/WS. No se modifica en esta entrega.
- **Madre**: micro-IA de planificación; feedback inicial vía Switch; plan → hijas (Spawner) → seguimiento → cierre. Registra plan/feedback en BD (`context`/`tasks`/`spawns`).
- **Switch**: cola prioritaria persistente (`task_queue`), prioridades `shub > operator > madre > hijas`; modelo activo+precalentado (7B on/off por actividad Operator); modo audio (Shub) y rotación dinámica; CLI hub integrado con registros Hermes (`cli_registry`).
- **Hermes**: gestor de modelos <2GB con crawler HF/OpenRouter básico, descarga en `/app/models/hermes`, registro dual (`models_local` + `model_registry`), mantenimiento a 30 modelos, registrador CLI (Playwright stub) sincronizado con `cli_registry`.
- **Spawner**: hijas efímeras con TTL/agresividad/contexto MCP; registra en `hijas_runtime` y notifica Tentáculo.
- **Hormiguero**: Reina clasifica tareas vía Switch al crear `queen_tasks`, registra evento forense para Madre.
- **MCP**: sandbox endurecido (timeout, bloqueo imports peligrosos, auditoría en `sandbox_exec`/`audit_logs`).

## BD Unificada
- Tablas faltantes creadas: `task_queue`, `tokens_usage`, `system_state`, `sandbox_exec`, `audit_logs`.
- Migración automática desde prefijos `madre_`, `hermes_`, `hive_` hacia tablas unificadas.
- `SystemState` alimentado por Switch (cola/modelos) y Madre (estado global).

## Endpoints Clave (v6.4)
- Madre: `/orchestrate` (plan + delegación a switch/hermes/spawner), `/madre/bridge` (hijas), métricas y salud.
- Switch: `/switch/route-v5` (cola persistente + selección modelo), `/switch/route` (compat), `/switch/queue/status|next`, admin `/switch/admin/preload_model`, `/switch/admin/set_default_model`, `/switch/models/available`.
- Hermes: `/hermes/list`, `/hermes/register_model`, `/hermes/search_models` (HF/OR + locales), `/hermes/sync` (mantenimiento + registry), `/hermes/reindex`, `/hermes/cli/list|register|renew`.
- Spawner: `/spawn`, `/spawn/list|status/{id}|kill/{id}|kill_all|cleanup`, `/spawn/output/{id}`.
- MCP: `/mcp/execute_safe|execute` (sandbox), `/mcp/copilot-bridge`, `/mcp/sandbox/check`.
- Hormiguero: `/hormiguero/task|tasks|task/{id}` con clasificación automática Reina + eventos para Madre.

## Contenedores
- Dockerfiles mantienen `ULTRA_LOW_MEMORY=true` y healthchecks en puertos canónicos 8000–8008/8011/8020.

## Validación DeepSeek R1
- Flujo tentacular confirmado: Tentáculo ↔ Madre (plan) ↔ Switch (cola+modelo) ↔ Hermes (búsqueda/registro modelos+CLI) ↔ Spawner (hijas TTL/agresividad) ↔ MCP (sandbox auditable) ↔ Hormiguero (clasificación Reina + eventos Madre).
- BD coherente y sin drift legacy; endpoints canónicos operativos para producción v6.4.
