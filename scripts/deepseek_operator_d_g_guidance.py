#!/usr/bin/env python3
"""
FASE D-G: DeepSeek R1 Auto-Architect para Operator UI + Backend Endpoints.

Este script invoca DeepSeek R1 en reasoning mode para:
1. Diseñar arquitectura UI 3-panel oscura
2. Validar endpoints canónicos faltantes
3. Generar código scaffold para FASE D-E-F-G
4. Crear plan de commits atómicos
"""

import os
import sys
from pathlib import Path
import json

# Load env
env_file = Path("/home/elkakas314/vx11/tokens.env")
if env_file.exists():
    try:
        import dotenv

        dotenv.load_dotenv(env_file)
    except ImportError:
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val

sys.path.insert(0, "/home/elkakas314/vx11")

try:
    from config.deepseek import call_deepseek_reasoner
except ImportError:
    print("[ERROR] DeepSeek not available")
    sys.exit(1)

# DeepSeek R1 architectural analysis prompt
prompt = """# VX11 OPERATOR FINALIZE — FASES D-G ARCHITECTURAL GUIDANCE (DEEPSEEK R1)

## CONTEXT
- FASE A: ✅ Auditoría completa (Jest timeout, 409 errors, fixtures missing)
- FASE B: ✅ Tests fixed (conftest.py, operative_mode, timeouts)
- FASE C: ✅ DeepSeek R1 provider selector (13/13 tests pass)
- Status: Necesita completar UI + endpoints + seguridad + validación + commits

## FASE D: Operator Visor Interactivo (Frontend + Backend)

### D.1 Backend Endpoints (Faltantes/Incompletos)

**Requeridos por contrato**:
1. POST /api/audit — inicia auditoría (retorna request_id + job)
2. GET /api/audit/{id}/download — descargar artefacto
3. GET /api/audit — listar auditorías recientes (paginado)
4. POST /api/module/{name}/power_up — encender módulo (vía Madre INTENT)
5. POST /api/module/{name}/power_down — apagar módulo
6. POST /api/module/{name}/restart — reiniciar módulo
7. GET /api/status/modules — salud de todos los módulos (cache 30s)
8. GET /api/explorer/fs?path=... (read-only, /app/ nada más)
9. GET /api/explorer/db?table=... (read-only, 100 rows max)
10. POST /api/settings — aplicar settings no-críticas (theme, etc)

**Estructura respuesta (todos)**:
```json
{
  "ok": true,
  "request_id": "req-uuid",
  "route_taken": "tentaculo_link:operator_backend:chat",
  "degraded": false,
  "errors": [],
  "data": { /* endpoint-specific */ }
}
```

### D.2 Frontend Architecture (3 Paneles)

**Layout oscuro (dark mode)**:
```
┌─────────────────────────────────────────────────────────┐
│ HEADER: VX11 Operator | Mode: operative_core | Health   │
├────────────────────┬──────────────────┬─────────────────┤
│                    │                  │                 │
│ LEFT PANEL         │ CENTER PANEL     │ RIGHT PANEL     │
│ (Dashboard)        │ (Chat+Events)    │ (Controls)      │
│                    │                  │                 │
│ - Module health    │ - Chat history   │ - Audit         │
│   grid             │ - SSE events     │ - Module cmds   │
│ - Last error/event │   timeline       │ - FS explorer   │
│ - Drill-down btn   │ - Filtering      │ - Settings      │
│                    │                  │                 │
├────────────────────┼──────────────────┼─────────────────┤
│ FOOTER: request_id | route_taken | degraded badge      │
└────────────────────┴──────────────────┴─────────────────┘
```

**Responsive mobile**: Stack vertical (left → center → right)

**Accesibilidad mínima**:
- aria-label en botones
- semantic HTML (button, nav, section)
- keyboard navigation (tab, enter)
- color contrast ≥4.5:1 para texto

### D.3 Frontend Components

**Paneles concretos**:

1. **DashboardPanel** (izquierda)
   - ModuleHealthGrid (9 módulos + colores: green/yellow/red/gray)
   - LastEventCard (timestamp, source, message)
   - DrillDownButton → modal con detalles

2. **ChatPanel** (centro)
   - ChatMessageList (scroll, timestamps, rol)
   - SSEEventsTimeline (con filtro: type, source, severity)
   - ChatInputForm (prompt + send)
   - AutoscrollToggle

3. **ControlPanel** (derecha)
   - AuditSection (Launch manual + table recents)
   - ModuleControlSection (power_up/down/restart con confirmación)
   - FSExplorer (path browser read-only)
   - DBExplorer (table selector + paginado)
   - SettingsToggle (theme, auto-refresh)

4. **RoutingGraphWidget** (overlay/drawer)
   - Muestra: Operator → tentaculo_link → {switch|madre|others}
   - Resalta route_taken actual
   - Badge "degraded" en rojo

### D.4 CSS Variables (Dark Theme)

```css
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --accent-green: #3fb950;
  --accent-yellow: #d29922;
  --accent-red: #f85149;
  --accent-blue: #58a6ff;
  --border-color: #30363d;
}
```

**Paleta módulos**:
- healthy: var(--accent-green)
- warning: var(--accent-yellow)
- error: var(--accent-red)
- unknown: var(--text-secondary)

## FASE E: Seguridad/Hardening (15 min)

1. **Rate Limiting**
   - 100 requests/min por auth token
   - Header X-RateLimit-Remaining
   - Retorn 429 si excedido

2. **CSRF Token**
   - Para POST /api/... (excepto /api/chat si ya tiene CORS setup)
   - Header X-CSRF-Token requerido
   - Validar contra sesión

3. **Logs Estructurados**
   - Cada response: request_id + route_taken + status + elapsed_ms
   - Log a stdout (JSON lines) para aggregation

## FASE F: Validación (10 min)

```bash
npm run build  # No errors
python -m pytest operator_backend/backend -q  # Pass >40/47
npm test  # Sin timeout (vitest debe terminar)
```

## FASE G: Commits Atómicos (10 min)

7 commits:
1. conftest + fixtures
2. language_model_selector + provider routing
3. backend endpoints (scaffold)
4. frontend UI 3-panel + components
5. routing graph + dark theme
6. rate limit + CSRF + logs
7. docs/ops + OPERATOR_DELIVERY_SUMMARY.txt

## RECOMENDACIONES DEEPSEEK R1

**GO/NO-GO Criteria**:
- ✅ Si pytest >40/47 → RELEASE
- ✅ Si npm test termina <30s → RELEASE
- ✅ Si DeepSeek provider selection validated → RELEASE
- ❌ Si cualquiera de arriba falla → ITERATE FASE B-C

**Prioridad**:
1. Endpoints mínimos (audit, module control)
2. UI 3-panel + dark theme
3. SSE events timeline
4. Hardening (después UI funciona)

**Riesgo**:
- SSE infinite stream en prod: mitiga con max_events=1000 en /api/events
- DeepSeek offline: fallback automático (ya implementado)
- Auth en tests: usar operative_mode fixture (ya en conftest.py)

**Time Budget**:
- D (1h), E (15min), F (10min), G (10min) = 1.5h total
- Si en 30min no ves progreso en D → skip UI details, release con panels básicos

¿Proceder con D-G en paralelo?
"""

result = call_deepseek_reasoner(prompt)

# Normalize result to a string for printing and file writing
if isinstance(result, tuple) and len(result) > 0:
    first = result[0]
    if isinstance(first, str):
        guidance_text = first
    else:
        try:
            guidance_text = json.dumps(first, indent=2, ensure_ascii=False)
        except Exception:
            guidance_text = str(first)
else:
    guidance_text = str(result)

print(guidance_text)

# Save to audit
audit_dir = Path("/home/elkakas314/vx11/docs/audit")
latest_audit = sorted(audit_dir.glob("202512*_operator_finalize_audit"))
if latest_audit:
    output_file = latest_audit[-1] / "deepseek_r1_d_g_guidance.txt"
    output_file.write_text(guidance_text)
    print(f"\n\n[✓] Guidance saved to {output_file}")
