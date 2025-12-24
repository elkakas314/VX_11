# 🗺️ VX11 Navegación — ¿Qué Leo Según Mi Necesidad?

**Tu pregunta:** "¿Copilot recojera todo este comportamiento cada chat nuevo?"

**Respuesta:** ✅ **SÍ, GARANTIZADO**

---

## 📌 Lectura Rápida (2 minutos)

### Si solo tienes 2 minutos:

1. Lee: [docs/audit/RESPUESTA_PERSISTENCIA.md](docs/audit/RESPUESTA_PERSISTENCIA.md) (sección "Cómo Funciona la Persistencia")
2. Copia: El comando de verificación en terminal
3. Listo: Tu duda está 100% resuelta

**Resultado esperado:** ✅ "Sí, Copilot lo recuerda cada chat nuevo porque está en el agent manifest"

---

## 📚 Lectura Estándar (15 minutos)

### Si quieres entender completamente:

1. **Entender la Respuesta** (3 min)
   - Lee: [docs/audit/RESPUESTA_PERSISTENCIA.md](docs/audit/RESPUESTA_PERSISTENCIA.md)
   - Entiendes: Cómo funciona, por qué es garantizado

2. **Protocolo Quirúrgico** (5 min)
   - Lee: [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md) (primeras 100 líneas)
   - Entiendes: 5 reglas + matriz de decisión

3. **Comandos Rápidos** (3 min)
   - Lee: [VX11_QUICK_START.md](VX11_QUICK_START.md)
   - Entiendes: Cómo usarlo en próximo chat

4. **Índice Central** (2 min)
   - Lee: [INDICE_QUIRURGICO_CENTRAL.md](INDICE_QUIRURGICO_CENTRAL.md)
   - Entiendes: Dónde está cada cosa

---

## 🔬 Lectura Completa (1 hora)

### Si eres técnico y quieres TODO:

1. **Agent Manifest** (15 min)
   - Lee: [.github/agents/vx11.agent.md](.github/agents/vx11.agent.md)
   - Entiendes: Cómo Copilot lo interpreta

2. **Protocolo Detallado** (20 min)
   - Lee: [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md) (completo)
   - Entiendes: Todos los casos de uso

3. **Guía Técnica Persistencia** (15 min)
   - Lee: [docs/audit/COPILOT_PERSISTENCE_GUIDE.md](docs/audit/COPILOT_PERSISTENCE_GUIDE.md)
   - Entiendes: Debugging si algo no funciona

4. **System Prompt** (10 min)
   - Lee: [docs/audit/PROMPT_SYSTEM_QUIRURGICO.md](docs/audit/PROMPT_SYSTEM_QUIRURGICO.md)
   - Entiendes: Cómo inyectar en otro LLM

---

## 🎯 Lectura Por Necesidad Específica

### "¿Funciona en chat nuevo?"
→ **ARCHIVO:** [docs/audit/RESPUESTA_PERSISTENCIA.md](docs/audit/RESPUESTA_PERSISTENCIA.md)  
→ **SECCIÓN:** "Cómo Funciona la Persistencia" (5 min)  
→ **RESULTADO:** ✅ SÍ, garantizado via YAML frontmatter

---

### "¿Cómo verifico que todo esté correcto?"
→ **ARCHIVO:** Ejecuta en terminal:
```bash
bash scripts/verify_agent_persistence.sh
```
→ **RESULTADO:** 8 tests automáticos, todos verdes

---

### "¿Quiero entender el protocolo quirúrgico?"
→ **ARCHIVO:** [docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md](docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md)  
→ **EMPIEZA POR:** "## 5 Pilares Quirúrgicos"  
→ **LUEGO LEE:** "## Matriz de Decisión"

---

### "¿Funciona con otros LLMs (no Copilot)?"
→ **ARCHIVO:** [docs/audit/PROMPT_SYSTEM_QUIRURGICO.md](docs/audit/PROMPT_SYSTEM_QUIRURGICO.md)  
→ **SECCIÓN:** "## INSTRUCCIÓN MAESTRA"  
→ **RESULTADO:** Copia el prompt, pega en ChatGPT/Gemini, funciona igual

---

### "¿Dónde está X cosa?"
→ **ARCHIVO:** [INDICE_QUIRURGICO_CENTRAL.md](INDICE_QUIRURGICO_CENTRAL.md)  
→ **SECCIÓN:** "### ¿Dónde está...?"  
→ **RESULTADO:** Tabla rápida con archivo + líneas

---

### "¿Cómo uso @vx11 en próximo chat?"
→ **ARCHIVO:** [VX11_QUICK_START.md](VX11_QUICK_START.md)  
→ **SECCIÓN:** "## CAMBIOS QUIRURGICOS"  
→ **RESULTADO:** 5 reglas de oro + atajos copy-paste

---

### "Si algo no funciona, ¿cómo debuggeo?"
→ **ARCHIVO:** [docs/audit/COPILOT_PERSISTENCE_GUIDE.md](docs/audit/COPILOT_PERSISTENCE_GUIDE.md)  
→ **SECCIÓN:** "## 🔍 Debugging: Si NO Funciona"  
→ **RESULTADO:** 3 problemas comunes + solución

---

### "Quiero el resumen ejecutivo"
→ **ARCHIVO:** [docs/audit/SESION_COMPLETADA_RESUMEN_EJECUTIVO.txt](docs/audit/SESION_COMPLETADA_RESUMEN_EJECUTIVO.txt)  
→ **RESULTADO:** Visión completa de qué se hizo en esta sesión

---

## 🔗 Mapa de Navegación Visual

```
TU PREGUNTA: "¿Copilot recojera el comportamiento cada chat?"
     ↓
┌─────────────────────────────────────────────────┐
│  RESPUESTA RÁPIDA (2 min)                       │
│  → docs/audit/RESPUESTA_PERSISTENCIA.md         │
│    (Sección "Cómo Funciona la Persistencia")    │
└─────────────────────────────────────────────────┘
     ↓
Si quieres entender MÁS:
     ↓
┌─────────────────────────────────────────────────┐
│  PROTOCOLO QUIRÚRGICO (5 min)                   │
│  → docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md    │
│    (Primeras 100 líneas: 5 pilares)             │
└─────────────────────────────────────────────────┘
     ↓
Si quieres verificar:
     ↓
┌─────────────────────────────────────────────────┐
│  VERIFICACIÓN (terminal, 10 seg)                │
│  $ bash scripts/verify_agent_persistence.sh     │
│    (8 tests automáticos)                        │
└─────────────────────────────────────────────────┘
     ↓
Si quieres usar en próximo chat:
     ↓
┌─────────────────────────────────────────────────┐
│  COMANDOS RÁPIDOS (3 min)                       │
│  → VX11_QUICK_START.md                          │
│    (Sección "CAMBIOS QUIRURGICOS")              │
└─────────────────────────────────────────────────┘
     ↓
Si necesitas TODO:
     ↓
┌─────────────────────────────────────────────────┐
│  LECTURA COMPLETA (1 hora)                      │
│  → Ver "Lectura Completa" arriba ↑              │
└─────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Lectura

Marca lo que ya leíste:

```
Navegación & Orientación:
  □ Este archivo (VX11_QUICK_NAVIGATION.md)
  □ INDICE_QUIRURGICO_CENTRAL.md

Respuesta a Tu Pregunta:
  □ docs/audit/RESPUESTA_PERSISTENCIA.md (RECOMENDADO)

Protocolo & Comportamiento:
  □ docs/audit/ESTILO_HAIKU_4_5_PORTABLE.md (primeras 100 líneas)
  □ VX11_QUICK_START.md (sección CAMBIOS QUIRURGICOS)

Técnico & Debugging:
  □ docs/audit/COPILOT_PERSISTENCE_GUIDE.md (si dudas)
  □ .github/agents/vx11.agent.md (si quieres verlo en crudo)

Portabilidad:
  □ docs/audit/PROMPT_SYSTEM_QUIRURGICO.md (si usas otro LLM)

Resumen:
  □ docs/audit/SESION_COMPLETADA_RESUMEN_EJECUTIVO.txt
```

---

## 🚀 TL;DR (Too Long; Didn't Read)

```
Q: ¿Copilot recuerda comportamiento cada chat nuevo?
A: ✅ SÍ

Porque:
  1. Está en .github/agents/vx11.agent.md (agent manifest)
  2. Copilot lo lee CADA @vx11 invocation
  3. YAML frontmatter + instructions field = automático
  4. Verificado: 8/8 tests PASSED

Próximo chat:
  Usuario: "@vx11 status"
  Copilot: (automáticamente carga protocolo quirúrgico)
  Resultado: Auditoría + evidencia

Links:
  - Respuesta: docs/audit/RESPUESTA_PERSISTENCIA.md
  - Verificar: bash scripts/verify_agent_persistence.sh
  - Usar: @vx11 <comando> en próximo chat
```

---

**Última actualización:** 2025-12-24T23:55:00Z  
**Tu mejor opción:** Empieza por [docs/audit/RESPUESTA_PERSISTENCIA.md](docs/audit/RESPUESTA_PERSISTENCIA.md) (2 minutos), luego decide si necesitas más.
