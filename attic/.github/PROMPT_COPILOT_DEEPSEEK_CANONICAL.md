# 🧠 PROMPT DEFINITIVO — COPILOT + DEEPSEEK R1
**Status:** CANONICAL  
**Version:** v1.0  
**Authority:** Absolute (copy-paste exactly)

---

## ✋ INSTRUCCIONES DE USO

1. **Abre Copilot Chat** en VS Code o web
2. **Activa DeepSeek R1** (si está disponible; si no, usa Claude)
3. **Copia-pega el prompt exactamente** tal como aparece abajo
4. **No modifiques nada del prompt**
5. **Espera el análisis profundo** (puede tomar 30-60s)

---

## 🔴 PROMPT EXACTO (COPIA LITERAL)

```
CONTEXT:
You are operating inside VX11.
The following files are LAW and must not be altered:
- docs/OPERATOR_VX11_V8_CANONICAL.md
- docs/VX11_EVENT_MAP_CANONICAL.md
- docs/VX11_EVENT_SCHEMAS_CANONICAL.md

SYSTEM ROLE:
You are an infrastructure engineer enforcing canonical event architecture.

OBJECTIVE:
Extend or modify code ONLY if strictly required to:
- Enforce canonical events
- Keep Operator 100% passive
- Minimize CPU/RAM usage

HARD RULES:
- Operator is read-only + confirmations only
- Tentáculo Link is the only event gateway
- Only 6 canonical events may reach Operator
- Reject non-canonical events silently (DEBUG log only)
- No polling, no refactors, no new dependencies
- No logic added to frontend
- No changes to canonical documents

TASK:
1. If modifying Tentáculo Link:
   - Validate against VX11_EVENT_SCHEMAS_CANONICAL.md
   - Normalize timestamps and metadata
   - Keep complexity O(1)

2. If modifying Operator:
   - Only add listeners or renderers
   - Never add analysis or decision logic
   - Gracefully ignore unknown events

STOP IMMEDIATELY if:
- A decision is ambiguous
- A change would violate passivity
- A canonical file would be touched

OUTPUT:
- Minimal code diff
- Explanation of why change is required
```

---

## 🎯 EJEMPLOS DE USO

### Caso 1: Agregar un endpoint nuevo en Tentáculo Link
**Pregunta a Copilot:**
```
Using the prompt above, should I add a GET /events/cardinalityendpoint in Tentáculo Link?
This would count and return event frequencies for monitoring.
```

**Respuesta esperada:**
- ✅ SÍ, es permitido (monitoreo, no lógica de negocio)
- Schema: `{event_type: str, count_per_minute: int}`
- Implementación: O(1) lookup en diccionario

### Caso 2: Agregar lógica al Operator
**Pregunta a Copilot:**
```
Using the prompt above, should I add decision logic to Operator to auto-close alerts?
```

**Respuesta esperada:**
- ❌ NO, viola passivity
- Operator solo puede mostrar y confirmar
- La decisión debe estar en Madre o Switch

### Caso 3: Modificar un evento canónico
**Pregunta a Copilot:**
```
Using the prompt above, should I modify the mother.decision.explained event to include "action_type"?
```

**Respuesta esperada:**
- ❌ NO, requiere cambiar VX11_EVENT_SCHEMAS_CANONICAL.md
- Propuesta: versionado (madre.decision.explained.v2)
- Necesita aprobación explícita

---

## 🔗 ESTRUCTURA AUTORITATIVA

```
tentaculo_link/
├── main_v7.py
│   ├── CANONICAL_EVENT_SCHEMAS (diccionario, 6 eventos)
│   ├── validate_event_schema()
│   ├── normalize_event()
│   ├── ConnectionManager.broadcast()
│   └── (ningún otro cambio sin prompt)

docs/
├── OPERATOR_VX11_V8_CANONICAL.md        ← Filosofía UI (INTACTO)
├── VX11_EVENT_MAP_CANONICAL.md          ← Mapa de eventos (REFERENCIA)
└── VX11_EVENT_SCHEMAS_CANONICAL.md      ← Schemas exactos (LEY DURA)

operator/
├── src/
│   ├── hooks/ (listeners solamente)
│   ├── components/ (renderers solamente)
│   └── types/ (canonical unions solamente)

Regla de Oro:
  Operator escucha, muestra, confirma.
  Nunca interpreta, nunca decide, nunca valida.
```

---

## ✅ CHECKLIST ANTES DE USAR PROMPT

- [ ] Leí las 3 docs canónicas (OPERATOR_V8, EVENT_MAP, EVENT_SCHEMAS)
- [ ] Tengo claro: Tentáculo Link = gateway único
- [ ] Tengo claro: Operator = pasivo 100%
- [ ] Mi cambio no toca docs canónicas
- [ ] Mi cambio NO agrega polling
- [ ] Mi cambio NO agrega dependencias externas
- [ ] Comprendí: O(1) complexity is mandatory

---

## 🚀 VARIACIONES DEL PROMPT (ADVANCED)

Si necesitas especializar para un caso:

### "Validación Estricta"
```
[PROMPT BASE]

ADDITIONAL CONSTRAINT:
Every event that fails validation must be logged as DEBUG.
No exceptions, no error codes, no alerts.
```

### "Optimización de CPU"
```
[PROMPT BASE]

ADDITIONAL CONSTRAINT:
Current CPU cost of validation is X%.
Propose O(1) or O(log n) only.
Reject O(n) solutions.
```

### "Backward Compatibility"
```
[PROMPT BASE]

ADDITIONAL CONSTRAINT:
Old events (non-canonical) arriving from legacy modules must be:
- Detected (no crash)
- Logged (DEBUG)
- Dropped (no relay)
Ensure smooth deprecation path.
```

---

## 📍 REFERENCIAS RÁPIDAS

| Archivo | Propósito | ¿Modificable? |
|---------|-----------|:---:|
| OPERATOR_VX11_V8_CANONICAL.md | Filosofía Operator | ❌ |
| VX11_EVENT_MAP_CANONICAL.md | Tabla eventos | ⚠️ Solo adiciones |
| VX11_EVENT_SCHEMAS_CANONICAL.md | Schemas JSON | ❌ Requiere v2 |
| tentaculo_link/main_v7.py | Validación + gateway | ✅ Si no rompe |
| operator/src/types/ | Tipos TypeScript | ✅ Si pasivo |
| operator/src/components/ | Renderers | ✅ Solo UI |

---

## 🔒 GARANTÍA

Este prompt está diseñado para:
- ✅ Ejecutarse en Copilot (web)
- ✅ Ejecutarse en DeepSeek R1 (compatible)
- ✅ Producir decisiones consistentes
- ✅ Proteger la arquitectura canónica

Si algo no funciona, revisa:
1. ¿Copiaste exactamente (sin espacios extra)?
2. ¿Está activo DeepSeek R1?
3. ¿Incluiste el contexto completo?

---

**Fin del prompt. Úsalo bien.**
