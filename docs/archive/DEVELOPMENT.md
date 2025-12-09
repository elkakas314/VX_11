# VX11 v5.0 — DEVELOPMENT GUIDE

## Setup Local (Python directo)

### Requisitos

- Python 3.11+
- pip
- SQLite3
- Docker (opcional, para producción)

### Instalación

1. **Clonar repo:**
   ```bash
   cd /home/elkakas314/vx11
   ```

2. **Crear venv (opcional pero recomendado):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # o en Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verificar sintaxis Python:**
   ```bash
   python3 -m compileall .
   ```

5. **Configurar variables de entorno:**
   ```bash
   cp tokens.env.sample tokens.env
   cp .env.example .env
   # Editar .env y tokens.env con valores reales (DEEPSEEK_API_KEY, etc.)
   ```

---

## Arranque Local (sin Docker)

### Opción 1: Arrancar todos los módulos (script)

```bash
chmod +x scripts/run_all_dev.sh
./scripts/run_all_dev.sh
```

Esto lanza 8 procesos `uvicorn` en background con `--reload` (hot reload habilitado).

### Opción 2: Arrancar módulo individual

```bash
# Terminal 1: Gateway
uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Madre
uvicorn madre.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3: Switch
uvicorn switch.main:app --host 0.0.0.0 --port 8002 --reload

# ... etc para los otros 5 módulos (puertos 8003–8007)
```

### Health checks

```bash
# Una vez que todo está corriendo:
for port in {8000..8007}; do
  echo "=== Checking port $port ==="
  curl -s http://localhost:$port/health | jq .
done
```

---

## Setup Docker

### Build

```bash
docker-compose build --no-cache
```

### Run

```bash
docker-compose up -d
```

### Logs

```bash
docker-compose logs -f                    # Ver logs de todos
docker-compose logs -f madre              # Solo Madre
docker-compose logs -f madre --tail 100   # Últimas 100 líneas
```

### Stop & Cleanup

```bash
docker-compose down
./scripts/cleanup.sh  # Limpia volúmenes (CUIDADO: borra BD)
```

---

## Desarrollo

### Estructura de proyecto

```
vx11/
├── config/
│   ├── settings.py          # Configuración central
│   ├── db_schema.py         # Modelos SQLAlchemy
│   ├── module_template.py   # Plantilla base para módulos
│   ├── deepseek.py          # Integración R1 Deepseek
│   ├── forensics.py         # Utilidades de auditoría
│   └── tokens.py            # Carga de tokens desde env
├── gateway/main.py          # Orquestador
├── madre/main.py            # Tareas autónomas
├── switch/main.py           # Router IA
├── hermes/main.py           # Ejecutor CLIs
├── hormiguero/main.py       # Paralelización
├── manifestator/main.py     # Auditoría
├── mcp/main.py              # Conversacional
├── shubniggurath/main.py    # Procesamiento IA
├── tests/                   # Unit tests
├── scripts/
│   ├── run_all_dev.sh
│   ├── stop_all_dev.sh
│   ├── restart_all_dev.sh
│   └── cleanup.sh
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── tokens.env.sample
└── .gitignore
```

### Agregar un módulo nuevo

1. Crear directorio:
   ```bash
   mkdir nuevo_modulo
   ```

2. Crear `nuevo_modulo/main.py`:
   ```python
   from fastapi import FastAPI
   from config.settings import settings
   
   app = FastAPI(title="Nuevo Módulo")
   
   @app.get("/health")
   async def health():
       return {"status": "healthy"}
   
   @app.get("/nuevo_modulo/info")
   async def info():
       return {"module": "nuevo_modulo", "port": 8008}
   ```

3. Elegir puerto (ej. 8008) y agregar a `config/settings.py`:
   ```python
   nuevo_modulo_port = 8008
   ```

4. Actualizar `gateway/main.py` en dict `PORTS`:
   ```python
   PORTS = {
       ...
       "nuevo_modulo": settings.nuevo_modulo_port,
   }
   ```

5. Agregar entrada a `docker-compose.yml`:
   ```yaml
   nuevo_modulo:
     build: ./nuevo_modulo
     ports:
       - "8008:8008"
     environment:
       - PORT=8008
     networks:
       - vx11-network
     mem_limit: 512m
     healthcheck:
       test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
       interval: 30s
   ```

6. Crear `nuevo_modulo/Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY . .
   CMD ["uvicorn", "nuevo_modulo.main:app", "--host", "0.0.0.0", "--port", "8008"]
   HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
     CMD curl -f http://localhost:8008/health || exit 1
   ```

7. Testar:
   ```bash
   uvicorn nuevo_modulo.main:app --port 8008 --reload
   curl http://localhost:8008/health
   ```

### Escribir tests

```bash
# Localización: tests/test_madre.py (ejemplo)
import pytest
from madre.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_task():
    response = client.post("/task", json={
        "title": "Test",
        "task_type": "test",
        "priority": 1
    })
    assert response.status_code == 200
    assert "task_id" in response.json()

# Correr:
pytest tests/test_madre.py -v
```

---

## Manifestator + VS Code Integration

### Endpoints clave

Ver `docs/API_REFERENCE.md` para detalles completos. Resumen:

- `GET /drift` — detectar cambios en módulos
- `POST /generate-patch` — generar patch con sugerencias IA
- `POST /apply-patch` — aplicar cambios (con rollback)

### Usar desde VS Code

#### Opción 1: Curl en Terminal

```bash
# Detectar drift en todos los módulos
curl http://localhost:8005/drift | jq .

# Detectar drift solo en Madre
curl "http://localhost:8005/drift?module=madre" | jq .

# Generar patch
curl -X POST http://localhost:8005/generate-patch \
  -H "Content-Type: application/json" \
  -d '{
    "module": "madre",
    "auto_suggest": true
  }' | jq .

# Aplicar patch (después de revisar)
curl -X POST http://localhost:8005/apply-patch \
  -H "Content-Type: application/json" \
  -d '{
    "patch_id": "patch-001",
    "validate": true,
    "rollback_on_error": true
  }' | jq .
```

#### Opción 2: VS Code REST Client (.rest file)

Crear `test.rest` (o similar):

```http
### Drift Detection
GET http://localhost:8005/drift

### Drift in Madre
GET http://localhost:8005/drift?module=madre

### Generate Patch
POST http://localhost:8005/generate-patch
Content-Type: application/json

{
  "module": "madre",
  "auto_suggest": true
}

### Apply Patch
POST http://localhost:8005/apply-patch
Content-Type: application/json

{
  "patch_id": "patch-001",
  "validate": true,
  "rollback_on_error": true
}
```

Usar extensión REST Client de VS Code (`⌘/Ctrl + ⇧ + P` → "Rest Client: Send Request").

#### Opción 3: MCP Chat (Copilot)

Usar `docs/FLOWS.md` para prompts sugeridos en Copilot Chat:

```
"Verificar drift en VX11 usando Manifestator:
- Endpoint: GET http://localhost:8005/drift
- Parsear respuesta JSON
- Si hay drifts, generar patch con POST /generate-patch
- Sugerir al usuario aplicar o descartar"
```

---

## Monitoring & Debugging

### Logs

```bash
# Locales (sin Docker):
tail -f logs/madre.log
tail -f logs/switch.log

# Docker:
docker-compose logs -f madre
docker-compose logs -f switch
```

### Database queries

```bash
# Acceder a SQLite directamente
sqlite3 data/madre.db

# Ver tablas
.tables

# Consulta típica:
SELECT * FROM tasks LIMIT 5;
SELECT * FROM ia_decisions LIMIT 10;
```

### Health & Metrics

```bash
# Gateway status completo
curl http://localhost:8000/vx11/status | jq .

# Hermes jobs activos
curl http://localhost:8003/hermes/jobs | jq .

# Colonia hormiguero
curl http://localhost:8004/hormiguero/colony/status | jq .

# Providers en Switch
curl http://localhost:8002/switch/providers | jq .
```

---

## Performance & Ultra-Low-Memory

### Verificar uso de memoria

```bash
# Local:
ps aux | grep uvicorn

# Docker:
docker stats
```

### Límites

- Max por contenedor: 512MB
- Max por modelo: 256MB
- Limpieza de caché: cada 300s
- Evicción LRU si se excede límite

### Ajustar en settings.py

```python
ULTRA_LOW_MEMORY = True
MAX_MEMORY_MB = 512
MAX_MODEL_SIZE_MB = 256
CACHE_TTL_SECONDS = 300
```

---

## CI/CD (future)

Estructura preparada para:
- GitHub Actions: test + lint en PRs
- Docker Hub push en releases
- Rollback automático si health checks fallan

---

## Troubleshooting

### Problema: "Port already in use"
```bash
# Encontrar y matar proceso
lsof -i :8001
kill -9 <PID>
```

### Problema: "ModuleNotFoundError"
```bash
# Asegurar que estás en venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Problema: BD corrupta
```bash
# Backup + reset
cp data/madre.db data/madre.db.bak
rm data/madre.db  # Se recreará automáticamente en el siguiente init
```

### Problema: Docker build falla
```bash
# Limpiar caché + rebuildar
docker-compose build --no-cache --force-rm
```

---

## Convenciones de código

- **Naming:** snake_case para funciones/variables, PascalCase para clases
- **Docstrings:** Usar Google-style docstrings
- **Typing:** Usar type hints en todas las funciones
- **Imports:** Organizar: stdlib, third-party, local
- **Linting:** (futuro) black + flake8 + mypy

---

## Recursos

- FastAPI docs: https://fastapi.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Docker docs: https://docs.docker.com/
- VX11 Architecture: `docs/ARCHITECTURE.md`
- VX11 API Reference: `docs/API_REFERENCE.md`
- VX11 Flows: `docs/FLOWS.md`

---

**VX11 v5.0 Development Guide — Local setup, testing, debugging, integración.**
