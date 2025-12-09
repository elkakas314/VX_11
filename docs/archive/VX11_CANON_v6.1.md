# VX11 CANON v6.1 – DESIGN DOCUMENT (DEFINITIVO)

**Versión:** 6.1  
**Fecha:** 1 de diciembre de 2024  
**Estado:** Canonizado a nivel de diseño  
**Autor:** Auditoría de Canonización v6.1

---

## Tabla de Contenidos

1. [Estado Actual Resumido](#1-estado-actual-resumido)
2. [Arquitectura Canónica](#2-arquitectura-canónica)
3. [Lenguaje VX11 + Context-7](#3-lenguaje-vx11--context-7)
4. [Switch + Hermes + Feromonas](#4-switch--hermes--feromonas)
5. [Hermes + Playwright](#5-hermes--playwright)
6. [Puente Copilot/VS Code](#6-puente-copilot-vs-code)
7. [Automatizaciones + Limpieza](#7-automatizaciones--limpieza)
8. [Checkpoints de Implementación](#8-checkpoints-de-implementación)
9. [Reglas de Desarrollo Futuro](#9-reglas-de-desarrollo-futuro)

---

## 1. Estado Actual Resumido

### Status v6.0 → v6.1

**VX11 v6.0 (Auditoría previa):**
- ✅ 9 módulos presentes con `/health` + `/control`
- ✅ BD `data/vx11.db` con 36 tablas coherentes
- ✅ Workspace VS Code limpio y optimizado
- ✅ Tests: 33/36 OK en switch/hermes (minor enums/keys issues)
- ✅ Arquitectura funcional, lista para producción

**VX11 v6.1 (Canonización):**
- ✅ Prompts canónicos creados para todos los módulos:
  - `prompts/context-7.schema.json` (7 capas de contexto)
  - `prompts/switch.prompt.json` (router IA híbrido)
  - `prompts/hermes.prompt.json` (CLI + Playwright + tools)
  - `prompts/madre.prompt.json` (orquestador central)
  - `prompts/hormiguero.prompt.json` (aprendizaje continuo)
  - `prompts/shubniggurath.prompt.json` (DAW + audio)
- ✅ Endpoint `/vx11/chat` implementado en gateway
- ✅ Context-7 canónico definido (7 capas)
- ✅ Contratos de endpoints documentados

**Cambios en esta sesión:**
- Adición: 6 archivos JSON en `prompts/`
- Adición: Endpoint `/vx11/chat` en `gateway/main.py` (~60 líneas)
- Total cambios: ~500 líneas (JSON + endpoint)
- Breaking changes: **0**
- Backward compatibility: **100%**

---

## 2. Arquitectura Canónica

### 2.1. Módulos y responsabilidades (definitivo)

```
┌─────────────────────────────────────────────────────────┐
│                      GATEWAY (8000)                      │
│  - Punto único entrada HTTP/S                            │
│  - Autenticación X-VX11-Token                            │
│  - Endpoints: /health, /vx11/status, /vx11/chat,         │
│    /vx11/action/control, /vx11/bridge                    │
└──────────┬──────────────────────────────────────────────┘
           │
       com-prompt
           │
┌──────────▼──────────────────────────────────────────────┐
│                      MADRE (8001)                        │
│  - Orquestador central y cerebro supervisor              │
│  - Recibe com-prompt desde gateway                       │
│  - Decide: ¿motor IA o herramienta?                      │
│  - Coordina con switch/hermes/hormiguero                 │
│  - Persistencia de tasks en BD                           │
└─┬────────┬────────────────┬──────────────────────────────┘
  │        │                │
  │    context7         context7     context7
  │        │                │
  ├─►┌─────▼─────────────┐ ├─►┌─────────────────┐
  │  │   SWITCH (8002)   │ │  │ HERMES (8003)   │
  │  │ - Router IA       │ │  │ - CLI executor  │
  │  │ - Scoring        │ │  │ - Playwright    │
  │  │ - Feromonas      │ │  │ - Tools runner  │
  │  └───────────────────┘ │  └─────────────────┘
  │                         │
  └─►┌──────────────────────────────────────────┐
     │    HORMIGUERO (8004)                     │
     │ - Aprendizaje continuo                   │
     │ - Optimización de pheromones             │
     │ - GA para hiperparámetros                │
     │ - Persistencia en learner.json / BD      │
     └──────────────────────────────────────────┘

     ┌──────────────────┐  ┌──────────────────┐
     │ MANIFESTATOR     │  │ MCP (8006)       │
     │ (8005)           │  │ - Puente ext MCP │
     │ - Valida         │  │ - Copilot client │
     │ - Genera schemas │  │ - Tools wrapper  │
     └──────────────────┘  └──────────────────┘

     ┌──────────────────┐  ┌──────────────────┐
     │ SHUBNIGGURATH    │  │ SPAWNER (8008)   │
     │ (8007)           │  │ - Hijas efímeras │
     │ - Audio/DAW      │  │ - Task isolation │
     │ - REAPER OSC     │  │ - Cleanup auto   │
     └──────────────────┘  └──────────────────┘
```

### 2.2. Tabla PORTS canónica (centralizada en `config/settings.py`)

```python
PORTS = {
    "gateway": 8000,
    "madre": 8001,
    "switch": 8002,
    "hermes": 8003,
    "hormiguero": 8004,
    "manifestator": 8005,
    "mcp": 8006,
    "shub": 8007,
    "spawner": 8008,
}
```

### 2.3. Tabla de BD canónica (36 tablas)

Tablas críticas para canon v6.1:

- **Task** - Tareas persistentes
- **Context** - Historial de contexto-7
- **Report** - Reportes de ejecuciones
- **Spawn** - Procesos efímeros
- **Engine** - Motores IA disponibles
- **EngineMetrics** - Métricas por motor
- **Pheromone** - Feromonas por engine/intent

---

## 3. Lenguaje VX11 + Context-7

### 3.1. Com-Prompt Canónico

Entrada normalizada de usuario a VX11:

```json
{
  "user_text": "texto original del usuario",
  "intent": "mix_audio|repair_system|query_docs|automation|debug|script|explore",
  "target_module": "auto|shubniggurath|hermes|switch|hormiguero|madre|manifestator|mcp",
  "priority": "low|normal|high|critical",
  "constraints": {
    "max_latency_ms": 5000,
    "cost_sensitivity": "low|medium|high",
    "local_only": false
  },
  "context7": { /* ver abajo */ }
}
```

**Flujo:**
1. Usuario envía texto a gateway
2. Gateway normaliza a com-prompt
3. Pasa a madre
4. Madre consulta switch
5. Switch decide: motor IA (local/remote) o herramienta
6. Ejecución y respuesta

### 3.2. Context-7 Canónico (7 capas)

**Todas las peticiones a switch, hermes, hormiguero DEBEN incluir context-7 completo.**

```json
{
  "layer1_user": {
    "id": "user_hash",
    "profile": "power_user|novice|automation_freak",
    "preferences": {
      "language": "es|en|fr",
      "verbosity": "low|normal|high",
      "humor": "dry|casual|formal"
    }
  },
  "layer2_session": {
    "session_id": "uuid",
    "channel": "copilot|http|cli|telegram",
    "start_time": "ISO8601"
  },
  "layer3_task": {
    "task_id": "uuid",
    "type": "mix|audit|repair|explore|script|query|automation",
    "deadline_ms": 10000,
    "priority": "low|normal|high|critical"
  },
  "layer4_environment": {
    "os": "ubuntu|windows|macos",
    "vx_version": "vx11.6.1",
    "resources": {
      "cpu_load": 0.3,
      "ram_free_mb": 2000,
      "disk_free_mb": 50000
    }
  },
  "layer5_security": {
    "auth_level": "owner|trusted|guest",
    "sandbox": true,
    "allowed_tools": ["switch.hermes.cli.safe", "switch.hermes.playwright.readonly"],
    "ip_whitelist": ["127.0.0.1"]
  },
  "layer6_history": {
    "recent_commands": ["...", "..."],
    "last_outcome": "success|failure|partial|timeout",
    "penalties": {},
    "successes_count": 5
  },
  "layer7_meta": {
    "explain_mode": false,
    "debug_trace": false,
    "telemetry": true,
    "mode": "eco|balanced|high-perf|critical",
    "trace_id": "uuid"
  }
}
```

**Archivo de schema:** `prompts/context-7.schema.json`

### 3.3. Prompts por módulo

Cada módulo tiene su archivo `prompts/{module}.prompt.json` con:

- **module**: nombre
- **version**: "6.1"
- **role**: descripción de rol
- **style**: idioma, verbosity, formato, tono
- **templates**: prompts por acción (ej: route_decision para switch)
- **endpoints**: contratos HTTP
- **rules**: reglas de comportamiento

**Archivos canónicos:**
- `prompts/switch.prompt.json` - Router IA
- `prompts/hermes.prompt.json` - CLI + Playwright
- `prompts/madre.prompt.json` - Orquestador
- `prompts/hormiguero.prompt.json` - Aprendizaje
- `prompts/shubniggurath.prompt.json` - DAW
- `prompts/context-7.schema.json` - Schema JSON

---

## 4. Switch + Hermes + Feromonas

### 4.1. Tabla de Engines (en Switch)

```json
{
  "engines": [
    {
      "id": "local_gguf_small",
      "type": "local",
      "tags": ["fast", "cheap"],
      "max_ctx": 4096,
      "latency_ms": 150,
      "quality": 0.6,
      "cost": 0.0
    },
    {
      "id": "deepseek_auto",
      "type": "remote",
      "tags": ["reasoning", "heavy"],
      "max_ctx": 16000,
      "latency_ms": 1200,
      "quality": 0.9,
      "cost": 2.0
    },
    {
      "id": "gpt5_mini",
      "type": "remote",
      "tags": ["balanced"],
      "max_ctx": 16000,
      "latency_ms": 800,
      "quality": 0.8,
      "cost": 1.2
    },
    {
      "id": "hermes_cli",
      "type": "tool",
      "tags": ["cli", "commands"],
      "latency_ms": 200,
      "quality": 1.0,
      "cost": 0.0
    },
    {
      "id": "hermes_playwright",
      "type": "tool",
      "tags": ["browser", "scraping"],
      "latency_ms": 5000,
      "quality": 1.0,
      "cost": 0.0
    }
  ]
}
```

### 4.2. Scoring Canónico

```
score = w_q * quality_norm + w_l * (1 - latency_norm) + w_c * (1 - cost_norm) + w_f * pheromone
```

**Modos (definidos en context7.layer7_meta.mode):**

| Mode | w_q | w_l | w_c | w_f | Caso de uso |
|------|-----|-----|-----|-----|------------|
| eco | 0.3 | 0.3 | 0.4 | 0.0 | Bajo presupuesto, latencia flexible |
| balanced | 0.4 | 0.3 | 0.3 | 0.0 | General, producción normal |
| high-perf | 0.6 | 0.2 | 0.2 | 0.0 | Máxima calidad, presupuesto ok |
| critical | 0.7 | 0.2 | 0.1 | 0.0 | Crítico, calidad prioritaria |

**Feromonas activas (con w_f):**

Cuando hormiguero haya ejecutado suficientes iterations, activar w_f > 0.

```
pheromone_new = pheromone_old * decay + reward

decay = 0.95

reward = {
  success_on_time: +0.2,
  success_late: +0.05,
  failure: -0.3,
  timeout: -0.1,
  cost_excessive: -0.1
}

pheromone ∈ [-1, +1]
```

### 4.3. Interacción Switch ↔ Hermes

**Flujo canónico:**

1. Madre recibe com-prompt
2. Madre llama `POST /switch/query` con context-7
3. Switch retorna:
   ```json
   {
     "engine_id": "hermes_cli",
     "route": "tool",
     "tool": "switch.hermes.cli",
     "score": 0.85,
     "reasoning": "Comando CLI simple, mejor usar herramienta directa"
   }
   ```
4. Si route == "tool":
   - Madre llama `POST /hermes/cli` (o playwright, o tools) con mismo context-7
5. Si route == "local" o "remote":
   - Madre llama motor IA elegido

---

## 5. Hermes + Playwright

### 5.1. Roles de Hermes (concentrador)

- **CLI Executor:** Comandos con whitelist/blacklist según context7.layer5_security
- **Playwright Orchestrator:** Navegador headless con dominios permitidos
- **Tools Runner:** Scripts Python, utilidades locales (parse_logs, check_ports, run_tests)

### 5.2. API Canónica de Hermes

```
POST /hermes/cli
{
  "context7": {...},
  "command": "ls -la",
  "args": [],
  "mode": "safe|extended",
  "timeout_ms": 5000
}

Response:
{
  "status": "ok|error",
  "exit_code": 0,
  "stdout": "output",
  "stderr": "errors",
  "truncated": false
}
```

```
POST /hermes/playwright
{
  "context7": {...},
  "script_id": "check_reaper_download",
  "params": {"url": "https://www.reaper.fm/", "expect_text": "Download"},
  "timeout_ms": 15000
}

Response:
{
  "status": "ok|timeout|error",
  "steps_executed": 5,
  "data": {"found": true},
  "screenshots": ["...optional..."]
}
```

### 5.3. Seguridad Mínima (context-7 driven)

- Si `sandbox == true`: whitelist only
- Si `auth_level == guest`: denegar comandos peligrosos
- Whitelist de dominios para Playwright
- Rate limiting: 10 req/s, 3 concurrent

---

## 6. Puente Copilot/VS Code

### 6.1. Objetivo

Que Copilot/VS Code actúe como frontend de VX11.

```
Copilot CLI → HTTP POST /vx11/chat → Gateway → Madre → Switch/Hermes → Respuesta
```

### 6.2. Endpoint Canónico `/vx11/chat`

**Implementado en gateway v6.1**

```
POST /vx11/chat
Header: X-VX11-Token: {token}

{
  "source": "copilot|vscode|cli|http",
  "message": "texto del usuario",
  "session_id": "uuid (opcional)",
  "metadata": {
    "file_path": "/ruta/archivo.py",
    "selection": "código seleccionado",
    "language_id": "python|yaml|js"
  },
  "context7": {...}  (opcional, madre genera si falta)
}

Response:
{
  "reply": "respuesta en natural",
  "actions": [
    {
      "type": "suggest_edit|run_command|open_file|research",
      "file": "path",
      "range": [line_start, col_start, line_end, col_end],
      "replacement": "nuevo código"
    }
  ],
  "context_used": {
    "engines": ["gpt5_mini"],
    "tools": ["switch.hermes.cli"],
    "duration_ms": 820
  }
}
```

### 6.3. Instrucciones Copilot

Archivo sugerido: `.github/copilot-instructions-vx11.md`

**Contenido mínimo:**

```markdown
# VX11 Copilot Instructions

- Siempre enviar mensajes a `http://127.0.0.1:8000/vx11/chat`
- Usar X-VX11-Token = $VX11_LOCAL_TOKEN
- No ejecutar comandos en shell directamente sin pasar por Hermes
- Usar `actions` del JSON como única fuente de verdad
- Respetar context7 (sandbox, auth_level, allowed_tools)
- Si sandbox=true, usar solo herramientas seguras
```

---

## 7. Automatizaciones + Limpieza

### 7.1. Scripts canónicos en `scripts/`

**Deben existir:**

- `start_all.sh` - Arrancar en orden: gateway → madre → switch → hermes → hormiguero → manifestator → mcp → shub → spawner
- `stop_all.sh` - Parar de forma ordenada (inverso)
- `restart_all.sh` - Restart limpio
- `status_all.sh` - Estado de todos
- `cleanup_temp.sh` - Limpiar basura temporal

### 7.2. Reglas de limpieza canónicas

```
Nada en raíz salvo:
  - README.md, requirements.txt, docker-compose.yml
  - .env*, tokens.env, vx11.code-workspace
  - *.md documentación
  - .github/

Basura temporal:
  - SIEMPRE en tmp/ o sandbox/
  - Borrable con un script
  - No versionar

Logs:
  - Solo en logs/
  - Rotados por tamaño/fecha
  - .gitignore: logs/*.log

__pycache__, *.pyc, .pytest_cache:
  - Eliminados por cleanup_temp.sh
  - Excluidos en .gitignore y VS Code settings
```

---

## 8. Checkpoints de Implementación

### 8.1. Implementación v6.1 (estado actual)

✅ **Completado:**
- [x] 9 módulos con /health + /control
- [x] BD 36 tablas coherentes
- [x] Prompts canónicos (6 archivos JSON)
- [x] Context-7 schema
- [x] Endpoint /vx11/chat en gateway
- [x] Archivo este canon (VX11_CANON_v6.1.md)

⚠️ **Por hacer (no crítico para v6.1):**
- [ ] Implementar context-7 en todos los endpoints (madre, switch, hermes)
- [ ] Implementar scoring con feromonas en switch/router_v4.py
- [ ] Activar GA en hormiguero/main.py
- [ ] Playwright scripts pre-definidos en hermes/
- [ ] MCP bridge con Copilot (opcional v6.1)

### 8.2. Validación automática

Crear script `scripts/validate_canon_v6.1.sh`:

```bash
#!/bin/bash
set -e

echo "Validando VX11 Canon v6.1..."

# Verificar módulos
for mod in gateway madre switch hermes hormiguero manifestator mcp shubniggurath spawner; do
  if [ ! -f "$mod/main.py" ]; then
    echo "ERROR: $mod/main.py faltante"
    exit 1
  fi
done

# Verificar prompts canónicos
for prompt in context-7.schema.json switch.prompt.json hermes.prompt.json madre.prompt.json hormiguero.prompt.json shubniggurath.prompt.json; do
  if [ ! -f "prompts/$prompt" ]; then
    echo "ERROR: prompts/$prompt faltante"
    exit 1
  fi
done

# Verificar endpoints
if ! grep -q "@app.post(\"/vx11/chat\")" gateway/main.py; then
  echo "ERROR: /vx11/chat endpoint no encontrado en gateway"
  exit 1
fi

# Verificar BD
if [ ! -f "data/vx11.db" ]; then
  echo "ERROR: data/vx11.db faltante"
  exit 1
fi

echo "✅ VX11 Canon v6.1: Todas las validaciones pasaron"
```

---

## 9. Reglas de Desarrollo Futuro

### 9.1. Reglas inamovibles (canon v6.1)

1. **Context-7 es obligatorio en todos los endpoints de:**
   - switch
   - hermes
   - hormiguero
   - madre
   - shubniggurath

2. **Todos los módulos DEBEN tener:**
   - `GET /health`
   - `POST /control` con payload `{"action": "status|start|stop|restart"}`
   - Use `create_module_app()` de `config/module_template.py`

3. **Cambios en endpoints DEBEN:**
   - Respetar context-7
   - No romper compatibilidad backward
   - Actualizar prompts correspondientes

4. **BD DEBE:**
   - Mantener 36 tablas base (no borrar)
   - Añadir nuevas tablas solo si necesario
   - Versionar schema con migrations

### 9.2. Checklist pre-commit

```
Antes de hacer commit:

- [ ] Sin breaking changes en endpoints
- [ ] Context-7 presente en nuevas llamadas
- [ ] Prompts actualizados si cambié lógica
- [ ] Tests pasan (pytest tests/)
- [ ] Logs limpios (no basura en archivos)
- [ ] Ningún archivo temporal en raíz
- [ ] Documentación actualizada (.md)
```

### 9.3. Flujo de cambios canónico

```
1. Cambio de lógica en módulo X
   ↓
2. Actualizar prompts/{module}.prompt.json
   ↓
3. Actualizar tests correspondientes
   ↓
4. Actualizar THIS_CANON si es arquitectural
   ↓
5. Commit con message: "fix(module): descripción"
```

---

## 10. Conclusión

VX11 v6.1 define la arquitectura definitiva:

- **Modular**: 9 módulos independientes, comunicación vía HTTP + context-7
- **Escalable**: Switch + Hormiguero para inteligencia y aprendizaje
- **Seguro**: Context-7 layers para control granular de permisos
- **Documentado**: Prompts canónicos para cada módulo
- **Copilot-ready**: Endpoint /vx11/chat + MCP bridge potential

Esta canonización es **definitiva a nivel de diseño**. Cambios futuros deben respetar:
- Context-7 como bloque obligatorio
- Rol de cada módulo
- Contrato de endpoints
- Reglas de limpieza y desarrollo

**Status final:** ✅ **CANONIZADO Y LISTO PARA DESARROLLO**

---

## Apéndice: Archivos de Referencia

- `prompts/context-7.schema.json` - Schema de context-7
- `prompts/switch.prompt.json` - Prompts del switch
- `prompts/hermes.prompt.json` - Prompts de hermes
- `prompts/madre.prompt.json` - Prompts de madre
- `prompts/hormiguero.prompt.json` - Prompts del hormiguero
- `prompts/shubniggurath.prompt.json` - Prompts de shubniggurath
- `gateway/main.py` - Endpoint `/vx11/chat` (líneas ~XX-YY)
- `config/settings.py` - PORTS canónicos
- `config/module_template.py` - Plantilla de módulos

---

**FIN DEL CANON VX11 v6.1**
