# VX11 AI Agent Advanced Guide — Patrones Avanzados & Ejemplos

**Complemento a: `.github/copilot-instructions.md`**

## Flujos de Trabajo Comunes para Agentes

### 1. Diagnóstico Completo del Sistema

```bash
# 1. Verificar estado global
curl -s http://127.0.0.1:8000/vx11/status | jq .

# 2. Health check de cada módulo
for port in {8000..8008}; do
  echo "Port $port:"
  curl -s http://127.0.0.1:$port/health | jq .status
done

# 3. Revisar logs forenses si algo falla
ls -lah /home/elkakas314/vx11/forensic/*/logs/ | head -20

# 4. Buscar crashes recientes
find /home/elkakas314/vx11/forensic/crashes -mtime -1 | head -10
```

### 2. Crear y Ejecutar una Tarea Conversacional Completa

```bash
# Paso 1: Enviar mensaje a MCP con acción
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8006/mcp/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Crea una tarea para validar la BD",
    "require_action": true,
    "context": {"target":"madre"}
  }' | jq -r .session_id)

echo "Session created: $SESSION_ID"

# Paso 2: Consultar status de la tarea (si se creó)
curl -s http://127.0.0.1:8001/task/list | jq '.tasks | last'

# Paso 3: Obtener resultados
curl -s http://127.0.0.1:8001/task/results | jq '.[-1]'
```

### 3. Routing IA: Elegir Proveedor Dinámicamente

```bash
# Ver modo actual y proveedores disponibles
curl -s http://127.0.0.1:8002/switch/status | jq .

# Cambiar a modo ECO (consume menos recursos)
curl -X POST http://127.0.0.1:8002/switch/set-mode \
  -H "Content-Type: application/json" \
  -d '{"mode":"ECO"}'

# Ver métricas de proveedores
curl -s http://127.0.0.1:8002/switch/hermes/status | jq '.engines'

# Hacer una consulta con routing inteligente
curl -X POST http://127.0.0.1:8002/switch/route \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explica el patrón de modulación en este sistema",
    "context": {"max_tokens":150}
  }' | jq .
```

### 4. Testing Integración Multi-Servicio

```bash
# Test: Control vía gateway de múltiples módulos
for module in "madre" "switch" "hermes" "mcp"; do
  echo "Testing $module..."
  curl -s -X POST http://127.0.0.1:8000/vx11/action/control \
    -H "Content-Type: application/json" \
    -d "{\"target\":\"$module\",\"action\":\"status\"}" | jq .
done

# Test: Persistencia en BD
sqlite3 /home/elkakas314/vx11/data/vx11.db "SELECT COUNT(*) FROM Task"

# Test: Historial conversacional
curl -s http://127.0.0.1:8001/chat/history | jq '.[-5:]'
```

---

## Patrones de Código: Agregar Nueva Funcionalidad

### Crear un Nuevo Módulo Mínimo

```python
# mi_modulo/main.py
from config.module_template import create_module_app
from fastapi import FastAPI

app = create_module_app("mi_modulo")

# Agregar endpoint personalizado
@app.post("/mi_modulo/execute")
async def execute_task(payload: dict):
    """Ejecuta tarea personalizada"""
    from config.forensics import write_log
    
    try:
        result = await process_payload(payload)
        write_log("mi_modulo", f"task_completed: {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        write_log("mi_modulo", f"error: {str(e)}", level="ERROR")
        raise
```

### Integrar con Gateway (requerido)

```python
# gateway/main.py — agregar a PORTS
PORTS = {
    # ... puertos existentes ...
    "mi_modulo": settings.mi_modulo_port,  # agregar en config/settings.py primero
}

# Agregar salud check en run_all_dev.sh
start_service "mi_modulo" "mi_modulo.main" "$MI_MODULO_PORT"
```

### Usar BD Unificada

```python
# Acceso a sesión unificada
from config.db_schema import get_session, Task, Context

def log_conversation(user_msg, assistant_msg):
    session = get_session()
    try:
        ctx = Context(
            role="user",
            content=user_msg,
            metadata={"source": "mi_modulo"}
        )
        session.add(ctx)
        session.commit()
    finally:
        session.close()
```

---

## Debugging Avanzado

### Capturar Traces Forenses Completos

```bash
# Obtener árbol de crashes
find /home/elkakas314/vx11/forensic/crashes -type f -name "*.json" \
  | xargs jq '.timestamp, .module, .exception' | tail -50

# Revisar hashes de archivos (auditoría de cambios)
ls /home/elkakas314/vx11/forensic/*/hashes/ | head -5
cat /home/elkakas314/vx11/forensic/madre/hashes/*.json | jq '.changed | length'

# Ver logs por módulo en tiempo real
tail -f /home/elkakas314/vx11/forensic/madre/logs/* | grep ERROR
```

### Análisis de Performance

```bash
# Ver latencia de endpoints
curl -w "\nTime: %{time_total}s\n" \
  -X POST http://127.0.0.1:8002/switch/route \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'

# Revisar métricas de switch
curl -s http://127.0.0.1:8002/switch/metrics | jq '.provider_stats'
```

---

## Convenciones de Naming & Paths

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| BD SQLite | `/app/data/{name}.db` | `/app/data/vx11.db` |
| Logs forenses | `forensic/{module}/logs/{timestamp}.log` | `forensic/madre/logs/20250102T120000Z.log` |
| Hash manifests | `forensic/{module}/hashes/*.json` | `forensic/gateway/hashes/20250102.json` |
| Crash dumps | `forensic/crashes/{module}_{timestamp}.json` | `forensic/crashes/switch_20250102T120000Z.json` |
| System prompts | `prompts/{module}.md` | `prompts/madre.md` |

---

## Errors Comunes & Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `DEEPSEEK_API_KEY not found` | Token no exportado | `source tokens.env && docker-compose up` |
| `Port 8001 already in use` | Servicio corriendo | `lsof -i :8001 && kill -9 <PID>` |
| `DB locked` | Acceso concurrente | Esperar 2s o reiniciar el módulo |
| `Module health check failed` | Dependencia no disponible | Ver `forensic/{module}/logs` |
| `No JSON response from endpoint` | Formato incorrecto | Buscar en `response.raw` |

---

## Variables de Entorno Críticas

```bash
# En tokens.env DEBEN estar:
export DEEPSEEK_API_KEY="sk-..."
export VX11_GATEWAY_TOKEN="vx11-token-..."

# En .env pueden estar:
DEBUG=false
ENABLE_AUTH=true
ENVIRONMENT=production

# En config/settings.py se leen durante startup
# Nunca uses valores hardcoded; siempre de settings
from config.settings import settings
port = settings.gateway_port
```

---

## Referencias de API por Módulo

### Gateway (`/vx11/*`)
- `GET /vx11/status` — Estado de puerto y PORTS mapping
- `POST /vx11/action/control` — Reenvío a módulo destino

### MCP (`/mcp/*`)
- `POST /mcp/chat` — Chat con `require_action: true/false`
- `WebSocket /mcp/ws` — Streaming opcional

### Madre (`/chat`, `/task`, `/orchestration/*`)
- `POST /chat` — Chat iterativo con historial
- `POST /task/create` — Crear tarea
- `GET /task/list` — Listar tareas

### Switch (`/switch/*`)
- `POST /switch/route` — Consulta a proveedor elegido
- `GET /switch/status` — Métricas de motores
- `POST /switch/set-mode` — ECO/BALANCED/HIGH-PERF/CRITICAL

---

**Última actualización:** 2 de diciembre de 2025  
**Versión:** VX11 6.2  
**Para reportar issues:** Revisar `forensic/` y `logs/` primero
