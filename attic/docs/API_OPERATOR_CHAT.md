# Operator Backend API — Chat Endpoint (Fase F)

**Versión:** 7.0 | **Módulo:** `operator_backend/backend`  
**Puerto:** 8011 | **Contrato:** `POST /operator/chat`

---

## Endpoint: `/operator/chat`

### Request

**Método:** `POST`  
**URL:** `http://127.0.0.1:8011/operator/chat` (desarrollo local)  
**Autenticación:** Header `X-VX11-Token`

**Body:**

```json
{
  "session_id": "session-001",
  "user_id": "local",
  "message": "¿Cuál es la capital de Francia?",
  "context_summary": "Conversación previa: El usuario preguntó sobre geografía",
  "metadata": {
    "source": "ui",
    "request_id": "req-123"
  }
}
```

**Campos:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `session_id` | string | No | UUID de sesión. Si omitido, se genera uno nuevo |
| `user_id` | string | No | ID de usuario (default: "local") |
| `message` | string | **Sí** | Mensaje del usuario |
| `context_summary` | string | No | Resumen del contexto de conversación (de Context-7) |
| `metadata` | object | No | Metadatos adicionales (source, request_id, etc.) |

### Response

**Status:** `200 OK`

**Body:**

```json
{
  "session_id": "session-001",
  "response": "La capital de Francia es París.",
  "tool_calls": null
}
```

**Campos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `session_id` | string | UUID de sesión (mismo que request o generado) |
| `response` | string | Respuesta del modelo IA |
| `tool_calls` | array | Llamadas a herramientas (null si no hay) |

---

## Flujo Interno

```
1. POST /operator/chat recibida
   ↓
2. Validar token X-VX11-Token (TokenGuard)
   ↓
3. Generar/obtener session_id
   ↓
4. Buscar sesión en BD (OperatorSession)
   - Si no existe: crear
   ↓
5. Registrar mensaje usuario en BD (OperatorMessage, role=user)
   ↓
6. Delegar a SwitchClient.query_chat()
   - Construir payload con messages + task_type + metadata
   - Enviar a Switch (http://switch:8002/switch/chat)
   - Timeout: 30s
   ↓
7. Recibir respuesta de Switch ({"response": "...", "model": "...", ...})
   ↓
8. Registrar mensaje asistente en BD (OperatorMessage, role=assistant)
   ↓
9. Retornar ChatResponse con session_id + response
```

---

## Ejemplos

### Happy Path

```bash
# Request
curl -X POST http://127.0.0.1:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-001",
    "user_id": "alice",
    "message": "Hola, ¿cómo estás?",
    "metadata": {"source": "web"}
  }'

# Response
{
  "session_id": "session-001",
  "response": "¡Hola Alice! Estoy funcionando correctamente. ¿En qué puedo ayudarte?",
  "tool_calls": null
}
```

### Con Context Summary

```bash
curl -X POST http://127.0.0.1:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-001",
    "message": "¿Y sobre el clima?",
    "context_summary": "Contexto anterior: Conversación sobre geografía de Francia"
  }'
```

### Nueva Sesión (sin session_id)

```bash
# Sin session_id → genera UUID automáticamente
curl -X POST http://127.0.0.1:8011/operator/chat \
  -H "X-VX11-Token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Primera pregunta"
  }'

# Response incluirá session_id generado
{
  "session_id": "a3f1b2c3-5d4e-6f7a-8b9c-0d1e2f3g4h5i",
  "response": "Hola, bienvenido. ¿En qué puedo ayudarte?",
  "tool_calls": null
}
```

---

## Error Handling

### 401 Unauthorized

```json
{
  "detail": "auth_required"
}
```

**Causa:** Falta header `X-VX11-Token` o token inválido

**Solución:** Incluir header válido
```bash
-H "X-VX11-Token: vx11-local-token"
```

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Causa:** Campo requerido faltante (ej. `message`)

**Solución:** Incluir todos los campos requeridos

### 500 Internal Server Error

```json
{
  "detail": "switch_unavailable"
}
```

**Causa:** Switch no disponible, timeout, o error en BD

**Solución:**
1. Chequear que Switch está activo: `curl http://127.0.0.1:8002/health`
2. Chequear logs del backend: `tail logs/operator_backend.log`
3. Reintentar con backoff (el frontend debería handlearlo)

---

## Persistencia

### Base de Datos

Todos los mensajes se registran en `data/runtime/vx11.db`:

| Tabla | Campo | Contenido |
|-------|-------|-----------|
| `operator_session` | `session_id` | UUID único |
| | `user_id` | ID del usuario |
| | `created_at` | Timestamp creación |
| `operator_message` | `session_id` | FK a sesión |
| | `role` | "user" \| "assistant" |
| | `content` | Texto del mensaje |
| | `created_at` | Timestamp |

### Retención

- Sesiones se guardan indefinidamente (salvo limpieza manual)
- Mensajes se guardan indefinidamente
- **Recomendación:** Implementar limpieza automática (ej. borrar sesiones >30 días) en próxima fase

---

## Integración con Frontend

### React Example

```typescript
async function sendChat(message: string, sessionId?: string): Promise<ChatResponse> {
  const response = await fetch('http://localhost:8011/operator/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-VX11-Token': 'vx11-local-token',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      metadata: { source: 'ui' },
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat error: ${response.status}`);
  }

  return response.json();
}
```

### Token Management

El token debe estar disponible en:
- **ENV:** `VITE_VX11_TOKEN` (durante build de frontend)
- **Fallback:** Usar `'vx11-local-token'` para dev local
- **Producción:** Usar token rotado desde secretos

```typescript
const token = import.meta.env.VITE_VX11_TOKEN || 'vx11-local-token';
```

---

## Performance

### Timeouts

| Componente | Timeout | Nota |
|------------|---------|------|
| SwitchClient | 30s | HTTP timeout a Switch |
| DB query | N/A | SQLite local, típicamente <10ms |
| Total endpoint | ~31s | Dominado por Switch timeout |

### Recomendaciones

1. **Frontend timeout:** 45s (buffer para retries)
2. **Streaming (opcional):** Usar WebSocket si respuestas son largas
3. **Polling:** Si backend está bajo carga, frontend podría sondear `/operator/session/{id}`

---

## Testing

### Unit Test

```python
import pytest
from fastapi.testclient import TestClient
from operator_backend.backend.main_v7 import app

client = TestClient(app)

def test_operator_chat_happy_path():
    response = client.post(
        "/operator/chat",
        headers={"X-VX11-Token": "vx11-local-token"},
        json={
            "message": "Hola",
            "metadata": {"test": True}
        }
    )
    assert response.status_code == 200
    assert "session_id" in response.json()
    assert "response" in response.json()

def test_operator_chat_auth_required():
    response = client.post(
        "/operator/chat",
        json={"message": "Hola"}
    )
    assert response.status_code == 401
```

---

## Futura Improvements (Post-Fase F)

- [ ] Session cleanup (por antigüedad)
- [ ] Rate limiting por user_id
- [ ] Streaming responses (WebSocket)
- [ ] Conversation tree (branching)
- [ ] Feedback scoring (user ratings)
- [ ] Export session as JSON/PDF

---

## Referencias

- `operator_backend/backend/main_v7.py` — Implementación del endpoint
- `operator_backend/backend/switch_integration.py` — SwitchClient
- `config/db_schema.py` — OperatorSession, OperatorMessage
- `docs/WORKFLOWS_VX11_LOW_COST.md` — Ejemplos de uso con curl

---

**Versión:** 7.0 | **Fase:** F | **Actualizado:** 2025-12-14
