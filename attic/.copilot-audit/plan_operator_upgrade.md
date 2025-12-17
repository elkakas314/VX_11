# Plan Operator UI Upgrade (Fases 2–6)

Base: .copilot-audit/operator_structure.json y operator_audit.md. Alcance exclusivo Operator frontend (`operator_backend/frontend/**` y `operator/**` shim si aplica). No tocar otros módulos. Mantener TypeScript estricto, sin exponer secretos.

## Archivos a modificar (ruta + propósito)
- operator_backend/frontend/package.json — agregar deps: zustand, @tanstack/react-query, reactflow, @monaco-editor/react, d3 (overlay ligero), tailwindcss/postcss/autoprefixer, react-window (virtualización), react-inspector, react-grid-layout; scripts si faltan (lint/test/build).
- operator_backend/frontend/vite.config.ts — alias `@/*`, integrar tailwind, asegurar puerto/WS; soportar env VITE_*.
- operator_backend/frontend/tsconfig.json (+tsconfig.node.json si aplica) — paths/strict, types de tests.
- operator_backend/frontend/.env.example — añadir VITE_OPERATOR_BASE_URL, VITE_WS_URL, VITE_VX11_TOKEN placeholders.
- operator_backend/frontend/src/config.ts — leer de envs nuevas; separar API_BASE/WS_BASE; headers seguros.
- operator_backend/frontend/src/services/api.ts — refactor a cliente con fetch/axios-lite + React Query friendly; endpoints confirmados.
- operator_backend/frontend/src/services/websocket.ts — nuevo cliente WS robusto (backoff, heartbeat 30s, routing).
- operator_backend/frontend/src/store/operatorStore.ts — Zustand slices: chat, traces, hormiguero, system, ui (selectors y memo).
- operator_backend/frontend/src/hooks/useOperatorStreams.ts — migrar/passthrough a store + react-query (o reemplazar con provider).
- operator_backend/frontend/src/App.tsx — envolver en QueryClientProvider + Zustand selectors + WebSocketProvider; lazy para bloques pesados.
- Componentes: ChatPanel.tsx, HormigueroMapPanel.tsx, HormigueroPanel.tsx, ManifestatorPanel.tsx, ShubPanel.tsx, SelfOverviewPanel.tsx, StatusBar.tsx, MiniStatusPanel.tsx, MiniMapPanel.tsx, EventsTimelinePanel.tsx, LogsPanel.tsx, MadrePanel.tsx, BrowserPanel.tsx — conectar a store/query; optimizar renders; dark theme tokens.
- operator_backend/frontend/src/styles.css (y/o tailwind) — tema dark, tokens accent1/2/ok/error, focus/ARIA.
- operator_backend/frontend/src/types/* — definir tipos de endpoints/WS; añadir TODO con guards si falta contrato.
- Tests: operator_backend/frontend/src/__tests__/* (Vitest+RTL) para ChatPanel y Manifestator; e2e skeleton Playwright.
- CI: .github/workflows/ci.yml (lint/typecheck/test/build) — solo si permitido en alcance Operator.
- .copilot-audit/merge_report.md — resumen final.

## Archivos a añadir
- operator_backend/frontend/src/store/operatorStore.ts
- operator_backend/frontend/src/services/websocket.ts
- operator_backend/frontend/src/query/client.ts (helper QueryClient)
- operator_backend/frontend/src/types/{api.ts,events.ts}
- operator_backend/frontend/src/components/hormiguero/{FlowCanvas.tsx, AntOverlay.tsx, NodeDrawer.tsx} (si se secciona)
- operator_backend/frontend/src/components/manifestator/{ManifestEditor.tsx, PatchPlanTable.tsx} (lazy/Monaco)
- operator_backend/frontend/src/components/chat/{MessageList.tsx, TraceSidebar.tsx} (si se modulariza)
- operator_backend/frontend/tailwind.config.js, postcss.config.js
- operator_backend/frontend/playwright.config.ts y tests/e2e skeleton
- operator_backend/frontend/src/__tests__/ChatPanel.test.tsx, ManifestatorPanel.test.tsx
- docs/SECRETS_ROTATE.md — pasos de rotación/mover a env/CI (sin claves)
- .copilot-audit/merge_report.md (al final)

## Archivos a archivar/retirar (mover a operator_backend/frontend/archived/20251212/)
- operator_backend/frontend/src/pages/Chat.jsx, Dashboard.jsx, Resources.jsx (+ CSS)
- operator_backend/frontend/src/api/operatorClient.js
- operator_backend/frontend/src/context/OperatorContext.jsx
- operator_backend/frontend/src/components/Layout.jsx, Layout.css
- operator_backend/frontend/src/components/HormigueroPanel_fixed.tsx
- operator_backend/frontend/components/ShubDashboard.vue
- operator_backend/frontend/build.sh
- operator_backend/frontend/README_OPERATOR_UI_v7.md
- operator_backend/frontend/dist/* (artefactos) — eliminar del repo; mantener en .gitignore

## Commits propuestos
1) chore: add operator upgrade plan — agrega .copilot-audit/plan_operator_upgrade.md  
2) chore: upgrade deps & config for operator UI — package.json, vite/tsconfig, tailwind/postcss, .env.example  
3) feat: add zustand store & react-query integration — store, query client, api refactor, App provider wiring  
4) feat: ws client with reconnect & routing — websocket service + provider + slices updates  
5) feat(hormiguero): react-flow map with d3 overlay — map refactor, drawer, scan/clean actions, lazy load  
6) feat(manifestator): monaco editor validate/patch/apply — editor, markers, patch table, guards  
7) feat(chat): optimistic chat with traces & bridge health — optimistic send, streaming fallback, sidebar traces  
8) feat(bridge/shub): bridge panel and shub dashboard controls — health gating, control actions, ws events  
9) style: dark theme tokens & perf tweaks — tailwind tokens, memo/selectors, virtualization, lazy splits  
10) chore: archive obsolete operator files — mover a archived/, actualizar .gitignore, docs/SECRETS_ROTATE.md  
11) test: add unit and e2e skeleton — Vitest/RTL tests, Playwright scaffold  
12) chore: ci workflow and final report — CI YAML, .copilot-audit/merge_report.md, git format-patch

## Riesgos / blockers
- Working tree ya modificado en múltiples módulos; cuidar commits solo con archivos Operator para no mezclar cambios ajenos.
- Schemas exactos de endpoints pueden variar; usar guards y TODO en src/types si falta contrato.
- Bundle size por Monaco/React Flow: usar lazy + Suspense y code splitting para contener.
- WS eventos pueden no incluir tipo esperado; agregar fallback handler y logs (silenciosos) con reconexión gradual.
- No exponer ni leer tokens.env; depender de VITE_VX11_TOKEN/env y documentar rotación.

## Estrategia de performance
- Zustand con selectors/memo para evitar renders globales.
- React Query con `staleTime`, `gcTime`, retries limitados y `suspense` opcional.
- Virtualización (react-window) en chat/trazas >200 items.
- Lazy load Monaco/React Flow/D3 overlay.
- Animaciones ligeras (CSS/requestAnimationFrame), evitar timers agresivos.

## Notas de seguridad
- Garantizar `.gitignore` incluye tokens.env y dist/.
- docs/SECRETS_ROTATE.md debe indicar rotación de claves y uso de variables de entorno/CI; no incluir valores.
