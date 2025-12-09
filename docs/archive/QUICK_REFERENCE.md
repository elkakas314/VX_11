# VX11 v5.0 — QUICK REFERENCE

**Acceso rápido a comandos, endpoints y documentación.**

---

## 🎯 Setup (5 minutos)

```bash
# 1. Configurar tokens
cp tokens.env.sample tokens.env
vim tokens.env  # Agregar DEEPSEEK_API_KEY

# 2. Levantar
docker-compose up -d

# 3. Verificar
for port in {8000..8007}; do curl -s http://localhost:$port/health | jq -r '.status'; done
```

---

## 📡 Puertos

| Puerto | Módulo | Endpoint | Función |
|--------|--------|----------|---------|
| 8000 | Gateway | `/health`, `/vx11/status` | Orquestador |
| 8001 | Madre | `/task`, `/madre/v3/autonomous/*` | Tareas autónomas |
| 8002 | Switch | `/switch/providers`, `/switch/route` | Router IA |
| 8003 | Hermes | `/hermes/exec`, `/hermes/available` | CLI executor |
| 8004 | Hormiguero | `/hormiguero/task`, `/hormiguero/colony/status` | Paralelización |
| 8005 | Manifestator | `/drift`, `/generate-patch`, `/apply-patch` | Auditoría |
| 8006 | MCP | `/mcp/chat`, `/mcp/action` | Conversacional |
| 8007 | Shub | `/shub/process`, `/shub/generate` | Procesamiento IA |

---

## 🔥 Comandos Frecuentes

### Health Check
```bash
curl http://localhost:8000/health
curl http://localhost:8000/vx11/status | jq .
```

### Crear Tarea (Madre)
```bash
curl -X POST http://localhost:8001/task \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","task_type":"test","priority":1}' | jq .
```

### Detectar Cambios (Manifestator)
```bash
curl http://localhost:8005/drift | jq .
```

### Generar Parche (Manifestator)
```bash
curl -X POST http://localhost:8005/generate-patch \
  -H "Content-Type: application/json" \
  -d '{"module":"madre","auto_suggest":true}' | jq .
```

### Listar CLIs (Hermes)
```bash
curl http://localhost:8003/hermes/available | jq .
```

### Ver Providers (Switch)
```bash
curl http://localhost:8002/switch/providers | jq .
```

### Ver Logs
```bash
docker-compose logs -f madre
docker-compose logs --tail 50 madre
```

### Parar Sistema
```bash
docker-compose down
```

### Limpiar Volúmenes (CUIDADO)
```bash
./scripts/cleanup.sh
# o
docker volume prune -f
```

---

## 📚 Documentación

| Doc | Propósito |
|-----|-----------|
| `docs/ARCHITECTURE.md` | Visión general, módulos, BD |
| `docs/API_REFERENCE.md` | Todos los endpoints |
| `docs/DEVELOPMENT.md` | Setup local, testing |
| `docs/FLOWS.md` | 10 diagramas Mermaid |
| `docs/MANIFESTATOR_INTEGRATION.md` | Auditoría + VS Code |
| `docs/FINAL_COMMANDS.md` | Validación + deployment |
| `README.md` | Quick start |

---

## 🛠 Troubleshooting

### Puerto en uso
```bash
lsof -i :8001 && kill -9 <PID>
```

### Módulo caído
```bash
docker-compose restart madre
docker logs vx11_madre_1 | tail -20
```

### BD corrupta
```bash
cp data/madre.db data/madre.db.bak
rm data/madre.db  # Se recreará automáticamente
```

### DEEPSEEK_API_KEY falta
```bash
source tokens.env
echo $DEEPSEEK_API_KEY  # Debe tener valor
docker-compose up -d --env-file tokens.env
```

---

## 🧪 Validación Rápida

```bash
# Compilar Python
python3 -m compileall .

# Validar docker-compose
docker-compose config

# Build (sin cache)
docker-compose build --no-cache

# Health check batch
for port in {8000..8007}; do
  echo "Port $port: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:$port/health)"
done

# Verificar imágenes
docker images | grep vx11 | wc -l  # Debe mostrar 8
```

---

## 🎨 Usar en VS Code

1. **Instalar REST Client** (ext: Huachao Mao)
2. **Usar `test.rest`**: Ctrl/Cmd + Alt + R
3. **Terminal**: `` Ctrl/Cmd + ` ``
4. **Copilot Chat**: Ctrl/Cmd + Shift + I

### Prompt Copilot
```
"Usa Manifestator para detectar cambios en madre, generar y aplicar parches si es seguro"
```

---

## 🔐 Seguridad

- Tokens en `tokens.env` (no comitear)
- Gateway token: `VX11_GATEWAY_TOKEN`
- JWT: cambiar en producción
- CORS: restringir en prod

---

## 💾 Configuración

- **Puertos**: config/settings.py (8000–8007)
- **Límite memoria**: MAX_MEMORY_MB = 512
- **GC interval**: MEMORY_CLEANUP_INTERVAL = 300s
- **BD**: data/madre.db (SQLite)

---

## 🚀 Deployment Producción

Ver `docs/FINAL_COMMANDS.md` para checklist completo (10 fases).

**Resumen:**
1. `python3 -m compileall .`
2. `docker-compose build --no-cache`
3. `docker-compose up -d`
4. Health checks batch
5. Monitorear logs

---

## 🎛️ Plug-and-Play (P&P) — Container State Management

**Controlar estados de módulos: `off`, `standby`, `active`.**

### Ver estados de todos los módulos
```bash
curl http://localhost:8001/orchestration/module_states | jq .
```

### Cambiar estado de un módulo
```bash
curl -X POST http://localhost:8001/orchestration/set_module_state \
  -H "Content-Type: application/json" \
  -d '{"module":"manifestator","state":"standby"}'
```

### Control local (sin Madre)
```bash
from config.container_state import set_state, get_state, is_active

set_state("manifestator", "standby")
if is_active("switch"):
    print("Switch está activo")
```

**Estados por defecto:** gateway/madre/switch/hermes/hormiguero/mcp = `active` | manifestator/shubniggurath/spawner = `standby`

---

## 🧠 Switch-Hermes Integration — Adaptive Engine Selection

**Seleccionar proveedores IA según modo y salud del motor.**

### Ver motor recomendado
```bash
curl -X POST http://localhost:8002/switch/hermes/select_engine \
  -H "Content-Type: application/json" \
  -d '{"query":"Calcula 2+2","available_engines":["hermes_local","deepseek"]}'
```

### Registrar resultado (feedback loop)
```bash
curl -X POST http://localhost:8002/switch/hermes/record_result \
  -H "Content-Type: application/json" \
  -d '{"engine":"hermes_local","success":true,"latency_ms":150}'
```

### Ver estado de motores
```bash
curl http://localhost:8002/switch/hermes/status | jq .
```

### Modos disponibles
- `ECO`: Local + CLI, 5s timeout (fallback: cli_bash)
- `BALANCED`: Mix ligero, 8s timeout (fallback: local engines)
- `HIGH-PERF`: Cloud engines, 15s timeout (fallback: deepseek)
- `CRITICAL`: Premium only, 30s timeout (fallback: openrouter)

**Circuit breaker:** Abre después de 5 errores, intenta reset cada 60s.

---

## 📞 Referencia Rápida

- **Docs**: `docs/`
- **APIs**: En cada módulo `main.py`
- **Config**: `config/settings.py`
- **Scripts**: `scripts/`
- **BD**: `data/*.db`
- **Logs**: `docker-compose logs -f`
- **P&P**: `config/container_state.py`
- **Switch-Hermes**: `config/switch_hermes_integration.py`

---

**VX11 v6.0 — P&P + Adaptive Routing Ready.** ⚡
