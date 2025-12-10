# Operator UI v7 — Estructura, Mejoras y Roadmap

**Fecha:** 9 dic 2025  
**Objetivo:** Documentar Operator UI actual, proponer mejoras, preparar para v8

---

## 1. Estructura Actual

### 1.1. Stack Tecnológico
- **Framework:** React 18 (TypeScript)
- **Build:** Vite
- **Styling:** Inline CSS (sin Tailwind actualmente)
- **API Client:** Fetch API + custom `src/services/api.ts`
- **Deployment:** Nginx container + SPA

### 1.2. Árbol de Componentes

```
operator_backend/frontend/
├── src/
│   ├── main.tsx                    — Entry React
│   ├── App.tsx                     — Root component
│   ├── config.ts                   — Config (API URL, etc.)
│   ├── components/
│   │   ├── ChatPanel.tsx           — Chat UI (user/assistant messages)
│   │   ├── Dashboard.tsx           — System dashboard (module status)
│   │   ├── StatusBar.tsx           — Status bar (health overview)
│   │   ├── LogsPanel.tsx           — Logs viewer
│   │   ├── MadrePanel.tsx          — Madre orchestrator info
│   │   ├── SwitchQueuePanel.tsx    — Switch queue status
│   │   ├── HermesPanel.tsx         — Hermes resources
│   │   ├── MCPPanel.tsx            — MCP tools
│   │   ├── HormigueroPanel.tsx     — Hormiguero queen/ants
│   │   ├── SpawnerPanel.tsx        — Spawner processes
│   │   ├── ShubPanel.tsx           — Shubniggurath status
│   │   ├── MiniMapPanel.tsx        — Mini system map
│   │   └── MiniStatusPanel.tsx     — Mini status
│   └── services/
│       └── api.ts                  — API calls (sendChat, getStatus, etc.)
├── components/
│   └── ShubDashboard.vue           — Vue component (legacy? or used?)
├── public/
│   ├── index.html
│   └── nginx.conf
├── package.json                    — Dependencies
├── vite.config.ts                  — Build config
└── Dockerfile                      — Build + serve with Nginx
```

### 1.3. Componentes Clave

| Componente | Función | Estado | Mejora |
|-----------|---------|--------|--------|
| **ChatPanel** | Chat user/assistant | ✅ FUNCIONAL | Mejorar burbujas, mostrar session_id, typing indicator |
| **Dashboard** | Status 10 módulos | ⚠️ BÁSICO | Expandable modules, color-coded health, drill-down |
| **StatusBar** | Health overview | ✅ OK | OK |
| **LogsPanel** | Ver logs | ✅ OK | OK |
| **MadrePanel** | Info Madre | ⚠️ BÁSICO | Mostrar ciclo actual, P&P states |
| **SwitchQueuePanel** | Cola Switch | ✅ OK | OK |
| **HermesPanel** | Recursos | ✅ OK | Mostrar catálogo completo |
| **MCPPanel** | Herramientas | ✅ OK | Expandible |
| **ShubPanel** | Audio Shub | ⚠️ MOCK | Cuando Shub tenga real processing |

---

## 2. Estado Actual de UI

### 2.1. Fortalezas
- ✅ Componentes modularizados
- ✅ Chat funcional (aunque básico)
- ✅ Integración con backend backend/main_v7.py
- ✅ Auto-scroll mensajes
- ✅ Session ID tracking
- ✅ Error handling

### 2.2. Debilidades
- ❌ **Estilo:** Inline CSS, poco consistente, no responsive bien en mobile
- ❌ **Chat:** No parece a ChatGPT (sin burbujas claras, sin avatar, sin timestamp visible)
- ❌ **Módulos Panel:** Estático, no se puede expandir/contraer, poco info detallada
- ❌ **Historial:** Sin historial de sesiones, sin persistencia
- ❌ **Responsividad:** No adaptado a tamaños pequeños
- ❌ **Componente Vue legado:** `components/ShubDashboard.vue` ¿se usa?
- ❌ **Sin Tests:** Frontend sin tests

---

## 3. Mejoras Propuestas (Inmediatas - v7.1)

### 3.1. Chat Estilo ChatGPT

**Cambios:**
1. **Burbujas Claras:**
   - User messages: azul, derecha, sin avatar
   - Assistant messages: gris, izquierda, con badge "Assistant"

2. **Indicador de Escritura:**
   - Animación "escribiendo..." mientras `sending === true`

3. **Timestamp Visible:**
   - Mostrar hora en formato compacto (12:34 PM)

4. **Scroll Automático:**
   - Ya implementado, mantener

5. **Soporte para Markdown:**
   - Permitir respuestas con formato (bold, code, listas)

**Código Ejemplo (ChatPanel mejorado):**

```tsx
// Burbuja user (ejemplo pseudocódigo)
<div className="message user">
  <div className="bubble">
    {message.content}
    <span className="timestamp">{formatTime(message.timestamp)}</span>
  </div>
</div>

// Burbuja assistant
<div className="message assistant">
  <div className="avatar">A</div>
  <div className="bubble">
    {message.content}
    <span className="timestamp">{formatTime(message.timestamp)}</span>
  </div>
</div>

// Indicador de escritura
{sending && <div className="typing">✓ Escribiendo...</div>}
```

**CSS:**
```css
.message {
  display: flex;
  margin: 8px 0;
}

.message.user {
  justify-content: flex-end;
}

.message.user .bubble {
  background: #007AFF;
  color: white;
  border-radius: 18px 4px 18px 18px;
}

.message.assistant {
  justify-content: flex-start;
}

.message.assistant .avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #666;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  font-size: 12px;
  font-weight: bold;
}

.message.assistant .bubble {
  background: #e5e5e5;
  color: #000;
  border-radius: 4px 18px 18px 4px;
}

.bubble {
  padding: 12px 16px;
  max-width: 60%;
  word-wrap: break-word;
  font-size: 14px;
  line-height: 1.4;
}

.timestamp {
  font-size: 11px;
  opacity: 0.7;
  margin-left: 8px;
}

.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  color: #999;
  font-size: 12px;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}
```

---

### 3.2. Panel de Módulos Mejorado

**Cambios:**
1. **Expandible/Collapsible:**
   - Click en módulo → expande para mostrar detalles

2. **Color-Coded Health:**
   - Verde: UP, healthy
   - Amarillo: DEGRADED
   - Rojo: DOWN, error
   - Gris: UNKNOWN

3. **Detalles Detallados:**
   - Puerto
   - Version
   - Uptime
   - Memory usage
   - Últimas acciones

4. **Mini Action Menu:**
   - Botones para restart, logs, drill-down (si aplicable)

**Estructura Ejemplo:**

```tsx
<div className="modules-grid">
  {Object.entries(modules).map(([name, mod]) => (
    <ModuleCard key={name} name={name} module={mod} />
  ))}
</div>

// ModuleCard
<div className={`module-card ${getHealth(mod)}`}>
  <div className="header" onClick={() => setExpanded(!expanded)}>
    <span className={`health-badge ${getHealth(mod)}`} />
    <span className="name">{name}</span>
    <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
  </div>
  {expanded && (
    <div className="details">
      <p>Port: {mod.port}</p>
      <p>Version: {mod.version}</p>
      <p>Uptime: {mod.uptime}</p>
      <div className="actions">
        <button onClick={() => restart(name)}>Restart</button>
        <button onClick={() => viewLogs(name)}>Logs</button>
      </div>
    </div>
  )}
</div>
```

---

### 3.3. Historial de Sesiones

**Cambios:**
1. **Left Sidebar:**
   - Lista de sesiones recientes
   - Click → carga sesión anterior
   - Delete para borrar

2. **Persistencia:**
   - LocalStorage en cliente (or API endpoint para guardar sesiones)

3. **Indicador:**
   - "Session #123" visible al usuario

---

## 4. Mejoras Secundarias (v7.2)

- [ ] Responsive design (Tailwind o CSS Grid moderno)
- [ ] Dark mode refinado
- [ ] Buscar en chat history
- [ ] Export chat como markdown
- [ ] Integración real-time con WebSocket (no polling)
- [ ] Tests Jest + Vitest para componentes

---

## 5. Limpieza de Código

### 5.1. Remover/Archivar

- [ ] `components/ShubDashboard.vue` — ¿Se usa? Si no, mover a archive
- [ ] Componentes muertos o sin usar
- [ ] Código commented-out

### 5.2. Consolidar

- [ ] Usar CSS module o Tailwind (no inline CSS en todos lados)
- [ ] Centralizar tipos (TypeScript interfaces)
- [ ] Centralizar constantes de colores, tamaños, etc.

### 5.3. Validar

- [ ] ESLint + Prettier configurados
- [ ] Sin console.log en production
- [ ] Sin hardcoded URLs (usar `config.ts`)

---

## 6. Roadmap UI

| Versión | Mejoras | Timeline |
|---------|---------|----------|
| **v7.1** | Chat ChatGPT, panel expandible | Inmediato |
| **v7.2** | Responsive, historial | 1-2 semanas |
| **v7.3** | WebSocket, tests | 2-3 semanas |
| **v8.0** | Completo redesign si necesario | Post v7 |

---

## 7. Comandos de Desarrollo

```bash
# Instalar deps
cd operator_backend/frontend
npm install

# Dev server (hot reload)
npm run dev

# Build production
npm run build

# Preview build
npm run preview

# Lint (if configured)
npm run lint
```

---

## 8. Deployment

### Current (Nginx Container)
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY . .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Improvements
- [ ] Multi-stage build optimizado
- [ ] Cache busting en production
- [ ] Gzip compression en nginx.conf
- [ ] Security headers

---

## 9. Archivo de Configuración Esperado

```typescript
// src/config.ts (ejemplo mejorado)
const API_BASE_URL = process.env.VITE_API_URL || "http://localhost:8011";

export const config = {
  api: {
    baseURL: API_BASE_URL,
    chat: `${API_BASE_URL}/operator/chat`,
    status: `${API_BASE_URL}/operator/status`,
    modules: `${API_BASE_URL}/operator/modules`,
  },
  ui: {
    chatBubbleMaxWidth: "60%",
    sessionStorageKey: "operator_session",
    pollingInterval: 5000, // ms
  },
};
```

---

## 10. Conclusiones

- ✅ UI funcional, pero básica
- ⚠️ Necesita mejoras visuales (ChatGPT-like) e interactividad (expandible panels)
- 🎯 Roadmap claro: v7.1 (quick wins) → v7.2 (robustez) → v8 (redesign si necesario)

**No rompes nada existente.** Solo mejoras incrementales.

---

**Documento completado:** 9 dic 2025

