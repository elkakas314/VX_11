# AUDIT: OPERATOR FRONTEND — ESTADO REAL

Ruta auditada: `/home/elkakas314/vx11/operator`

Resumen

El frontend `operator/` es una app React + Vite + TypeScript que renderiza correctamente, incluye `src/` con `ChatView`, `useChat`, `event-client`, `TabsView`, y estilos. Sin embargo existen duplicados y artefactos:
- `operator/` incluye `node_modules/` y `dist/`.
- Existe otro frontend en `operator_backend/frontend/` con su propio `node_modules/` y Dockerfile.

1) Estructura (carpetas principales)

- `src/` — código fuente (components, hooks, services, types, config)
- `public/` — assets
- `node_modules/` — dependencias (dev)
- `dist/` — build artifacts
- `package.json`, `vite.config.ts`, `tsconfig.json`, `README.md`

2) Componentes clave

- `src/components/chat/ChatView.tsx` — UI principal del chat (input, messages, typing animation)
- `src/components/dashboard/TabsView.tsx` — router de pestañas (7 pestañas)
- `src/components/layout/Layout.tsx` — Sidebar + header
- `src/components/panels/*` — paneles (forensics, decisions, etc.)

3) Hooks

- `src/hooks/useChat.ts` — lógica de chat: backend probe (4 candidatos), persistencia localStorage (200 mensajes), fallback local echo, typing animation. Robustez alta.
- `src/hooks/useDashboardEvents.ts` — WebSocket client usage: subscribes a 6 eventos canónicos y reconexión.

4) Services

- `src/services/chat-api.ts` — probeChatApi(), sendChat(): maneja headers `X-VX11-Token`, timeouts, parsing de respuesta.
- `src/services/event-client.ts` — EventClient, subscribe/unsubscribe, reconnect.

5) Chat

- Dual-mode: intenta backend (POST /operator/chat u otros candidatos) y si falla cae a modo local (echo con hint). Esto evita pérdida de UX si backend no existe.
- Frontend espera una respuesta con `{ reply, session_id, metadata }`.

6) Tipos y config

- `src/types/*` — `chat.ts`, `canonical-events.ts` — tipos bien definidos.
- `src/config/vx11.config.ts` — URLs y envs (usa `import.meta.env`).

7) Qué existe / qué no

- Existe: UI completa, fallback local, probe HTTP, WebSocket client.
- No existe: backend real conectado por defecto en el entorno dev local (POST /operator/chat responde 404 si endpoint absent).

8) Duplicados e infrautilizados

- Código duplicado: otro frontend en `operator_backend/frontend/` con similar estructura. El repo mantiene ambas UIs.
- Infrautilizado: `reactflow` instalado pero pocas o ninguna integración real en la UI actual (consultar TabsView). Podría estar previsto para funciones futuras.

9) Riesgos y observaciones

- Riesgo de drift: si ambos frontends evolucionan por separado, el despliegue (docker-compose) puede usar uno mientras los desarrolladores editan el otro.
- Recomendación: elegir un frontend canónico y documentarlo.

10) Recomendaciones (sin cambios automáticos)

- Documentar claramente en `docs/` cuál frontend es canónico.
- Limpiar `dist/` y excluir `node_modules/` del control de versiones.
- Añadir tests de integración que verifiquen la ruta `POST /operator/chat` en entorno CI (mock Switch si es necesario).

---
Fecha: 2025-12-14
