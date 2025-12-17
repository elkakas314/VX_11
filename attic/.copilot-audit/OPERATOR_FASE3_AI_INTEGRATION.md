# 🤖 FASE 3 — INTEGRACIÓN CON IA (DEEPSEEK R1)

**Objetivo:** Flujo completo desde chat del Operator hasta reasoning real con DeepSeek R1, respetando que Operator es PASIVO

---

## 🎯 ARQUITECTURA COMPLETA (FASE 3)

```
┌─────────────────────────────────────────────────────────────┐
│                  OPERATOR FRONTEND                          │
│                   (Pasivo, Observa)                         │
│                                                             │
│  User → Chat input: "¿Cuál es el problema con Hormiguero?"  │
│  ↓                                                          │
│  sendMessage() → POST /operator/chat                        │
│  ↓                                                          │
│  Renderiza respuesta en ChatView (typing animation)         │
│  ↓                                                          │
│  NO ejecuta acciones                                        │
│  NO controla Switch                                         │
│  NO modifica sistema                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              OPERATOR BACKEND (8011)                         │
│           (Forwarder, valida token)                         │
│                                                             │
│  POST /operator/chat                                        │
│  ├─ Parse request: { message, session_id, metadata }       │
│  ├─ Validate X-VX11-Token                                  │
│  ├─ Log conversación a BD (operator_session, messages)      │
│  ├─ Build Switch payload                                   │
│  └─ Delegate to Switch                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ POST http://switch:8002/switch/route-v5
                       │ {
                       │   "prompt": "¿Cuál es el problema con Hormiguero?",
                       │   "intent": "chat",
                       │   "source": "operator",
                       │   "session_id": "uuid-...",
                       │   "context": { "module_focus": "hormiguero" }
                       │ }
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                 SWITCH (8002)                               │
│             (Router IA, Decisor)                            │
│                                                             │
│  route_v5() — PASO 3 (GA optimizer, Hermes fusion)          │
│  ├─ Detect intent: "chat" → routing type                    │
│  ├─ Genetic algorithm score models                          │
│  │  ├─ deepseek_r1 (reasoning: +10, speed: -5)             │
│  │  ├─ llama2-local (reasoning: +8, speed: +8)             │
│  │  └─ gpt4 (reasoning: +10, speed: -2)                    │
│  ├─ Select best: deepseek_r1 (reasoning ⊕ available)       │
│  ├─ Prepare context (BD snapshot, recent events)           │
│  └─ Call Hermes                                            │
│                                                             │
│  ✅ NO modifica Operator                                    │
│  ✅ NO ejecuta acciones autónomas                           │
│  ✅ Solo reasoning puro                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ POST https://api.deepseek.com/v1/chat/completions
                       │ {
                       │   "model": "deepseek-r1",
                       │   "messages": [
                       │     {
                       │       "role": "system",
                       │       "content": "Eres Operator de VX11. Observa y explica..."
                       │     },
                       │     {
                       │       "role": "user",
                       │       "content": "¿Cuál es el problema con Hormiguero?"
                       │     }
                       │   ],
                       │   "temperature": 0.3,
                       │   "max_tokens": 2000,
                       │   "thinking": {
                       │     "type": "enabled",
                       │     "budget_tokens": 1000
                       │   }
                       │ }
                       │ Authorization: Bearer sk-...
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│         DEEPSEEK R1 (Remote API)                            │
│      (Reasoning Model, OpenAI compatible)                   │
│                                                             │
│  1. Pensamiento (interno, no visible)                       │
│     <thinking>                                              │
│       - Horniguero es Queen + 8 Ants (paralelización)       │
│       - Problema típico: queue saturation o GA timeout      │
│       - Necesito más contexto...                            │
│     </thinking>                                             │
│                                                             │
│  2. Respuesta (visible)                                     │
│     "Horniguero organiza paralelización via Queen+Ants...   │
│      El problema común es cuando la cola se satura y...     │
│      Recomendación: escalar workers o revisar GA config"    │
│                                                             │
│  Response JSON:                                             │
│  {                                                          │
│    "id": "chatcmpl-...",                                    │
│    \"usage\": {                                              │
│      \"prompt_tokens\": 245,                                │
│      \"completion_tokens\": 156,                            │
│      \"total_tokens\": 401                                  │
│    },                                                       │
│    \"choices\": [{                                          │
│      \"finish_reason\": \"stop\",                            │
│      \"message\": {                                         │
│        \"role\": \"assistant\",                              │
│        \"content\": \"Horniguero organiza...\"               │
│      }                                                     │
│    }]                                                       │
│  }                                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                 SWITCH (8002) — RESPONSE                    │
│                                                             │
│  return {                                                   │
│    \"response\": \"Horniguero organiza paralelización...\"   │
│    \"model\": \"deepseek-r1\",                               │
│    \"elapsed_ms\": 3200,                                    │
│    \"tokens_used\": 401,                                    │
│    \"session_id\": \"uuid-...\"                              │
│  }                                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│           OPERATOR BACKEND (8011) — RESPONSE                │
│                                                             │
│  return OperatorChatResponse {                              │
│    \"reply\": \"Horniguero organiza paralelización...\"      │
│    \"session_id\": \"uuid-...\",                             │
│    \"metadata\": {                                          │
│      \"model\": \"deepseek-r1\",                             │
│      \"reasoning_time_ms\": 3200,                           │
│      \"tokens_used\": 401                                   │
│    }                                                        │
│  }                                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            OPERATOR FRONTEND — RENDER                       │
│                                                             │
│  ChatView recibe reply                                      │
│  ↓                                                          │
│  typeInto(assistantId, reply) — typing animation           │
│  ↓                                                          │
│  Render: \"Horniguero organiza...\" en chat                 │
│  ↓                                                          │
│  Metadata visible: \"⚡ deepseek-r1 | 3.2s | 401 tokens\"   │
│  ↓                                                          │
│  ✅ User observa reasoning resultado                        │
│  ✅ Operator sigue siendo pasivo                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 FLUJO DE PERSISTENCIA (BD)

### En Operator Backend (8011)

```python
# operator_backend/backend/main_v7.py

from config.db_schema import OperatorSession, OperatorMessage

@app.post("/operator/chat")
async def operator_chat(req: OperatorChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    
    # 1. Get or create session
    db = get_session("operator")
    session = db.query(OperatorSession).filter_by(
        session_id=session_id
    ).first()
    
    if not session:
        session = OperatorSession(
            session_id=session_id,
            user_id="operator",
            created_at=datetime.now(),
            status="active"
        )
        db.add(session)
        db.commit()
    
    # 2. Save user message
    user_msg = OperatorMessage(
        session_id=session_id,
        role="user",
        content=req.message,
        timestamp=datetime.now()
    )
    db.add(user_msg)
    db.commit()
    
    # 3. Call Switch
    switch_payload = {
        "prompt": req.message,
        "intent": "chat",
        "source": "operator",
        "session_id": session_id,
        "context": {
            "conversation_length": len(session.messages),
        }
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.switch_url}/switch/route-v5",
            json=switch_payload,
            headers=AUTH_HEADERS
        )
    
    result = resp.json()
    reply = result.get("response", "…")
    
    # 4. Save assistant message
    asst_msg = OperatorMessage(
        session_id=session_id,
        role="assistant",
        content=reply,
        timestamp=datetime.now(),
        metadata={
            "model": result.get("model"),
            "tokens": result.get("tokens_used"),
        }
    )
    db.add(asst_msg)
    db.commit()
    db.close()
    
    # 5. Return
    return OperatorChatResponse(
        reply=reply,
        session_id=session_id,
        metadata={
            "model": result.get("model"),
            "reasoning_time_ms": result.get("elapsed_ms", 0),
            "tokens_used": result.get("tokens_used"),
        }
    )
```

**Tablas BD necesarias (en config/db_schema.py):**
```python
class OperatorSession(Base):
    __tablename__ = "operator_sessions"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True)
    user_id = Column(String, default="operator")
    created_at = Column(DateTime)
    status = Column(String, default="active")
    messages = relationship("OperatorMessage", back_populates="session")

class OperatorMessage(Base):
    __tablename__ = "operator_messages"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey("operator_sessions.session_id"))
    role = Column(String)  # "user" | "assistant"
    content = Column(Text)
    timestamp = Column(DateTime)
    metadata = Column(JSON, default={})
    session = relationship("OperatorSession", back_populates="messages")
```

---

## 🧪 QUÉ HACE CADA MÓDULO (FASE 3)

| Módulo | Acción | Observación |
|--------|--------|-------------|
| **Operator Frontend** | Acepta input, envía POST, renderiza | ✅ Pasivo, observa |
| **Operator Backend** | Valida token, delega, persiste BD | ✅ Forwarder puro |
| **Switch** | Selecciona motor (GA), prepara contexto | ✅ Decisor inteligente |
| **DeepSeek R1** | Razona, genera respuesta | ✅ Motivo externo |
| **Madre** | NO hace nada (sigue ciclo 30s autónomo) | ✅ Desacoplado |
| **Hormiguero** | NO hace nada (sigue paralelización) | ✅ Desacoplado |
| **Manifestator** | Audita, detecta drift | ✅ Observador |

**Conclusión:** Zero coupling, cero cambios a módulos existentes

---

## 🔐 SEGURIDAD & VALIDACIONES

### 1. Token Validation (Operator Backend)
```python
def token_guard(x_vx11_token: str = Header(None)):
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != VX11_TOKEN:
            raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@app.post("/operator/chat", dependencies=[Depends(token_guard)])
async def operator_chat(...):
    pass
```

### 2. Rate Limiting (Operator Backend)
```python
# Limitar a 30 mensajes/minuto por session
@app.post("/operator/chat")
async def operator_chat(req: OperatorChatRequest):
    rate_key = f"operator_chat:{req.session_id}"
    count = cache.increment(rate_key, 60)  # 60s window
    if count > 30:
        raise HTTPException(status_code=429, detail="Too many requests")
```

### 3. Content Validation
```python
# Rechazo inputs peligrosos
if len(req.message) > 2000:
    raise HTTPException(status_code=400, detail="Message too long")

if any(cmd in req.message.lower() for cmd in ["rm -rf", "DROP TABLE"]):
    raise HTTPException(status_code=400, detail="Invalid command")
```

---

## 📊 OBSERVABILIDAD (PHASE 3)

### Logging (Operator Backend)
```python
import logging
log = logging.getLogger("vx11.operator")

@app.post("/operator/chat")
async def operator_chat(req: OperatorChatRequest):
    log.info(f"Chat request: session={req.session_id}, len={len(req.message)}")
    
    # ... call Switch ...
    
    log.info(f"Chat response: model={result.get('model')}, elapsed={result.get('elapsed_ms')}ms")
    
    # Also call forensics
    from config.forensics import write_log
    write_log("operator", "chat", {
        "session_id": session_id,
        "model": result.get("model"),
        "tokens": result.get("tokens_used"),
    })
```

### Metrics (Frontend)
```typescript
// In ChatView.tsx, display metadata
<div className="text-xs text-gray-500 mt-1">
  ⚡ {metadata.model} | {metadata.reasoning_time_ms}ms | {metadata.tokens_used} tokens
</div>
```

---

## 🚨 ERROR CASES (PHASE 3)

### Case 1: DeepSeek API Down
```
Frontend sends: "Hola"
  ↓
Operator Backend calls Switch
  ↓
Switch tries DeepSeek, gets 503 Service Unavailable
  ↓
Switch fallback: tries local model (Hermes)
  ↓
Local model returns: "Servicio remoto no disponible, usando modo local"
  ↓
Frontend receives: reply visible, metadata shows "local" model
  ↓
✅ Chat never breaks, user sees explanation
```

### Case 2: Switch Timeout
```
Frontend sends: "¿Cuál es el problema?"
  ↓
Operator Backend calls Switch (15s timeout)
  ↓
Switch doesn't respond in 15s
  ↓
Operator Backend catches timeout, returns error
  ↓
Frontend shows: "Timeout - backend no responde" (12s visible)
  ↓
User clicks "Local Mode" or retries
  ↓
✅ Chat UI never breaks
```

### Case 3: Token Invalid
```
Frontend sends: X-VX11-Token: wrong-token
  ↓
Operator Backend receives, checks token
  ↓
Token mismatch → 401 Unauthorized
  ↓
Frontend catch block: "Unauthorized: token inválido"
  ↓
User sets VITE_VX11_TOKEN correctly
  ↓
✅ Chat recovers next message
```

---

## 📝 CAMBIOS REQUERIDOS POR MÓDULO

### Operator Backend (NEW)
```python
# operator_backend/backend/main_v7.py
- Add OperatorChatRequest, OperatorChatResponse
- Add @app.post("/operator/chat")
- Add DB models OperatorSession, OperatorMessage
- Add token validation, rate limiting
- Add logging/forensics calls
```

**Archivos a crear/modificar:**
- `operator_backend/backend/main_v7.py` (add endpoint)
- `config/db_schema.py` (add tables)

### Switch (ZERO changes)
- ✅ No cambios necesarios
- Solo llama a Switch endpoint existente

### Operator Frontend (ZERO changes)
- ✅ No cambios necesarios
- chat-api.ts ya soporta el contrato

---

## ✨ RESULTADO FINAL (FASE 3)

```
User en Operator Frontend:
  "¿Por qué Manifestator genera parches?"
  [Enter]
  
Operator Backend:
  ✓ Validates token
  ✓ Persists message to BD
  ✓ Calls Switch.route_v5
  ✓ Gets response from DeepSeek R1
  ✓ Saves response to BD
  ✓ Returns to Frontend

Operator Frontend:
  ✓ Receives { reply: "...", metadata: {...} }
  ✓ Animates typing of response
  ✓ Shows metadata: "⚡ deepseek-r1 | 2.1s | 340 tokens"
  ✓ Maintains localStorage persistence

Chat History:
  ✓ Survives page reload
  ✓ Searchable by session_id in BD
  ✓ Tied to user_id ("operator")
```

---

## 🎯 CHECKLIST FASE 3

- [ ] OperatorSession, OperatorMessage tables in DB
- [ ] `/operator/chat` endpoint implemented
- [ ] Token validation in place
- [ ] Rate limiting configured
- [ ] Error handling for all cases
- [ ] DeepSeek R1 integration verified
- [ ] Local fallback if remote fails
- [ ] Logging & forensics calls added
- [ ] Frontend env vars documented
- [ ] Tests for happy path + error cases

**Listo para FASE 4: Mejoras sin romper**

