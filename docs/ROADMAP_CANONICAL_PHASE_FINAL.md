# 🧭 ROADMAP CANÓNICO — VX11 v1.0 FASE FINAL
**Status:** EJECUCIÓN ORDENADA  
**Owner:** Tentáculo Link  
**Last Updated:** 2025-12-13 14:30 UTC

---

## 📍 ESTADO ACTUAL (COMPLETADO)

✅ **FASE V1-V4: Event Validation Middleware**
- Schemas canónicos (6 eventos)
- Validación en Tentáculo Link
- Normalización automática
- Aislamiento de Operator

✅ **Documentación Autoritativa**
- `OPERATOR_VX11_V8_CANONICAL.md` — Filosofía + UI
- `VX11_EVENT_MAP_CANONICAL.md` — Mapa de eventos
- `VX11_EVENT_SCHEMAS_CANONICAL.md` — Schemas exactos
- `.github/PROMPT_COPILOT_DEEPSEEK_CANONICAL.md` — Prompt definitivo

✅ **Sincronización**
- Git: 0 ahead / 0 behind
- Archivos: 4 commitados
- Status: LIMPIO

---

## 🧱 ESTRUCTURA FINAL (AUTORITATIVA)

```
tentaculo_link/
├── main_v7.py
│   ├── CANONICAL_EVENT_SCHEMAS ✅
│   ├── validate_event_schema() ✅
│   ├── normalize_event() ✅
│   ├── ConnectionManager.broadcast() ✅
│   └── (responsabilidad única: validar + rechazar + sintetizar + emitir)

docs/
├── OPERATOR_VX11_V8_CANONICAL.md ✅ (NO TOCAR)
├── VX11_EVENT_MAP_CANONICAL.md ✅ (REFERENCIA)
└── VX11_EVENT_SCHEMAS_CANONICAL.md ✅ (LEY DURA)

.github/
├── copilot-instructions.md ✅ (Guía AI)
└── PROMPT_COPILOT_DEEPSEEK_CANONICAL.md ✅ (Prompt definitivo)

operator/
├── src/hooks/ ✅ (Listeners solamente)
├── src/components/ ✅ (Renderers solamente)
└── src/types/ ✅ (Canonical unions solamente)

Principio de Oro:
  Operator escucha, muestra, confirma.
  Nunca interpreta, nunca decide, nunca valida.
```

---

## 🚀 PRÓXIMOS 3 PASOS (ORDEN NATURAL)

### 1️⃣ TESTS DE EVENTOS (UNITARIOS)
**Objetivo:** Validar que la validación funciona
**Duración:** 30 minutos
**Scope:** 10-15 tests unitarios

```python
# tests/test_event_validation.py

def test_canonical_event_accepted():
    """Evento válido → pasa"""
    event = {...}  # system.alert válido
    assert validate_event_schema(event) is not None

def test_invalid_payload_rejected():
    """Payload malformado → drop"""
    event = {...}  # Falta campo requerido
    assert validate_event_schema(event) is None

def test_oversized_payload_rejected():
    """Payload > max_size → drop"""
    event = {...}  # > 3KB
    assert validate_event_schema(event) is None

def test_non_canonical_event_rejected():
    """Evento fuera whitelist → drop"""
    event = {"type": "custom.event", ...}
    assert validate_event_schema(event) is None

# ... 10+ más
```

**Resultado esperado:**
- ✅ 100% pass rate
- ✅ Coverage > 85%
- ✅ Execution time < 10ms

---

### 2️⃣ CONTADOR DE CARDINALIDAD (MÉTRICA SIMPLE)
**Objetivo:** Detectar spam o loops
**Duración:** 20 minutos
**Scope:** Diccionario + endpoint DEBUG

```python
# En tentaculo_link/main_v7.py

class EventCardinalityCounter:
    """Track events/minute for debugging"""
    def __init__(self):
        self.counters = {}
        self.window_start = time.time()
    
    def increment(self, event_type: str):
        """Increment counter for event type"""
        if event_type not in self.counters:
            self.counters[event_type] = {"count": 0, "start": time.time()}
        self.counters[event_type]["count"] += 1
    
    def get_stats(self) -> dict:
        """Return events/min (reset if > 1 min elapsed)"""
        now = time.time()
        if now - self.window_start > 60:
            self.counters = {}
            self.window_start = now
        return {k: v["count"] for k, v in self.counters.items()}

cardinality = EventCardinalityCounter()

@app.get("/debug/events/cardinality")
async def get_event_stats():
    """DEBUG endpoint: event frequency stats"""
    return cardinality.get_stats()
```

**Resultado esperado:**
- ✅ Endpoint responde en < 1ms
- ✅ Memoria: < 1KB/evento
- ✅ Útil para detectar spam fuuro

---

### 3️⃣ VISUALIZACIÓN DE CORRELACIÓN (OPCIONAL)
**Objetivo:** Mostrar relaciones event→event
**Duración:** 45 minutos (si se ejecuta)
**Scope:** Grafo ligero en Operator

```python
# En Tentáculo Link: correlación de eventos
# En Operator: renderización en React Flow

EventA → EventB (relación temporal)
  ↓
Grafo DAG simple
  ↓
Debug timeline (ya existe)
```

**Nota:** Solo cuando 1️⃣ + 2️⃣ estén sólidos.

---

## 📋 CHECKLIST DE EJECUCIÓN

### Paso 1: Tests
- [ ] Crear `tests/test_event_validation.py`
- [ ] Implementar 10-15 tests unitarios
- [ ] Ejecutar: `pytest tests/test_event_validation.py -v`
- [ ] Verificar: pass rate 100%, coverage > 85%
- [ ] Commit + push

### Paso 2: Cardinalidad
- [ ] Implementar `EventCardinalityCounter` en main_v7.py
- [ ] Agregar endpoint `/debug/events/cardinality`
- [ ] Test manual: `curl http://localhost:8000/debug/events/cardinality`
- [ ] Verificar: respuesta JSON con conteos
- [ ] Commit + push

### Paso 3: Correlación (opcional)
- [ ] Extender diccionario de eventos con `related_events`
- [ ] Renderizar en Operator timeline
- [ ] Test E2E: verificar grafo en UI
- [ ] Commit + push (o posponer)

---

## 🔗 REFERENCIAS RÁPIDAS

| Archivo | Propósito | Estado |
|---------|-----------|:------:|
| [tentaculo_link/main_v7.py](tentaculo_link/main_v7.py) | Gateway + validación | ✅ LISTO |
| [docs/VX11_EVENT_SCHEMAS_CANONICAL.md](docs/VX11_EVENT_SCHEMAS_CANONICAL.md) | Schemas exactos | ✅ LISTO |
| [.github/PROMPT_COPILOT_DEEPSEEK_CANONICAL.md](.github/PROMPT_COPILOT_DEEPSEEK_CANONICAL.md) | Prompt IA | ✅ LISTO |
| tests/test_event_validation.py | Tests unitarios | 🟡 TODO |
| [operator/src/hooks/useHormiguero.ts](operator/src/hooks/useHormiguero.ts) | Listener pasivo | ✅ LISTO |

---

## ⚠️ REGLAS INMUTABLES

Mientras ejecutas los 3 pasos:

1. **NO modificar** `OPERATOR_VX11_V8_CANONICAL.md`
2. **NO añadir** nuevos eventos canónicos sin versioning
3. **NO añadir** lógica de decisión al Operator
4. **NO tocar** `tokens.env` ni `docker-compose.yml`
5. **NO crear** dependencias externas sin autorización

---

## 🎯 META FINAL

Al terminar Step 1-3:

- ✅ Sistema validado (unit tests 100% pass)
- ✅ Monitoreo activo (cardinalidad/min)
- ✅ Visibilidad completa (correlación opcional)
- ✅ Documentación autoritativa (3 docs canónicas)
- ✅ Prompt IA garantizado (exacto, sin drift)
- ✅ Operator 100% pasivo (listeners solamente)
- ✅ Tentáculo Link gatekeeping (whitelist O(1))

**Sistema estable. Listo para evolución.**

---

**FIN DE ROADMAP**

Próximo comando: `Adelante con Paso 1: Tests de eventos`
