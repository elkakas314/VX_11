# madre/main.py - Mapeo Exacto de Errores y Soluciones

## ERROR 1: Línea 205 - status=StatusEnum.DONE.value (ChatResponse)
**Contexto**: Función `/madre/intent` - Deep Seek successful response
**Código Actual**:
```python
200:     response = ChatResponse(
201:         response=deepseek_result["response"],
202:         session_id=session_id,
203:         intent_id=intent_id,
204:         plan_id=plan_id,
205:         status=StatusEnum.DONE.value,  ❌ ERROR
206:         mode=ModeEnum.MADRE.value,    ❌ ERROR
207:         provider=deepseek_result["provider"],
208:         model=deepseek_result["model"],
...
```

**Problema**: ChatResponse espera `StatusEnum` enum, no string
**Solución**: Remover `.value`
```python
205:         status=StatusEnum.DONE,  ✅ CORRECTO
206:         mode=ModeEnum.MADRE,    ✅ CORRECTO
```

---

## ERROR 2: Línea 253-254 - session_mode Assignment
**Contexto**: Detección de modo basada en dominio
**Código Actual**:
```python
250:  # Step 3: Detect mode from domain
251:  if dsl.domain == "audio":
252:      session_mode = "AUDIO_ENGINEER"  ❌ String, no ModeEnum
253:      _SESSIONS[session_id]["mode"] = "AUDIO_ENGINEER"
254:  else:
255:      session_mode = "MADRE"  ❌ String, no ModeEnum
256:      _SESSIONS[session_id]["mode"] = "MADRE"
```

**Problema**: session_mode es string, pero se pasa a modelos que esperan ModeEnum
**Impacto**: Causa errores en líneas 267, 306, 341 (modo inválido)

**Solución**:
```python
250:  # Step 3: Detect mode from domain
251:  if dsl.domain == "audio":
252:      session_mode = ModeEnum.AUDIO_ENGINEER  ✅ Enum
253:      _SESSIONS[session_id]["mode"] = ModeEnum.AUDIO_ENGINEER.value
254:  else:
255:      session_mode = ModeEnum.MADRE  ✅ Enum
256:      _SESSIONS[session_id]["mode"] = ModeEnum.MADRE.value
```

---

## ERROR 3: Línea 267 - mode Parameter (IntentV2)
**Contexto**: Creación de IntentV2
**Código Actual**:
```python
264: intent = IntentV2(
265:     intent_id=intent_id,
266:     session_id=session_id,
267:     mode=session_mode,  ❌ Es string (por línea 252-256)
268:     dsl=dsl,
269:     risk=risk,
...
```

**Problema**: Cuando session_mode es string "AUDIO_ENGINEER", Pylance reporta type error
**Solución**: Será automática una vez se corrija línea 252-256

---

## ERROR 4: Línea 305 - status="WAITING" (ChatResponse)
**Contexto**: Confirmación requerida workflow
**Código Actual**:
```python
300: response = ChatResponse(
301:     response="Action requires confirmation...",
302:     session_id=session_id,
303:     intent_id=intent_id,
304:     plan_id=plan_id,
305:     status="WAITING",  ❌ ERROR: WAITING no es StatusEnum válido
306:     mode=session_mode,  ❌ ERROR: session_mode es string
...
```

**Problema 1**: StatusEnum define {QUEUED, RUNNING, DONE, ERROR}, no WAITING
**Problema 2**: session_mode es string (línea 252-256)

**Solución Opción A** (usar StatusEnum.RUNNING):
```python
305:     status=StatusEnum.RUNNING,  ✅ Indica en progreso, pendiente confirmación
```

**Solución Opción B** (crear StatusEnum.WAITING):
```python
# En tentaculo_link/models_core_mvp.py:
class StatusEnum(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"  ← Agregar
    DONE = "DONE"
    ERROR = "ERROR"
```

**Recomendación**: Usar Opción A (RUNNING) para MVP, Opción B en Phase 2

---

## ERROR 5: Línea 306 - mode=session_mode (ChatResponse)
**Contexto**: Same ChatResponse as ERROR 4
**Código Actual**:
```python
306:     mode=session_mode,  ❌ ERROR: String, not ModeEnum
```

**Problema**: session_mode es string (por línea 252-256)
**Solución**: Automática al corregir línea 252-256

---

## ERROR 6: Línea 341 - mode=mode_enum (ChatResponse)
**Contexto**: Plan execution response
**Código Actual**:
```python
335: response = ChatResponse(
336:     response=f"Plan executed. Mode: {session_mode}...",
337:     session_id=session_id,
338:     intent_id=intent_id,
339:     plan_id=plan_id,
340:     status=plan.status,
341:     mode=mode_enum,  ❌ ERROR: Is string from session_mode
342:     provider=provider,
...
```

**Código Previo**:
```python
333: mode_enum = session_mode  # It's already the right value
```

**Problema**: `mode_enum = session_mode` cuando session_mode es string
**Solución**: Automática al corregir línea 252-256

---

## ERROR 7: Línea 807 - Endpoint Return Type
**Contexto**: API route registration
**Código Actual**:
```python
805: try:
806:     app.add_api_route("/madre/task", _madre_task_alias, methods=["POST"])
807: except Exception:
808:     pass
```

**Función _madre_task_alias**:
```python
async def _madre_task_alias(req: MadreTaskAliasRequest):
    """..."""
    return ChatResponse(...) | dict[str, Any]  # ← Retorna ChatResponse O dict
```

**Problema**: FastAPI `add_api_route` espera un tipo de retorno único
**Solución**:
```python
# Opción A: Especificar response_model
app.add_api_route(
    "/madre/task",
    _madre_task_alias,
    methods=["POST"],
    response_model=Union[ChatResponse, Dict[str, Any]]
)

# Opción B: Usar Annotated (Python 3.9+)
from typing import Annotated, Union
response_type = Annotated[Union[ChatResponse, Dict], "response"]

# Opción C: Retornar siempre ChatResponse
async def _madre_task_alias(req: MadreTaskAliasRequest) -> ChatResponse:
    ...
    return ChatResponse(...)
```

**Recomendación**: Opción B o C (simplificar a ChatResponse siempre)

---

## ERROR 8: Línea 1095 - Unbound intent_log_id
**Contexto**: Función `/vx11/intent` - exception handler
**Código Actual**:
```python
1010: async def vx11_intent(req: CoreMVPIntentRequest):
1011:     """POST /vx11/intent..."""
1012:     try:
1013:         correlation_id = req.correlation_id or str(uuid.uuid4())
1014:         intent_log_id = MadreDB.create_intent_log(...)  ← Definido en try
1015:         ...
1016:     except Exception as e:
1017:         ...
1018:         MadreDB.close_intent_log(
1019:             intent_log_id,  ❌ ERROR: intent_log_id puede no estar definido
1020:             result_status="error",
1021:        )
```

**Problema**: Si error ocurre ANTES de línea 1014, intent_log_id nunca se define

**Solución**:
```python
1010: async def vx11_intent(req: CoreMVPIntentRequest):
1011:     """POST /vx11/intent..."""
1012:     correlation_id = req.correlation_id or str(uuid.uuid4())
1013:     intent_log_id: Optional[str] = None  ← Inicializar ANTES de try
1014:
1015:     try:
1016:         intent_log_id = MadreDB.create_intent_log(...)
1017:         ...
1018:     except Exception as e:
1019:         ...
1020:         if intent_log_id:  ← Safe check
1021:             MadreDB.close_intent_log(
1022:                 intent_log_id,
1023:                 result_status="error",
1024:             )
```

---

## ORDEN DE CORRECCIONES (Dependencias)

1. **PRIMERO**: Línea 1095 (inicializar intent_log_id)
   - No depende de nada
   - Crítica para safety

2. **SEGUNDO**: Líneas 252-256 (cambiar session_mode a ModeEnum)
   - Resuelve errores en 267, 306, 341
   - Facilita corrección de 305

3. **TERCERO**: Línea 305 (cambiar "WAITING" a StatusEnum.RUNNING)
   - Depende de corrección 2

4. **CUARTO**: Líneas 205-206 (remover .value en ChatResponse)
   - Simple find/replace
   - No depende de otras correcciones

5. **QUINTO**: Línea 807 (endpoint return type)
   - Última prioridad
   - Puede hacerse como refactor separado

---

## VALIDACIÓN POST-CORRECCIÓN

```bash
# 1. Syntax check
python3 -m py_compile madre/main.py

# 2. Type check
pylance check madre/main.py

# 3. Run tests
pytest tests/test_core_mvp.py -v

# 4. Curl test
bash test_core_mvp.sh
```

---

## ARCHIVOS RELACIONADOS

- `tentaculo_link/models_core_mvp.py`: Define StatusEnum, ModeEnum
- `madre/core/models.py`: Define ChatResponse (línea 106)
- `tests/test_core_mvp.py`: Tests del core MVP

---

**Generado**: 2026-01-01 16:00:00Z
**Análisis por**: GitHub Copilot
**Estado**: Listo para implementación
