# VX11 v6.3 – AUDITORÍA FORENSE ACTUAL

Informe generado en modo solo lectura. Ningún archivo ha sido modificado más allá de este reporte permitido.

## 1. Estructura de carpetas y archivos

```
tentaculo_link/
  main.py  routes/  clients/  ws/  Dockerfile  data/files/
madre/
  main.py  bridge_handler.py  Dockerfile
switch/
  main.py  router_v5.py  adapters.py  pheromone_engine.py  scoring_engine.py  learner.json  pheromones.json  Dockerfile
hermes/
  main.py  model_scanner.py  scanner_v2.py  leonidas.py  registry_manager.py  Dockerfile
hormiguero/
  main.py  core/{queen,ant_colony,task_distributor,reina_ia}.py  genetic_algorithm.py  Dockerfile
manifestator/
  main.py  autopatcher_v2.py  dsl.py  Dockerfile
spawner/
  main.py  ephemeral_v2.py  Dockerfile
shub/
  main.py  shub_core_init.py  shub_routers.py  shub_reaper_bridge.py  dsp_pipeline.py  Dockerfile  docs/  tests/
mcp/
  main.py  tools_wrapper.py  conversational_v2.py  Dockerfile
operator/
  backend/{main.py,services/*,Dockerfile}  frontend/{src/*,Dockerfile}  disabled/main.py  main.py
config/
  settings.py  db_schema.py  database.py  tokens.py  orchestration_bridge.py  metrics.py  utils.py  deepseek.py ...
scripts/
  *.sh  systemd/*.service  secure/secure_tokens.env.master
data/
  vx11.db  vx11_test.db  tentaculo_link/files/  backups/*.db.bak
tests/
  ~30 test_*.py + conftest.py
docker-compose.yml
```

- Archivos sospechosos de duplicado/obsolescencia: múltiples `__pycache__` en todos los módulos; `shub/.pytest_cache`; tests `__pycache__` con dos versiones de pytest.  
- Carpetas que parecen contenedores vacíos/temporales: `tentaculo_link/data/files/` (solo contenedor), `data/backups/` (solo .bak).

## 2. Estado de módulos clave

### Tentáculo Link – Estado actual
- Rol real: puerta de entrada FastAPI/WS; valida token y reenvía chat a switch, tareas a hormiguero, eventos a madre/shub; agrega health de módulos. No implementa lógica de modelo propia.  
- Archivos: `main.py` (app), `routes/`, `clients/`, `ws/`, `Dockerfile`.  
- Endpoints:  
  - GET `/health`, `/vx11/status`, `/vx11/health-aggregate` (sondea puertos 8000–8008 y 8011).  
  - POST `/vx11/orchestrate` (usa `config.orchestration_bridge` a switch/hermes/madre localhost).  
  - GET `/vx11/validate/copilot-bridge`.  
  - POST `/events/ingest` (broadcast WS opcional).  
  - POST `/files/upload` (guarda en `data/tentaculo_link/files`).  
  - WS `/ws` (canales chat/event/control).  
- Conexiones salientes: HTTP a `switch` `/switch/route-v5`, `hormiguero` `/tasks/ingest`, `shub` `/shub/ingest`, `madre` `/events/ingest`; usa cabecera `X-VX11-Token` con `VX11_TENTACULO_LINK_TOKEN`/`VX11_GATEWAY_TOKEN`/`settings.api_token`; URLs de settings (gateway hostnames en Docker).  
- BD: no toca tablas directamente; logs vía `config.forensics`.  
- Recursos: ULTRA_LOW_MEMORY=True en settings y env docker; healthcheck definido en compose; logs via `write_log`.

### Madre – Estado actual
- Rol real: orquestador FastAPI con tareas simples (marca pending→completed), chat que enruta a switch, scheduler que publica estado a tentáculo; delega spawner marcado “no configurado”.  
- Archivos: `main.py` (app), `bridge_handler.py`, `Dockerfile`, README.  
- Endpoints: health `/health`; métricas `/metrics/cpu|memory|queue|throughput`; tasks `/task`, `/task/{id}`, `/tasks`; chat `/chat`; orquestación `/orchestrate` (spawn→error, route→switch, exec→hermes); bridge `/madre/bridge`, `/madre/hija/{id}`, `/madre/hijas`; módulo P&P `/orchestration/module_states`, `/orchestration/set_module_state`; status `/status`.  
- Conexiones salientes: HTTP a `switch` `/switch/route`, `hermes` `/hermes/exec`, spawner `/spawn` (pero _delegate_spawner retorna error “no configurado”), a tentáculo `/events/ingest`; headers token gateway.  
- BD: usa `get_session("madre"/"vx11")` tablas `tasks`, `context`, `reports`, `spawns`, `ModuleHealth`, `MadrePolicy`, `MadreAction`, `SchedulerHistory`, `SystemState`; escribe state/acciones/ledger mínimo.  
- Recursos: ULTRA_LOW_MEMORY env; healthcheck en compose; monitor asincrónico cada ~5s.

### Switch – Estado actual
- Rol real: router con cola prioritaria in-memory; selecciona modelo de `ModelManager` (semillas `general-7b` activo, `audio-engineering` warm); persistencia en `task_queue` tabla (si existe). CLI mode envía a hermes.  
- Archivos: `main.py` (app v6.3), `router_v5.py`, `adapters.py`, `pheromone_engine.py`, `scoring_engine.py`, configs JSON, `Dockerfile`.  
- Endpoints: `/health`; POST `/switch/route-v5` (cola y respuesta simulada; CLI→`hermes:8003/hermes/cli/execute`); GET `/switch/queue/status`, `/switch/queue/next`; admin `/switch/admin/preload_model`, `/switch/admin/set_default_model`; `/switch/models/available`.  
- Conexiones salientes: a hermes host `hermes` puerto 8003; usa header token.  
- BD: usa `TaskQueue` (tabla no existe en BD real), `ModelManager` in-memory; persiste queue en `task_queue` si disponible.  
- Recursos: ULTRA_LOW_MEMORY env; healthcheck en compose.

### Hermes – Estado actual
- Rol real: gestor de modelos locales y CLI; registra modelos creando binarios vacíos y guardando hash/tamaño; no ejecuta inferencia real.  
- Archivos: `main.py`, `model_scanner.py`, `scanner_v2.py`, `registry_manager.py`, `leonidas.py`, `Dockerfile`.  
- Endpoints: `/health`; `/hermes/list`; `/hermes/register_model`; `/hermes/search_models`; `/hermes/sync`; `/hermes/reindex`; CLI `/hermes/cli/list|available|renew|register`.  
- Conexiones salientes: ninguna externa salvo posibles filesystem; no llama otros módulos.  
- BD: tablas `models_local`, `models_remote_cli`; escribe entradas y marca deprecated; reindexa tamaños.  
- Recursos: ULTRA_LOW_MEMORY env; healthcheck en compose; logs via `write_log`.

### Spawner (hijas efímeras) – Estado actual
- Rol real: crea procesos locales con comandos permitidos (echo/python/node/ls/cat/bash), TTL y heartbeat; persiste metadatos hijas; notifica tentáculo.  
- Archivos: `main.py`, `ephemeral_v2.py`, `Dockerfile`.  
- Endpoints: `/health`; POST `/spawn`; GET `/spawn/list`, `/spawn/status/{id}`; POST `/spawn/kill/{id}`, `/spawn/kill_all`, `/spawn/cleanup`; GET `/spawn/output/{id}`.  
- Conexiones salientes: notifica tentáculo `/events/ingest`; usa token header.  
- BD: tablas `hijas_runtime`, `system_events`; `_persist_hija` guarda estado; `_update_hija_db` al terminar/matar.  
- Recursos: ULTRA_LOW_MEMORY env; healthcheck en compose.

### Hormiguero – Estado actual
- Rol real: gestor de tareas “ants” mezclando persistencia y registro in-memory; crea ants y dispara `process_task` (core); expone Reina IA y GA pero lógica interna mínima/simulada.  
- Archivos: `main.py`, core/queen.py, ant_colony.py, task_distributor.py, reina_ia.py, genetic_algorithm.py, Dockerfile.  
- Endpoints: `/health`; métricas `/metrics/cpu|memory|queue|throughput`; tareas `/hormiguero/task`, `/hormiguero/tasks`, `/hormiguero/task/{task_id}`; control `/control` (escala workers, crea tareas legacy); ants CRUD `/ant`, `/ant/{name}`, `/ant/{name}/run`; Reina `/hormiguero/reina/classify|optimize-priority|suggest-ants`; GA `/hormiguero/ga/optimize|summary`.  
- Conexiones salientes: Reina IA usa switch endpoint `http://127.0.0.1:{switch_port}`; no otros llamados externos.  
- BD: usa `config.database` (`queen_tasks`, `ants`, `VX11Event`); mezcla ANTS dict in-memory.  
- Recursos: ULTRA_LOW_MEMORY env; healthcheck en compose.

### MCP – Estado actual
- Rol real: sandbox FastAPI; limita recursos a módulos seguros para eval; audit trail básico.  
- Archivos: `main.py`, `tools_wrapper.py`, `conversational_v2.py`, `Dockerfile`.  
- Endpoints: `/health`; `/mcp/copilot-bridge` (solo recursos `/mcp/tools` y `/mcp/chat`); `/mcp/execute_safe` y `/mcp/execute`; `/mcp/sandbox/check`.  
- Conexiones salientes: ninguna.  
- BD: tablas `sandbox_exec`, `audit_logs` (definidas); registra en `_record_sandbox`, `_audit` (solo si tablas existen).  
- Recursos: ULTRA_LOW_MEMORY env; healthcheck en compose.

### BD unificada (config/db_schema.py + data/vx11.db)
- Esquema definido: tablas `tasks/context/reports/spawns/ia_decisions/module_health/model_registry/cli_registry/engines`, `tokens_usage`, `task_queue`, `events`, `system_state`, `madre_policies/actions`, `forensic_ledger`, `hijas_runtime`, `sandbox_exec`, `audit_logs`, `hermes_ingest`, `operator_jobs`, shub tablas (`shub_projects/tracks/analysis/fx_chains/presets`), hormiguero (`queen_tasks`, `ants`), `cli_registry`, etc.  
- Estado real (sqlite inspect): tablas presentes: `madre_*`, `hermes_*`, `hive_*` (legacy), unificadas `tasks/context/reports/spawns/ia_decisions/module_health/model_registry/cli_registry/engines`, `shub_*`, `operator_jobs`, `hermes_ingest`, `madre_policies`, `madre_actions`, `forensic_ledger`, `vx11_events`, `queen_tasks`, `ants`.  
- Tablas faltantes respecto a schema: `tokens_usage`, `task_queue`, `system_state`, `sandbox_exec`, `audit_logs` (definidas pero no encontradas), `cli_registry` duplicada (existe unificada y con prefijos legacy).  
- Uso:  
  - madre: `tasks/context/reports/spawns`, `module_health`, `madre_policies/actions`, `scheduler_history`, `system_state` esperado pero tabla ausente.  
  - switch: intenta `task_queue` (no existe).  
  - hermes: `models_local`, `models_remote_cli`.  
  - spawner: `hijas_runtime`, `system_events`.  
  - mcp: `sandbox_exec`, `audit_logs` (no presentes).  
  - operator: `operator_jobs`.  
  - shub: `shub_*`.  
  - hormiguero: `queen_tasks`, `ants`.  
- Inconsistencia principal: coexistencia de prefijos legacy (`madre_*, hermes_*, hive_*`) y ausencia de tablas nuevas requeridas por algunos módulos.

## 3. Base de datos unificada – Estado real

- Lista completa de tablas y columnas (sqlite `data/vx11.db`):  
  - `madre_tasks(id, uuid PK unique, name, module, action, status, created_at, updated_at, result, error)`  
  - `madre_ia_decisions(id PK, prompt_hash, provider, prompt, response, confidence, created_at)`  
  - `madre_module_health(id PK, module, status, last_ping, error_count, uptime_seconds, updated_at)`  
  - `madre_context(id PK, task_id, key, value, scope, created_at)`  
  - `madre_reports(id PK, task_id, report_type, summary, details, metrics, created_at)`  
  - `madre_spawns(id PK, uuid unique, name, cmd, pid, status, started_at, ended_at, exit_code, stdout, stderr, parent_task_id, created_at)`  
  - `madre_model_registry(id PK, name unique, path, provider, type, size_bytes, tags, last_used, score, available, meta_json, created_at, updated_at)`  
  - `madre_cli_registry(id PK, name unique, bin_path, available, last_checked, cli_type, token_config_key, rate_limit_daily, used_today, notes, updated_at)`  
  - `madre_engines(id PK, name unique, engine_type, domain, endpoint, version, quota_tokens_per_day, quota_used_today, quota_reset_at, latency_ms, cost_per_call, enabled, last_used, created_at, updated_at)`  
  - `hermes_tasks` (igual estructura madre_tasks), `hermes_ia_decisions`, `hermes_module_health`, `hermes_context`, `hermes_reports`, `hermes_spawns`, `hermes_model_registry`, `hermes_cli_registry`, `hermes_engines` (análogos a madre_*)  
  - `hive_tasks` ... `hive_engines` (legacy análogo)  
  - Unificadas: `tasks`, `ia_decisions`, `module_health`, `model_registry`, `cli_registry`, `engines`, `context`, `reports`, `spawns` (estructura similar a prefijos)  
  - Shub: `shub_projects`, `shub_tracks`, `shub_analysis`, `shub_fx_chains`, `shub_presets`  
  - Operator: `operator_jobs(job_id unique, intent, status, payload, result, created_at, updated_at)`  
  - Hermes ingest: `hermes_ingest(path, size_bytes, duration_sec, status, created_at)`  
  - Policies: `madre_policies(module, error_threshold, idle_seconds, enable_autosuspend, created_at, updated_at)`  
  - Actions: `madre_actions(module, action, reason, created_at)`  
  - Ledger: `forensic_ledger(event, payload, hash, created_at)`  
  - Eventos: `vx11_events(id PK, timestamp default CURRENT_TIMESTAMP, module, level, message, payload, idx module/id)`  
  - Hormiguero: `queen_tasks(task_id idx, task_type, status, priority, payload JSON, result JSON, created_at, updated_at)`; `ants(task_id, ant_type, status, payload JSON, result JSON, created_at, idx)`  
- Tablas definidas pero no existentes: `tokens_usage`, `task_queue`, `system_state`, `sandbox_exec`, `audit_logs` (según `config/db_schema.py`).  
- Campos definidos pero no usados: varios `meta_json`, `score` en registries; `latency_ms`, `cost_per_call` en `engines` no referenciados en código actual.  
- Tablas presentes pero no referenciadas por código activo: prefijos `hive_*`, quizá `madre_model_registry/cli_registry/engines` (no vistas en main).  

## 4. Flujos tentaculares reales

- Entrada usuario: operator frontend → operator backend (`/intent`/`/intent/chat`) → tentáculo `/events/ingest` o switch directo (via clients); uploads `/shub/upload` → tentáculo `/files/upload`.  
- Tentáculo: WS/HTTP recibe y reenvía: chat → switch `/switch/route-v5`; control hacia hormiguero `/tasks/ingest`, shub `/shub/ingest`, madre `/events/ingest`; health aggregate sondea puertos locales.  
- Madre: orquesta /orchestrate con switch/hermes; spawner delegado no configurado (responde error). Publica `system_state_update` a tentáculo.  
- Switch: procesa `/switch/route-v5`; si metadata `mode=cli` llama a `http://hermes:8003/hermes/cli/execute`; si no, responde stub con modelo activo.  
- Hermes: no llama a otros; responde a switch/clients.  
- Shub: no llamado directo desde tentáculo excepto `clients.notify_shub` en tentáculo para eventos; operator puede llamar via tentáculo upload; routers internos.  
- MCP: accesible pero sólo mediante token; audita sandbox_exec/audit_logs si existieran tablas; sin llamadas entrantes explícitas salvo cliente externo.  
- Hormiguero: recibe `/hormiguero/task` de tentáculo/control; puede llamar switch en Reina IA; usa mezcla in-memory/DB.  
- Spawner: recibe `/spawn` (desde madre teórico) y registra en DB/heartbeat; notifica tentáculo eventos spawn_created.  
- Flujos rotos/ausentes: spawner no integrado en madre (delegado error); switch persiste en `task_queue` inexistente; tablas sandbox_exec/audit_logs ausentes para MCP; `system_state` ausente para madre scheduler.

## 5. Docker-compose y contenedores

- Servicios:  
  - tentaculo_link (build ./tentaculo_link/Dockerfile, port 8000:8000, vols logs/data/sandbox/models, mem 512m, health curl /health)  
  - madre (./madre/Dockerfile, 8001:8001, vols logs/data/sandbox/models, mem 512m, depends tentáculo)  
  - switch (./switch/Dockerfile, 8002:8002, vols logs/data/models, mem 512m, depends tentáculo)  
  - hermes (./hermes/Dockerfile, 8003:8003, vols logs/data/models, mem 512m, depends tentáculo)  
  - hormiguero (./hormiguero/Dockerfile, 8004:8004, vols logs/data, mem 512m, depends tentáculo)  
  - manifestator (./manifestator/Dockerfile, 8005:8005, vols logs/data, repo read-only `.:/app/vx11:ro`, mem 512m, depends tentáculo)  
  - mcp (./mcp/Dockerfile, 8006:8006, vols logs/data, mem 512m, depends tentáculo)  
  - shub (./shub/Dockerfile, 8007:8007, vols logs/data/models, mem 512m, depends tentáculo)  
  - spawner (./spawner/Dockerfile, 8008:8008, vols logs/data/sandbox, mem 512m, depends tentáculo)  
  - operator-backend (./operator/backend/Dockerfile, 8011:8011, vols logs/data/models, mem 512m, depends tentáculo+switch)  
  - operator-frontend (build operator/frontend, 8020:8020, depends operator-backend)  
- Incoherencias: no hay servicio para `operator/main.py` raíz ni `operator/disabled`; compose expone todos puertos 8000–8008/8011/8020 alineados con settings.  

## 6. Tests y huecos de cobertura

- Tests presentes en `tests/`: cubren tentáculo_link, madre, switch (deepseek/local/providers), hermes (waveform/cli detection), hormiguero (queen), manifestator drift, mcp, spawner endpoints, operator intents, shub (pro/api/mode_c/io/simple), integración pnp, modos, db_schema, dynamic optimization.  
- Tests adicionales en `shub/tests/` (core y reaper bridge).  
- Módulos sin tests dedicados visibles: mcp tools wrapper (solo básicos), manifestator DSL interna, spawner heartbeat en profundidad, operator frontend.  
- Posibles pruebas obsoletas: referencian endpoints `switch/route` (existe), spawner endpoints presentes; nada apunta a endpoints inexistentes salvo potencial falta de `task_queue`/`system_state` tablas usadas por código pero no en BD.

## 7. Lista de incoherencias y “sorpresas” detectadas

- `config/settings.py` declara versión `6.2.0` aunque se pide 6.3.  
- BD real carece de tablas definidas (`task_queue`, `tokens_usage`, `system_state`, `sandbox_exec`, `audit_logs`), pero código intenta usarlas (switch, madre scheduler, mcp).  
- Prefijos legacy `madre_*`, `hermes_*`, `hive_*` conviven con tablas unificadas; riesgo de drift y consultas inconsistentes.  
- Spawner no está integrado en madre (endpoint devuelve error “spawner_url no configurado”).  
- Manifestator blueprint busca `docs/VX11_v6.3_CANONICAL.json`; no confirmado presente.  
- Sombras de stdlib: módulo `operator/` interfiere con import de `operator` al usar python desde root (afecta scripts como inspección sqlite).  
- Artifacts residuales: `__pycache__`, `.pytest_cache`, backups `.db.bak`.  
- Tokens por defecto: si env vacío, se usa `settings.api_token = "vx11-token-production"`; cabecera `X-VX11-Token` común en todos los servicios.
