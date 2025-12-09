# VX11 v5.0 — API REFERENCE

## Gateway (Puerto 8000)

Base URL: `http://localhost:8000`

### GET /health
Verificar salud del gateway.
- **Response:** `{ "status": "healthy", "timestamp": "..." }`

### GET /vx11/status
Estado del sistema y puertos mapeados.
- **Response:**
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
    },
    "timestamp": "2025-01-30T10:00:00Z"
  }
  ```

### POST /vx11/action/control
Controlar módulos (status, start, stop, restart).
- **Request:**
  ```json
  {
    "target": "madre",
    "action": "status"
  }
  ```
- **Response:**
  ```json
  {
    "target": "madre",
    "action": "status",
    "response": { "status": "active", "uptime": 3600 }
  }
  ```

---

## Madre (Puerto 8001)

Base URL: `http://localhost:8001`

### GET /health
Verificar salud de Madre.
- **Response:** `{ "status": "healthy" }`

### POST /task
Crear una nueva tarea.
- **Request:**
  ```json
  {
    "title": "Analizar datos",
    "description": "Procesar archivo CSV",
    "task_type": "analysis",
    "priority": 1,
    "context": {}
  }
  ```
- **Response:**
  ```json
  {
    "task_id": "uuid-123",
    "status": "created",
    "created_at": "2025-01-30T10:00:00Z"
  }
  ```

### GET /tasks
Listar todas las tareas.
- **Query params:**
  - `status`: "pending" | "running" | "completed" | "failed"
  - `limit`: 50 (default)
  - `offset`: 0 (default)
- **Response:**
  ```json
  {
    "tasks": [
      {
        "task_id": "uuid-123",
        "title": "Analizar datos",
        "status": "completed",
        "created_at": "2025-01-30T10:00:00Z"
      }
    ],
    "total": 1
  }
  ```

### GET /tasks/{task_id}
Obtener detalle de una tarea.
- **Response:**
  ```json
  {
    "task_id": "uuid-123",
    "title": "Analizar datos",
    "status": "running",
    "progress": 45,
    "result": null,
    "error": null
  }
  ```

### POST /madre/v3/autonomous/start
Iniciar ciclo autónomo (cada 30s).
- **Request:** `{ "enabled": true }`
- **Response:** `{ "autonomous_mode": "started" }`

### POST /madre/v3/autonomous/stop
Detener ciclo autónomo.
- **Request:** `{ "enabled": false }`
- **Response:** `{ "autonomous_mode": "stopped" }`

### POST /chat
Enviar mensaje conversacional (futuro MCP).
- **Request:** `{ "message": "¿Qué tareas tengo pendientes?" }`
- **Response:** `{ "response": "Tienes 3 tareas pendientes..." }`

---

## Switch (Puerto 8002)

Base URL: `http://localhost:8002`

### GET /health
Verificar salud de Switch.
- **Response:** `{ "status": "healthy" }`

### GET /switch/providers
Listar providers disponibles con métricas.
- **Response:**
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
      {
        "name": "local",
        "model": "mistral-7b",
        "latency_ms": 50,
        "success_rate": 0.95,
        "available": true
      }
    ]
  }
  ```

### GET /switch/context
Obtener contexto de decisiones previas.
- **Response:**
  ```json
  {
    "recent_decisions": [
      {
        "task_type": "analysis",
        "preferred_provider": "deepseek",
        "confidence": 0.92
      }
    ]
  }
  ```

### POST /switch/route
Elegir mejor provider para un prompt.
- **Request:**
  ```json
  {
    "prompt": "Analiza este código",
    "task_type": "code_analysis",
    "constraints": {
      "max_latency_ms": 500,
      "min_confidence": 0.8
    }
  }
  ```
- **Response:**
  ```json
  {
    "selected_provider": "deepseek",
    "model": "deepseek-r1",
    "confidence": 0.95,
    "reasoning": "Mejor ratio latencia/precisión para code_analysis"
  }
  ```

---

## Hermes (Puerto 8003)

Base URL: `http://localhost:8003`

### GET /health
Verificar salud de Hermes.
- **Response:** `{ "status": "healthy", "active_jobs": 0 }`

### GET /hermes/available
Listar CLIs y herramientas detectadas.
- **Response:**
  ```json
  {
    "clis": [
      { "name": "python", "version": "3.11.0", "path": "/usr/bin/python3" },
      { "name": "ffmpeg", "version": "6.0", "path": "/usr/bin/ffmpeg" }
    ],
    "total": 45
  }
  ```

### POST /hermes/exec
Ejecutar un CLI con parámetros.
- **Request:**
  ```json
  {
    "cli": "python",
    "args": ["-c", "print('hello')"],
    "timeout": 30
  }
  ```
- **Response:**
  ```json
  {
    "job_id": "job-456",
    "stdout": "hello\n",
    "stderr": "",
    "return_code": 0,
    "duration_ms": 45
  }
  ```

### GET /hermes/jobs
Listar jobs en ejecución o completados.
- **Query params:**
  - `status`: "running" | "completed" | "failed"
  - `limit`: 20
- **Response:**
  ```json
  {
    "jobs": [
      {
        "job_id": "job-456",
        "cli": "python",
        "status": "completed",
        "return_code": 0
      }
    ]
  }
  ```

### GET /hermes/models
Listar modelos HF descargados o disponibles.
- **Response:**
  ```json
  {
    "models": [
      {
        "name": "mistral-7b",
        "size_mb": 14000,
        "cached": true,
        "last_used": "2025-01-30T09:30:00Z"
      }
    ],
    "total_cached_mb": 14000,
    "max_cache_mb": 256
  }
  ```

---

## Hormiguero (Puerto 8004)

Base URL: `http://localhost:8004`

### GET /health
Verificar salud del Hormiguero.
- **Response:** `{ "status": "healthy", "ants": 4 }`

### POST /hormiguero/task
Crear tarea paralela.
- **Request:**
  ```json
  {
    "task": "procesar_archivos",
    "items": ["file1.txt", "file2.txt", "file3.txt"],
    "parallelism": 2
  }
  ```
- **Response:**
  ```json
  {
    "colony_task_id": "colony-789",
    "status": "running",
    "progress": 0,
    "total_items": 3
  }
  ```

### GET /hormiguero/colony/status
Obtener estado de la colonia.
- **Response:**
  ```json
  {
    "queen_alive": true,
    "ants_count": 4,
    "ants_idle": 2,
    "ants_busy": 2,
    "total_completed": 150,
    "cpu_usage": 45
  }
  ```

### GET /hormiguero/tasks
Listar tareas paralelas.
- **Response:**
  ```json
  {
    "tasks": [
      {
        "colony_task_id": "colony-789",
        "status": "running",
        "progress": 66
      }
    ]
  }
  ```

---

## Manifestator (Puerto 8005)

Base URL: `http://localhost:8005`

### GET /health
Verificar salud de Manifestator.
- **Response:** `{ "status": "healthy" }`

### GET /drift
Detectar cambios respecto a baseline.
- **Query params:**
  - `module`: "gateway" | "madre" | ... (opcional, todos si vacío)
- **Response:**
  ```json
  {
    "modules_analyzed": ["gateway", "madre", "switch"],
    "drifts": [
      {
        "module": "madre",
        "file": "main.py",
        "changes": 2,
        "severity": "low"
      }
    ],
    "total_drifts": 1
  }
  ```

### POST /generate-patch
Generar patch para los cambios detectados.
- **Request:**
  ```json
  {
    "module": "madre",
    "drifts": ["line 45: changed logic"],
    "auto_suggest": true
  }
  ```
- **Response:**
  ```json
  {
    "patch_id": "patch-001",
    "module": "madre",
    "patch_content": "--- old\n+++ new\n...",
    "suggestion": "Cambio de lógica aparentemente benigno. Recomiendo revisar.",
    "validation": "pending"
  }
  ```

### POST /apply-patch
Aplicar un patch generado.
- **Request:**
  ```json
  {
    "patch_id": "patch-001",
    "validate": true,
    "rollback_on_error": true
  }
  ```
- **Response:**
  ```json
  {
    "patch_id": "patch-001",
    "status": "applied",
    "validation_passed": true,
    "rollback_performed": false
  }
  ```

### GET /patches
Listar histórico de patches.
- **Response:**
  ```json
  {
    "patches": [
      {
        "patch_id": "patch-001",
        "module": "madre",
        "applied": true,
        "created_at": "2025-01-30T09:00:00Z"
      }
    ]
  }
  ```

---

## MCP (Puerto 8006)

Base URL: `http://localhost:8006`

### GET /health
Verificar salud de MCP.
- **Response:** `{ "status": "healthy", "conversations": 2 }`

### POST /mcp/chat
Enviar mensaje conversacional.
- **Request:**
  ```json
  {
    "session_id": "session-abc",
    "message": "¿Qué módulo está más cargado?",
    "context": {}
  }
  ```
- **Response:**
  ```json
  {
    "session_id": "session-abc",
    "response": "Hermes está procesando 3 modelos. Switch tiene 2 decisiones pendientes.",
    "actions_suggested": ["check_hermes", "optimize_switch"]
  }
  ```

### POST /mcp/action
Ejecutar acción sugerida.
- **Request:**
  ```json
  {
    "session_id": "session-abc",
    "action": "check_hermes",
    "parameters": {}
  }
  ```
- **Response:**
  ```json
  {
    "action": "check_hermes",
    "status": "completed",
    "result": { "active_jobs": 3, "queue": 5 }
  }
  ```

### GET /mcp/sessions
Listar sesiones conversacionales.
- **Response:**
  ```json
  {
    "sessions": [
      {
        "session_id": "session-abc",
        "created_at": "2025-01-30T09:00:00Z",
        "messages_count": 5
      }
    ]
  }
  ```

---

## Shub Niggurath (Puerto 8007)

Base URL: `http://localhost:8007`

### GET /health
Verificar salud de Shub.
- **Response:** `{ "status": "healthy" }`

### POST /shub/process
Procesar archivo o input.
- **Request:**
  ```json
  {
    "input_path": "/app/sandbox/document.pdf",
    "processor": "ocr",
    "options": { "language": "es" }
  }
  ```
- **Response:**
  ```json
  {
    "job_id": "shub-001",
    "status": "running",
    "progress": 30,
    "estimated_time_sec": 45
  }
  ```

### POST /shub/generate
Generar contenido IA.
- **Request:**
  ```json
  {
    "task_type": "summary",
    "input_text": "Lorem ipsum...",
    "language": "es",
    "max_tokens": 200
  }
  ```
- **Response:**
  ```json
  {
    "generated_text": "Resumen breve del contenido...",
    "tokens_used": 145,
    "model": "mistral-7b"
  }
  ```

### GET /shub/jobs
Listar jobs en ejecución.
- **Response:**
  ```json
  {
    "jobs": [
      {
        "job_id": "shub-001",
        "task_type": "summary",
        "status": "completed",
        "result": "Resumen..."
      }
    ]
  }
  ```

---

## Ejemplos rápidos (curl)

### Health check global
```bash
for port in {8000..8007}; do
  echo "=== Port $port ==="
  curl -s http://localhost:$port/health | jq .
done
```

### Crear tarea en Madre
```bash
curl -X POST http://localhost:8001/task \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test task",
    "task_type": "analysis",
    "priority": 1
  }' | jq .
```

### Obtener providers en Switch
```bash
curl http://localhost:8002/switch/providers | jq .
```

### Ejecutar CLI en Hermes
```bash
curl -X POST http://localhost:8003/hermes/exec \
  -H "Content-Type: application/json" \
  -d '{
    "cli": "python",
    "args": ["-c", "print(42)"],
    "timeout": 10
  }' | jq .
```

### Enviar mensaje MCP
```bash
curl -X POST http://localhost:8006/mcp/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test",
    "message": "Health check"
  }' | jq .
```

---

**VX11 v5.0 API Reference — Todos los endpoints y ejemplos.**
