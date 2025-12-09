# VX11 v5.0 — MANIFESTATOR INTEGRATION & VS CODE

## Visión General

**Manifestator** es el módulo de auditoría, detección de cambios (drift detection) y generación automática de parches. Se ejecuta en puerto **8005** y se integra con **VS Code** a través de curl, REST Client, y MCP (Model Context Protocol).

---

## Arquitectura de Manifestator

```
Manifestator (Puerto 8005)
│
├─ Detector de Drift
│  ├─ Comparar módulos con baseline v5.0
│  ├─ Detectar cambios en código (.py)
│  └─ Registrar severidad (low, medium, high, critical)
│
├─ Generador de Parches
│  ├─ Crear diff automático
│  ├─ Sugerir fixes con IA (si auto_suggest=true)
│  └─ Persistir patch en BD con patch_id
│
├─ Validador
│  ├─ Verificar que el parche es válido
│  ├─ Correr tests (si existen)
│  └─ Confirmar que no rompe salud
│
└─ Aplicador
   ├─ Aplicar parche a archivo
   ├─ Rollback automático si falla
   └─ Registrar resultado en historial
```

---

## Endpoints Principales

Base URL: `http://localhost:8005`

### 1. GET /health
Verificar que Manifestator está activo.

**Request:**
```bash
curl http://localhost:8005/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-30T10:15:00Z"
}
```

---

### 2. GET /drift
Detectar cambios en módulos respecto a baseline.

**Request:**
```bash
# Todos los módulos
curl http://localhost:8005/drift

# Solo un módulo específico
curl "http://localhost:8005/drift?module=madre"

# Solo módulos críticos
curl "http://localhost:8005/drift?modules=madre,switch,hermes"
```

**Response:**
```json
{
  "scan_timestamp": "2025-01-30T10:15:00Z",
  "modules_analyzed": ["gateway", "madre", "switch"],
  "drifts": [
    {
      "module": "madre",
      "file": "madre/main.py",
      "line_start": 45,
      "line_end": 50,
      "change_type": "modification",
      "severity": "low",
      "description": "Cambio en lógica de routing",
      "suggestion": "Revisar lógica antes de aplicar"
    },
    {
      "module": "switch",
      "file": "switch/router_v4.py",
      "line_start": 120,
      "line_end": 125,
      "change_type": "modification",
      "severity": "medium",
      "description": "Nuevo scoring algorithm",
      "suggestion": "Validar con tests antes de aplicar"
    }
  ],
  "total_drifts": 2,
  "critical_drifts": 0,
  "recommendation": "Revisar y aplicar parches con validación"
}
```

---

### 3. POST /generate-patch
Generar parche para cambios detectados.

**Request:**
```bash
# Generar patch automático sin sugerencias IA
curl -X POST http://localhost:8005/generate-patch \
  -H "Content-Type: application/json" \
  -d '{
    "module": "madre",
    "auto_suggest": false
  }'

# Con sugerencias IA (requiere DEEPSEEK_API_KEY)
curl -X POST http://localhost:8005/generate-patch \
  -H "Content-Type: application/json" \
  -d '{
    "module": "madre",
    "auto_suggest": true,
    "include_reason": true
  }'

# Para múltiples cambios
curl -X POST http://localhost:8005/generate-patch \
  -H "Content-Type: application/json" \
  -d '{
    "modules": ["madre", "switch"],
    "auto_suggest": true
  }'
```

**Response:**
```json
{
  "patch_id": "patch-20250130-001",
  "module": "madre",
  "created_at": "2025-01-30T10:15:00Z",
  "patch_content": "--- madre/main.py.orig\n+++ madre/main.py\n@@ -45,5 +45,5 @@\n-    old_code = True\n+    new_code = False\n",
  "changes_count": 1,
  "auto_suggestion": {
    "ai_reasoning": "Cambio aparentemente intencional. Ajuste lógico sin impacto crítico.",
    "confidence": 0.87,
    "recommendation": "SAFE_TO_APPLY"
  },
  "validation_status": "pending",
  "applicable": true
}
```

---

### 4. POST /apply-patch
Aplicar un parche generado.

**Request:**
```bash
# Aplicar con validación automática
curl -X POST http://localhost:8005/apply-patch \
  -H "Content-Type: application/json" \
  -d '{
    "patch_id": "patch-20250130-001",
    "validate": true,
    "rollback_on_error": true,
    "dry_run": false
  }'

# Dry-run: ver qué sucedería sin cambiar nada
curl -X POST http://localhost:8005/apply-patch \
  -H "Content-Type: application/json" \
  -d '{
    "patch_id": "patch-20250130-001",
    "validate": true,
    "rollback_on_error": true,
    "dry_run": true
  }'
```

**Response:**
```json
{
  "patch_id": "patch-20250130-001",
  "module": "madre",
  "status": "applied_successfully",
  "applied_at": "2025-01-30T10:16:00Z",
  "changes_applied": 1,
  "validation_passed": true,
  "health_check": {
    "module": "madre",
    "status": "healthy",
    "uptime": 3600
  },
  "rollback_available": true,
  "dry_run": false,
  "message": "Parche aplicado exitosamente. Sistema estable."
}
```

---

### 5. GET /patches
Obtener histórico de parches aplicados.

**Request:**
```bash
# Todos los parches
curl http://localhost:8005/patches

# Filtrar por módulo
curl "http://localhost:8005/patches?module=madre"

# Filtrar por estado
curl "http://localhost:8005/patches?status=applied"

# Últimos 10 parches
curl "http://localhost:8005/patches?limit=10&offset=0"
```

**Response:**
```json
{
  "total": 15,
  "patches": [
    {
      "patch_id": "patch-20250130-001",
      "module": "madre",
      "status": "applied_successfully",
      "created_at": "2025-01-30T10:15:00Z",
      "applied_at": "2025-01-30T10:16:00Z",
      "changes": 1,
      "rollback_available": true
    },
    {
      "patch_id": "patch-20250130-000",
      "module": "switch",
      "status": "applied_successfully",
      "created_at": "2025-01-30T09:30:00Z",
      "applied_at": "2025-01-30T09:31:00Z",
      "changes": 2,
      "rollback_available": false
    }
  ]
}
```

---

### 6. POST /rollback-patch
Revertir un parche aplicado.

**Request:**
```bash
curl -X POST http://localhost:8005/rollback-patch \
  -H "Content-Type: application/json" \
  -d '{
    "patch_id": "patch-20250130-001"
  }'
```

**Response:**
```json
{
  "patch_id": "patch-20250130-001",
  "status": "rolled_back",
  "rolled_back_at": "2025-01-30T10:20:00Z",
  "module": "madre",
  "changes_reverted": 1,
  "validation": {
    "module_health": "healthy",
    "status": "OK"
  }
}
```

---

## Integración con VS Code

### Opción 1: Usar REST Client Extension

1. **Instalar extensión** (si no está):
   - Ctrl/Cmd + Shift + P → "Extensions: Install Extensions"
   - Buscar "REST Client" (Huachao Mao)
   - Instalar

2. **Crear archivo `test.rest`** en raíz (ya existe):
   ```http
   ### Drift Detection
   GET http://localhost:8005/drift

   ### Drift in Madre only
   GET http://localhost:8005/drift?module=madre

   ### Generate Patch (Madre)
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
     "patch_id": "patch-20250130-001",
     "validate": true,
     "rollback_on_error": true,
     "dry_run": false
   }

   ### List Patches
   GET http://localhost:8005/patches

   ### List Patches for Madre
   GET http://localhost:8005/patches?module=madre
   ```

3. **Usar**: 
   - Click en "Send Request" (encima de cada bloque)
   - O: Ctrl/Cmd + Alt + R

---

### Opción 2: Usar Terminal Integrada con curl

1. **Abrir terminal** en VS Code: `` Ctrl/Cmd + ` ``

2. **Ejecutar comandos:**
   ```bash
   # Detectar drift
   curl http://localhost:8005/drift | jq .

   # Generar patch
   curl -X POST http://localhost:8005/generate-patch \
     -H "Content-Type: application/json" \
     -d '{"module":"madre","auto_suggest":true}' | jq .

   # Aplicar patch
   curl -X POST http://localhost:8005/apply-patch \
     -H "Content-Type: application/json" \
     -d '{"patch_id":"patch-20250130-001","validate":true}' | jq .
   ```

---

### Opción 3: Usar MCP (Model Context Protocol)

Si se integra con Copilot Chat en VS Code:

**Prompt sugerido:**
```
"Verificar drift en VX11 usando Manifestator:
1. GET http://localhost:8005/drift → detectar cambios
2. Analizar drifts retornados
3. Si hay cambios low/medium:
   - POST http://localhost:8005/generate-patch con auto_suggest=true
   - Mostrar AI suggestions
4. Preguntar al usuario si desea aplicar
5. Si sí:
   - POST http://localhost:8005/apply-patch con dry_run=true (primero)
   - Mostrar resultados
   - Si OK, aplicar sin dry_run"
```

**Invocar:**
- Abrir Copilot Chat (Ctrl/Cmd + Shift + I en VS Code)
- Pegar prompt o escribir: "Manifestator: check drift"
- Agent ejecutará el flujo automáticamente

---

## Ejemplos Prácticos

### Caso 1: Detectar y Revisar Cambios

```bash
#!/bin/bash

echo "=== Manifestator: Drift Detection ==="

# Paso 1: Detectar drift
echo "1. Detectando cambios..."
DRIFT=$(curl -s http://localhost:8005/drift)
echo "$DRIFT" | jq .

# Paso 2: Extraer severidad
CRITICAL=$(echo "$DRIFT" | jq '.critical_drifts')
echo "Drifts críticos: $CRITICAL"

if [ "$CRITICAL" -gt 0 ]; then
  echo "⚠️ Se encontraron cambios críticos. Revisar antes de aplicar."
else
  echo "✓ No hay cambios críticos. Seguro para proceder."
fi
```

### Caso 2: Generar y Aplicar Patch (Automático)

```bash
#!/bin/bash

MODULE=${1:-madre}
echo "=== Manifestator: Auto-Patch for $MODULE ==="

# Paso 1: Generar patch
echo "1. Generando parche para $MODULE..."
PATCH=$(curl -s -X POST http://localhost:8005/generate-patch \
  -H "Content-Type: application/json" \
  -d "{\"module\":\"$MODULE\",\"auto_suggest\":true}")

PATCH_ID=$(echo "$PATCH" | jq -r '.patch_id')
echo "Patch ID: $PATCH_ID"

# Paso 2: Mostrar sugerencias IA
AI_SUGGESTION=$(echo "$PATCH" | jq '.auto_suggestion.recommendation')
echo "Recomendación IA: $AI_SUGGESTION"

# Paso 3: Aplicar si es seguro
if [ "$AI_SUGGESTION" == "\"SAFE_TO_APPLY\"" ]; then
  echo "2. Aplicando parche..."
  RESULT=$(curl -s -X POST http://localhost:8005/apply-patch \
    -H "Content-Type: application/json" \
    -d "{\"patch_id\":\"$PATCH_ID\",\"validate\":true,\"rollback_on_error\":true}")
  
  STATUS=$(echo "$RESULT" | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" == "applied_successfully" ]; then
    echo "✓ Parche aplicado exitosamente"
  else
    echo "✗ Error al aplicar parche"
  fi
else
  echo "⚠️ Recomendación IA: NO aplicar. Revisar manualmente."
fi
```

### Caso 3: Dry-Run (Simular Cambios)

```bash
#!/bin/bash

PATCH_ID=${1:-patch-20250130-001}

echo "=== Manifestator: Dry-Run para $PATCH_ID ==="

curl -s -X POST http://localhost:8005/apply-patch \
  -H "Content-Type: application/json" \
  -d "{
    \"patch_id\":\"$PATCH_ID\",
    \"validate\":true,
    \"rollback_on_error\":true,
    \"dry_run\":true
  }" | jq .

echo "Nota: Dry-run=true, no se aplicarán cambios reales."
```

---

## Flujo Típico en VS Code

### Workflow Manual

1. **Terminal**: Abrir (`Ctrl/Cmd + ` `)
2. **Detectar**:
   ```bash
   curl http://localhost:8005/drift | jq .
   ```
3. **Revisar**: Leer cambios detectados
4. **REST Client** (`test.rest`):
   - Ir a sección "Generate Patch"
   - Click "Send Request"
   - Revisar sugerencias IA
5. **Editar** (si necesario):
   - Abrir archivo sugerido en VS Code
   - Verificar cambios propuestos
6. **Aplicar**:
   - REST Client: sección "Apply Patch"
   - Click "Send Request" con `dry_run=true` primero
   - Si OK, cambiar a `dry_run=false` y re-ejecutar

### Workflow Automático (Copilot)

1. **Abrir Copilot Chat** (Ctrl/Cmd + Shift + I)
2. **Escribir**:
   ```
   "Usa Manifestator para detectar cambios en madre, generar y aplicar parches si es seguro"
   ```
3. **Copilot**:
   - Ejecutará curl automáticamente
   - Analizará drift
   - Generará patch con IA
   - Aplicará si es seguro
   - Reportará resultados

---

## Configuración en settings.py

```python
# Auto-patch configuration
MANIFESTATOR_AUTO_SCAN_ENABLED = True
MANIFESTATOR_SCAN_INTERVAL_MINUTES = 10

# Parches
MANIFESTATOR_AUTO_PATCH_ENABLED = False  # Requiere confirmación manual
MANIFESTATOR_PATCH_VALIDATION_ENABLED = True
MANIFESTATOR_ROLLBACK_ON_ERROR = True

# IA suggestions
MANIFESTATOR_AI_SUGGESTIONS = True
MANIFESTATOR_AI_PROVIDER = "deepseek"  # o "local"
```

---

## Troubleshooting

### Problema: Manifestator no responde
```bash
curl http://localhost:8005/health
# Si falla, revisar logs:
docker logs -f manifestator
```

### Problema: Patch no se aplica
```bash
# Verificar validación
curl -s -X POST http://localhost:8005/apply-patch \
  -H "Content-Type: application/json" \
  -d '{"patch_id":"...", "validate":true}' | jq .

# Si falla validación, ver detalle
```

### Problema: DEEPSEEK_API_KEY no configurada
```bash
# Asegurar que tokens.env está cargado
source tokens.env
echo $DEEPSEEK_API_KEY

# En Docker:
docker-compose up -d --env-file tokens.env
```

---

## Referencias

- **Documentación Completa**: `docs/ARCHITECTURE.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Desarrollo**: `docs/DEVELOPMENT.md`
- **Flows**: `docs/FLOWS.md`

---

**VX11 v5.0 Manifestator — Auditoría, drift detection, auto-patching integrado con VS Code.**
