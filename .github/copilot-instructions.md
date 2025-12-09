# Instrucciones para Agentes de IA - VX11 v7.0

**Proposito:** Guiar a agentes IA para ser inmediatamente productivos en este ecosistema modular, entendiendo orquestacion, flujos de datos, patrones de codigo y comandos criticos.

---

## Arquitectura esencial

**9+ modulos independientes orchestrados por un frontdoor unico:**

1. **Tentaculo Link** (8000, alias gateway) - Puerta unica: proxy, autenticacion (X-VX11-Token), enrutamiento de chat/tareas/eventos a modulos destino, encapsula respuestas de texto en {"raw": "..."}.
2. **Madre** (8001) - Cerebro: orquestador central con ciclo cada 30s, crea tareas, gestiona container state (P&P), planificacion con IA, delegacion a hijas efimeras via Spawner.
3. **Switch** (8002) - ✅ **v7.0 COMPLETADO**: Router IA con prioridades (shub>operator>madre>hijas), cola persistente, CLI-first para chat, local-first para tareas, integración Hermes/Shub.
4. **Hermes** (8003) - ✅ **v7.0 COMPLETADO**: Discovery + CLI + catálogo de modelos, registro de CLI providers (DeepSeek R1), background workers para límites de tokens, endpoints `/hermes/resources`, `/hermes/register/*`, `/hermes/discover`.
5. **Hormiguero** (8004) - Paralelizacion: Reina inteligente (resuelve conflictos), hormigas workers (tareas paralelas), feromonas (metricas), mutacion genetica.
6. **Manifestator** (8005) - Auditoria + parches: deteccion de drift, generacion automatica de parches, integracion VS Code, hashes forenses.
7. **MCP** (8006) - Conversacional: interfaz Copilot, herramientas sandboxeadas, validacion de acciones.
8. **Shubniggurath** (8007) - Audio: analisis espectral, mix ligero, diagnostico, heuristicas (delega IA pesada a Switch).
9. **Spawner** (8008) - Ejecucion efeimera: ejecuta scripts en sandbox, captura stdout/stderr, auditoria de procesos, integracion con Madre.
10. **Operator** (8011) - Dashboard: monitoreo de Shub + Operator, integracion con PostgreSQL.

**BD unificada:** Todos comparten data/runtime/vx11.db (SQLite single-writer). Tablas: tasks, context, reports, spawns, ia_decisions, task_queue, system_state, **cli_providers, local_models_v2, model_usage_stats, switch_queue_v2** (v7.0 NEW).

---

## Setup critico

**Local (venv + uvicorn, hot reload):**
```bash
cp tokens.env.sample tokens.env && vim tokens.env  # DEEPSEEK_API_KEY, OPENAI_API_KEY obligatorios
source .venv/bin/activate && ./scripts/run_all_dev.sh  # Arranca 9+ modulos secuencialmente
# Validar: for port in {8000..8008}; do curl http://localhost:$port/health; done
# Switch/Hermes: curl http://localhost:8002/health && curl http://localhost:8003/health
```

**Docker (preferred para produccion/testing):**
```bash
source tokens.env  # Carga en sesion actual
docker-compose up -d && docker-compose logs -f madre
# Health: docker-compose ps  # Todos deben estar "running"
# Verificar Switch/Hermes específicamente
docker-compose logs -f switch hermes
```

**Quick verification:**
```bash
curl http://localhost:8000/vx11/status            # Gateway status
curl http://localhost:8001/orchestration/module_states | jq .  # P&P states
curl http://localhost:8002/switch/queue/status    # Switch queue
curl http://localhost:8003/hermes/resources       # Hermes catalog
```

---

## Patrones de codigo que DEBES seguir

### 1. Creacion de modulos (StandardApp)
Todos reutilizan config/module_template.create_module_app:
```python
from config.module_template import create_module_app
app = create_module_app("nombre_modulo")  # Registra automaticamente:
# - Middleware forense (captura excepciones -> crash dumps en forensic/{module}/)
# - Endpoints estandar: /health, /control (status|start|stop|restart)
# - write_log() de telemetria
# - write_hash_manifest() de auditoria (hashes .py para drift detection)
```

### 2. Configuracion (NUNCA hardcodear puertos/localhost)
SIEMPRE usa config/settings:
```python
from config.settings import settings

# CORRECTO
url = settings.switch_url or f"http://switch:{settings.switch_port}"
headers = {settings.token_header: settings.api_token}  # "X-VX11-Token"
timeout = settings.hermes_timeout  # 30s

# PROHIBIDO
url = "http://localhost:8002"  # Hardcodear hostname
port = 8001  # Hardcodear puerto
```

### 3. Base de Datos (BD unificada SQLite)
TODOS los modulos comparten una unica instancia SQLite en data/runtime/vx11.db:
```python
from config.db_schema import get_session, Task, Context, Report, Spawn, IADecision

# CORRECTO (single-writer pattern)
db = get_session("nombre_modulo")
task = db.query(Task).filter_by(name="mi_tarea").first()
db.add(Task(...))  # Crear nueva tarea
db.commit()  # CRITICO: siempre commit() explicitamente
db.close()  # O usar context manager

# PROHIBIDO (deprecated)
from config.database import SessionLocal  # NO USAR
```

**Modelos clave:**
- Task: tareas orchestradas, UUID unico, estado (pending|running|completed|failed)
- Context: metadatos por tarea (scope: global|module|spawn)
- Report: metricas, logs, forensics
- Spawn: procesos efimeros (Spawner), PID, exit_code, stdout/stderr
- IADecision: persistencia para aprendizaje de routing (Switch)

### 4. Forensics y Logging (Auditoria automatica)
Cada modulo automaticamente registra logs en forensic/{module}/ via config/forensics.py:
```python
from config.forensics import write_log, write_hash_manifest

# Logging telemetria
write_log("nombre_modulo", "evento_importante")
write_log("nombre_modulo", "error_critico", level="ERROR")

# Hashes forense (drift detection): solo archivos .py
write_hash_manifest("nombre_modulo", filter_exts={".py"})
```

**Detalles:**
- forensic/{module}/ contiene timestamps, hashes SHA256, crash dumps (excepciones)
- Middleware ForensicMiddleware captura automaticamente excepciones no manejadas
- Usalo para auditoria ante cambios no autorizados (Manifestator consume estos hashes)

### 5. Container State Management (P&P)
Cambiar estado de modulo **sin reiniciar** (Plug-and-Play):
```python
from config.container_state import get_active_modules, get_standby_modules, should_process

# Chequea si modulo esta habilitado
if should_process("manifestator"):  
    # procesar tarea
    pass
```

**Estados:** active (procesando) | standby (bajo consumo) | off (desactivado)

**Endpoint Madre:**
```bash
# Ver estado P&P
curl http://localhost:8001/orchestration/module_states | jq .

# Cambiar a standby (reduce memoria)
curl -X POST http://localhost:8001/orchestration/set_module_state \
  -H "Content-Type: application/json" \
  -d '{"module":"manifestator","state":"standby"}'
```

---

## Patrones de Comunicacion Inter-Modulos (CRITICO)

**NUNCA codifiques 127.0.0.1 o localhost en production code. Usa Docker hostnames desde config/settings.**

### 1. URLs y Headers de Autenticacion
```python
from config.settings import settings
from config.tokens import get_token
import httpx

# URLs de otros modulos
switch_url = settings.switch_url or f"http://switch:{settings.switch_port}"
hermes_url = settings.hermes_url or f"http://hermes:{settings.hermes_port}"
spawner_url = settings.spawner_url or f"http://spawner:{settings.spawner_port}"

# Token de autenticacion
token = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
headers = {settings.token_header: token}  # "X-VX11-Token"

# Llamada inter-modulo
async with httpx.AsyncClient() as client:
    resp = await client.post(f"{switch_url}/switch/route", headers=headers, json={"prompt": "..."})
```

### 2. Flujo de Datos Tipico (Tentacular)
```
usuario -> Tentaculo Link (8000) [proxy + auth]
         | POST /mcp/chat (require_action=true)
         -> Madre (8001) [planificacion]
         | Que motor usar?
         -> Switch (8002) [routing adaptativo]
         | propone: hermes_local (score 0.95)
         -> Hermes (8003) [CLI + model discovery]
         | ejecuta comando
         -> retorna resultado
         <- Madre: registra en BD (IADecision) + guarda en Task
         <- Tentaculo: encapsula en {"raw": "..."} si es texto
         <- usuario
```

### 3. Integracion Spawner (Hijas Efimeras)
Madre crea tareas, Spawner las ejecuta:
```python
# En Madre
task = Task(
    uuid="...",
    module="spawner",
    action="exec",
    name="validate_script",
    # params en Context
)
db.add(task)
db.commit()

# Spawner detecta, ejecuta scripts/validate.py, guarda resultado en Spawn
# Madre consulta: db.query(Spawn).filter_by(parent_task_id=task.uuid)
```

---

## Switch + Hermes v7.0 (NUEVO en v7.0)

**Switch es el router IA central** con prioridades:
- CLI-first para chat: DeepSeek R1 si hay token
- Local-first para tareas: modelos <2GB por task_type
- Prioridades: shub (0) > operator (1) > madre (2) > hijas (3)
- Cola persistente en `switch_queue_v2` (BD)

**Hermes es el gestor de recursos**:
- Endpoints: `/hermes/resources`, `/hermes/register/cli`, `/hermes/register/local_model`, `/hermes/discover`
- Catálogo en `switch/hermes/models_catalog.json`
- Background worker: resetea límites de CLI cada hora
- Discovery stub: búsqueda en HuggingFace/OpenRouter

**Cómo usarlos:**

```python
# Desde Madre: pedir chat
import httpx
from config.settings import settings

async def chat_with_switch():
    resp = await httpx.post(
        f"{settings.switch_url}/switch/chat",
        json={
            "messages": [{"role": "user", "content": "Hola"}],
            "metadata": {"task_type": "chat", "source": "madre"}
        },
        headers={"X-VX11-Token": get_token("VX11_GATEWAY_TOKEN")}
    )
    return resp.json()

# Desde Spawner: ejecutar tarea
async def task_with_switch():
    resp = await httpx.post(
        f"{settings.switch_url}/switch/task",
        json={
            "task_type": "summarization",
            "payload": {"text": "..."},
            "source": "hija"
        },
        headers={"X-VX11-Token": get_token("VX11_GATEWAY_TOKEN")}
    )
    return resp.json()
```

**Documentación completa:** `docs/VX11_SWITCH_HERMES_v7_COMPLETION.md`

---

## Casos de Uso Especificos

### 1. Conversacion -> Accion (MCP -> Madre -> Switch -> Shub/Spawner)
```bash
# Usuario en Copilot: "Valida mi codigo Python"
curl -X POST http://localhost:8006/mcp/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"user-abc",
    "message":"Valida mi codigo Python",
    "require_action":true
  }'

# MCP -> crea Task(module=spawner, action=exec)
# -> Madre la ve -> Spawner: python3 -m compileall . en sandbox
# -> Guarda stdout/stderr en Spawn + BD
# -> Madre retorna resultado a Tentaculo -> usuario
```

### 2. Plug-and-Play (P&P) - Control Granular
```bash
# Ver estado de todos los modulos
curl http://localhost:8001/orchestration/module_states | jq .

# Cambiar manifestator a standby (bajo consumo)
curl -X POST http://localhost:8001/orchestration/set_module_state \
  -H "Content-Type: application/json" \
  -d '{"module":"manifestator","state":"standby"}'

# Activar de nuevo
curl -X POST http://localhost:8001/orchestration/set_module_state \
  -d '{"module":"manifestator","state":"active"}'
```

### 3. Adaptive Routing (Switch -> Hermes)
```bash
# Switch recibe prompt, consulta Hermes sobre motores disponibles
curl -X POST http://localhost:8002/switch/hermes/select_engine \
  -H "X-VX11-Token: token" \
  -d '{"query":"Explica async/await","available_engines":["hermes_local","deepseek","openrouter"]}'

# Respuesta: {"recommended":"hermes_local","score":0.95,"reason":"local,fast"}

# Registrar feedback (mejora scoring futuro)
curl -X POST http://localhost:8002/switch/hermes/record_result \
  -d '{"engine":"hermes_local","success":true,"latency_ms":150,"tokens":500}'
```

### 4. Auditoria y Drift Detection (Manifestator)
```bash
# Detectar cambios en modulos
curl http://localhost:8005/drift | jq .

# Generar parche para cambios detectados
curl -X POST http://localhost:8005/generate-patch \
  -d '{"module":"switch","drift_type":"code_modification"}'

# Aplicar parche
curl -X POST http://localhost:8005/apply-patch \
  -d '{"patch_id":"patch-xyz"}'
```

### 5. Audio Analysis (Shub)
```bash
# Analizar archivo audio
curl -X POST http://localhost:8007/shub/analyze \
  -H "Content-Type: application/json" \
  -d '{"input_path":"/data/audio.wav"}'

# Obtener recomendaciones de FX
curl -X POST http://localhost:8007/shub/recommend \
  -d '{"file_hash":"abc123","target":"balanced"}'
```

---

## Testing y Debugging Realistas

**Suite recomendada:**
```bash
# Desarrollo local con servicios vivos
source .venv/bin/activate
./scripts/run_all_dev.sh &
pytest tests/test_endpoints.py -v
kill %1
```

**Suite completa con logs:**
```bash
pytest tests/ -v --tb=short | tee logs/pytest_phase7.txt
```

**Monitoreo de logs en tiempo real:**
- Local: tail -f logs/madre_dev.log / tail -f logs/switch_dev.log
- Docker: docker-compose logs -f <servicio> (ej: docker-compose logs -f madre)
- Forensics: tail -f forensic/{modulo}/*.log (auditoria automatica)

**Validacion previa (CI):**
```bash
python3 -m compileall .                 # Verificar sintaxis Python
docker-compose config                  # Validar compose
docker-compose build --no-cache        # Build sin cache
```

**Troubleshooting:**
| Problema | Solucion |
|----------|----------|
| switch no levanta | Revisa tokens.env: faltan DEEPSEEK_API_KEY / OPENAI_API_KEY |
| Puerto ya en uso | lsof -i :8001 para encontrar PID, luego kill -9 <PID> |
| DB bloqueada | Agrega timeout=30 en config/db_schema.get_session() |
| Response sin datos | Gateway convierte texto en {"raw":"..."} -> verifica key raw |
| Modulo no responde | Usa /health para confirmar, check docker-compose logs para errores |

---

## Documentos de Referencia Clave

| Archivo | Proposito |
|---------|----------|
| docs/ARCHITECTURE.md | Arquitectura completa, modulos, flujos (diagramas ASCII y Mermaid) |
| docs/API_REFERENCE.md | Todos los endpoints con ejemplos curl por modulo |
| docs/DEVELOPMENT.md | Guia de setup local, debugging, testing |
| docs/FLOWS.md | 10+ diagramas Mermaid de flujos end-to-end |
| docs/MANIFESTATOR_INTEGRATION.md | Auditoria, parches, integracion VS Code |
| docs/OPERATOR_DASHBOARD_v7.0.md | Dashboard frontend + backend integration |
| README.md | Quick start, features, P&P examples |
| prompts/madre.md | System prompt de Madre (interaccion modulos) |
| prompts/hermes.md | System prompt de Hermes (discovery + CLI) |

---

## Consejos finales y errores comunes

1. **Nunca codifiques puertos o localhost** - Si hardcodeas 127.0.0.1:8001, pierde flexibilidad Docker. Usa siempre config/settings.{module}_url.
2. **Siempre source tokens.env antes de levantar** - Sobre todo antes de switch (necesita DEEPSEEK_API_KEY / OPENAI_API_KEY).
3. **SQLite single-writer** - Si ves bloqueos, agrega timeout=30 en config/db_schema.get_session(). Usa db.commit() explicitamente.
4. **Gateway envuelve texto en {"raw":"..."}** - Cuando inspecciones respuestas, asegurate de revisar la clave raw si no es JSON.
5. **Check health antes de tests** - Validar que todos los modulos levantaron: for port in {8000..8008}; do curl http://localhost:$port/health; done
6. **Usar httpx no requests** - httpx es async-first y se integra mejor con FastAPI (async/await).
7. **Logs en forensic/{module}/** - No logs en build/artifacts/logs/ desde modulos; usa siempre write_log().
8. **No crear archivos nuevos** - Salvo que sea explicitamente pedido. Usar replace_string_in_file para parches.

---

## VX11 RULES (Protocolo Deep Surgeon v6.7+)

**PROHIBICIONES ABSOLUTAS:**
- NO usar localhost ni 127.0.0.1 en codigo de modulos (excepto endpoints opcionales).
- SIEMPRE usar settings.{module}_url o f"http://{hostname}:{port}" desde settings.
- NO generar archivos nuevos salvo que sea explicitamente pedido.
- NO mover carpetas ni renombrar modulos.
- NO reescribir modulos enteros; usar replace_string_in_file para parches minimos.
- NO cambiar docker-compose.yml, puertos ni nombres de servicios.
- TODO parche de codigo debe ser con replace_string_in_file o multi_replace_string_in_file.
- NO inventar rutas, funciones, modelos ni engines. Usar SOLO lo que existe en workspace.

**REGLAS DE COHERENCIA:**
- Switch -> Hermes -> Shub -> Madre -> Spawner -> Hormiguero (flujo tentacular).
- Hormiguero: Reina + hormigas + feromonas + mutacion bajo consumo.
- Madre: contexto7 -> planificacion -> hijas efimeras via Spawner.
- Switch: scoring persistente, throttle, adaptive routing (IA ligera + CLI).
- Feromonas expuestas en /health e integrables con Operator.

**HERRAMIENTAS PERMITIDAS:**
- read_file, replace_string_in_file, multi_replace_string_in_file
- list_dir, grep_search, file_search, semantic_search
- run_in_terminal para validacion (py_compile, tests selectivos)
- NO crear archivos, NO mover nada, NO usar tools de generacion masiva.
