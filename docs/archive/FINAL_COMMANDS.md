# VX11 v5.0 — FINAL COMMANDS & VALIDATION

Este documento contiene todos los comandos para **validar, compilar, construir, levantar y verificar** VX11 v5.0. **NO se ejecutan automáticamente** — solo se documentan para uso manual.

---

## Fase 0: Pre-requisitos

### 0.1 Verificar Python

```bash
# Mostrar versión
python3 --version
# Esperado: Python 3.11.x o superior

# Verificar pip
pip --version
```

### 0.2 Verificar Docker

```bash
# Mostrar versión
docker --version
# Esperado: Docker 20.10+

# Verificar docker-compose
docker-compose --version
# Esperado: Docker Compose 1.29+

# Verificar que el daemon está activo
docker ps
```

### 0.3 Verificar Variables de Entorno

```bash
# Cargar tokens (requerido para algunos módulos)
source tokens.env
# o
export $(cat tokens.env | xargs)

# Verificar que DEEPSEEK_API_KEY está cargada
echo $DEEPSEEK_API_KEY
# Debe mostrar: sk-...
```

---

## Fase 1: Validación Estática

### 1.1 Compilación Python (sintaxis)

```bash
# Compilar todos los archivos .py
python3 -m compileall .

# Comando alternativo (más detalles):
python3 -m py_compile *.py config/*.py gateway/*.py madre/*.py switch/*.py hermes/*.py hormiguero/*.py manifestator/*.py mcp/*.py shubniggurath/*.py

# Salida esperada:
# Compiling ...
# Compiling ... 
# (sin errores)
```

### 1.2 Linting (Opcional, si está instalado pylint/flake8)

```bash
# Revisar sintaxis y style
flake8 config/ gateway/ madre/ switch/ hermes/ hormiguero/ manifestator/ mcp/ shubniggurath/ --max-line-length=120

# O con pylint
pylint config/settings.py --disable=all --enable=E,F
```

### 1.3 Tipo de datos (Opcional, si está instalado mypy)

```bash
# Verificar type hints
mypy config/settings.py --ignore-missing-imports

# Contra toda la carpeta:
mypy . --ignore-missing-imports
```

---

## Fase 2: Verificación de Archivos

### 2.1 Verificar estructura de directorios

```bash
# Listar estructura
ls -la .

# Verificar que existen todos los módulos
test -d config && echo "✓ config/" || echo "✗ config/ falta"
test -d gateway && echo "✓ gateway/" || echo "✗ gateway/ falta"
test -d madre && echo "✓ madre/" || echo "✗ madre/ falta"
test -d switch && echo "✓ switch/" || echo "✗ switch/ falta"
test -d hermes && echo "✓ hermes/" || echo "✗ hermes/ falta"
test -d hormiguero && echo "✓ hormiguero/" || echo "✗ hormiguero/ falta"
test -d manifestator && echo "✓ manifestator/" || echo "✗ manifestator/ falta"
test -d mcp && echo "✓ mcp/" || echo "✗ mcp/ falta"
test -d shubniggurath && echo "✓ shubniggurath/" || echo "✗ shubniggurath/ falta"
test -d docs && echo "✓ docs/" || echo "✗ docs/ falta"
test -d scripts && echo "✓ scripts/" || echo "✗ scripts/ falta"

# Verificar archivos críticos
test -f docker-compose.yml && echo "✓ docker-compose.yml" || echo "✗ falta"
test -f requirements.txt && echo "✓ requirements.txt" || echo "✗ falta"
test -f .gitignore && echo "✓ .gitignore" || echo "✗ falta"
test -f .env.example && echo "✓ .env.example" || echo "✗ falta"
test -f tokens.env.sample && echo "✓ tokens.env.sample" || echo "✗ falta"
```

### 2.2 Verificar permisos de scripts

```bash
# Asegurar que scripts son ejecutables
chmod +x scripts/run_all_dev.sh
chmod +x scripts/stop_all_dev.sh
chmod +x scripts/restart_all_dev.sh
chmod +x scripts/cleanup.sh

# Verificar
ls -la scripts/
# Esperado: -rwxr-xr-x ... scripts/run_all_dev.sh
```

### 2.3 Verificar documentación

```bash
# Verificar que todos los .md existen
test -f docs/ARCHITECTURE.md && echo "✓ docs/ARCHITECTURE.md" || echo "✗ falta"
test -f docs/API_REFERENCE.md && echo "✓ docs/API_REFERENCE.md" || echo "✗ falta"
test -f docs/DEVELOPMENT.md && echo "✓ docs/DEVELOPMENT.md" || echo "✗ falta"
test -f docs/FLOWS.md && echo "✓ docs/FLOWS.md" || echo "✗ falta"
test -f docs/MANIFESTATOR_INTEGRATION.md && echo "✓ docs/MANIFESTATOR_INTEGRATION.md" || echo "✗ falta"
```

---

## Fase 3: Validación de Configuración

### 3.1 Verificar config/settings.py

```bash
# Verificar que settings.py compila
python3 -c "from config.settings import settings; print(f'Puertos: {settings.gateway_port}-{settings.shub_port}')"

# Salida esperada: Puertos: 8000-8007
```

### 3.2 Verificar imports

```bash
# Verificar que todos los módulos importan settings correctamente
python3 -c "from gateway.main import app; print('✓ gateway imports OK')"
python3 -c "from madre.main import app; print('✓ madre imports OK')"
python3 -c "from switch.main import app; print('✓ switch imports OK')"
python3 -c "from switch.hermes.main import app; print('✓ hermes imports OK')"
python3 -c "from hormiguero.main import app; print('✓ hormiguero imports OK')"
python3 -c "from manifestator.main import app; print('✓ manifestator imports OK')"
python3 -c "from mcp.main import app; print('✓ mcp imports OK')"
python3 -c "from shubniggurath.main import app; print('✓ shubniggurath imports OK')"
```

### 3.3 Verificar docker-compose.yml

```bash
# Validar sintaxis del docker-compose
docker-compose config

# Salida esperada: YAML válido, lista de servicios (gateway, madre, ..., shub)
```

---

## Fase 4: Build Docker

### 4.1 Build de imágenes

```bash
# Build completo con no-cache
docker-compose build --no-cache

# Salida esperada:
# Building gateway ... done
# Building madre ... done
# ... etc para 8 servicios
```

### 4.2 Verificar imágenes construidas

```bash
# Listar imágenes
docker images | grep vx11

# Salida esperada:
# vx11-gateway       latest      ...
# vx11-madre         latest      ...
# ... etc para 8 servicios
```

---

## Fase 5: Levantamiento del Sistema

### 5.1 Opción A: Levantar con Docker (Producción/Recomendado)

```bash
# Levantar todos los servicios en background
docker-compose up -d

# Salida esperada:
# Creating vx11_gateway_1 ... done
# Creating vx11_madre_1 ... done
# ... etc para 8 servicios
```

### 5.2 Opción B: Levantar locales (Desarrollo)

```bash
# Terminal 1: Gateway
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload

# Esperar "Uvicorn running on http://0.0.0.0:8000"

# Terminal 2: Madre
uvicorn madre.main:app --host 0.0.0.0 --port 8001 --reload

# ... repetir para los 6 módulos restantes en terminales separadas
# Puertos: 8002 (switch), 8003 (hermes), 8004 (hormiguero), 8005 (manifestator), 8006 (mcp), 8007 (shub)
```

### 5.3 Esperar a que estén listos

```bash
# Esperar 10-15 segundos para que todos los contenedores inicien
sleep 15

# O verificar manualmente cada pocos segundos
docker-compose logs --tail 50 -f
```

---

## Fase 6: Health Checks

### 6.1 Health de gateway

```bash
curl http://localhost:8000/health
```

**Salida esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-30T10:30:00Z"
}
```

### 6.2 Health check batch (todos los módulos)

```bash
# Verificar todos los puertos 8000-8007
for port in {8000..8007}; do
  echo "=== Port $port ==="
  curl -s http://localhost:$port/health | jq . || echo "✗ Port $port FAILED"
done
```

**Salida esperada:**
```
=== Port 8000 ===
{
  "status": "healthy"
}
=== Port 8001 ===
{
  "status": "healthy"
}
... etc para puertos 8002-8007
```

### 6.3 Gateway status

```bash
curl http://localhost:8000/vx11/status | jq .
```

**Salida esperada:**
```json
{
  "gateway": "running",
  "modules": {
    "madre": 8001,
    "switch": 8002,
    "hermes": 8003,
    "hormiguero": 8004,
    "manifestator": 8005,
    "mcp": 8006,
    "shub": 8007
  }
}
```

### 6.4 Verificar logs

```bash
# Ver logs de todos
docker-compose logs -f

# Ver logs de un módulo específico
docker-compose logs -f madre

# Últimas 100 líneas
docker-compose logs --tail 100 madre

# Sin seguimiento (salida estática)
docker-compose logs madre
```

---

## Fase 7: Pruebas Funcionales

### 7.1 Crear tarea en Madre

```bash
curl -X POST http://localhost:8001/task \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Testing VX11",
    "task_type": "test",
    "priority": 1,
    "context": {}
  }' | jq .
```

**Salida esperada:**
```json
{
  "task_id": "uuid-...",
  "status": "created",
  "created_at": "2025-01-30T10:30:00Z"
}
```

### 7.2 Listar providers en Switch

```bash
curl http://localhost:8002/switch/providers | jq .
```

**Salida esperada:**
```json
{
  "providers": [
    {
      "name": "deepseek",
      "model": "deepseek-r1",
      "latency_ms": 250,
      "success_rate": 0.98,
      "available": true
    },
    ...
  ]
}
```

### 7.3 Detectar CLIs en Hermes

```bash
curl http://localhost:8003/hermes/available | jq .
```

**Salida esperada:**
```json
{
  "clis": [
    {"name": "python", "version": "3.11.0", "path": "/usr/bin/python3"},
    ...
  ],
  "total": 45
}
```

### 7.4 Detectar drift en Manifestator

```bash
curl http://localhost:8005/drift | jq .
```

**Salida esperada:**
```json
{
  "scan_timestamp": "2025-01-30T10:30:00Z",
  "modules_analyzed": [...],
  "drifts": [],
  "total_drifts": 0,
  "critical_drifts": 0
}
```

### 7.5 Enviar mensaje a MCP

```bash
curl -X POST http://localhost:8006/mcp/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "message": "Health check"
  }' | jq .
```

---

## Fase 8: Limpieza & Shutdown

### 8.1 Parar servicios (Docker)

```bash
# Detener todos los contenedores (mantiene volúmenes)
docker-compose down

# Salida esperada:
# Stopping vx11_shub_1 ... done
# Stopping vx11_mcp_1 ... done
# ... etc
# Removing vx11_... network vx11-network
```

### 8.2 Limpiar volúmenes (CUIDADO: borra datos)

```bash
# Remover volúmenes (BD, logs, etc.)
docker volume prune -f

# O usar script:
./scripts/cleanup.sh
```

### 8.3 Verificar estado

```bash
# Verificar que no quedan contenedores
docker ps -a | grep vx11
# Salida: (vacía, significa que todo está parado)
```

---

## Fase 9: Troubleshooting

### 9.1 Si un contenedor falla al iniciar

```bash
# Ver logs del contenedor
docker logs vx11_madre_1
# o
docker-compose logs madre

# Buscar línea de error
docker-compose logs madre 2>&1 | grep -i error

# Restart del contenedor
docker-compose restart madre
```

### 9.2 Si puerto está en uso

```bash
# Encontrar proceso usando puerto
lsof -i :8001
# o
netstat -tulpn | grep 8001

# Matar proceso
kill -9 <PID>

# Liberar en Docker
docker-compose down
docker system prune -f
```

### 9.3 Si BD está corrupta

```bash
# Backup
cp data/madre.db data/madre.db.bak

# Remover (se recreará en siguiente init)
rm data/madre.db

# Restart de servicios
docker-compose restart madre
```

### 9.4 Si hay problemas de memoria

```bash
# Ver uso de memoria
docker stats

# Ver logs de memory errors
docker-compose logs | grep -i memory

# Ajustar mem_limit en docker-compose.yml si es necesario
# (por defecto: 512m)
```

---

## Fase 10: Validación Final

### 10.1 Checklist Completo

```bash
#!/bin/bash
echo "=== VX11 v5.0 Final Validation Checklist ==="

echo "✓ 1. Verificar Python..." && python3 --version
echo "✓ 2. Verificar Docker..." && docker --version
echo "✓ 3. Compilar Python..." && python3 -m compileall . > /dev/null && echo "  OK"
echo "✓ 4. Validar docker-compose..." && docker-compose config > /dev/null && echo "  OK"
echo "✓ 5. Verificar imágenes..." && docker images | grep vx11 | wc -l && echo "  servicios"

echo ""
echo "=== Sistema Levantado ==="
docker ps --filter "name=vx11" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "=== Health Checks ==="
for port in {8000..8007}; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health)
  if [ "$STATUS" == "200" ]; then
    echo "✓ Port $port: OK"
  else
    echo "✗ Port $port: FAILED (HTTP $STATUS)"
  fi
done

echo ""
echo "=== Validación Completa ==="
echo "✓ Todos los servicios están activos"
echo "✓ Health checks satisfactorios"
echo "✓ Sistema listo para uso"
```

---

## Resumen de Comandos Más Usados

```bash
# Compilar
python3 -m compileall .

# Validar Docker
docker-compose config

# Construir
docker-compose build --no-cache

# Levantar
docker-compose up -d

# Ver logs
docker-compose logs -f madre

# Health check
curl http://localhost:8000/health

# Status completo
curl http://localhost:8000/vx11/status | jq .

# Parar
docker-compose down

# Limpiar
./scripts/cleanup.sh
```

---

## Documentación Asociada

- **ARCHITECTURE.md** — Arquitectura completa de VX11
- **API_REFERENCE.md** — Todos los endpoints
- **DEVELOPMENT.md** — Guía de desarrollo local
- **FLOWS.md** — 10 diagramas de flujo
- **MANIFESTATOR_INTEGRATION.md** — Integración auditoría + VS Code

---

**VX11 v5.0 — Comandos de validación, construcción, levantamiento y verificación.**

*Nota: Este documento es una referencia. Ejecutar comandos de forma manual según necesidad.*
