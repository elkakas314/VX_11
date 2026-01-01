# Análisis Completo de Errores de Pylance - madre/main.py

## Resumen General
**Archivo**: `/home/elkakas314/vx11/madre/main.py` (1154 líneas)
**Errores Reportados**: 8 total
**Root Cause**: Uso inconsistente de `StatusEnum`/`ModeEnum` - a veces como `.value` (string), a veces como enum

---

## 1. ARQUITECTURA DEL ARCHIVO

### Imports Críticos (Líneas 1-46)
```python
import httpx  ✅ PRESENTE
from tentaculo_link.models_core_mvp import StatusEnum, ModeEnum  ✅ PRESENTE
```

### Modelos Utilizados
- **ChatResponse** (línea 106 en core/models.py): Espera `status: StatusEnum`, `mode: ModeEnum`
- **IntentV2**: Espera `mode: str` (más flexible)
- **PlanV2**: Espera `status: str`

---

## 2. ERRORES IDENTIFICADOS (Actualizado con líneas nuevas)

### Grupo A: ChatResponse Initialization Errors (Líneas 205-206)
**Ubicación**: Función `/madre/intent` - Deep Seek response handling
```python
# Línea 205-206
response = ChatResponse(
    status=StatusEnum.DONE.value,  # ❌ Error: expects StatusEnum, got str
    mode=ModeEnum.MADRE.value,     # ❌ Error: expects ModeEnum, got str
```
**Problema**: ChatResponse espera enums, no strings
**Solución**: Remover `.value`

---

### Grupo B: String Mode Assignment (Línea 253-254)
**Ubicación**: Función `/madre/intent` - Mode detection
```python
# Línea 253-254
session_mode = "AUDIO_ENGINEER"  # ← Asignado como string
_SESSIONS[session_id]["mode"] = "AUDIO_ENGINEER"
```
**Problema**: `session_mode` debe ser `ModeEnum` para uso posterior

---

### Grupo C: ChatResponse with String Status (Línea 305)
**Ubicación**: Confirmation workflow
```python
# Línea 305
response = ChatResponse(
    status="WAITING",  # ❌ Error: expects StatusEnum, got Literal['WAITING']
    mode=session_mode,  # ❌ Error: session_mode es string, expects ModeEnum
```
**Problema**: "WAITING" no es StatusEnum válido (debería ser DONE/ERROR/QUEUED/RUNNING)

---

### Grupo D: Response Dict vs ChatResponse Mismatch (Línea 807)
**Ubicación**: Endpoint `_madre_task_alias`
```python
# Línea 807
app.add_api_route("/madre/task", _madre_task_alias, methods=["POST"])
```
**Problema**: `_madre_task_alias` retorna `ChatResponse | dict`, pero endpoint espera solo `Response`

---

### Grupo E: Unbound Variable (Línea 1095)
**Ubicación**: Exception handler en `/vx11/intent`
```python
# Línea 1095
MadreDB.close_intent_log(
    intent_log_id,  # ❌ Posiblemente desvinculado
```
**Problema**: `intent_log_id` se define en try block, pero se usa en except block

---

## 3. ANÁLISIS DETALLADO POR LÍNEA

| Línea | Error | Tipo | Severidad | Context |
|-------|-------|------|-----------|---------|
| 205 | `status=StatusEnum.DONE.value` → `ChatResponse` | Type Mismatch | ALTO | Usar `StatusEnum.DONE` |
| 206 | `mode=ModeEnum.MADRE.value` → `ChatResponse` | Type Mismatch | ALTO | Usar `ModeEnum.MADRE` |
| 253-254 | `session_mode = "AUDIO_ENGINEER"` | String vs Enum | ALTO | Usar `ModeEnum.AUDIO_ENGINEER` |
| 267 | `mode=session_mode` (str) → IntentV2 | Type Mismatch | MEDIO | session_mode es string |
| 305 | `status="WAITING"` | Invalid Status | ALTO | StatusEnum no tiene WAITING |
| 306 | `mode=session_mode` (str) → ChatResponse | Type Mismatch | ALTO | session_mode es string |
| 341 | Similar a 306 | Type Mismatch | ALTO | Same issue |
| 807 | Return type mismatch | Signature Error | MEDIO | endpoint expects Response |
| 1095 | `intent_log_id` unbound | Scope Error | MEDIO | Define fuera try/except |

---

## 4. PROBLEMAS RAÍZ

### Problema 1: StatusEnum vs .value inconsistency
**Ubicación**: Líneas 205-206, 1051-1146
**Raíz**: Dos contextos diferentes:
- **ChatResponse init**: Espera `StatusEnum` enum (NO .value)
- **Dict response**: Necesita `.value` para JSON serialización

**Evidencia**:
```python
# INCORRECTO (línea 205-206)
response = ChatResponse(status=StatusEnum.DONE.value)  # ChatResponse espera enum

# CORRECTO (línea 205-206)
response = ChatResponse(status=StatusEnum.DONE)  # Pass enum directly

# CORRECTO (línea 1051)
{"status": StatusEnum.QUEUED.value}  # Dict needs string value
```

### Problema 2: Mode Type Confusion
**Ubicación**: Líneas 253-254, 267, 306, 341
**Raíz**: `session_mode` asignado como string, pero modelos esperan `ModeEnum`

**Flujo Problemático**:
```python
session_mode = "AUDIO_ENGINEER"  # ← String
# ...
intent = IntentV2(mode=session_mode)  # ← Espera ModeEnum o str
# ...
response = ChatResponse(mode=session_mode)  # ← Espera ModeEnum
```

### Problema 3: Invalid StatusEnum Values
**Ubicación**: Línea 305
**Raíz**: StatusEnum define {QUEUED, RUNNING, DONE, ERROR}, pero código pasa "WAITING"

**Análisis**:
- StatusEnum válidos: QUEUED, RUNNING, DONE, ERROR
- StatusEnum inválidos: WAITING, PENDING

---

## 5. PLAN DE CORRECCIONES

### Corrección 1: Líneas 205-206 (ChatResponse status/mode)
```python
# De:
status=StatusEnum.DONE.value,
mode=ModeEnum.MADRE.value,

# A:
status=StatusEnum.DONE,
mode=ModeEnum.MADRE,
```

### Corrección 2: Líneas 253-254 (session_mode assignment)
```python
# De:
session_mode = "AUDIO_ENGINEER"
_SESSIONS[session_id]["mode"] = "AUDIO_ENGINEER"

# A:
session_mode = ModeEnum.AUDIO_ENGINEER if dsl.domain == "audio" else ModeEnum.MADRE
_SESSIONS[session_id]["mode"] = session_mode.value
```

### Corrección 3: Línea 305 (Invalid WAITING status)
```python
# De:
status="WAITING",

# A:
status=StatusEnum.RUNNING,  # O crear StatusEnum.WAITING si es necesario
```

### Corrección 4: Líneas 267, 306, 341 (mode parameter)
```python
# Automático una vez corregida línea 253-254, ya que session_mode será ModeEnum
```

### Corrección 5: Línea 807 (endpoint return type)
```python
# De:
app.add_api_route("/madre/task", _madre_task_alias, methods=["POST"])

# A:
app.add_api_route("/madre/task", _madre_task_alias, methods=["POST"], response_model=ChatResponse | dict)
# O tipado mejor: use Union
```

### Corrección 6: Línea 1095 (unbound intent_log_id)
```python
# Función vx11_intent debe inicializar:
async def vx11_intent(req: CoreMVPIntentRequest):
    correlation_id = req.correlation_id or str(uuid.uuid4())
    intent_log_id: Optional[str] = None  # ← Inicializar antes de try

    try:
        intent_log_id = MadreDB.create_intent_log(...)  # Asignar en try
    except Exception as e:
        if intent_log_id:  # ← Safe check
            MadreDB.close_intent_log(intent_log_id, ...)
```

---

## 6. IMPACTO DE CORRECCIONES

### Sin Breaking Changes
✅ Todas las correcciones son compatibles hacia atrás
✅ No afectan contratos de API
✅ No requieren cambios en BD

### Tests Necesarios
- Verificar ChatResponse initialization
- Probar mode detection (audio vs normal)
- Probar intent_log_id cleanup

---

## 7. RESUMEN EJECUTIVO

| Aspecto | Estado | Acción |
|---------|--------|--------|
| **Imports** | ✅ Completos | Ninguna |
| **StatusEnum usage** | ⚠️ Inconsistente | Remover `.value` en ChatResponse |
| **ModeEnum usage** | ⚠️ Inconsistente | Convertir strings a ModeEnum |
| **Invalid statuses** | ❌ "WAITING" | Reemplazar con RUNNING o crear WAITING |
| **Unbound variables** | ⚠️ intent_log_id | Inicializar en entrada de función |
| **Endpoint types** | ⚠️ Response mismatch | Añadir response_model |

---

**Próximos Pasos**: Implementar correcciones siguiendo orden de dependencias
1. Línea 1095 (init intent_log_id)
2. Líneas 253-254 (ModeEnum)
3. Línea 305 (StatusEnum válido)
4. Líneas 205-206 (ChatResponse)
5. Línea 807 (endpoint type)
