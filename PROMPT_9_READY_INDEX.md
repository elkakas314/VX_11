# PROMPT 9 READY FOR DEEPSEEK R1 — QUICK INDEX

**Fecha**: 28 de diciembre de 2025  
**Estado**: ✅ COMPLETO Y LISTO

---

## QUÉ SE PREPARÓ

### 1. **PROMPT 9 — ESTRUCTURA COMPLETA**
📄 **Archivo**: [PROMPT_9_FOR_DEEPSEEK_R1.md](PROMPT_9_FOR_DEEPSEEK_R1.md)

**Contiene**:
- Contexto misión (8 secciones claras)
- 0 invariantes duras (no negociables)
- 1 bootstrap obligatorio (lista de lectura)
- 2 estado base (asumir como cierto)
- 3 pausa para pedir input del visor ← **CRÍTICO**: El modelo se detiene aquí y pide el TXT
- 4 trabajo (4 tareas atómicas)
- 5 restricciones de dependencias
- 6 salida final (contrato de entrega)
- 7 notas finales

**Uso**: Copiar contenido completo → pegar a DeepSeek R1

---

### 2. **PROMPT 9 INTEGRATED — CON VISOR SPEC**
📄 **Archivo**: [PROMPT_9_INTEGRATED_DEEPSEEK_R1.md](PROMPT_9_INTEGRATED_DEEPSEEK_R1.md)

**Contiene**:
- PROMPT 9 completo (arriba)
- **+** SPEC del Visor ya parseado en MATRIZ TRAZABLE
  - Features P0 (11 features, production-minimum)
  - Features P1 (6 features, advanced)
  - Features P2 (3 features, future)
  - API endpoints P0/P1/P2 (24 endpoints)
  - Security + Auth (6 tareas)

**Ventaja**: DeepSeek R1 no necesita parsear el JSON; la matriz ya está hecha.

**Uso**: Copiar si quieres que DeepSeek parta CON el visor spec ya integrado (sin pausa en sección 3)

---

### 3. **SPEC CANONICAL — JSON LIMPIO**
📄 **Archivo**: [docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json](docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json)

**Contiene**:
- Metadata (v7.0.0-superpack)
- Canon invariants (5: single_entrypoint, solo_madre, no_unsafe_ui, db_ownership, security_minimum)
- Current state observed (frontend + backend actual)
- Target operator product (qué es, qué debe hacer)
- Frontend spec completo (IA + visual design + UX + features + state management)
- Backend spec completo (API surface canonico + auth + security + data model)
- Module integration contracts
- Testing + quality gates
- Implementation phases (P0/P1/P2)
- Acceptance criteria

**Referencia**: Punto de verdad para todas las decisiones.

---

## FLUJOS DE USO

### **OPCIÓN A: Uso Rápido de PROMPT 9 Original**
```
1. Copiar [PROMPT_9_FOR_DEEPSEEK_R1.md](PROMPT_9_FOR_DEEPSEEK_R1.md)
2. Pegar a DeepSeek R1
3. DeepSeek ejecuta bootstrap
4. DeepSeek pide: "Pega aquí el TXT del visor"
5. Tú pegas [VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json](docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json)
6. DeepSeek parseamatriz + procede
```

**Tiempo interactivo**: 1 pausa (sección 3)

---

### **OPCIÓN B: Uso Integrado (Sin Pausa)**
```
1. Copiar [PROMPT_9_INTEGRATED_DEEPSEEK_R1.md](PROMPT_9_INTEGRATED_DEEPSEEK_R1.md)
2. Pegar a DeepSeek R1
3. DeepSeek ejecuta bootstrap DIRECTAMENTE
4. Matriz ya está lista (no pide input)
5. Procede con 4 tareas atómicas
```

**Tiempo interactivo**: 0 pausas (automático end-to-end)

---

## CHECKLIST FINAL

- ✅ PROMPT 9 listo (secciones 0-8 completas)
- ✅ Bootstrap obligatorio documentado (10 archivos a leer)
- ✅ Pausa automática para pedir visor spec (sección 3)
- ✅ 4 tareas atómicas claras (plan, UI, API, verificación)
- ✅ P0 gates específicos (scripts curl exactos)
- ✅ Salida final estructurada (resumen, matriz, commits)
- ✅ Visor spec completo en JSON (v7.0.0-superpack)
- ✅ Visor spec parseado en matriz (P0/P1/P2 + endpoints)
- ✅ Invariantes documentadas (single_entrypoint, solo_madre, OFF_BY_POLICY, etc.)
- ✅ Restricciones claras (no librerías random, no secrets, no stubs)

---

## REFERENCIAS RÁPIDAS

| Documento | Uso | Link |
|-----------|-----|------|
| PROMPT_9_FOR_DEEPSEEK_R1.md | Usar si quieres pausa + input interactivo | [Link](PROMPT_9_FOR_DEEPSEEK_R1.md) |
| PROMPT_9_INTEGRATED_DEEPSEEK_R1.md | Usar si quieres end-to-end automático | [PROMPT_9_INTEGRATED_DEEPSEEK_R1.md](PROMPT_9_INTEGRATED_DEEPSEEK_R1.md) |
| docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json | Punto de verdad del visor spec | [Link](docs/canon/VX11_OPERATOR_SUPERPACK_CANONICAL_v7.0.0.json) |

---

## TAREA PARA EL USUARIO

**Opción 1**: Copiar una de los dos PROMPT 9 y pegarlo a DeepSeek R1 ahora.

**Opción 2**: Esperar a sesión próxima + usar uno de los PROMPT 9.

**Recomendación**: **OPCIÓN B (PROMPT_9_INTEGRATED_DEEPSEEK_R1.md)** porque:
- Sin pausas innecesarias
- Matriz ya lista
- DeepSeek puede trabajar end-to-end en ~9-12 horas
- Entrega final: resumen + commits + evidencia

---

**FIN**
