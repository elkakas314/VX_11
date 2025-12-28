# PROMPT 9 — VX11 OPERATOR: PULIDO INTENSIVO + INTEGRACIÓN VISOR AVANZADO
## DeepSeek R1 — ARQUITECTO + IMPLEMENTADOR QUIRÚRGICO VX11

---

## CONTEXTO MISIÓN

**Repositorio**: `/home/elkakas314/vx11`  
**Fecha**: 28 de diciembre de 2025  
**Estado Previo**: Operator P0 cerrado (API en tentaculo_link, UI servida estática)  
**Objetivo**: Pulir Operator UI (UX + visual), integrar visor avanzado (según requisitos), dejar todo bonito y funcional SIN romper invariantes.

---

## 0) INVARIANTES DURAS (NO NEGOCIABLES)

```
1) Single Entrypoint: TODO externo entra por tentaculo_link:8000
   - Prohibido frontend llamando a 8001 (madre), 8002 (switch), 8003 (hermes), etc.
   - Proxy obligatorio en tentaculo_link

2) Runtime Default: policy = solo_madre
   - Solo: madre + redis + tentaculo_link UP
   - switch/hermes/hormiguero/spawner/operator_backend: OFF_BY_POLICY
   - UI debe funcionar "degradado" sin que esto sea error

3) operator_backend ELIMINADO
   - Prohibido resucitarlo
   - API vive en tentaculo_link:/operator/api/*
   - NO hay :8011

4) Cambios Mínimos + Auditables
   - Evidencia en docs/audit/<TIMESTAMP>_OPERATOR_P9_*/
   - Nada destructivo fuera de allowlist (CLEANUP_EXCLUDES_CORE.txt)

5) Seguridad
   - x-vx11-token obligatorio en /operator/api/*
   - Mantener guards existentes
   - Read-only por defecto

6) Persistencia
   - Tokens (.env files) nunca commiteados
   - BD intacta
   - Docker-compose.yml sin cambios de estructura
```

---

## 1) BOOTSTRAP OBLIGATORIO

**LEER PRIMERO** (falta = bloqueo):

```
docs/audit/CLEANUP_EXCLUDES_CORE.txt
docs/audit/DB_SCHEMA_v7_FINAL.json
docs/audit/DB_MAP_v7_FINAL.md
docs/audit/PERCENTAGES.json
docs/audit/SCORECARD.json
docs/canon/INDEX.json
docker-compose.yml (perfiles + policy)
tentaculo_link/main_v7.py (lines 1-220, /operator/ui mount, /operator/api router)
operator/frontend/vite.config.ts, package.json, tsconfig.json
operator/frontend/src/services/api.ts (endpoints actuales)
operator_ui_visibility_diagnostic.sh (si existe)
```

**EJECUTAR SNAPSHOT** (guardar en docs/audit/<TIMESTAMP>_OPERATOR_P9_BASELINE/):

```bash
git status --porcelain=v1
git log --oneline -5
docker compose ps
curl -s http://localhost:8000/health | jq .
curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/status | jq .
curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/status | jq .
```

---

## 2) ESTADO BASE (ASUMIR COMO CIERTO)

✅ Operator UI se sirve estático desde `/operator/ui` (StaticFiles dist)  
✅ Operator API P0 vive en `/operator/api/*` (tentaculo_link)  
✅ Policy activa: solo_madre (switch/hermes/hormiguero/spawner OFF_BY_POLICY)  
✅ Frontend debe funcionar degradado aunque switch esté KO  
✅ Último commit: `bc1e03f vx11: Operator P0 close — API in tentaculo_link + UI stable`

---

## 3) 🛑 PAUSA OBLIGATORIA: PEDIR INPUT DEL VISOR AVANZADO

**DETENTE AQUÍ**. No hagas nada más hasta que el usuario pegue el TXT.

**MENSAJE A USUARIO**:

```
Para poder implementar el visor avanzado de Operator correctamente,
necesito que pegues aquí el archivo TXT con la descripción de 
funciones/paneles/endpoints que quieres que tenga.

Formato esperado:
- Descripción de cada feature (qué es, qué hace, dónde se muestra)
- Datos que necesita (endpoints API, estructura JSON)
- Interactividad (solo lectura, botones, inputs)
- Prioridad: P0 (imprescindible), P1 (deseable), P2 (futuro)

Por favor, pega el TXT completo:
---
[AQUÍ VA EL TXT]
---
```

**CUANDO RECIBAS EL TXT**:

A) Parsearlo y extraer lista de requisitos (una fila = un requisito)
B) Clasificar: P0 / P1 / P2
C) Crear matriz trazable: `docs/audit/<TIMESTAMP>_OPERATOR_P9_VISOR_REQUIREMENTS.md`
   ```markdown
   | ID  | Descripción | Prioridad | Endpoint(s) | Archivo(s) | Estado | Notas |
   |-----|-------------|-----------|-------------|------------|--------|-------|
   | V1  | Panel Chat  | P0        | /operator/api/chat | ChatPanel.tsx | TODO | ... |
   | V2  | Scorecard   | P0        | /operator/api/scorecard | ScorePanel.tsx | TODO | ... |
   | ... | ... | ... | ... | ... | ... | ... |
   ```

---

## 4) TRABAJO: 4 TAREAS ATÓMICAS

### TAREA 1 — Auditoría + Plan Ejecutable (SIN CAMBIOS)

**Entregable**: `docs/audit/<TIMESTAMP>_OPERATOR_P9_PLAN.md`

**Incluir**:
- Resumen de cambios planeados
- Riesgos identificados + mitigación
- Archivos a tocar + líneas aprox.
- Endpoints nuevos (si aplica)
- Criterios P0/P1 para esta tarea
- Matriz de requisitos del visor (del TXT parseado)
- Timeline estimado

**Guardar en**:
```
docs/audit/<TIMESTAMP>_OPERATOR_P9_BASELINE/
  - git_snapshot.txt
  - docker_snapshot.txt
  - health_checks.json
  - plan.md
```

---

### TAREA 2 — Pulido Visual + UX (Frontend)

**Objetivo**: UI "acabada", oscura, usable, sin glitch.

**Requisitos Mínimos**:

1. **Layout Sólido**
   - Navegación clara (tabs o sidebar)
   - Responsive (no rompe en móvil ni escritorio)
   - Consistent spacing/alignment

2. **Estados** (✨ CRÍTICO)
   - Loading: skeleton screens / spinners
   - Error boundaries: mensajes claros (no crashes)
   - Empty states: especialmente OFF_BY_POLICY
     ```
     "⊘ Switch is OFF by policy (solo_madre mode)
      Chat unavailable until policy changes."
     ```
   - Success: confirmación visual de acciones

3. **Chat Panel** (si está en requisitos visor)
   - Scroll automático a último mensaje
   - Markdown básico (`**bold**`, `_italic_`, `` `code` ``)
   - Copy button en bloques código
   - Historial por sesión (botón "Clear" visible)
   - Indicador: "typing...", "degraded", etc.

4. **Status/Power/Scorecard** (si están en requisitos)
   - Legible: colores contrastantes, fonts claros
   - Badges para policy (solo_madre = azul)
   - Badges para estado (ok=🟢, degraded=🟡, off_by_policy=⚪)
   - Gráficos si procede (pero NO D3 pesado; mini canvas o SVG OK)

5. **Topología** (si está en requisitos)
   - Render JSON + mini visual (grafo simple)
   - Estado de cada nodo (UP, OFF_BY_POLICY, ARCHIVED)
   - Fácil de leer, no necesita interact.

6. **Panel Debug** (toggle opcional)
   - Botón 🔧 (bottom-right)
   - Click → muestra JSON crudo de última respuesta
   - Copy JSON button
   - Close button
   - NO imprime en consola (todo UI)

7. **Degradación Graceful** (✨ CRÍTICO)
   - Si switch OFF: chat muestra "degraded" (no error)
   - Si hermes OFF: panel hormigas muestra "not loaded" (no rompe)
   - Si hormiguero OFF: health panel muestra "off_by_policy" (no vacío)
   - Nunca: blank page, 500 error, infinite loading

**TypeScript / Red Squiggles**:
- Asegurar types correctos
- `tsconfig.json`: `"types": ["node", "vitest/globals"]` (si hay tests)
- `vitest.config.ts`: `globals: true` (si usas describe/it global)
- Imports bien: no `default exports` raros
- Build: `npm run build` debe pasar sin warnings de unused code

---

### TAREA 3 — Integración Funcional (API ↔ UI) + Visor (según TXT)

**Ajustes API** (`tentaculo_link/main_v7.py`):
- Asegurar que `/operator/api/*` endpoints devuelven shapes estables
- Si visor requiere endpoint nuevo: agregarlo (pero P0 = 200 + data estable)
- OFF_BY_POLICY modules: responder `{status:"off_by_policy", reason:"solo_madre"}` (NO 500)

**Ajustes Frontend** (`operator/frontend/src/services/api.ts`):
- Todoo via `/operator/api/*` (single entrypoint)
- Métodos por endpoint:
  ```typescript
  async status()
  async modules()
  async chat(msg, sessionId)
  async events(limit?)
  async scorecard()
  async topology()
  // + nuevos según TXT
  ```

**Implementar Visor** (según TXT parseado):
- Crear componentes para cada requisito P0 del visor
- Ubicar en `operator/frontend/src/components/`
- Conectar a API via `api.ts`
- Mostrar datos reales o "off_by_policy" (nunca stubs)

**Opcionales P1** (si no rompen nada):
- SSE streaming para eventos (degradable a polling)
- Dark mode toggle (respeta preferencia del SO)
- Responsive mobile-first

---

### TAREA 4 — Verificación P0 + Evidencia + Commits

**CRITERIOS P0** (DEBE PASAR TODO):

#### Frontend
```bash
npm ci
npm run build
# Output: ✓ built in X.XXs (no warnings de unused, no errors)

npm test 2>/dev/null || echo "No tests configured"
# Si hay tests: PASS
```

#### Backend
```bash
python3 -m py_compile tentaculo_link/main_v7.py
# Output: [sin output] = OK
```

#### Runtime (solo_madre policy)
```bash
# Services
docker compose ps
# Esperado: madre, redis, tentaculo_link UP; switch/hermes/etc DOWN

# Static UI
curl -s http://localhost:8000/operator/ui/ | grep -q "<title>"
# Output: [exit 0] = página carga

# CSS/JS assets
curl -sI http://localhost:8000/operator/ui/assets/index-*.css | grep -q "200"
curl -sI http://localhost:8000/operator/ui/assets/index-*.js | grep -q "200"
# Output: [ambas 200] = OK

# API endpoints
curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/status | jq ".policy" | grep -q "solo_madre"

curl -s -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/modules | jq ".modules.switch.status" | grep -q "OFF_BY_POLICY"

curl -s -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}' \
  http://localhost:8000/operator/api/chat | jq ".degraded" | grep -q "true"
# Todas: [exit 0] = OK

# TS compilation check
npx tsc --noEmit
# Output: [sin output] = OK

# Browser test (final)
curl -s http://localhost:8000/operator/ui/ | head -50 | grep -E "<title>|<script|<link"
# Output: debe ver title + scripts + links = OK
```

**EVIDENCIA** en `docs/audit/<TIMESTAMP>_OPERATOR_P9_EVIDENCE/`:
- `frontend_build.txt` (npm run build output)
- `backend_syntax.txt` (python compile output)
- `runtime_checks.txt` (todos los curl outputs)
- `ts_check.txt` (npx tsc --noEmit output)
- `screenshots.txt` (descripciones de UI state)

**COMMITS** (atómicos, en orden):

```
Commit A: "vx11: Operator P9 — plan + baseline audit"
  - docs/audit/<ts>_OPERATOR_P9_BASELINE/ + PLAN.md + REQUIREMENTS.md
  - SIN cambios en código

Commit B: "vx11: Operator P9 — frontend polish + visor UI"
  - operator/frontend/src/components/* (componentes nuevos)
  - operator/frontend/src/App.tsx (layout + tabs)
  - operator/frontend/src/App.css (estilos mejorados)
  - Puede incluir tsconfig fix si aplica

Commit C: "vx11: Operator P9 — API adjustments + new endpoints"
  - tentaculo_link/main_v7.py (nuevos endpoints si el TXT lo requiere)
  - operator/frontend/src/services/api.ts (nuevos métodos)
  
Commit D: "vx11: Operator P9 — verification + evidence"
  - docs/audit/<ts>_OPERATOR_P9_EVIDENCE/
  - operator_ui_visibility_diagnostic.sh (si lo actualizaste)
  - docs/audit/<ts>_OPERATOR_P9_SUMMARY.md (resumen final)

$ git push vx_11_remote main
```

---

## 5) RESTRICCIONES DE DEPENDENCIAS

✅ PERMITIDAS:
- Librerías ya en `package.json` (React, TypeScript, Vite, etc.)
- Librerías muy pequeñas (<10KB gzipped) si JUSTIFICADAS
- Componentes escritos a mano (siempre preferible)

❌ PROHIBIDAS:
- Agregar D3, Chart.js, Material-UI, Tailwind, etc. "porque sí"
- `npm audit fix --force` (rompe versiones)
- Cualquier librería que NO esté justificada en el PLAN

⚠️ SI NECESITAS una librería:
- Justificar en `docs/audit/<ts>_OPERATOR_P9_PLAN.md`
- Medir impacto: `npm run build` antes/después (delta KB)
- Documentar en evidencia

---

## 6) SALIDA FINAL (QUÉ ENTREGARÉ AL USUARIO)

### 1️⃣ **Resumen Ejecutivo** (~1 página)

```
Título: "Operator P9 — Pulido + Visor Integrado"

Secciones:
- ¿Qué cambió? (lista de cambios)
- ¿Qué se añadió? (componentes, endpoints, features)
- ¿Qué se degradó? (nada, si todo P0 pass)
- ¿Qué queda P1/P2? (futuros)
- Estado: READY FOR PRODUCTION ✓
```

### 2️⃣ **Matriz de Requisitos del Visor**

```
Tabla con estados DONE/TODO para cada requisito del TXT:
- V1, V2, V3... (IDs)
- ¿Implementado?
- ¿Testado en runtime?
- ¿Pasa P0 gates?
```

### 3️⃣ **Rutas + Endpoints Finales**

```markdown
### Frontend Routes
- GET  /operator/ui/           → VX11 Operator (static HTML)
- GET  /operator/ui/assets/    → CSS, JS, images

### API Endpoints (all require x-vx11-token header)
- GET  /operator/api/status       → policy + core health + OFF_BY_POLICY
- GET  /operator/api/modules      → module list + state
- POST /operator/api/chat         → chat (degraded if switch OFF)
- GET  /operator/api/events       → events polling
- GET  /operator/api/scorecard    → PERCENTAGES + SCORECARD JSON
- GET  /operator/api/topology     → graph + policy annotation
- [+ nuevos según TXT parseado]
```

### 4️⃣ **Lista de Commits**

```bash
bc1e03f vx11: Operator P0 close — API in tentaculo_link + UI stable [PREV]
<new>   vx11: Operator P9 — plan + baseline audit
<new>   vx11: Operator P9 — frontend polish + visor UI
<new>   vx11: Operator P9 — API adjustments + new endpoints
<new>   vx11: Operator P9 — verification + evidence
```

### 5️⃣ **Archivos Clave Modificados**

```
tentaculo_link/main_v7.py (+ líneas P9 endpoints)
operator/frontend/src/components/* (nuevos componentes)
operator/frontend/src/App.tsx (layout refactor)
operator/frontend/src/App.css (estilos mejorados)
operator/frontend/src/services/api.ts (nuevos métodos)
operator/frontend/tsconfig.json (si necesitó fixes)
```

---

## 7) NOTAS FINALES

- **Paranoia VX11**: Cada cambio auditado, nada hecho "a ciegas"
- **Fallback Graceful**: Si switch OFF, UI no rompe
- **Single Entrypoint**: Cero llamadas a puertos internos desde frontend
- **P0 First**: Todo debe pasar gates básicos
- **Evidence Trail**: docs/audit/<ts>_OPERATOR_P9_*/ tiene todo

---

## 8) INICIAR

1. Lee bootstrap obligatorio ✓
2. Ejecuta snapshot ✓
3. **PIDE AL USUARIO**: TXT del visor avanzado
4. Parsearlo y crear matriz ✓
5. TAREA 1: Plan (sin cambios) ✓
6. TAREA 2: Frontend polish ✓
7. TAREA 3: API + visor integration ✓
8. TAREA 4: P0 gates + commits ✓
9. Entregar salida final

**START AQUÍ** (ejecuta bootstrap snapshot primero).
