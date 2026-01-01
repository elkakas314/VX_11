# Resumen Visual: 8 Errores de Pylance en madre/main.py

## Tabla Resumen Rápida

| # | Línea | Tipo Error | Severidad | Descripción | Solución |
|---|-------|-----------|-----------|-------------|----------|
| 1 | 205 | Type Mismatch | 🔴 ALTO | `status=StatusEnum.DONE.value` en ChatResponse | Remover `.value` → `StatusEnum.DONE` |
| 2 | 206 | Type Mismatch | 🔴 ALTO | `mode=ModeEnum.MADRE.value` en ChatResponse | Remover `.value` → `ModeEnum.MADRE` |
| 3 | 253-254 | Type Mismatch | 🔴 ALTO | `session_mode = "AUDIO_ENGINEER"` string | Cambiar a `ModeEnum.AUDIO_ENGINEER` |
| 4 | 267 | Cascading Error | 🟡 MEDIO | `mode=session_mode` cuando es string | Automático al corregir #3 |
| 5 | 305 | Invalid Enum | 🔴 ALTO | `status="WAITING"` no existe en StatusEnum | Cambiar a `StatusEnum.RUNNING` |
| 6 | 306 | Cascading Error | 🟡 MEDIO | `mode=session_mode` cuando es string | Automático al corregir #3 |
| 7 | 341 | Cascading Error | 🟡 MEDIO | `mode=mode_enum` cuando es string | Automático al corregir #3 |
| 8 | 807 | Signature Mismatch | 🟡 MEDIO | Return type `ChatResponse \| dict` vs `Response` | Añadir response_model o unificar tipo |
| 9 | 1095 | Unbound Variable | 🟡 MEDIO | `intent_log_id` posiblemente sin definir | Inicializar `intent_log_id: Optional[str] = None` |

---

## Agrupación por Root Cause

### Grupo A: ModeEnum vs String (Cascading Errors)
```
Líneas: 253-254 (ROOT) → 267, 306, 341 (cascading)
Problema: session_mode asignado como string "AUDIO_ENGINEER" | "MADRE"
Impacto: 4 errores dependientes de 1 raíz
Solución: Cambiar a ModeEnum enum
```

### Grupo B: ChatResponse Enum Usage
```
Líneas: 205-206, 305-306, 341
Problema 1: `.value` no debe usarse en ChatResponse init
Problema 2: session_mode es string cuando espera ModeEnum
Solución: Remover `.value` + corregir Grupo A
```

### Grupo C: StatusEnum Valores Inválidos
```
Línea: 305
Problema: "WAITING" no es StatusEnum válido
StatusEnum válidos: QUEUED, RUNNING, DONE, ERROR
Solución: Usar RUNNING o crear WAITING enum
```

### Grupo D: Type System Issues
```
Línea: 807, 1095
Problema 1: Endpoint return type mismatch
Problema 2: Unbound variable en exception handler
Solución: Tipado correcto + inicialización preventiva
```

---

## Detalle por Error

### ERROR 1 & 2: ChatResponse `.value` Usage (Líneas 205-206)
```python
❌ INCORRECTO:
response = ChatResponse(
    status=StatusEnum.DONE.value,  # .value → string
    mode=ModeEnum.MADRE.value,      # .value → string
)

✅ CORRECTO:
response = ChatResponse(
    status=StatusEnum.DONE,         # Pass enum directly
    mode=ModeEnum.MADRE,            # Pass enum directly
)

🔍 RAZÓN: ChatResponse espera el enum type, no su valor string
```

### ERROR 3: Mode as String vs Enum (Línea 253-254)
```python
❌ INCORRECTO:
if dsl.domain == "audio":
    session_mode = "AUDIO_ENGINEER"  # Type: str
else:
    session_mode = "MADRE"            # Type: str

✅ CORRECTO:
if dsl.domain == "audio":
    session_mode = ModeEnum.AUDIO_ENGINEER  # Type: ModeEnum
else:
    session_mode = ModeEnum.MADRE           # Type: ModeEnum

🔍 RAZÓN: Modelos esperan ModeEnum, no string literals
```

### ERROR 4, 6, 7: Cascading Errors (Líneas 267, 306, 341)
```python
🎯 CAUSA RAÍZ: session_mode es string (ERROR 3)

💥 SÍNTOMAS:
- Línea 267: IntentV2(mode=session_mode)  # type error
- Línea 306: ChatResponse(mode=session_mode)  # type error
- Línea 341: ChatResponse(mode=mode_enum)  # mode_enum derived from session_mode

✅ SOLUCIÓN: Corregir ERROR 3 (session_mode = ModeEnum)
```

### ERROR 5: Invalid Status Value (Línea 305)
```python
❌ PROBLEMA:
response = ChatResponse(
    status="WAITING",  # WAITING no existe en StatusEnum
)

📋 StatusEnum valores válidos:
- QUEUED: Tarea encolada, no iniciada
- RUNNING: En ejecución
- DONE: Completada
- ERROR: Error durante ejecución

✅ SOLUCIÓN OPCIÓN A (Recomendada):
response = ChatResponse(
    status=StatusEnum.RUNNING,  # Indica: pendiente confirmación
)

✅ SOLUCIÓN OPCIÓN B (Phase 2):
# Agregar WAITING a StatusEnum:
class StatusEnum(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"  # ← Nuevo
    DONE = "DONE"
    ERROR = "ERROR"
```

### ERROR 8: Endpoint Return Type (Línea 807)
```python
❌ PROBLEMA:
async def _madre_task_alias(req):
    return ChatResponse(...) | dict  # Retorna ChatResponse O dict

app.add_api_route(
    "/madre/task",
    _madre_task_alias,  # Espera response_model específico
    methods=["POST"]
)

✅ SOLUCIÓN OPCIÓN A (Mejor):
from typing import Union

app.add_api_route(
    "/madre/task",
    _madre_task_alias,
    methods=["POST"],
    response_model=Union[ChatResponse, dict]
)

✅ SOLUCIÓN OPCIÓN B (Simplificar):
# Cambiar función para retornar siempre ChatResponse
async def _madre_task_alias(req) -> ChatResponse:
    ...
    return ChatResponse(...)
```

### ERROR 9: Unbound Variable (Línea 1095)
```python
❌ PROBLEMA:
async def vx11_intent(req):
    try:
        correlation_id = req.correlation_id or str(uuid.uuid4())
        intent_log_id = MadreDB.create_intent_log(...)  ← Línea 1
        # Si error aquí ↓
    except Exception as e:
        MadreDB.close_intent_log(
            intent_log_id,  ← ¿Definido? NO si error en línea 1
        )

✅ SOLUCIÓN:
async def vx11_intent(req):
    correlation_id = req.correlation_id or str(uuid.uuid4())
    intent_log_id: Optional[str] = None  ← Inicializar AFUERA try

    try:
        intent_log_id = MadreDB.create_intent_log(...)
        ...
    except Exception as e:
        if intent_log_id:  ← Safe check
            MadreDB.close_intent_log(intent_log_id, ...)
```

---

## Plan de Correcciones (Orden Recomendado)

### Fase 1: Safety & Core Fixes
**Prioridad**: ALTA  
**Tiempo**: ~5 min
```
1. Línea 1095: Inicializar intent_log_id
   - No depende de nada
   - Previene crashes
```

### Fase 2: Type System Fixes
**Prioridad**: ALTA  
**Tiempo**: ~10 min
```
2. Líneas 253-254: session_mode = ModeEnum
   - Resuelve 4 errores cascading
   
3. Línea 305: Cambiar status="WAITING"
   - Depende de fase 2
   
4. Líneas 205-206: Remover .value en ChatResponse
   - Simple find/replace
```

### Fase 3: API Cleanup
**Prioridad**: MEDIA  
**Tiempo**: ~10 min
```
5. Línea 807: Fix endpoint return type
   - Refactor, puede hacerse después
```

---

## Checklist de Implementación

- [ ] **1095**: Agregar `intent_log_id: Optional[str] = None`
- [ ] **253**: Cambiar `"AUDIO_ENGINEER"` → `ModeEnum.AUDIO_ENGINEER`
- [ ] **254**: Cambiar `_SESSIONS[...]["mode"]` → usar `.value`
- [ ] **255**: Cambiar `"MADRE"` → `ModeEnum.MADRE`
- [ ] **256**: Cambiar `_SESSIONS[...]["mode"]` → usar `.value`
- [ ] **305**: Cambiar `status="WAITING"` → `status=StatusEnum.RUNNING`
- [ ] **205**: Cambiar `StatusEnum.DONE.value` → `StatusEnum.DONE`
- [ ] **206**: Cambiar `ModeEnum.MADRE.value` → `ModeEnum.MADRE`
- [ ] **807**: Agregar `response_model` o unificar tipo retorno
- [ ] **Test**: `python3 -m py_compile madre/main.py`
- [ ] **Test**: `pytest tests/test_core_mvp.py -v`
- [ ] **Test**: `bash test_core_mvp.sh`

---

## Impacto Esperado

**Errores Resueltos**: 9 / 9  
**Breaking Changes**: 0  
**Syntax Errors**: 0 (post-fix)  
**Type Errors**: 0 (post-fix)  
**Runtime Impact**: Ninguno  

---

**Documento Generado**: 2026-01-01 16:00:00Z  
**Análisis Completado**: ✅ LISTO PARA IMPLEMENTACIÓN
