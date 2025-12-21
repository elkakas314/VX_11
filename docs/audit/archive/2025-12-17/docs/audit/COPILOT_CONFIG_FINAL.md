# COPILOT_CONFIG_FINAL.md — Configuración Canónica v7.2

**Fecha:** 2025-12-17  
**Estado:** ✓ Completado (Modo Cirujano Activado)

---

## Resumen de cambios

### FASE A — Inventario
- ✓ pwd: `/home/elkakas314/vx11`
- ✓ git status: cambios detectados (archivos nuevos + modificados)
- ✓ Localizados 2 archivos FINAL en docs/audit:
  - `docs/audit/DB_MAP_v7_FINAL.md`
  - `docs/audit/DB_SCHEMA_v7_FINAL.json`

### FASE B — Limpieza de agentes antiguos
- ✓ Carpeta `docs/audit/copilot_archive/` creada
- ✓ Movidos 3 agentes personalizados al archivo:
  - `VX11-Inspector.prompt.md` → archive
  - `VX11-Operator-Lite.prompt.md` → archive
  - `VX11-Operator.prompt.md` → archive
- ✓ Eliminada carpeta `.github/copilot-agents/` (vacía)

### FASE C — Configuración canónica NUEVA
Se reescribieron/crearon exactamente estos archivos:

| Archivo | Acción | Contenido |
|---------|--------|----------|
| `.vscode/settings.json` | Recreado | JSON limpio, maxRequests=250, autoApprove selectivo |
| `AGENTS.md` | Reescrito | Contrato cirujano: lotes, forense, DBMAP |
| `.github/copilot-instructions.md` | Reescrito | Prioridades + qué NO hacer sin preguntar |
| `.github/agents/vx11.agent.md` | Reescrito | Agente único canónico (sin preguntas) |
| `.github/instructions/vx11_global.instructions.md` | Recreado | Reglas globales (AGENTS + forense + DBMAP) |

### Archivos ARCHIVADOS (en docs/audit/copilot_archive/)
```
VX11-Inspector.prompt.md
VX11-Operator-Lite.prompt.md
VX11-Operator.prompt.md
```

---

## Configuración FINAL activa

### VS Code (`.vscode/settings.json`)
- `chat.agent.maxRequests`: 250 (AUMENTADO para menos interrupciones)
- `chat.tools.terminal.enableAutoApprove`: true
- Comando regex whitelist:
  - ✓ pwd, ls, realpath, find, tree, cat, rg, grep
  - ✓ python, python3, pytest
  - ✓ git (status, diff, log, show, grep, ls-files)
  - ✓ docker ps, docker compose config
  - ✗ rm, rmdir, mv, cp, chmod, sudo, kill, pkill
  - ✗ git reset --hard, git clean -fd, git push
  - ✗ docker compose up, docker compose down

### AGENTS.md (Contrato cirujano)
1. **Regla de oro:** No preguntes entre pasos, ejecuta en lotes
2. **Excepciones:** Solo pregunta por destructivas (rm/rmdir), movimientos fuera de canon, docker-compose, cambios masivos
3. **Ritual obligatorio:** pwd + realpath + git status + buscar DB_MAP/DB_SCHEMA FINAL
4. **Forense:** Todos los reportes en docs/audit/, no duplicados

### .github/copilot-instructions.md
- Prioridad 1: Respeta AGENTS.md
- Prioridad 2: Consulta DB_MAP_*FINAL* y DB_SCHEMA_*FINAL*
- Prioridad 3: Mantén repo limpio (sin duplicados)
- Auto-aprobado: Inventarios, búsquedas, config, reportes
- Requiere confirmación: rm/rmdir, movimientos grandes, docker-compose, git destructivos

### .github/agents/vx11.agent.md
- Agente **único** para VX11
- Modo: Cirujano (sin parar a preguntar)
- Fuente de verdad: DB_MAP/DB_SCHEMA FINAL en docs/audit
- Forense: docs/audit (actualiza existentes, no clones)

### .github/instructions/vx11_global.instructions.md
- Reglas globales aplicables a todo el repo
- Referencia a AGENTS.md como fuente primaria
- Evidencia y reportes SIEMPRE en docs/audit
- Consulta DBMAP FINAL antes de cambios estructurales

---

## Flujo de trabajo NEW (sin preguntas)

```
Usuario pide tarea
  ↓
Agente VX11 (modo cirujano):
  1. pwd + git status (auto, sin preguntar)
  2. Buscar DB_MAP/DB_SCHEMA FINAL en docs/audit (auto)
  3. Interpretar requerimiento contra FINAL
  4. Ejecutar en LOTES (sin parar entre pasos)
  5. Generar evidencia en docs/audit/
  ↓
Resultado: tareas completadas + reportes forenses
```

---

## Rutas FINALES

```
Agentes:           .github/agents/vx11.agent.md           (ÚNICO ACTIVO)
Instrucciones:     .github/instructions/vx11_global.instructions.md + vx11_workflows.instructions.md
Copilot Settings:  .github/copilot-instructions.md
VS Code Settings:  .vscode/settings.json
Contrato:          AGENTS.md (raíz)
BD Truth:          docs/audit/DB_MAP_v7_FINAL.md + DB_SCHEMA_v7_FINAL.json
Archive:           docs/audit/copilot_archive/
```

---

## Cambios clave

| Aspecto | Antes | Ahora |
|--------|-------|-------|
| Agentes activos | 3+ (VX11-Inspector, VX11-Operator, VX11-Operator-Lite) | 1 (vx11) |
| maxRequests | 200-250 (inconsistente) | **250** (fijo, AUMENTADO) |
| Preguntas por acción | MUCHAS | MÍNIMAS (lotes) |
| Auto-aprobación | Limitada | EXTENDIDA (regex) |
| Fuente de verdad | Difusa | **DB_MAP/DB_SCHEMA FINAL en docs/audit** |
| Forense | Ad-hoc | SISTÉMÁTICO (docs/audit/, sin duplicados) |

---

## ✓ PRÓXIMAS FASES

### FASE D — Git commit (FASE E en request)
```bash
git add AGENTS.md .github/copilot-instructions.md \
  .github/agents/vx11.agent.md \
  .github/instructions/vx11_global.instructions.md \
  .vscode/settings.json \
  docs/audit/copilot_archive/ \
  docs/audit/COPILOT_CONFIG_FINAL.md

git commit -m "chore(copilot): agente vx11 y menos preguntas (modo cirujano)"
git status -sb
```

---

## Limpieza realizada

- ✗ `.github/copilot-agents/` — ELIMINADA (vacía tras mover prompts)
- ✓ `docs/audit/copilot_archive/` — CREADA (contiene 3 prompts antiguos)
- ✓ `.vscode/settings.json` — RECREADO (JSON limpio, dual-object corrompido eliminado)
- ✓ `AGENTS.md` — REESCRITO (limpio, sin duplicados)
- ✓ `.github/copilot-instructions.md` — REESCRITO (limpio, prioridades claras)

---

**Versión:** 7.2 Modo Cirujano  
**Mantenedor:** Copilot VX11  
**Estado:** ✓ LISTO PARA COMMIT  
