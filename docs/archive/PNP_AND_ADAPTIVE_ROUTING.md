# VX11 v6.0 — Plug-and-Play & Adaptive Routing

**Documentación técnica de Container State Management y Switch-Hermes Integration**

---

## 🎯 Visión General

VX11 v6.0 introduce dos capacidades empresa-grade:

1. **Plug-and-Play (P&P)**: Gestión unificada de estados de módulos
2. **Adaptive Engine Selection**: Selección inteligente de proveedores IA con circuit breaker

Ambas integradas en todas las 9 módulos de forma transparent y backward-compatible.

---

## 📦 Plug-and-Play (P&P) — Container State Management

### Propósito

Permitir control granular del lifecycle de cada módulo sin reiniciar servicios:
- Escalar abajo módulos subutilizados (`standby`)
- Mantener disponibilidad de módulos críticos (`active`)
- Desactivar módulos temporalmente (`off`)

### Estados

| Estado | Significado | Procesamiento | Uso |
|--------|-------------|----------------|----|
| `active` | Módulo activo y procesando | Procesa toda entrada | Normal |
| `standby` | Modo bajo consumo | Rechaza entrada, escucha eventos | Conservar recursos |
| `off` | Desactivado | Rechaza todo | Mantenimiento |

### Configuración por Defecto

```python
# Módulos críticos (activos por defecto)
gateway, madre, switch, hermes, hormiguero, mcp = "active"

# Módulos opcionales (standby por defecto)
manifestator, shubniggurath, spawner = "standby"
```

### API

#### Cambiar estado de un módulo
```bash
POST /orchestration/set_module_state
Content-Type: application/json

{
  "module": "manifestator",
  "state": "standby"  # or "active", "off"
}
```

**Response:**
```json
{
  "status": "ok",
  "module": "manifestator",
  "state": "standby",
  "previous_state": "active",
  "timestamp": "2025-12-01T19:30:00.123456"
}
```

#### Obtener estados de todos los módulos
```bash
GET /orchestration/module_states
```

**Response:**
```json
{
  "modules": {
    "gateway": {"state": "active", "last_changed": "..."},
    "madre": {"state": "active", "last_changed": "..."},
    "manifestator": {"state": "standby", "last_changed": "..."},
    ...
  }
}
```

#### Obtener estado de un módulo
```bash
GET /control/get_state
```

#### Cambiar estado (endpoint local)
```bash
POST /control/state
Content-Type: application/json

{"state": "standby"}
```

### Uso Programático

```python
from config.container_state import (
    set_state, get_state, is_active, should_process,
    get_active_modules, get_standby_modules
)

# Cambiar estado
set_state("manifestator", "standby")

# Verificar estado
if is_active("switch"):
    print("Switch está activo")

# Obtener lista de módulos activos
active = get_active_modules()
print(f"Módulos activos: {active}")

# Usar en rutinas de procesamiento
if should_process("hermes"):
    hermes.execute(query)
```

### Integración en Madre

Madre es el orquestador de P&P. Puede:
1. Monitorear carga y decidir escalamiento
2. Activar módulos según demanda
3. Generar reportes de utilización

**Endpoints de orquestación (Madre):**
- `GET /orchestration/module_states` — Ver todos los estados
- `POST /orchestration/set_module_state` — Cambiar estado

---

## 🧠 Switch-Hermes Integration — Adaptive Engine Selection

### Propósito

Seleccionar automáticamente el mejor proveedor IA (hermes_local, deepseek, openrouter, etc.) basado en:
- Modo operacional actual (ECO, BALANCED, HIGH-PERF, CRITICAL)
- Salud del motor (métricas, latencia, errores)
- Circuit breaker (evitar motores fallando)
- Cadenas de fallback (resiliencia)

### Arquitectura

#### EngineMetrics (por motor)

Rastrea por cada motor:
```python
{
    "engine_name": "hermes_local",
    "total_requests": 150,
    "successful_requests": 148,
    "failed_requests": 2,
    "consecutive_errors": 0,
    "avg_latency_ms": 42.5,
    "last_error": None,
    "circuit_breaker_open": False,
    "circuit_breaker_opened_at": None,
    "status": "available"  # or "error"
}
```

**Circuit Breaker Logic:**
- Abre: 5 errores consecutivos
- Cierra: Intenta reset cada 60s
- Efecto: Rechaza motor hasta reset

#### AdaptiveEngineSelector

Selecciona motor inteligentemente:
```python
selector.set_available_engines(["hermes_local", "deepseek", "cli_bash"])
selector.set_mode("BALANCED")

selection = selector.select_engine()
# {
#   "status": "ok",
#   "engine": "hermes_local",
#   "mode": "BALANCED",
#   "profile": {
#     "timeout_ms": 8000,
#     "max_concurrent": 4,
#     "preferred_engines": ["hermes_local", "openrouter_text", "local_cli"],
#     "fallback_chain": ["local_cli"]
#   }
# }
```

### Modos

| Modo | Timeout | Concurrency | Preferred | Fallback |
|------|---------|-------------|-----------|----------|
| ECO | 5s | 2 | hermes_local, cli_bash | cli_bash |
| BALANCED | 8s | 4 | hermes_local, openrouter_text, local_cli | local_cli |
| HIGH-PERF | 15s | 8 | deepseek, openrouter_text | deepseek |
| CRITICAL | 30s | 16 | openrouter_text | openrouter_premium |

### API

#### Seleccionar motor
```bash
POST /switch/hermes/select_engine
Content-Type: application/json

{
  "query": "Calcula la suma de 1+1",
  "available_engines": ["hermes_local", "deepseek", "cli_bash"]
}
```

**Response:**
```json
{
  "status": "ok",
  "engine": "hermes_local",
  "mode": "BALANCED",
  "profile": {
    "timeout_ms": 8000,
    "max_concurrent": 4,
    "preferred_engines": ["hermes_local", "openrouter_text"],
    "fallback_chain": ["local_cli"]
  },
  "timestamp": "2025-12-01T19:35:00"
}
```

#### Registrar resultado (feedback loop)
```bash
POST /switch/hermes/record_result
Content-Type: application/json

{
  "engine": "hermes_local",
  "success": true,
  "latency_ms": 145,
  "error": null  # or "Timeout" if success=false
}
```

**Response:**
```json
{
  "status": "ok",
  "engine": "hermes_local",
  "recorded": true,
  "metrics": {
    "total_requests": 151,
    "successful": 149,
    "failed": 2,
    "error_rate_percent": 1.32,
    "avg_latency_ms": 142.3
  }
}
```

#### Ver estado de motores
```bash
GET /switch/hermes/status
```

**Response:**
```json
{
  "status": "ok",
  "mode": "BALANCED",
  "available_engines": ["hermes_local", "deepseek"],
  "healthy_engines": ["hermes_local"],
  "metrics": {
    "hermes_local": {
      "total_requests": 151,
      "successful": 149,
      "failed": 2,
      "error_rate": 1.32,
      "avg_latency_ms": 142.3,
      "circuit_breaker_open": false
    },
    "deepseek": {
      "total_requests": 10,
      "successful": 5,
      "failed": 5,
      "error_rate": 50.0,
      "avg_latency_ms": 2500.0,
      "circuit_breaker_open": true
    }
  }
}
```

### Uso Programático

```python
from config.switch_hermes_integration import get_selector

selector = get_selector()

# Configurar motores disponibles
selector.set_available_engines(["hermes_local", "deepseek", "cli_bash"])

# Cambiar modo según carga
if high_load:
    selector.set_mode("CRITICAL")
else:
    selector.set_mode("BALANCED")

# Seleccionar motor
selection = selector.select_engine()
engine = selection["engine"]

# Ejecutar en motor seleccionado
result = execute_on_engine(engine, query)

# Registrar resultado (feedback loop)
selector.record_engine_result(
    engine=engine,
    success=result["success"],
    latency_ms=result["duration_ms"],
    error=result.get("error")
)

# Revisar salud
status = selector.get_status()
print(f"Motors en buen estado: {status['healthy_engines']}")
```

### Circuit Breaker Behavior

**Ejemplo de degradación:**

```
Motor: deepseek
Requests: 5, Success: 5 → AVAILABLE
Requests: 6, Error   → consecutive_errors=1 → AVAILABLE
Requests: 7, Error   → consecutive_errors=2 → AVAILABLE
Requests: 8, Error   → consecutive_errors=3 → AVAILABLE
Requests: 9, Error   → consecutive_errors=4 → AVAILABLE
Requests: 10, Error  → consecutive_errors=5 → CIRCUIT BREAKER OPEN ⚠️

select_engine() ← Rechazará deepseek, usará fallback (openrouter)

[Esperar 60s]
select_engine() ← Intenta reset de circuit breaker
Si deepseek responde: consecutive_errors=0, REABRE
Si deepseek falla: consecutive_errors=1, Se reintenta reset
```

---

## 📊 Flujo Combinado (P&P + Switch-Hermes)

```
Usuario envía query a /mcp/chat
    ↓
MCP obtiene modo: switch.get_status().mode → "BALANCED"
    ↓
MCP consulta: switch.select_engine() → "hermes_local"
    ↓
MCP verifica: container_state.is_active("hermes_local") → True
    ↓
MCP ejecuta: hermes.execute(query)
    ↓
MCP registra: switch.record_engine_result(hermes_local, success=True, latency_ms=120)
    ↓
MCP retorna: response + metadata
```

---

## 🔧 Configuración Avanzada

### Cambiar profiles de modo

En `config/switch_hermes_integration.py`:

```python
ENGINE_PROFILES = {
    "CUSTOM": {
        "preferred_engines": ["hermes_local", "custom_provider"],
        "timeout_ms": 12000,
        "max_concurrent": 6,
        "fallback_chain": ["cli_bash"]
    }
}
```

### Personalizar circuit breaker

En `config/switch_hermes_integration.py`, clase `EngineMetrics`:

```python
CIRCUIT_BREAKER_THRESHOLD = 5  # Errores antes de abrir
CIRCUIT_BREAKER_TIMEOUT = 60  # Segundos antes de intentar reset
```

### Agregar nuevo motor

```python
# 1. Registrar
selector.register_engine("custom_engine")

# 2. Agregar a available_engines
selector.set_available_engines([..., "custom_engine"])

# 3. Usar profiles
ENGINE_PROFILES["BALANCED"]["preferred_engines"].append("custom_engine")
```

---

## 🧪 Testing

**Unit tests:** `tests/test_pnp_and_switch_integration.py`

```bash
# Tests de P&P
pytest tests/test_pnp_and_switch_integration.py::TestContainerStatePnP -v

# Tests de switch-hermes
pytest tests/test_pnp_and_switch_integration.py::TestAdaptiveEngineSelector -v

# Tests de métricas
pytest tests/test_pnp_and_switch_integration.py::TestEngineMetrics -v
```

---

## 📝 Cambios en v6.0

- ✅ **P&P:** config/container_state.py (120 líneas)
- ✅ **P&P:** config/state_endpoints.py (80 líneas)
- ✅ **Switch-Hermes:** config/switch_hermes_integration.py (260 líneas)
- ✅ **module_template.py:** +30 líneas (integración P&P)
- ✅ **madre/main.py:** +40 líneas (endpoints de orquestación)
- ✅ **switch/main.py:** +80 líneas (endpoints switch-hermes)
- ✅ **Tests:** +200 líneas (test_pnp_and_switch_integration.py)

**Total: ~450 líneas de nuevo código**

**Breaking changes: 0**

**Backward compatibility: 100%**

---

## 🚀 Proximos Pasos

1. Implementar auto-scaling en Madre (usar P&P según CPU/Memory)
2. Agregar persistencia de métricas (guardar en vx11.db)
3. Dashboard de monitoreo (WebSocket de estado en tiempo real)
4. Machine learning para predicción de carga

---

**VX11 v6.0 — Enterprise Container Management** 🎛️⚡
