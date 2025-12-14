# VX11 Operator Agent Manual — Uso, Costo, Ejemplos, Troubleshooting

**Versión:** 7.1 | **Fecha:** 2025-12-14  
**Audiencia:** Desarrolladores, DevOps, Copilot users  
**Objetivo:** Guía operativa para los 3 agentes permanentes

---

## 1. Descripción General

VX11 tiene **3 agentes canónicos** disponibles en Copilot Chat:

### 🟢 VX11-Operator (Full Execution)
- **Rol:** Ejecuta workflows reales (validación, reparación, tareas, chat)
- **Modo:** Execution-capable con autosync condicional
- **Autosync:** Sí, si validación completa pasa (8 checks)
- **Costo:** Medio-Alto (incluye DeepSeek R1 cuando necesario)

### 🔵 VX11-Inspector (Audit Only)
- **Rol:** Auditoría y forense (nunca modifica nada)
- **Modo:** Read-only, genera reportes
- **Autosync:** No (nunca commiteao)
- **Costo:** Medio (análisis detallado)

### 🟡 VX11-Operator-Lite (Low Cost)
- **Rol:** Tareas simples, bajo costo
- **Modo:** Rules-based, NO DeepSeek por defecto
- **Autosync:** Restringido (docs/limpieza solamente)
- **Costo:** Bajo (FREE para status/chat)

---

## 2. Cuándo Usar Cada Uno

### Usar VX11-Operator si:
- ✅ Necesitas ejecutar fix drift automático
- ✅ Necesitas run task (ir a Madre/Spawner)
- ✅ Necesitas validación + reparación combinada
- ✅ Auditoría compleja de imports (DeepSeek reasoning)
- ✅ Arquitectura change decision (reasoning pesado)

### Usar VX11-Inspector si:
- ✅ ANTES de Operator (siempre chequear primero)
- ✅ Auditoría de seguridad (secrets, gitignore)
- ✅ Forensic analysis (deep dive)
- ✅ Auditoría de CI workflows
- ✅ Verification que no hay drift crítico

### Usar VX11-Operator-Lite si:
- ✅ Necesitas status rápido (gratis)
- ✅ Necesitas cleanup seguro
- ✅ Necesitas chat simple
- ✅ Estás "atorado" pero con presupuesto bajo
- ✅ Validación básica (syntax only)

---

## 3. Tabla de Costos

| Agente | Comando | Costo | Tiempo | Uso |
|--------|---------|-------|--------|-----|
| **Lite** | `status` | FREE | 2s | Binary health |
| **Lite** | `validate` | FREE | 10s | Syntax check |
| **Lite** | `cleanup` | FREE | 30s | Safe maintenance |
| **Lite** | `health` | FREE | 5s | Port checks |
| **Lite** | `chat: msg` | $0.01-0.05 | 5s | Simple text |
| **Lite** | `use deepseek: task` | $0.10-0.50 | 30s | Optional reasoning |
| **Operator** | `status` | $0.01 | 2s | + full health detail |
| **Operator** | `validate` | $0.05 | 30s | Full validation suite |
| **Operator** | `fix drift` | $0.10-0.50 | 1-5m | Auto-repair + validate |
| **Operator** | `run task: desc` | $0.10-1.00 | Variable | Task spawning |
| **Operator** | `chat: msg` | $0.01-0.05 | 5s | Full reasoning |
| **Operator** | `audit imports` | $0.50-2.00 | 10s | DeepSeek reasoning |
| **Operator** | `cleanup` | $0.05 | 30s | Intelligent cleanup |
| **Inspector** | `audit structure` | $0.05 | 5s | Layout check |
| **Inspector** | `audit imports` | $0.50 | 10s | Deep analysis |
| **Inspector** | `audit security` | $0.05 | 5s | Secret scan |
| **Inspector** | `detect drift` | $0.10-0.50 | 10s | Full drift report |
| **Inspector** | `forensics` | $1.00-5.00 | 5m | Deep analysis |

**Estimación mensual (dev team 5 personas):**
- Heavy users (3/day): $50-100/mes
- Medium users (1/day): $20-30/mes
- Light users (1/week): $5-10/mes
- **Team average: $30-50/mes**

---

## 4. Comandos de Referencia

### VX11-Operator

```
@vx11-operator status
  → Salud del sistema + último drift + incidentes

@vx11-operator validate
  → Python syntax + Docker + imports + secrets + .gitignore + tests

@vx11-operator fix drift
  → Auto-repair (docs, imports, files) + validate + autosync check

@vx11-operator run task: build the operator UI
  → Envía a Madre, spawna workers, espera completación

@vx11-operator chat: What is the gateway status?
  → Chat con Switch + DeepSeek si es necesario

@vx11-operator audit imports
  → Análisis profundo de imports, violaciones, cycles

@vx11-operator cleanup
  → Limpieza segura (logs viejos, forensics, snapshots)
```

### VX11-Inspector

```
@vx11-inspector audit structure
  → Layout validation (directorios, archivos canónicos, naming)

@vx11-inspector audit imports
  → Cross-module violations, dead imports, cycles

@vx11-inspector audit security
  → Secretos, tokens, API keys, .gitignore compliance

@vx11-inspector audit ci
  → GitHub Actions workflows validation

@vx11-inspector audit docs
  → Staleness, broken links, missing documentation

@vx11-inspector detect drift
  → Full drift scan + severity assessment

@vx11-inspector forensics
  → Deep analysis (memory, processes, DB, logs)
```

### VX11-Operator-Lite

```
@vx11-operator-lite status
  → Binary check (OK / ERROR)

@vx11-operator-lite validate
  → Syntax only (no docker, no imports analysis)

@vx11-operator-lite cleanup
  → Safe cleanup (no reasoning needed)

@vx11-operator-lite health
  → HTTP health checks (all ports)

@vx11-operator-lite chat: Hello?
  → Chat simple (no reasoning)

@vx11-operator-lite use deepseek: Should I refactor this?
  → Optional reasoning (cost +3x)
```

---

## 5. Flujo Recomendado (Daily Ops)

### Morning Check (5 min, FREE)

```
@vx11-operator-lite status
  → ¿System healthy? ✓ or ✗
```

Si ✗ → proceed a step 2.

### If Issues Detected (Audit, ~$1)

```
@vx11-inspector detect drift
  → Qué está roto?
```

### Fix Issues (Variable cost)

```
@vx11-operator fix drift
  → Auto-repair lo que sea safe
```

### Verify (5 sec, FREE)

```
@vx11-operator validate
  → ¿Todo pasó? ✓ or ✗
```

Si ✓ → autosync automático. Si ✗ → manual review.

---

## 6. Autosync Rules

### ✅ Autosync SI (todas las condiciones):

1. Validación completa pasa
2. Sin secretos detectados
3. Sin node_modules/dist tracked
4. CI workflows sanos
5. Sin cross-module imports
6. Tests pasan
7. Git clean (no divergencia de main)

### ❌ Autosync BLOQUEADO si ALGUNO:

- ❌ Token o API key expuesto
- ❌ node_modules o dist en git
- ❌ CI workflow roto
- ❌ Cross-module import nuevo
- ❌ Tests reventados
- ❌ DB schema corrupto
- ❌ Port conflict
- ❌ Fork 50+ commits atrás

**Cuando se detecta ANY:** Agente STOP inmediato. Crea `docs/audit/AGENT_INCIDENT_<timestamp>.md`. Nunca continúa.

---

## 7. Ejemplos Reales

### Example 1: Fijar Stale Docs

```
User: @vx11-operator fix drift

Operator:
1. Detecta: docs/ARCHITECTURE.md es stale (última edición hace 60 días)
2. Analiza: Contiene referencias a módulos deprecated
3. Actualiza: Timestamps, referencias, content
4. Valida: ✓ Python syntax, ✓ imports, ✓ tests
5. Autosync: YES (low-risk doc update)

Result: ✅ Stale docs fixed, autosync completed
```

### Example 2: Auditar Imports Cruzados

```
User: @vx11-operator audit imports

Operator (with DeepSeek):
1. Escanea: Todos los imports en tentaculo_link/, madre/, switch/
2. Detecta: madre/tasks.py:45 tiene "from switch import Switch"
3. Analiza: Esto es violación de HTTP-only pattern
4. Propone: Refactorizar a HTTP call (GET switch/status)
5. Genera: Reporte con sugerencia de fix

Result: 
  ❌ VIOLATION: Cross-module import in madre/tasks.py
  ✅ SUGGESTION: Use HTTP GET to switch:8002/status instead
  
Operator (auto):
  Then: @vx11-operator fix drift → refactoriza a HTTP
```

### Example 3: Limpiar Forensics Viejos

```
User: @vx11-operator cleanup

Operator:
1. Identifica: forensic/crashes/ contiene 150 crash dumps (30 días+)
2. Archiva: Mueve a forensic/archive/2025-12-14.tar.gz
3. Limpia: Mantiene solo últimos 5 crashes recientes
4. Resultado: Freed 500MB

Result: ✅ Cleanup completed (500MB freed)
```

### Example 4: Inspector Full Security Audit

```
User: @vx11-inspector audit security

Inspector:
1. Scans: Secretos en código tracked
   ✓ None detected
2. .gitignore: Checks node_modules, dist not tracked
   ✓ Compliant
3. Tokens: Verifica tokens.env, tokens.env.master no tracked
   ✓ OK (.gitignore exclusion active)
4. API Keys: Checks VITE_*, DEEPSEEK_* in source
   ✓ Only in .env (correct)

Result: ✅ No security issues found
Report: docs/audit/AUDIT_SECURITY_20251214T180000Z.md
```

---

## 8. Troubleshooting

### Problem: "Gateway not responding"

**Causes:**
- Tentáculo Link (port 8000) is down
- Docker compose not running
- Network connectivity issue

**Fix:**
```
@vx11-operator-lite health
  → Chequea todos los puertos

If fails:
  docker-compose up -d
  Wait 10s
  @vx11-operator-lite health → retry
```

### Problem: "Autosync blocked: secrets detected"

**Causes:**
- Token hardcoded en código
- API key en archivo Python
- .env accidentalmente commiteado

**Fix:**
```
@vx11-inspector audit security
  → Find exactly what secret

Then:
  1. Remove from code
  2. Add to .env (NOT tracked)
  3. Rotate token in production
  4. @vx11-operator fix drift
```

### Problem: "Validation fails: cross-module imports"

**Cause:**
```
madre/tasks.py: from switch import Switch
```

**Fix:**
```
@vx11-operator audit imports
  → See detailed violation + suggestion

@vx11-operator fix drift
  → Auto-refactors to HTTP call
```

### Problem: "Task times out (10min limit)"

**Cause:**
- Madre/Spawner no responden
- DB lento
- Task muy pesada

**Fix:**
```
@vx11-operator-lite health
  → Check all ports

If Madre dead:
  docker-compose restart madre
  Wait 10s
  Retry

If DB slow:
  @vx11-operator cleanup
  (removes old logs, archives old crashes)
  Retry
```

### Problem: "Chat returns timeout"

**Cause:**
- Switch no responde
- DeepSeek API timeout
- Network issue

**Fix:**
```
@vx11-operator-lite health
  → Verify switch:8002 responding

If Switch dead:
  docker-compose restart switch
  Retry

If DeepSeek timeout:
  @vx11-operator-lite chat: msg (uses cheap model instead)
```

---

## 9. Advanced Usage

### Debugging with Inspector

```
@vx11-inspector forensics
  → Deep memory, processes, DB, logs analysis
  
Creates: docs/audit/FORENSICS_<timestamp>.md
```

### Batch Cleanup

```
@vx11-operator cleanup
  (removes logs >30d, archives crashes >7d, etc)
```

### Selective Drift Fix

```
@vx11-operator fix drift
  (Auto-detects and fixes: stale docs, unused files,
   import violations, tracked ignored files, old forensics)
```

---

## 10. Cost Optimization Tips

1. **Use Lite for simple checks** (saves 90% cost)
2. **Inspector before Operator** (audit first, act later)
3. **Batch operations** (@vx11-operator cleanup en vez de múltiples small tasks)
4. **Use DeepSeek selectively** (Lite + `use deepseek` cuando REALMENTE necesites reasoning)
5. **Automated validation** (GitHub Actions hace checks antes de trigger agente)

---

## 11. Quick Reference Card

```
🟢 VX11-Operator
   Full execution, with autosync
   Use: Complex tasks, fixes, reasoning
   Cost: Medium-High
   
🔵 VX11-Inspector  
   Audit only, read-only
   Use: BEFORE Operator, security reviews
   Cost: Medium
   
🟡 VX11-Operator-Lite
   Rules-based, low-cost
   Use: Quick checks, cleanup, simple chat
   Cost: Low/Free
```

---

**VX11 Operator Manual v7.1** — Operación eficiente, costo controlado, seguridad garantizada.

