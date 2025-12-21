# Auditoría Operator UI (Fase 1)

## Estructura relevante
- `operator/` → shim Python (`operator/backend/main.py` reexporta `operator_backend.backend.main_v7.py`), `operator/Dockerfile`.
- `operator_backend/frontend/` → Vite + React 18 + TS estricto. Entradas `src/main.tsx`, `src/App.tsx`, configuración `src/config.ts`, estilos `src/styles.css`.
- Componentes activos: `src/components/ChatPanel.tsx`, `HormigueroMapPanel.tsx`, `HormigueroPanel.tsx`, `ManifestatorPanel.tsx`, `ShubPanel.tsx`, `SelfOverviewPanel.tsx`, `StatusBar.tsx`, `MiniStatusPanel.tsx`, `MiniMapPanel.tsx`, `EventsTimelinePanel.tsx`, `LogsPanel.tsx`, `MadrePanel.tsx`, `SwitchQueuePanel.tsx`, `HermesPanel.tsx`, `MCPPanel.tsx`, `SpawnerPanel.tsx`, `BrowserPanel.tsx`, `DeepSeekHelper.tsx`, `ShortcutsPanel.tsx`.
- Estado/red: `src/hooks/useOperatorStreams.ts` (polling + WebSocket), `src/services/api.ts` (fetch wrappers + `wsConnect`), `src/config.ts` (URLs, token header).
- Legacy/no usados: `src/pages/*.jsx` + CSS, `src/api/operatorClient.js` (axios), `src/context/OperatorContext.jsx`, `components/ShubDashboard.vue`, `src/components/Layout.jsx` + CSS, `src/components/HormigueroPanel_fixed.tsx`, `build.sh`, `README_OPERATOR_UI_v7.md`, `dist/*` artefactos.
- Backend relevante: `operator_backend/backend/main_v7.py` (endpoints /ws), soportes `browser.py`, `cli_hub.py`, `web_bridge.py`, `switch_integration.py`, `services/*`.

## Endpoints y WS detectados (uso frontend)
- `/operator/system/status` (`src/services/api.ts`, `useOperatorStreams.ts`).
- `/operator/chat` (`ChatPanel.tsx`, `src/services/api.ts`).
- `/operator/session/{id}` (`ChatPanel.tsx`, `src/services/api.ts`).
- `/operator/manifestator/validate|patchplan|apply` (`ManifestatorPanel.tsx`, `src/services/api.ts`).
- `/operator/hormiguero/scan|clean` (`HormigueroMapPanel.tsx`, `HormigueroPanel.tsx`, `src/services/api.ts`).
- `/operator/bridge/health` (`useOperatorStreams.ts`), `/operator/bridge/deepseek_web`, `/operator/bridge/gemini_web` (`ChatPanel.tsx`).
- `/operator/shub/dashboard`, `/operator/shub/control` (`ShubPanel.tsx`, `src/services/api.ts`).
- `/operator/self/overview` (`SelfOverviewPanel.tsx`).
- Extras en código actual: `/operator/madre/*`, `/operator/spawner/*`, `/operator/switch/*`, `/operator/cli/*`, `/operator/hormiguero/events|queen_tasks`, `/ui/events` (polling eventos UI).
- WebSocket: cliente en `src/services/api.ts#wsConnect` -> `ws(s)://<OPERATOR_BASE_URL>/ws` (default `http://operator_backend:8011`). Backend en `operator_backend/backend/main_v7.py` expone `/ws` y `/ws/{session_id}`; eventos `bootstrap|status|heartbeat|echo`. Sin reconexión ni heartbeat del lado cliente.

## Estado de componentes clave (faltantes vs objetivo)
- `ChatPanel.tsx`: chat funcional con sesiones locales y feedback; sin streaming real, sin TanStack Query ni store global, sin virtualización >200 msgs, WebSocket no se usa para trazas, bridge web sin health gating completo.
- `HormigueroMapPanel.tsx`: mapa SVG estático con incidentes; sin React Flow, sin overlay D3 animado, sin drawer de detalle/acciones enriquecidas, acciones scan/clean sin cache/query.
- `ManifestatorPanel.tsx`: textarea simple; muestra JSON plano de validate/patch/apply; sin Monaco, sin markers, sin tabla de patch plan ni confirmaciones UX.
- `ShubPanel.tsx`: polling 8s dashboard, intents básicos; controles son stub, no valida health/bridge, sin estados deshabilitados.
- `SelfOverviewPanel.tsx`: polling 15s; sin cache, sin memo con selectors, sin loading states.

## Librerías
- Presentes: React 18, React DOM 18, Vite 4, TypeScript 5.9, @vitejs/plugin-react. Sin router.
- Ausentes (necesarias para el plan): Zustand, @tanstack/react-query, React Flow, Monaco, Tailwind/tokens, D3 (overlay ligero), virtualización (react-window/virt), testing stack (Vitest/RTL/Playwright no configurados en frontend).
- Legacy sin uso: axios (referenciado pero no en package.json), componente Vue `components/ShubDashboard.vue`.

## Obsoletos/duplicados dentro de Operator
- `src/pages/Chat.jsx`, `Dashboard.jsx`, `Resources.jsx` + CSS: UI antigua con axios/context; no usada por `App.tsx`.
- `src/api/operatorClient.js`, `src/context/OperatorContext.jsx`: cliente/contexto legacy.
- `src/components/Layout.jsx` + `Layout.css`: wrapper no referenciado.
- `src/components/HormigueroPanel_fixed.tsx`: duplicado de `HormigueroPanel.tsx`.
- `components/ShubDashboard.vue`: legado Vue.
- `build.sh`: bundle manual Node<18; fuera de flujo Vite.
- `README_OPERATOR_UI_v7.md`: roadmap 2025 desactualizado.
- `dist/*`: artefactos de build presentes en repo.

## Configuración sensible
- Tokens locales en `tokens.env` (y `tokens.env.master` / `tokens.env.sample`) en raíz; no exponer contenido. `.gitignore` ya los excluye, pero requieren rotación y variables de entorno en runtime.
- Config frontend usa `VITE_VX11_TOKEN` y `VITE_OPERATOR_API_URL`; valor por defecto apunta a `http://operator_backend:8011`.

## Riesgos y recomendaciones inmediatas
- Carga redundante por polling sin cache (status/events/bridge/shub). Integrar TanStack Query con `staleTime` y retries razonables.
- WebSocket sin reconexión/heartbeat → perder eventos silenciosamente. Implementar backoff + ping cada 30s y ruteo por tipo (`status_update`, `hormiguero_event`, `shub_event`, `browser_task/cli_call`).
- Sin estado global → re-render amplio y duplicación de lógica. Introducir Zustand slices (chat/traces/hormiguero/system/ui) con selectors.
- UI pesada en listas sin virtualización → riesgo de rendimiento. Virtualizar trazas/chat si >200 items.
- Manifestator/Hormiguero carecen de herramientas pro (Monaco, React Flow, overlays). Planear migración con lazy/code-splitting para contener bundle.
