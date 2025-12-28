# PLAN CIERRE PRODUCCIÓN REAL VX11 — P0 BASELINE

**Fecha**: 2025-12-29T00:48Z  
**Estado baseline**: OK (solo_madre, chat degradado, UI relativo)  
**Commits**: main @ f5185e5 (limpio)  
**DB**: 73 tablas, 1.1M filas, integrity=ok

---

## HALLAZGOS BASELINE

### 1. Frontend UI (api.ts / App.tsx)
- **✅ CORRECTO**: BASE_URL es relativo (`''`) por defecto → no hardcodes en fetch()
- **⚠️ DEBUG ONLY**: `debugData.apiBase` tiene hardcode `http://localhost:8000` (cosmético, no afecta rutas)
- **STATUS**: Chat UI funciona, degradado con fallback local en `solo_madre`

### 2. Chat Runtime
- **✅ FUNCIONANDO**: POST /operator/api/chat responde 200 con fallback degraded
- **RUTA ACTUAL**: solo_madre → local_llm_degraded
- **TIMEOUT**: 6s intenta switch, fallback después

### 3. DB Integridad
- **✅ PASS**: quick_check=ok, integrity_check=ok, foreign_key_check=ok
- **TABLAS**: 73 (canon)
- **FILAS**: 1.1M

### 4. Docker State (SOLO_MADRE POLICY)
- **✅ MADRE**: UP (8001)
- **✅ REDIS**: UP
- **✅ TENTACULO**: UP (8000)
- **❌ SWITCH/HERMES/SHUBNIGGURATH/ETC**: OFF (por política)

---

## INPUTS INGESTADOS

### PDF
- **Path**: `docs/Informe de Auditoría Remoto (A).pdf`
- **SHA256**: b9f60a2f5baa05d0a8721e30f117fa3a443f9455bafeb655789df2e1af5965b9
- **Size**: 90K

### ZIP (Documentos_1.zip)
- **Path**: `docs/Documentos_1.zip`
- **Descomprimido en**: `docs/inbox/20251228T234445Z_inputs/unzipped/`
- **Archivos**:
  1. `hormiguero_manifetsaator.txt` (103K) — INEE/Builder/Colonia Remota SPEC
  2. `operatorjson.txt` (30K) — Canonical Operator spec
  3. `shubjson.txt` (131K) — Colonia + agentes JSON spec
  4. `diagrams.txt` (18K) — ASCII diagrams

---

## PLAN DE 5 FASES

### FASE 0 ✅ DONE
- Baseline capturadon
- PDF + ZIP ingestados
- Specs leídas

### FASE 1: UI FIX (OPCIONAL, COSMÉTICA)
- **Acción**: Remover hardcode `http://localhost:8000` de debugData.apiBase
- **Razón**: Está en comentario debugData, no afecta runtime (ya está relativo)
- **Tiempo**: 5 min

### FASE 2: CHAT RUNTIME (CONFIRMACIÓN)
- **Status**: Ya funciona (degraded en solo_madre)
- **Acción**: Validar que /operator/api/chat responde 200 siempre
- **Tests**: curl con solo_madre ON
- **Tiempo**: 5 min

### FASE 3: VENTANAS TEMPORALES (CHECK)
- **Requerimiento**: Poder activar switch de forma controlada (ventanas)
- **Status**: MADRE tiene `/madre/power/service/start` pero NO hay ventanas con TTL
- **Acción**: 
  - Crear endpoints en madre: `/madre/power/window/{open,close,status}`
  - TTL enforcement (job simple)
  - Power events table (si no existe)
- **Tiempo**: 30 min

### FASE 4: INTEGRACIÓN INEE/BUILDER/REWARDS (HANDOFF)
- **Scope**: Código completo en ZIP es ~240KB de SPEC (no todo implementable en 1 sesión)
- **Estrategia**: 
  - Crear estructura canónica: `hormiguero/{inee,builder,rewards}/`
  - Migrations DB para tablas INEE (si no existen)
  - Feature flags OFF por defecto
  - Endpoints stubs (devuelven "disabled")
  - NO ejecutar lógica de simulación/execute en esta fase
- **Tiempo**: 90 min (si es aditivo puro)

### FASE 5: GATES + POST-TASK + CIERRE
- **Tests P0**: Deben pasar (sin regresión)
- **post_task**: Regenerar DB maps, SCORECARD, PERCENTAGES
- **Secret scan**: rg + gitleaks → 0
- **FINAL_SIGNOFF.md**: Documentar qué se tocó, qué se verificó
- **Tiempo**: 20 min

---

## RIESGOS IDENTIFICADOS

| Riesgo | Impacto | Mitigación |
|--------|---------|-----------|
| INEE integración rompe contratos | Alto | Aditivo-only, feature flags OFF por defecto |
| DB schema migrations sin test | Medio | Usar gen_db_map post-change, verify integridad |
| Switch window no se cierra (TTL timeout) | Medio | Implementar TTL enforcement en madre |
| Secretos en ZIP (tokens) | Alto | Scan ZIP antes de commitear |
| Peso de las specs (240K) | Bajo | Distribuir en fases, fase 4 solo stubs |

---

## DECISION DE EJECUCIÓN

**RECOMENDACIÓN**: Ejecutar FASE 1 + 2 + 3 + 5 en orden. FASE 4 (INEE/Builder) se parchea en siguiente sesión (es grande y debe ser verificado por DRI humano).

**BLOCKERS ACTUALES**: Ninguno. Sistema está estable en baseline.

---

## PRÓXIMOS PASOS

1. Commitear evidencia P0
2. Ejecutar FASE 1 (UI fix cosmética)
3. Ejecutar FASE 2 (confirm chat)
4. Ejecutar FASE 3 (windows reales)
5. Ejecutar FASE 5 (gates + post-task)
6. Generar FINAL_SIGNOFF
7. Push a main
