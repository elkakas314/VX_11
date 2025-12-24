# 📚 ÍNDICE — CAMBIOS QUIRURGICOS + HERRAMIENTAS VX11

**Generado:** 2025-12-24T23:25:00Z  
**Propósito:** Encontrar rápidamente lo que necesitas

---

## 🗂️ Archivos por Necesidad

### 🔬 "Necesito entender CAMBIOS QUIRURGICOS"

**Lee primero:**
- [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md)
  - ✓ 5 Pilares (Mínimo, Auditoría, Validación, Evidencia, Nunca Destructivo)
  - ✓ Matriz decisión por tipo de cambio
  - ✓ Ejemplos prácticos (bug, config, limpieza, BD, refactor)
  - ✓ Checklist "¿es quirúrgico?"
  - ✓ KPIs de validación

**Luego:**
- [.github/agents/vx11.agent.md](.github/agents/vx11.agent.md) (línea ~35)
  - ✓ Sección "ESTILO QUIRURGICO — HAIKU 4.5 PORTABLE" integrada
  - ✓ 10-paso checklist quirúrgico
  - ✓ Core Rules actualizados

### 🔧 "Voy a EDITAR CÓDIGO en VX11"

**Antes de editar:**
1. Leer: [VX11_QUICK_START.md](VX11_QUICK_START.md) sección "CAMBIOS QUIRURGICOS"
2. Seguir: [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md) - Caso 1 (Arreglar Bug)
3. Usar: Checklist de 10 pasos de `.github/agents/vx11.agent.md`

**Durante:**
- Cambio MÍNIMO (una cosa = un cambio)
- Validación post: `python -m py_compile archivo.py`
- Guardar evidencia: `docs/audit/$TS/`

**Después:**
- Registrar en CHANGE_SUMMARY.md
- Validar side-effects
- Reportar qué cambió

### 🗑️ "Necesito BORRAR algo"

**Lee:**
- [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md) - Caso 3 (Limpiar Logs)
- [VX11_QUICK_START.md](VX11_QUICK_START.md) sección "CAMBIOS QUIRURGICOS"

**Proceso:**
1. Pre-backup: `cp archivo archivo.backup`
2. DRY-RUN: mostrar qué se va a borrar
3. Ask confirmación
4. Mover a attic/ (NOT rm)
5. Guardar evidencia

### 💾 "Necesito EDITAR BD"

**Lee:**
- [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md) - Matriz decisión BD
- [.github/agents/vx11.agent.md](.github/agents/vx11.agent.md) - LIMPIEZA QUIRURGICA - Vaciar Tabla BD

**Proceso:**
1. Pre-backup: `cp data/runtime/vx11.db backup_PRE.db`
2. Pre-check: `PRAGMA quick_check`, `integrity_check`, `foreign_key_check`
3. DRY-RUN: SELECT antes de DELETE
4. Ask confirmación
5. Ejecutar
6. Post-check: repetir PRAGMAs
7. Guardar evidencia

### 🚀 "Voy a USAR OTRO MODELO (GPT-5, Mini, Raptor)"

**Copia + pega:**
- [docs/audit/PROMPT_SYSTEM_QUIRURGICO.md](docs/audit/PROMPT_SYSTEM_QUIRURGICO.md) - INSTRUCCIÓN MAESTRA
- Pegalo en tu prompt
- Agrega tu solicitud
- Modelo sigue protocolo quirúrgico automáticamente

### 🧰 "Necesito HERRAMIENTAS/ATAJOS VX11"

**Auditoría rápida:**
- [VX11_QUICK_START.md](VX11_QUICK_START.md) #1 - Status en 1 línea
- [VX11_QUICK_START.md](VX11_QUICK_START.md) #2 - Full Audit

**Monitoreo:**
- [VX11_QUICK_START.md](VX11_QUICK_START.md) #4 - Monitor Loop
- [.github/agents/vx11.agent.md](.github/agents/vx11.agent.md) - HERRAMIENTAS AVANZADAS

**Limpieza:**
- [VX11_QUICK_START.md](VX11_QUICK_START.md) #5 - Cleanup Safe
- [.github/agents/vx11.agent.md](.github/agents/vx11.agent.md) - LIMPIEZA QUIRURGICA

**Más herramientas:**
- [docs/audit/VX11_AGENT_TOOLS_INDEX.md](docs/audit/VX11_AGENT_TOOLS_INDEX.md) - Índice completo
- [.github/agents/vx11.agent.md](.github/agents/vx11.agent.md) - Quick Commands + Herramientas Avanzadas

---

## 📋 Archivos Principales (Referencia)

### 🎯 Core Bootstrap

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| [.github/agents/vx11.agent.md](.github/agents/vx11.agent.md) | MAIN — Todo lo que necesitas (herramientas + atajos + limpieza + quirúrgico) | 1100+ |

### 📚 Documentación Quirúrgica (NEW)

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md) | Guía completa protocolo quirúrgico (portable a ANY LLM) | 350 |
| [docs/audit/PROMPT_SYSTEM_QUIRURGICO.md](docs/audit/PROMPT_SYSTEM_QUIRURGICO.md) | Prompts + instrucciones por tipo para ANY modelo | 280 |
| [docs/audit/20251224T214931Z/CAMBIOS_QUIRURGICOS_ESTILO_HAIKU_PORTABLE.md](docs/audit/20251224T214931Z/CAMBIOS_QUIRURGICOS_ESTILO_HAIKU_PORTABLE.md) | Sumario implementación + guía uso | 200 |

### ⚡ Quick Reference

| Archivo | Propósito | Lineas |
|---------|-----------|--------|
| [VX11_QUICK_START.md](VX11_QUICK_START.md) | 7 comandos listos + cambios quirúrgicos agregados | 120 |
| [docs/audit/VX11_AGENT_TOOLS_INDEX.md](docs/audit/VX11_AGENT_TOOLS_INDEX.md) | Índice de herramientas + árbol decisión + tutorial | 200 |

### 🔍 Sumarios

| Archivo | Propósito |
|---------|-----------|
| [docs/audit/20251224T214931Z/VX11_AGENT_IMPROVEMENTS_SUMMARY.md](docs/audit/20251224T214931Z/VX11_AGENT_IMPROVEMENTS_SUMMARY.md) | Resumen mejoras v2.0→v2.1 |
| [docs/audit/20251224T214931Z/IMPROVEMENTS_COMPLETE_SUMMARY.md](docs/audit/20251224T214931Z/IMPROVEMENTS_COMPLETE_SUMMARY.md) | Resumen ejecutivo completo |

---

## 🎯 Atajos por Urgencia

### ⚡ "Necesito esto AHORA"

```
Status en 1 línea:
  → VX11_QUICK_START.md #1

Cambios quirúrgicos:
  → VX11_QUICK_START.md sección "CAMBIOS QUIRURGICOS"

Audit completa:
  → VX11_QUICK_START.md #2
```

### 📖 "Tengo tiempo de leer"

```
Protocolo quirúrgico:
  → docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md

System prompts (otro modelo):
  → docs/audit/PROMPT_SYSTEM_QUIRURGICO.md

Herramientas VX11:
  → .github/agents/vx11.agent.md
```

### 🔬 "Quiero entender TODO"

```
Empezar por:
  1. VX11_QUICK_START.md
  2. docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md
  3. .github/agents/vx11.agent.md
  4. docs/audit/VX11_AGENT_TOOLS_INDEX.md
```

---

## 📐 Matriz: ¿Qué Archivo Usar?

```
¿Necesito...?

CAMBIOS QUIRURGICOS
├─ Entender protocolo → ESTILO_HAIKU_4_5_PORTABLE.md
├─ Prompts para otro modelo → PROMPT_SYSTEM_QUIRURGICO.md
├─ Checklist rápida → VX11_QUICK_START.md
└─ Detalles en bootstrap → .github/agents/vx11.agent.md

HERRAMIENTAS/ATAJOS
├─ Status rápido → VX11_QUICK_START.md #1
├─ Audit completa → VX11_QUICK_START.md #2
├─ Herramientas avanzadas → .github/agents/vx11.agent.md
└─ Índice herramientas → VX11_AGENT_TOOLS_INDEX.md

LIMPIEZA QUIRURGICA
├─ Recetas → .github/agents/vx11.agent.md
├─ Ejemplos → ESTILO_HAIKU_4_5_PORTABLE.md
└─ Quick ref → VX11_QUICK_START.md #5

OTRO MODELO (GPT-5, Mini, Raptor)
├─ System prompt → PROMPT_SYSTEM_QUIRURGICO.md
└─ Documentación protocolo → ESTILO_HAIKU_4_5_PORTABLE.md
```

---

## 🚀 Flujo Recomendado

### Primer Uso:

```
1. Leer: VX11_QUICK_START.md (5 min)
2. Leer: CAMBIOS QUIRURGICOS section (3 min)
3. Guardar: docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md (reference)
4. Guardar: docs/audit/PROMPT_SYSTEM_QUIRURGICO.md (for other models)
5. Usar: atajos copy-paste
```

### Operación Diaria:

```
1. Status: VX11_QUICK_START.md #1
2. Audit si necesario: VX11_QUICK_START.md #2
3. Cambio: Seguir protocolo quirúrgico
4. Validar: VX11_QUICK_START.md validación
5. Evidencia: docs/audit/$TS/
```

### Con Otro Modelo:

```
1. Copiar: docs/audit/PROMPT_SYSTEM_QUIRURGICO.md
2. Pegar: INSTRUCCIÓN MAESTRA en prompt
3. Agregar: tu solicitud
4. Ejecutar: modelo sigue protocolo
```

---

## 📞 "¿Dónde está...?"

| Busco | Archivo |
|-------|---------|
| Status rápida | VX11_QUICK_START.md #1 |
| Audit completa | VX11_QUICK_START.md #2 |
| Atajos copy-paste | VX11_QUICK_START.md o .github/agents/vx11.agent.md |
| Cambios quirúrgicos | docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md |
| Prompts para otro modelo | docs/audit/PROMPT_SYSTEM_QUIRURGICO.md |
| Herramientas VX11 | .github/agents/vx11.agent.md o VX11_AGENT_TOOLS_INDEX.md |
| Limpieza recetas | .github/agents/vx11.agent.md sección LIMPIEZA |
| Monitor real-time | .github/agents/vx11.agent.md HERRAMIENTAS AVANZADAS |
| Índice completo | VX11_AGENT_TOOLS_INDEX.md |

---

## ✅ Checklist: ¿Estoy Listo?

- [ ] ¿Leí VX11_QUICK_START.md?
- [ ] ¿Entiendo 5 pilares quirúrgicos?
- [ ] ¿Conozco cuándo usar cada archivo?
- [ ] ¿Guardé PROMPT_SYSTEM_QUIRURGICO.md (si uso otro modelo)?
- [ ] ¿Tengo atajos copy-paste guardados?
- [ ] ¿Sé dónde guardar evidencia (docs/audit/$TS/)?

---

**Bookmark estos archivos:**
1. **VX11_QUICK_START.md** — Todos los días
2. **docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md** — Antes de editar código
3. **docs/audit/PROMPT_SYSTEM_QUIRURGICO.md** — Si usas otro LLM
4. **.github/agents/vx11.agent.md** — Referencia general

---

**Última actualización:** 2025-12-24T23:25:00Z  
**Status:** ✅ TODO LISTO PARA USAR
