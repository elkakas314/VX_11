# PROMPT 9R — VX11 OPERATOR "RE-QUETE PULIDO" (SIN DeepSeek R1 local; USAR TOKEN por API)

**Versión**: PROMPT 9R  
**Fecha**: 2025-12-28  
**Objetivo**: Frontend Operator UI + integración API real (single entrypoint tentaculo_link:8000)  
**Timebox**: 4 tareas × 60–90 min cada una

---

## ROL

Eres el **implementador quirúrgico de VX11 Operator (frontend)** + su integración con `/operator/api/*` en tentaculo_link.

**OBJETIVO CRÍTICO**: 
- Pulir fuerte el visor (UI oscura, usable, **cero pantallas en blanco**)
- Integrar funciones del TXT del visor (que pegarás al inicio)
- Dejar evidencia + commits atómicos

---

## INVARIANTES (NO ROMPER)

1. **Single entrypoint**: TODO por `tentaculo_link:8000`. Nada de llamar directo a 8001/8002/8003 desde frontend.
2. **Runtime default**: policy **"solo_madre"** (madre+redis+tentaculo_link). Lo demás = OFF_BY_POLICY.
3. **Seguridad**:
   - Nada de secretos en git
   - Nada de "scripts nuevos permanentes" salvo si es imprescindible → preferir heredocs bash

---

## CONTEXTO CANÓNICO (RUTA)

- **Repo root**: `/home/elkakas314/vx11`
- **Spec canonical**: `docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json`
- **API backend**: `tentaculo_link/main_v7.py` (prefijo `/operator/api/*`)
- **Frontend**: `operator/frontend/` (React + TypeScript)
- **Bootstrap checklist**: `docs/audit/COPILOT_BOOTSTRAP_CHECKLIST.txt`

---

## INPUTS OBLIGATORIOS EN ESTE CHAT

### A) TXT del visor (ESPERA A QUE LO PEGUE)
- Pegaré un TXT con funciones avanzadas (P0/P1/P2)
- TÚ lo parseas → checklist + implementación

### B) Si hay contradicción
- Manda **canon VX11** + seguridad **por delante**

---

## MODO "DEEPSEEK POR TOKEN" (HERRAMIENTA OPCIONAL, NO BLOQUEANTE)

**NO necesito DeepSeek R1 local.** Si hay token → úsalo por API como herramienta de ayuda.

### 0) Detectar token (NO commitear)

```bash
# En terminal:
echo $DEEPSEEK_API_KEY
# o verificar en tokens.env
cat tokens.env | grep DEEPSEEK
```

Si **NO existe**: sigue igual SIN DeepSeek (no te bloquees).

### 1) Llamada rápida a DeepSeek (one-off, sin crear archivos permanentes)

```python
python3 - <<'PY'
import os
from openai import OpenAI

# Detectar token
key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("DEEPSEEK_TOKEN")
if not key:
    print("NO_DEEPSEEK_KEY: continuando sin DeepSeek")
    exit(0)

client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
resp = client.chat.completions.create(
    model="deepseek-reasoner",   # o "deepseek-chat" para más rápido
    messages=[
        {
            "role": "system",
            "content": "Eres ingeniero senior React+TS. Devuelve SOLO cambios concretos, sin relleno."
        },
        {
            "role": "user",
            "content": """Dame plan de refactor UI VX11 Operator:
- Layout 3 paneles (nav left, main center, sidebar right)
- Dark theme + accesibilidad (WCAG AA)
- Estados: loading, error, empty, degraded
- Componentes reutilizables
- Limitaciones: OFF_BY_POLICY no es error, es estado esperado"""
        }
    ],
    stream=False
)
print(resp.choices[0].message.content)
PY
```

### 2) Regla de oro

- **DeepSeek SOLO sugiere.** TÚ aplicas cambios, ejecutas gates, haces commits.
- Guarda prompts/respuestas en: `docs/audit/<ts>_OPERATOR_P9R_LLM/` (trazabilidad)

---

## FALLBACK "GEMINI CLI" (OPCIONAL)

Si quieres Gemini CLI como herramienta secundaria:

```bash
npm install -g @google/gemini-cli
gemini --version
```

Si no está disponible o falla auth: ignóralo (no bloquea).

**Referencia**: [Google Gemini CLI GitHub](https://github.com/GoogleCloudPlatform/google-cloud-cli)

---

## EJECUCIÓN: 4 TAREAS ATÓMICAS

Cada tarea: **60–90 min real**. Si te atascas: **PARAS y reportas BLOCKED** con evidencia.

---

### TAREA A — AUDIT + PLAN (SIN CÓDIGO)

**Duración**: 60 min  
**Entrega**: `docs/audit/<ts>_OPERATOR_P9R_PLAN.md`

#### Lectura obligatoria (en orden):

1. `docs/audit/CLEANUP_EXCLUDES_CORE.txt`
2. `docs/audit/DB_SCHEMA_v7_FINAL.json`
3. `docs/audit/DB_MAP_v7_FINAL.md`
4. `docs/audit/PERCENTAGES.json` + `SCORECARD.json`
5. `tentaculo_link/main_v7.py` (API backend)
6. `operator/frontend/src/services/api.ts` (API client)
7. `operator/frontend/src/App.tsx` + `App.css`
8. `docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json`

#### Entonces:

- **Espera a que pegue el TXT del visor** (funciones P0/P1/P2)
- Conviértelo a **matriz trazable**:
  | Función | P0/P1/P2 | Archivo | Componente | Riesgo |
  |---------|----------|---------|-----------|--------|
  
- Documento: riesgos, archivos a tocar, checklist P0 en orden ejecución

#### Commit A:
```bash
git add docs/audit/<ts>_OPERATOR_P9R_PLAN.md
git commit -m "vx11: PROMPT9R TAREA A — audit + plan (P0/P1/P2 matrix)"
```

---

### TAREA B — FRONTEND "RE-QUETE PULIDO" (VISUAL + UX)

**Duración**: 80 min  
**Objetivo P0**:

- ✅ Dark theme consistente (tokens, variables CSS)
- ✅ Cero "pantalla en blanco" (loading/error/empty states perfectos)
- ✅ Navegación clara (tabs/rail), atajos keyboard (Ctrl+Enter, Ctrl+K, Esc)
- ✅ Responsive (mobile-first thinking)
- ✅ Chat usable aunque esté degraded (OFF_BY_POLICY ≠ error)
- ✅ NO depender de endpoints inexistentes: si P1/P2 → stub bonito, no roto

#### Gates (antes de commit):

```bash
cd operator/frontend
npm ci
npm run build
npx tsc --noEmit
```

#### Commit B:
```bash
git add operator/frontend/
git commit -m "vx11: PROMPT9R TAREA B — frontend pulido (UI dark, UX, P0)"
```

---

### TAREA C — INTEGRACIÓN API REAL (SINGLE ENTRYPOINT)

**Duración**: 70 min  
**Objetivo**:

- Frontend **SOLO** llama a `/operator/api/*` (nada directo a 8001/8002)
- Implementa/ajusta `tentaculo_link/main_v7.py` para cumplir TXT (P0 primero)
- Shapes estables, siempre 200 OK (OFF_BY_POLICY como estado válido)

#### Gates (antes de commit):

```bash
# Backend
python3 -m py_compile tentaculo_link/main_v7.py

# API endpoints
curl -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/api/status \
  http://localhost:8000/operator/api/modules \
  http://localhost:8000/operator/api/chat \
  http://localhost:8000/operator/api/events \
  http://localhost:8000/operator/api/scorecard \
  http://localhost:8000/operator/api/topology
```

#### Commit C:
```bash
git add tentaculo_link/main_v7.py operator/frontend/src/services/api.ts
git commit -m "vx11: PROMPT9R TAREA C — integración API (single entrypoint + P0)"
```

---

### TAREA D — GATES + EVIDENCE + CIERRE

**Duración**: 60 min  
**Evidencia**: `docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/`

#### Archivos a generar:

```
docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/
├── frontend_build.txt       (npm build output)
├── typescript_check.txt     (tsc --noEmit output)
├── backend_syntax.txt       (python3 -m py_compile)
├── docker_ps.txt            (docker compose ps)
├── api_checks.json          (curl responses)
└── RESUMEN.md               (qué quedó P1/P2, siguientes pasos)
```

#### Ejecutar gates:

```bash
cd /home/elkakas314/vx11

# Frontend
cd operator/frontend && npm run build > ../../docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/frontend_build.txt 2>&1
npx tsc --noEmit > ../docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/typescript_check.txt 2>&1
cd ../..

# Backend
python3 -m py_compile tentaculo_link/main_v7.py > docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/backend_syntax.txt 2>&1

# Docker
docker compose ps > docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/docker_ps.txt

# API checks (si servicios está up)
curl -s http://localhost:8000/operator/api/status | jq . > docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/api_checks.json
```

#### RESUMEN.md (contenido):

```markdown
# OPERATOR P9R — RESUMEN EJECUCIÓN

**Fecha**: [ts]
**Commits**: A / B / C / D

## Matriz P0/P1/P2 (Final)

| Requisito | Función | Estado | Archivo |
|-----------|---------|--------|---------|
| ... | ... | ✅/🟡/❌ | ... |

## Qué quedó P1/P2

- [ ] Realtime metrics (websocket)
- [ ] Dark mode persistencia
- [ ] ...

## Siguiente PROMPT

Recomendado: **PROMPT 10** (operacionalización, monitoring, hardening)

## Evidence links

- frontend_build.txt
- typescript_check.txt
- backend_syntax.txt
- api_checks.json
```

#### Commit D:

```bash
git add docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/
git commit -m "vx11: PROMPT9R TAREA D — gates + evidence + cierre (P0 complete)"
```

#### Push:

```bash
git push vx_11_remote main
```

---

## FORMATO DE SALIDA OBLIGATORIO (AL FINAL)

### 1. Matriz requisitos

| P0/P1/P2 | Función | Estado | Archivo/Componente | Blocker |
|----------|---------|--------|-------------------|---------|
| P0 | Dark theme | ✅ | App.css | — |
| P0 | Chat offline | ✅ | App.tsx | — |
| P1 | Websocket realtime | 🟡 | — | No requerido P0 |
| P2 | Analytics | ❌ | — | Deferred |

### 2. Commits exactos (A/B/C/D)

```
A: vx11: PROMPT9R TAREA A — audit + plan (P0/P1/P2 matrix)
B: vx11: PROMPT9R TAREA B — frontend pulido (UI dark, UX, P0)
C: vx11: PROMPT9R TAREA C — integración API (single entrypoint + P0)
D: vx11: PROMPT9R TAREA D — gates + evidence + cierre (P0 complete)
```

### 3. Evidencia

```
docs/audit/<ts>_OPERATOR_P9R_PLAN.md
docs/audit/<ts>_OPERATOR_P9R_EVIDENCE/
  ├── frontend_build.txt
  ├── typescript_check.txt
  ├── backend_syntax.txt
  ├── docker_ps.txt
  ├── api_checks.json
  └── RESUMEN.md
```

### 4. Qué falta (P1/P2) y siguiente PROMPT

- [ ] Realtime metrics (websocket)
- [ ] Persistencia de preferencias (localStorage)
- [ ] Hardening de seguridad (CORS, CSP)

**Siguiente**: PROMPT 10 (operacionalización + monitoring)

---

## EMPIEZA YA

### Paso 1: LEE BOOTSTRAP
- `docs/audit/COPILOT_BOOTSTRAP_CHECKLIST.txt` (contexto mínimo)

### Paso 2: TAREA A
- Lee archivos en orden (arriba)
- **ESPERA a que pegue el TXT del visor**
- Genera matriz P0/P1/P2
- Commit A

### Paso 3: ESPERA TXT
- Pega el TXT del visor (funciones)
- Integra con matriz
- Refina checklist

### Paso 4: TAREAS B/C/D
- Ejecuta en orden
- Timebox 60–90 min c/u
- Gates antes de cada commit

---

## REFERENCIAS RÁPIDAS

**DeepSeek Docs**: https://api-docs.deepseek.com  
**OpenAI SDK**: https://github.com/openai/openai-python  
**Gemini CLI**: https://github.com/GoogleCloudPlatform/google-cloud-cli  

**VX11 Canonical**: `/home/elkakas314/vx11/docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json`  
**Backend API**: `/home/elkakas314/vx11/tentaculo_link/main_v7.py`  
**Frontend**: `/home/elkakas314/vx11/operator/frontend/`

---

**FIN TEMPLATE PROMPT 9R**
