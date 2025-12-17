# VX11 — EVENT SCHEMAS CANONICAL
Version: v1.0
Status: CANONICAL
Scope: System-wide events (Operator-facing + synthetic)
Owner: Tentáculo Link

---

## 🔒 PRINCIPIOS INMUTABLES

- Este archivo define **el contrato exacto** de eventos VX11.
- Ningún módulo puede emitir eventos fuera de este esquema.
- Tentáculo Link valida, normaliza y rechaza eventos no conformes.
- Operator **solo escucha**, nunca interpreta ni corrige.
- Todo evento debe ser:
  - Semántico
  - Escaso
  - Pasivo
  - Versionable

---

## 📊 TAXONOMÍA DE SEVERIDAD

| Nivel | Código | Uso |
|------|-------|-----|
| L1 | INFO | Estado normal |
| L2 | WARNING | Atención |
| L3 | ERROR | Incidente |
| L4 | CRITICAL | Riesgo sistémico |

---

## 🧠 EVENTOS CANÓNICOS (WHITELIST)

---

### 1️⃣ system.alert

```yaml
event: system.alert
severity: L4
nature: incident
emitter: Tentáculo Link (synthetic)
consumer: Operator
frequency: rare
payload:
  type: object
  required:
    - alert_id
    - severity
    - message
    - timestamp
  properties:
    alert_id:
      type: string
    severity:
      type: string
      enum: [L3, L4]
    message:
      type: string
    correlated_events:
      type: array
      items: string
    timestamp:
      type: integer
max_payload_size: 2KB
```

---

### 2️⃣ system.correlation.updated

```yaml
event: system.correlation.updated
severity: L2
nature: meta
emitter: Tentáculo Link (synthetic)
consumer: Operator
frequency: low
payload:
  type: object
  required:
    - correlation_id
    - related_events
    - strength
    - timestamp
  properties:
    correlation_id: string
    related_events:
      type: array
      items: string
    strength:
      type: number
      minimum: 0
      maximum: 1
    timestamp: integer
max_payload_size: 2KB
```

---

### 3️⃣ forensic.snapshot.created

```yaml
event: forensic.snapshot.created
severity: L3
nature: forensic
emitter: Tentáculo Link
consumer: Operator
frequency: rare
payload:
  type: object
  required:
    - snapshot_id
    - reason
    - timestamp
  properties:
    snapshot_id: string
    reason: string
    timestamp: integer
max_payload_size: 1KB
```

---

### 4️⃣ madre.decision.explained

```yaml
event: madre.decision.explained
severity: L2
nature: decision
emitter: Madre
consumer: Operator
frequency: occasional
payload:
  type: object
  required:
    - decision_id
    - summary
    - confidence
    - timestamp
  properties:
    decision_id: string
    summary: string
    decision_tree:
      type: array
      items: string
    alternatives:
      type: array
      items: string
    confidence:
      type: number
      minimum: 0
      maximum: 1
    timestamp: integer
max_payload_size: 3KB
```

---

### 5️⃣ switch.tension.updated

```yaml
event: switch.tension.updated
severity: L2
nature: state
emitter: Switch
consumer: Operator
frequency: every_10s
payload:
  type: object
  required:
    - value
    - components
    - timestamp
  properties:
    value:
      type: integer
      minimum: 0
      maximum: 100
    components:
      type: object
      properties:
        load: number
        complexity: number
        risk: number
    timestamp: integer
max_payload_size: 1KB
```

---

### 6️⃣ shub.action.narrated

```yaml
event: shub.action.narrated
severity: L2
nature: narration
emitter: Shub
consumer: Operator
frequency: occasional
payload:
  type: object
  required:
    - action
    - reason
    - next_step
    - timestamp
  properties:
    action: string
    reason: string
    next_step: string
    timestamp: integer
max_payload_size: 2KB
```

---

## 🚫 EVENTOS PROHIBIDOS

- Cualquier evento no listado aquí
- Eventos de polling
- Eventos de ejecución directa
- Eventos con payload dinámico sin schema
- Eventos emitidos directamente a Operator sin Tentáculo Link

---

## 🔄 VERSIONADO

- Cualquier cambio incrementa versión del archivo
- Eventos deprecados deben marcarse y mantenerse 1 versión
- Tentáculo Link es responsable de compatibilidad

---

## ⚖️ AUTORIDAD

**Este archivo es canónico.**

Si un evento no está aquí, no existe.
