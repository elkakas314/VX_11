# 🧠 REDISEÑO CANÓNICO — OPERATOR VX11 (v8.0)

## 📋 RESUMEN EJECUTIVO

Operator VX11 se redefine como **interfaz cognitiva pura**: observación, conversación y confirmación. Manteniendo los 5 pilares canónicos (Dashboard, Hormiguero, Chat, Manifestator, Shub), se añaden mejoras alineadas con el principio de "cerebro externo". Todas las mejoras son de visualización o confirmación, nunca de ejecución. La arquitectura mantiene Tentáculo Link como único gateway, WS como transporte principal, y frontend sin lógica de negocio. El resultado es un Operator más informativo pero igual de pasivo, que maximiza claridad minimizando CPU.

---

## 🔧 REDISEÑO OPERATOR (ESTRUCTURADO)

### **Nueva Jerarquía de Pantallas**

```
OPERATOR v8.0
├── 🏠 Dashboard (default)
│    ├── Hormiguero Mini-Mapa (centro)
│    ├── Panel Estado VX11
│    │   ├── Madre: estado/tono
│    │   ├── Switch: routing activo
│    │   ├── Hermes: modelos cargados
│    │   └── Health: recursos (semáforo)
│    ├── Alertas Contextuales
│    └── Quick Actions (solo confirmaciones)
├── 🐜 Hormiguero Visual (vista expandida)
│    ├── Reina + 8 tipos hormigas (iconografía fija)
│    ├── Incidentes como edges etiquetados
│    ├── Feromonas: gradiente de color + intensidad
│    └── Panel Detalle (click → info estática)
├── 💬 Chat Madre
│    ├── Canal 1: Conversación humana
│    ├── Canal 2: Decisiones auto-explicadas
│    └── Canal 3: Peticiones de permiso
├── 📋 Manifestator
│    ├── Modo Drift Viewer (read-only)
│    ├── Modo Plan Comparator (before/after)
│    └── Confirmación Triple Check
├── 🔊 Shub Narrativo
│    ├── Timeline Audio (qué + por qué)
│    ├── Presets Aplicables (solo con confirmación)
│    └── Acciones Reversibles (último paso)
└── 🕐 Timeline Forense (nueva)
     ├── Eventos VX11 cronológicos
     ├── Filtros por módulo/severidad
     └── Snapshots guardados
```

---

## 🚀 MEJORAS PROPUESTAS (ALINEADAS)

### **1. Timeline Forense Integrada**
- **Qué**: Lista cronológica de eventos VX11
- **Dónde**: Panel lateral colapsable
- **Reglas**: 
  - Solo lectura
  - Max 1000 eventos en frontend
  - Filtros simples (módulo, tipo, severidad)
  - Enlace a snapshots guardados

### **2. Sistema de Snapshots**
- **Qué**: Captura estado VX11 en tiempo t
- **Cómo**: Botón "Capture Now" en Dashboard
- **Almacén**: Backend (no local)
- **Uso**: Comparación en Manifestator

### **3. Modo Freeze Mejorado**
- **Interfaz**: Toggle grande en Dashboard
- **Efecto**: Bloquea ejecución automática
- **Visual**: Banner rojo "FROZEN" en todas las pantallas
- **Comportamiento**: Madre sigue observando, no actúa

### **4. Perfil Humano como Hint**
- **Sección**: "Preferencias" (ajustes de UI)
- **Contenido**:
  - Slider Agresividad (1-10) → hint para Madre
  - Toggle Coste vs Calidad → hint para Switch
  - Nivel de Intervención (alto/medio/bajo) → hint para alertas
- **Regla**: NO afecta lógica directamente, solo sugiere

### **5. Visualización de Flujos Mejorada**
- **En Hormiguero**: 
  - Animación sutil de feromonas (CSS, no JS pesado)
  - Tooltip con metadatos (no datos crudos)
  - Agrupación visual de incidentes relacionados
- **En Dashboard**:
  - Mini-gráfico de actividad (last 24h)
  - Solo 3 estados: normal, alerta, crítico

### **6. Reducción de Ruido Visual**
- **Sistema de Prioridades**:
  - Nivel 1 (Crítico): Rojo, requiere atención
  - Nivel 2 (Alerta): Amarillo, observación
  - Nivel 3 (Info): Gris, colapsable
- **Regla**: Por defecto mostrar solo Nivel 1-2

---

## 📡 ARQUITECTURA DE EVENTOS

### **WebSocket Events (Tentáculo Link → Operator)**
```
1. hormiguero.state_update
   - {nodes, edges, pheromones, timestamp}
   - Frecuencia: 2-5s (depende de carga)

2. madre.message
   - {type: "query"|"explain"|"permission", content, urgency}
   
3. system.alert
   - {module, severity, message, suggested_action}
   
4. manifest.drift_detected
   - {before_snapshot, after_snapshot, plan}
   
5. shub.narrative
   - {action, reason, next_step}
   
6. task.progress
   - {task_id, status, progress_%}
```

### **HTTP Polling (Fallback/Low Priority)**
```
GET /api/vx11/health          // Cada 60s si WS caído
GET /api/vx11/events?last_id= // Timeline, cada 120s
GET /api/vx11/snapshots       // Al abrir Manifestator
```

### **Operator → Backend (Solo Intents)**
```
POST /confirm {action: "authorize"|"deny", context}
POST /chat    {message: "texto humano"}
POST /freeze  {state: true|false}
POST /profile {preferences: hints}
```

---

## ⚡ NOTAS DE BAJO CONSUMO

### **Frontend Optimization**
1. **Canvas vs SVG**: Hormiguero usa Canvas estático, redibuja solo al recibir WS
2. **Virtual Scrolling**: Timeline forense muestra max 50 eventos visibles
3. **Throttling WS**: 
   - Normal: 1 mensaje/2s
   - Crítico: 1 mensaje/500ms
4. **No Polling Agresivo**: 
   - Health check cada 60s solo si WS inactivo > 30s
5. **Cache Limitado**: 
   - Max 100 eventos en memoria
   - Max 5 snapshots cargados

### **Backend Considerations**
1. **Tentáculo Link comprime** datos antes de enviar
2. **Solo cambios delta** en hormiguero updates
3. **Madre resume** mensajes largos (>500 chars)

---

## ✅ CHECKLIST IMPLEMENTACIÓN

### **Fase 1: Core Canónico**
- [ ] Dashboard con layout 3-columnas (Hormiguero mini, Estado, Alertas)
- [ ] Conexión WebSocket a Tentáculo Link
- [ ] Pantalla Hormiguero con Canvas básico
- [ ] Chat Madre con 3 canales diferenciados
- [ ] Manifestator en modo solo-lectura inicial
- [ ] Shub con timeline narrativa básica

### **Fase 2: Mejoras Visuales**
- [ ] Sistema de prioridades (3 niveles)
- [ ] Animaciones CSS de feromonas (keyframes simples)
- [ ] Panel Timeline Forense colapsable
- [ ] Modo Freeze con toggle global
- [ ] Perfil Humano (preferencias como hints)

### **Fase 3: Optimización**
- [ ] Throttling WS implementado
- [ ] Virtual scrolling en timeline
- [ ] Compresión de datos en Tentáculo Link
- [ ] Cache límites aplicados
- [ ] Fallback a polling (health cada 60s)

### **Fase 4: Validación**
- [ ] Operator NO ejecuta lógica (auditoría código)
- [ ] Todo pasa por Tentáculo Link (verificar endpoints)
- [ ] CPU frontend < 15% en reposo
- [ ] WS mensajes < 5KB promedio
- [ ] Confirmación humana requerida para acciones

---

## 🎯 PRINCIPIO FINAL

**"Operator es un espejo, no un motor. Refleja VX11, no lo dirige."**

Cada pixel, cada evento, cada interacción debe pasar este test: ¿Estoy mostrando algo que ya ocurrió o pidiendo permiso para lo próximo? Si la respuesta es "ejecutando", el diseño está roto.

---

**ENTREGABLE**: Este diseño canónico extendido mantiene control humano radical, minimiza consumo de recursos, y proporciona mayor claridad sin añadir complejidad. Operator sigue siendo interfaz pura, mientras VX11 (Madre, Switch, Hermes, Hormiguero, Manifestator, Shub) contiene toda la inteligencia.
