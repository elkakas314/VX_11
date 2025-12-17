# 🔌 FASE 2 — DEFINIR CONTRATO BACKEND REAL

**Objetivo:** Especificar exactamente qué endpoint backend necesita Operator sin romper arquitectura VX11

---

## 📋 CONTRATO MÍNIMO DE CHAT

### Endpoint: POST /operator/chat

```http
POST http://localhost:8011/operator/chat
  o
POST http://localhost:8000/operator/chat (via gateway)

Headers:
  Content-Type: application/json
  X-VX11-Token: {value from VITE_VX11_TOKEN or config.tokens}

Body:
{
  "message": string,  // Single message (user input)
  "session_id": string (optional),
  "metadata": object (optional)
}

Response (200 OK):
{
  "reply": string,    // ← Assistant response
  "session_id": string,
  "metadata": {
    "model": string,
    "reasoning_time_ms": number,
    "tokens_used": number
  }
}

Error Cases:
  401 Unauthorized → "X-VX11-Token invalid or missing"
  404 Not Found → "Endpoint does not exist"
  500 Server Error → Backend exception
  408 Timeout → Operator will use local fallback
```

**Por qué este contrato:**
- ✅ Operator envía `{ "message": "..." }` (chat-api.ts ya lo soporta)
- ✅ Response `{ "reply": "..." }` es lo que chat-api.ts espera
- ✅ Optional session_id para conversación persistente
- ✅ Metadata para observación (reasoning time, tokens)

---

## 🎯 DÓNDE VIVIR EL ENDPOINT

### Opción 1: Operator Backend (8011) ← **RECOMENDADO**
```
operator_backend/backend/main_v7.py
  @app.post("/operator/chat")
  async def chat_endpoint(req: ChatRequest):
    # delegate to Switch → DeepSeek
```

**Ventajas:**
- Operator backend ya existe
- Responsabilidad clara: "observar y conversar"
- NO modifica Switch ni Madre
- Timeout independiente
- Fácil integración con session store local

**Ruta:** `operator_backend/backend/main_v7.py` línea ~300

---

### Opción 2: Gateway (Tentáculo Link 8000)
```
tentaculo_link/main_v7.py
  @app.post("/operator/chat")
  → relay to Madre/Switch
```

**Desventajas:**
- Gateway es "dumb proxy", debe no tener lógica
- Complica autenticación (Gateway no autentica, es transparente)
- Mejor mantenerlo simple

**Veredicto:** ❌ No recomendado (rompe separación)

---

### Opción 3: Switch (8002)
```
switch/main.py
  @app.post("/switch/operator/chat")
```

**Desventajas:**
- Switch es router IA (decide qué motor usar)
- Chat de Operator es "dumb passthrough"
- Operator no debe influir en decisiones Switch

**Veredicto:** ❌ Confunde responsabilidades

---

## ✅ RECOMENDACIÓN FINAL

**Implementar en: `operator_backend/backend/main_v7.py`**

```python
# operator_backend/backend/main_v7.py

from pydantic import BaseModel

class OperatorChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class OperatorChatResponse(BaseModel):
    reply: str
    session_id: str
    metadata: Dict[str, Any]

@app.post("/operator/chat")
async def operator_chat(req: OperatorChatRequest) -> OperatorChatResponse:
    """
    Conversational chat for Operator dashboard.
    
    Operator is PASSIVE:
    - Does not execute actions
    - Does not control system
    - Observes and reports
    - Reasoning done by backend
    
    Flow:
      1. Operator sends message
      2. Backend calls Switch.route_v5 with chat intent
      3. Switch selects DeepSeek R1 (or local model)
      4. Response returned to Operator
      5. Operator renders (non-interactive)
    """
    session_id = req.session_id or str(uuid.uuid4())
    
    # Call Switch router
    switch_payload = {
        "prompt": req.message,
        "intent": "chat",
        "source": "operator",
        "session_id": session_id,
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.switch_url}/switch/route-v5",
            json=switch_payload,
            headers=AUTH_HEADERS
        )
    
    result = resp.json()
    reply = result.get("response", "…")
    
    return OperatorChatResponse(
        reply=reply,
        session_id=session_id,
        metadata={
            "model": result.get("model"),
            "reasoning_time_ms": result.get("elapsed_ms", 0),
        }
    )
```

---

## 🔄 FLUJO COMPLETO: Frontend → Backend → IA

```
┌─────────────────────────────────────────────────────────────┐
│ OPERATOR FRONTEND (React, 5173)                             │
│                                                             │
│  ChatView.tsx                                               │
│    user input: "¿Qué hace Switch?"                          │
│    sendMessage("¿Qué hace Switch?")                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ POST /operator/chat
                     │ { message: "¿Qué hace Switch?" }
                     │ X-VX11-Token: vx11-local-token
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ OPERATOR BACKEND (8011)                                      │
│                                                             │
│  operator_backend/backend/main_v7.py                        │
│    @app.post("/operator/chat")                              │
│    └─ validates token ✓                                     │
│    └─ builds Switch payload                                 │
│    └─ calls Switch                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ POST http://switch:8002/switch/route-v5
                     │ { prompt: "¿Qué hace Switch?",
                     │   intent: "chat",
                     │   source: "operator" }
                     │ X-VX11-Token: vx11-local-token
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ SWITCH (8002)                                                │
│                                                             │
│  switch/main.py                                             │
│    route_v5()                                               │
│    ├─ detect intent: "chat"                                 │
│    ├─ select engine: "deepseek_r1" (or local model)         │
│    ├─ call Hermes                                           │
│    └─ return response                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ POST https://api.deepseek.com/v1/chat/completions
                     │ { messages: [...], model: "deepseek-r1", ... }
                     │ Authorization: Bearer {DEEPSEEK_API_KEY}
                     │
                     │ (O bien, modelo local via Hermes)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ DEEPSEEK R1 (REMOTE) O LOCAL (via Hermes)                   │
│                                                             │
│  API Response:                                              │
│  { "choices": [{ "message": { "content": "Switch es..." }}] │
│  }                                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ response: "Switch es el router IA..."
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ OPERATOR BACKEND (8011)                                      │
│                                                             │
│  return OperatorChatResponse                                │
│  { reply: "Switch es el router IA...",                      │
│    session_id: "uuid",                                      │
│    metadata: { model: "deepseek-r1", ... }                  │
│  }                                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP 200
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ OPERATOR FRONTEND (React)                                    │
│                                                             │
│  chat-api.ts → sendChat()                                   │
│    parse response.reply                                     │
│    call typeInto(assistantId, reply)                        │
│    render message in ChatView ← **USER SEES RESPONSE**      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 TESTING DEL CONTRATO

### Test 1: Backend No Existe
```bash
curl -X POST http://localhost:8011/operator/chat \
  -H "Content-Type: application/json" \
  -H "X-VX11-Token: vx11-local-token" \
  -d '{"message":"test"}'

# Esperado: 404 Not Found
# Operator: Fallback a local ✓
```

### Test 2: Token Inválido
```bash
curl -X POST http://localhost:8011/operator/chat \
  -H "Content-Type: application/json" \
  -H "X-VX11-Token: wrong-token" \
  -d '{"message":"test"}'

# Esperado: 401 Unauthorized
# Operator: Error message visible ✓
```

### Test 3: Backend Existe + Switch Conectado
```bash
curl -X POST http://localhost:8011/operator/chat \
  -H "Content-Type: application/json" \
  -H "X-VX11-Token: vx11-local-token" \
  -d '{"message":"¿Cuál es tu nombre?"}'

# Esperado: 200 OK
# { "reply": "Soy Operator de VX11...", "session_id": "...", "metadata": {...} }
# Operator: Renders message in chat ✓
```

---

## 🔐 AUTENTICACIÓN

### Token Flow
```
Frontend env: VITE_VX11_TOKEN = "vx11-local-token"
              (o undefined, header omitted)
                ↓
Header: X-VX11-Token: vx11-local-token
                ↓
Operator Backend: verify against config.tokens.get_token()
                ↓
If valid: forward to Switch
If invalid: 401 Unauthorized
```

### En VX11 (config/tokens.py)
```python
VX11_GATEWAY_TOKEN = "vx11-local-token"
VX11_OPERATOR_TOKEN = "vx11-local-token"
```

✅ Ambos son "vx11-local-token" (dev mode), idénticos OK

---

## ⚡ TIMEOUTS

### Frontend → Operator Backend
- Default: 12 segundos (chat-api.ts)
- Si timeout: fallback a local, muestra timeout error

### Operator Backend → Switch
- Default: 15 segundos (propuesto)
- Si timeout: operator backend retorna error
- Error: Frontend muestra error + hint

### Switch → DeepSeek
- Configurable en Switch
- Default: ~30s para reasoning (R1 es lento)
- Si timeout: Switch retorna partial response o error

**Decisión:** Operator frontend 12s OK (suficiente buffer)

---

## 📊 VARIABLES DE ENTORNO FINALES

### Frontend (.env en operator/)
```bash
# Chat backend
VITE_VX11_CHAT_URL=http://localhost:8011/operator/chat

# Auth token
VITE_VX11_TOKEN=vx11-local-token

# Backend service (para otros endpoints)
VITE_OPERATOR_BACKEND_URL=http://localhost:8011
```

### Backend (.env en operator_backend/)
```bash
# VX11 tokens
VX11_OPERATOR_TOKEN=vx11-local-token
VX11_GATEWAY_TOKEN=vx11-local-token

# Switch connection
SWITCH_URL=http://switch:8002

# API keys for Switch → Hermes
DEEPSEEK_API_KEY={your-key}
OPENAI_API_KEY={your-key}
```

---

## 🎯 ARQUITECTURA FINAL (Propuesta)

```
┌─ Operator Frontend (React) — PASIVO
│  ├─ No ejecuta acciones
│  ├─ Chat es observación
│  ├─ WebSocket para eventos (futuro)
│  └─ Env: VITE_VX11_CHAT_URL, VITE_VX11_TOKEN
│
├─ Operator Backend (8011) — FORWARDER
│  ├─ POST /operator/chat
│  ├─ Valida token
│  ├─ Delega a Switch
│  └─ Retorna response
│
├─ Switch (8002) — ROUTER IA
│  ├─ POST /switch/route-v5
│  ├─ Selecciona motor (DeepSeek R1, local, etc.)
│  ├─ Ejecuta reasoning
│  └─ Retorna respuesta
│
└─ Madre (8001) — ORQUESTADOR
   ├─ Decisiones autónomas
   ├─ Creación de tareas
   ├─ NO responde a Operator
   └─ Publica eventos (futuro)
```

**Respeto a VX11:**
- ✅ HTTP-only communication
- ✅ Tokens centralizados
- ✅ No rompe módulos existentes
- ✅ Operator es pasivo (no controla)
- ✅ Switch mantiene responsabilidad
- ✅ Madre no se modifica

---

## 📝 CHECKLIST FASE 2

- [ ] Endpoint `/operator/chat` definido
- [ ] Contrato JSON especificado (request/response)
- [ ] Variables de entorno documentadas
- [ ] Token auth flow establecido
- [ ] Timeouts definidos
- [ ] Error cases mapeados
- [ ] Arquitectura validada contra VX11 canon

**Listo para FASE 3: Implementación**

