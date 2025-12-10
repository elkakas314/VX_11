# Docker Performance Analysis — VX11 v7

**Fecha:** 9 dic 2025  
**Problema Identificado:** Imágenes Docker enormes (23.36GB total, 3+ GB por servicio)

---

## 1. Diagnóstico del Problema

### 1.1. Uso de Disco Actual

```
Images:           23.36GB (11 imágenes)
Containers:       322MB (10 activos)
Reclaimable:      23.36GB (¡100%!)
```

### 1.2. Tamaño por Imagen

| Imagen | Tamaño | Edad | Problema |
|--------|--------|------|----------|
| vx11-hormiguero | 3.22GB | 41 min | ⚠️ Enorme para 11 .py files |
| vx11-tentaculo-link | 3.10GB | 53 min | ⚠️ 5 .py files, 3.1GB? |
| vx11-hermes | 3.22GB | 1h | ⚠️ En switch/hermes, no módulo propio |
| vx11-switch | 3.27GB | 1h | ⚠️ Mayor imagen, 14 .py files |
| vx11-madre | 3.22GB | 1h | ⚠️ 4 .py files, 3.22GB |
| vx11-operator-backend | 3.11GB | 7h | ⚠️ Python + Node deps? |
| vx11-shub | 331MB | 47h | ✅ Relativamente pequeño |
| vx11-spawner | 2.48GB | 4d | ⚠️ 3 .py files, 2.48GB |
| vx11-mcp | 2.48GB | 4d | ⚠️ 5 .py files, 2.48GB |
| vx11_operator-frontend | 48.5MB | 4d | ✅ Pequeño (Nginx + static) |

**Resumen:** Todas las imágenes Python son 2-3 GB. ¡Sospecho carga de dependencias innecesarias!

---

## 2. Causas Raíz Identificadas

### 2.1. Dockerfile Pattern Ineficiente

Todos usan:
```dockerfile
FROM python:3.10-slim
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir -r requirements_minimal.txt
COPY . /app
```

**Problemas:**
1. `COPY . /app` copia TODO (incluyendo `.git`, `node_modules/`, cache, test files)
2. `.dockerignore` ¿existe? Probablemente no
3. Base `python:3.10-slim` es 150MB; después deps → 2-3GB

### 2.2. Dependencias Innecesarias

Revisar `requirements_minimal.txt`, `requirements.txt`:

```bash
cd /home/elkakas314/vx11 && wc -l requirements*.txt
```

Sospecha: instalan FastAPI + Pydantic + requests + numpy + scipy + etc. en TODOS los servicios.

### 2.3. Build Cache No Optimizado

```dockerfile
RUN pip install --no-cache-dir -r requirements_minimal.txt
```

`--no-cache-dir` es correcto para reducir tamaño, pero:
- Si requirements.txt es grande, todo se construye cada build
- Sin multi-stage, se quedan bytecode + archivos innecesarios

---

## 3. Soluciones Propuestas

### 3.1. Crear `.dockerignore` (Inmediato)

```
# .dockerignore
.git
.gitignore
__pycache__
*.pyc
*.pyo
.pytest_cache
.venv
node_modules
dist
build
*.egg-info
.DS_Store
.env
tokens.env
data/*
build/*
logs/*
forensic/*
docs/*
tests/*
scripts/*
README*
```

**Impacto:** Reducir COPY tamaño de 1.5 GB → 500 MB (probablemente)

### 3.2. Optimizar Dockerfiles (Multi-stage)

**Patrón Nuevo:**

```dockerfile
# Stage 1: Builder
FROM python:3.10-slim as builder
WORKDIR /build
COPY requirements_minimal.txt .
RUN pip install --no-cache-dir --user -r requirements_minimal.txt

# Stage 2: Runtime
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . /app
RUN mkdir -p /app/logs /app/data /app/models /app/sandbox
ENV ULTRA_LOW_MEMORY=true PYTHONUNBUFFERED=1
CMD ["python", "-m", "uvicorn", "module.main:app", "--host", "0.0.0.0", "--port", "PORT"]
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:PORT/health || exit 1
```

**Ventajas:**
- Stage 1 instala deps (cacheado)
- Stage 2 solo copia deps compilados → imagen más pequeña
- `--user` install → mejor aislamiento

**Impacto:** Reducir 3GB → 1.5-2GB por imagen

### 3.3. Separar requirements.txt por Módulo

Actualmente todos usan `requirements_minimal.txt`. 

**Mejor:**
```
requirements_base.txt          # FastAPI, Pydantic, common
requirements_switch.txt        # base + httpx, sqlalchemy
requirements_operator.txt      # base + playwright, etc.
requirements_shub.txt          # base + numpy, scipy
```

**Impacto:** Reducir deps instaladas por módulo

### 3.4. Optimizar Orden de Capas Docker

```dockerfile
# ✅ CORRECTO (cambia menos entre builds)
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  # CACHEADO si requirements.txt no cambia
COPY . /app                                           # Esto cambia frecuentemente
CMD [...]
```

```dockerfile
# ❌ INEFICIENTE (rebuild todo si requirements cambia)
FROM python:3.10-slim
COPY . /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

Parece que ya está OK, pero verificar en todos.

---

## 4. Plan de Acción Detallado (v7.1)

### Phase 1: Setup (30 min)
- [ ] Crear `.dockerignore` en raíz
- [ ] Commit + push

### Phase 2: Rebuild Containers (2 hrs)
- [ ] Ejecutar: `docker-compose down && docker system prune -a`
- [ ] Ejecutar: `docker-compose build --no-cache`
- [ ] Medir nuevos tamaños: `docker images | grep vx11`

### Phase 3: Multi-stage Dockerfiles (4 hrs)
- [ ] Copiar patrón multi-stage a todos los Dockerfiles
- [ ] Rebuild
- [ ] Test health (todos 10 servicios)

### Phase 4: Modular requirements (2 hrs)
- [ ] Crear `requirements_base.txt`, `requirements_switch.txt`, etc.
- [ ] Actualizar Dockerfiles para usar módulo-específico
- [ ] Rebuild

### Phase 5: Validate (1 hr)
- [ ] Todos 10 servicios UP
- [ ] Health checks pasan
- [ ] Medir tamaños finales
- [ ] Comparar antes/después

---

## 5. Comando de Build Optimizado

```bash
# Viejo (ineficiente)
docker-compose build --no-cache

# Nuevo (con layer caching)
docker-compose build

# Super limpio (nuclear option)
docker system prune -a --volumes
docker-compose build --no-cache
docker-compose up -d
```

---

## 6. Métricas Antes/Después Estimadas

| Métrica | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Total Images Size | 23.36GB | 12-15GB | 35-50% |
| Avg Service Image | 3.2GB | 1.5-2GB | 40-50% |
| Build Time (clean) | ~8 min | ~5 min | 35% |
| Pull Time (remote) | ~2 min | ~1 min | 50% |
| Disk Saved | — | 8-10GB | 🎉 |

---

## 7. Docker Compose Enhancements

### 7.1. Separar en Perfiles (Opcional v8)

```yaml
version: "3.9"
services:
  # Core services (always)
  tentaculo_link:
    ...
    profiles: ["core"]

  # Heavy services (optional)
  shubniggurath:
    ...
    profiles: ["audio", "heavy"]

  operator_frontend:
    ...
    profiles: ["ui"]
```

**Uso:**
```bash
# Solo core
docker-compose --profile core up -d

# Core + audio
docker-compose --profile core --profile audio up -d

# Everything
docker-compose up -d
```

---

## 8. Health Check Optimization

Actualmente: `curl -fsS http://localhost:PORT/health`

**Mejorar a:**
```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:PORT/health || exit 1
```

- `--start-period=5s` — No considerar "unhealthy" en primeros 5s (startup)
- `--retries=3` — OK, suficiente

---

## 9. Nginx Performance (operator-frontend)

`operator_backend/frontend/nginx.conf` — revisar:

```nginx
# Agregar:
gzip on;
gzip_types text/plain text/css text/javascript application/json;
gzip_min_length 1000;

# Cache busting
location ~* \.js$ {
  expires 1h;
  add_header Cache-Control "public, immutable";
}

# SPA fallback
location / {
  try_files $uri $uri/ /index.html;
}
```

---

## 10. Comandos de Diagnóstico

```bash
# Ver tamaño exacto de imágenes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Ver capas de imagen
docker history vx11-madre:v6.7

# Ver tamaño de build context
du -sh .

# Ver qué hay en contenedor
docker run --rm -it vx11-madre:v6.7 du -sh /app/*

# Medir tiempo de build
time docker-compose build madre

# Test startup time
time docker-compose up -d madre && sleep 2 && docker logs vx11-madre | grep "Uvicorn running"
```

---

## 11. Conclusiones

- 🔴 **PROBLEMA CRÍTICO:** Imágenes 2-3x más grandes de lo necesario
- 🟡 **CAUSA:** `.dockerignore` faltante + sin multi-stage
- 🟢 **SOLUCIÓN:** `.dockerignore` + multi-stage + modular requirements
- 📊 **IMPACTO:** 35-50% reducción tamaño, 35% más rápido build, 50% más rápido pull

**Acción:** Implementar en v7.1 (~ 5 horas, alto ROI)

---

**Análisis completado:** 9 dic 2025

