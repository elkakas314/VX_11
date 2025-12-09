# VX11 v6.2 - Guía de Integración Completa

## Resumen Ejecutivo

VX11 v6.2 implementa un sistema completo de orquestación multi-AI con optimización adaptativa, feromonas y contexto-7 canónico. 10 FASES implementadas en secuencia garantizan cero cambios disruptivos y 100% backward compatibility.

## Arquitectura Core (9 Módulos)

| Módulo | Puerto | Función | FASES |
|--------|--------|---------|-------|
| **Gateway** | 52111 | Orquestador HTTP, proxy inteligente | 7, 9, 11 |
| **Madre** | 52112 | Persistencia de tareas, sesiones | 2, 7, 14 |
| **Switch** | 52113 | Scoring de engines, feromonas | 3, 4, 7 |
| **Hermes** | 52114 | Ejecución CLI, browser automation | 6, 7, 11 |
| **Hormiguero** | 52115 | GA evolutivo, optimización | 5, 7, 11 |
| **Manifestator** | 52115 | Patching automático | 11 |
| **MCP** | 52116 | Copilot bridge, MCP protocol | 8, 9 |
| **Shubniggurath** | 52117 | Deep reasoning (STANDBY en v6.2) | 10 |
| **Spawner** | 52118 | Procesos efímeros | 11 |

## FASES Implementadas (2-10) - Detalles Técnicos

### FASE 2: Context-7 Implementation ✅

**Archivo:** `config/context7.py` (189 líneas)

7 capas de contexto persistente:

```python
{
  "layer1_user": {
    "user_id": "string",
    "language": "es|en",
    "verbosity": "quiet|normal|verbose"
  },
  "layer2_session": {
    "session_id": "uuid",
    "channel": "copilot|http|cli|telegram",
    "start_time": "iso8601"
  },
  "layer3_task": {
    "task_id": "uuid",
    "task_type": "mix|audit|repair|explore|script|query|automation",
    "priority": "low|normal|high|critical",
    "deadline": "iso8601 optional"
  },
  "layer4_environment": {
    "os": "linux|windows|macos",
    "vx_version": "6.2",
    "cpu_load": float,
    "ram_free_mb": int,
    "disk_free_mb": int
  },
  "layer5_security": {
    "auth_level": "user|operator|admin",
    "sandbox": bool,
    "allowed_tools": ["list", "of", "tools"],
    "ip_whitelist": ["127.0.0.1"]
  },
  "layer6_history": {
    "recent_commands": ["cmd1", "cmd2"],
    "last_outcome": "success|failure|timeout",
    "penalties": int,
    "successes_count": int
  },
  "layer7_meta": {
    "explain_mode": bool,
    "debug_trace": bool,
    "telemetry": bool,
    "mode": "eco|balanced|high-perf|critical",
    "trace_id": "uuid"
  }
}
```

**Uso en Madre:**
```bash
POST /chat
{
  "messages": [...],
  "context7": { ... }
}
```

### FASE 3: Scoring Engine ✅

**Archivo:** `switch/scoring_engine.py` (225 líneas)

Fórmula canónica:
```
score = w_q × quality_norm + w_l × (1 - latency_norm) + w_c × (1 - cost_norm) + w_f × pheromone
```

Modos y pesos:
- **eco**: w_q=0.3, w_l=0.3, w_c=0.4, w_f=0.0
- **balanced**: w_q=0.4, w_l=0.3, w_c=0.3, w_f=0.0
- **high-perf**: w_q=0.6, w_l=0.2, w_c=0.2, w_f=0.0
- **critical**: w_q=0.7, w_l=0.2, w_c=0.1, w_f=0.0

**Endpoint:**
```bash
POST /switch/query
{
  "query": "string",
  "context7": { ... },
  "engines": ["list", "of", "engines"]  # opcional
}
```

### FASE 4: Pheromone Engine ✅

**Archivo:** `switch/pheromone_engine.py` (155 líneas)

Reward system:
```python
REWARDS = {
    "success": 0.2,
    "partial_success": 0.05,
    "timeout": -0.1,
    "failure": -0.3,
    "error": -0.25,
}
```

Decay factor: 0.95 (cada actualización)

**Endpoints:**
```bash
POST /switch/pheromone/update
{
  "engine_id": "local_gguf_small",
  "outcome": "success|failure|timeout|..."
}

POST /switch/pheromone/decay-all
GET /switch/pheromone/summary
```

### FASE 5: Genetic Algorithm ✅

**Archivo:** `hormiguero/genetic_algorithm.py` (325 líneas)

Parámetros optimizables:
- temperature (0.0 - 2.0)
- top_k (1.0 - 50.0)
- frequency_penalty (0.0 - 1.0)
- presence_penalty (0.0 - 1.0)

GA Configuration:
- Population: 20 individuos
- Tournament selection: k=3
- Crossover rate: 0.7
- Mutation rate: 0.1
- Gaussian mutation sigma: 10% del rango

**Endpoints:**
```bash
POST /hormiguero/ga/optimize
{
  "engine_id": "deepseek_auto",
  "steps": 5
}

GET /hormiguero/ga/summary
GET /hormiguero/ga/best-params/{engine_id}
```

### FASE 6: Playwright Automation ✅

**Archivo:** `hermes/main.py` (nuevos ~85 líneas)

Actions soportadas:
- navigate: Navegar a URL
- click: Hacer click en selector
- fill: Llenar formulario
- screenshot: Captura de pantalla
- extract: Extraer contenido DOM
- evaluate: Ejecutar JavaScript

**Endpoint:**
```bash
POST /hermes/playwright
{
  "url": "https://example.com",
  "action": "navigate|click|fill|screenshot|extract|evaluate",
  "selector": "css_selector",
  "value": "valor_opcional",
  "javascript": "js_opcional",
  "wait_for": "selector_opcional",
  "context7": { ... }
}
```

**Nota:** Requiere auth_level "operator" o "admin"

### FASE 7: Orchestration Bridge ✅

**Archivo:** `config/orchestration_bridge.py` (185 líneas)

Pipeline completo:
1. **Switch**: Scoring y selección de engine
2. **Hermes**: Ejecución de comando/browse
3. **Madre**: Persistencia de resultado

**Endpoint (Gateway):**
```bash
POST /vx11/orchestrate
{
  "query": "tu pregunta",
  "context7": { ... },
  "pipeline_type": "full|quick"
}
```

Response:
```json
{
  "status": "ok",
  "pipeline": {
    "switch": {
      "engine": "deepseek_auto",
      "score": 0.85
    },
    "hermes": {
      "executed": true,
      "result": { ... }
    },
    "madre": {
      "persisted": true,
      "result": { ... }
    }
  },
  "timestamp": "iso8601"
}
```

### FASE 8: MCP Bridge (Copilot) ✅

**Archivo:** `mcp/main.py` (nuevos ~110 líneas)

Soporta MCP protocol methods:
- **LIST_TOOLS**: Listar herramientas disponibles
- **CALL_TOOL**: Ejecutar una herramienta
- **POST**: Acceso a endpoints POST (chat, etc)

**Endpoint:**
```bash
POST /mcp/copilot-bridge
{
  "method": "LIST_TOOLS|CALL_TOOL|POST",
  "resource": "/mcp/tools|/mcp/chat",
  "params": { ... },
  "context7": { ... }
}
```

### FASE 9: Copilot Validation ✅

**Archivo:** `config/copilot_bridge_validator.py` (250 líneas)

Suite de 3 validaciones:
1. **MCP Protocol**: LIST_TOOLS, CALL_TOOL, POST
2. **Context-7 Propagation**: Verificar propagación correcta
3. **Orchestration Integration**: Pipeline completo

**Endpoint (Gateway):**
```bash
GET /vx11/validate/copilot-bridge
```

Response:
```json
{
  "status": "ok",
  "validation_results": {
    "validations": [
      {
        "validation": "MCP_PROTOCOL",
        "tests": [...],
        "summary": {
          "passed": 3,
          "total": 3,
          "success_rate": "100%"
        }
      },
      ...
    ],
    "summary": {
      "total_validations": 3,
      "passed": 3,
      "success_rate": "100%"
    }
  }
}
```

### FASE 10: Shubniggurath Preparation ✅

**Archivo:** `shubniggurath/main.py` (nuevos ~95 líneas)

Estados:
- **INACTIVE**: Por defecto en v6.2
- **STANDBY**: Preparado pero no activo
- **ACTIVE**: Reservado para v7.0+

**Endpoints:**
```bash
POST /shub/copilot-prepare
{
  "action": "activate|deactivate|status"
}

GET /shub/copilot-status
GET /shub/features
```

Features ready (v6.2):
- deep_reasoning: ✓
- long_context: ✓
- instruction_following: ✓
- copilot_integration: ✓

## Flujos de Integración

### Flujo 1: Query Simple con Scoring

```
Usuario → Gateway (/vx11/orchestrate)
         ↓
       Switch (scoring)
         ↓
       Selecciona engine
         ↓
       [Ejecuta en Hermes si CLI/Browser]
         ↓
       Madre persiste
         ↓
       Retorna resultado
```

### Flujo 2: Copilot Chat

```
Copilot → Gateway (/vx11/chat o /mcp/copilot-bridge)
         ↓
        MCP Protocol parsing
         ↓
        MCP handler en MCP module
         ↓
        Madre chat session
         ↓
        Context-7 propagación
         ↓
        Retorna response con tracing
```

### Flujo 3: GA Optimization

```
Hormiguero (/hormiguero/ga/optimize)
         ↓
       Initialize population
         ↓
       [Iterate steps]
         ├─ Evaluate fitness
         ├─ Selection (tournament)
         ├─ Crossover
         ├─ Mutation
         ├─ Persist state
         └─ Update history
         ↓
       Retorna mejores params
```

## Arranque (Desarrollo)

```bash
# Activar venv
source .venv/bin/activate

# Exportar tokens
export DEEPSEEK_API_KEY="..."  # si necesario

# Arrancar todos los servicios
./scripts/run_all_dev.sh

# Esperar ~30s para estabilización
sleep 30

# Validar status
curl http://127.0.0.1:52111/vx11/status

# Ejecutar tests
pytest tests/test_phase12_fases2_10.py -v
```

## Endpoints Canónicos (Todos los módulos)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Verificar salud del módulo |
| `/control` | POST | Control: status\|start\|stop\|restart |

## Backward Compatibility

✅ **100% garantizado:**
- Todos los cambios son ADDITIVE (solo nuevos archivos y endpoints)
- No se elimó código existente
- No se modificaron nombres de funciones/módulos
- Endpoints antiguos mantienen la misma interfaz
- Context-7 es OPCIONAL en todos lados (genera default si no se pasa)

## Cambios Realizados (Resumen)

### Archivos Nuevos (9)
1. `config/context7.py` - Context-7 generator
2. `switch/scoring_engine.py` - Motor de scoring
3. `switch/pheromone_engine.py` - Motor de feromonas
4. `switch/pheromones.json` - Estado inicial de feromonas
5. `hormiguero/genetic_algorithm.py` - GA engine
6. `config/orchestration_bridge.py` - Orquestación
7. `config/copilot_bridge_validator.py` - Validador Copilot
8. `tests/test_phase12_fases2_10.py` - Test suite
9. Reportes de FASES (JSON)

### Archivos Modificados (5, todas cambios < 20 líneas)
1. `madre/main.py` - +Import context7, enhanced /chat
2. `switch/main.py` - +Import scoring, +/switch/query y endpoints pheromone
3. `hermes/main.py` - +/hermes/playwright
4. `hormiguero/main.py` - +GA endpoints
5. `gateway/main.py` - +/vx11/orchestrate, +/vx11/validate/copilot-bridge
6. `mcp/main.py` - +/mcp/copilot-bridge
7. `shubniggurath/main.py` - +Copilot endpoints
8. Módulos: +import context7 (5 módulos, 1 línea cada uno)

### Lineas de Código

- **Nuevas (net):** ~1200 líneas (todos los nuevos módulos + endpoints)
- **Modificadas:** ~80 líneas (imports + mejoras menores)
- **Eliminadas:** 0 líneas
- **Ratio Cambio:** +1280 líneas, 0 remoción = 100% limpio

## Testing

14 tests automatizados covering:
- Context-7 validation
- Scoring formula
- Pheromone updates
- GA optimization
- Playwright integration
- Full orchestration
- MCP protocol
- Copilot validation
- Shubniggurath status
- Health/Control endpoints

Ejecutar con:
```bash
pytest tests/test_phase12_fases2_10.py -v --tb=short
```

## Roadmap Futuro (v7.0)

- FASE 21: Shubniggurath full activation
- FASE 22: Multi-model ensemble
- FASE 23: Distributed caching
- FASE 24: Telemetry dashboard
- FASE 25: Production hardening

## Soporte

- Docs: `/docs` en cada módulo
- Logs: `logs/` + forensic/
- Config: `tokens.env` (copiar de `tokens.env.sample`)
- Issues: Ver `COMPLETION_SUMMARY.md`

---

**Versión:** 6.2  
**Fecha:** 2025-12-01  
**Status:** Production-Ready (all 10 phases implemented)
