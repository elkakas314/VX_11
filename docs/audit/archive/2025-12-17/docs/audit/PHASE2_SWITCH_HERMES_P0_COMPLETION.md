# Phase 2 — Switch/Hermes P0 Closure  ✅

## Objetivo Alcanzado
**Cierre de 7 fallos de pytest en switch/hermes → 0 fallos (128/128 tests passing)**

## Cambios Implementados

### 1. Gestión de Stdlib `operator` (CRÍTICA)
- **Problema:** Carpeta local `operator/` sombreaaba stdlib, causando ImportError en pytest y otros módulos
- **Solución:**
  - ✅ Renombré `operator/` → `operator_local/` 
  - ✅ Implementé `sitecustomize.py` para pre-llenar símbolos stdlib en `operator` module
  - ✅ Actualicé `operator_local/__init__.py` con importaciones explícitas de stdlib

### 2. Endpoints Faltantes en Switch (5 nuevos)
- ✅ `POST /switch/hermes/select_engine` — agregué campo `profile: MODE_PROFILES[CURRENT_MODE]`
- ✅ `GET /switch/hermes/status` — agregué campo `healthy_engines[]` + `metrics{}`
- ✅ `POST /switch/chat` — agregué campo `reply: content_val` (alias de `content`)
- ✅ `GET /switch/context` — NEW endpoint: retorna modo, modelos activos, stats cola
- ✅ `GET /switch/providers` — NEW endpoint: lista CLIs + modelos locales

### 3. Event Loop en Pytest (Asyncio Safe)
- ✅ Implementé `_ensure_event_loop()` en `conftest.py` que se ejecuta:
  - Al inicio de la sesión pytest
  - Como fixture `@pytest.fixture(autouse=True)` antes de cada test
- ✅ Maneja Windows policy y race conditions entre tests

### 4. Endpoint `/intent` en Operator Backend
- ✅ Agregué `POST /intent` en `operator_backend/backend/main_v7.py`
- ✅ Enriquecimiento automático de metadata:
  - Detecta "mix", "mezcla", "mixing", "blend"
  - Agrega `mode: "mix"` y `mix_ops: ["normalize", "eq", "limiter"]`
- ✅ Routing hacia Switch con metadata enriched

### 5. Pytest Configuration
- ✅ Removí `--timeout=15` del `pytest.ini` (plugin no instalado)
- ✅ Removí importación `pytest_timeout` de `configure_pytest_timeout` fixture

### 6. Test Fixes
- ✅ `test_operator_intent_proxy` — actualizado mock para `operator_backend.backend.main_v7.SwitchClient`
- ✅ `test_hermes_status_endpoint` — ahora pasa con campo `metrics`
- ✅ `test_spawner_sends_callback` — event loop fixture resolvió race condition

## Métricas

| Métrica | Before | After | Status |
|---------|--------|-------|--------|
| Fallos pytest | 7 | 0 | ✅ PASSED |
| Tests passed | 121 | 128 | ✅ +7 |
| Endpoints nuevos | 0 | 2 | ✅ /context, /providers |
| Campos aggregados | 3 | 5 | ✅ reply, profile, healthy_engines, metrics |

### Ejecución Final
```
pytest -k "hermes or switch" tests/ -q
========= 128 passed, 3 skipped, 504 deselected, 15 warnings in 19.12s =========
```

## Archivos Modificados

1. **switch/main.py** (4 patches)
   - L1375: +`"reply": content_val` 
   - L751: +`"profile": MODE_PROFILES[CURRENT_MODE]`
   - L775: +`"healthy_engines"` y `"metrics"`
   - L683: +`GET /switch/context`, `GET /switch/providers`

2. **operator_backend/backend/main_v7.py** (1 new endpoint)
   - +`POST /intent` — intent routing + metadata enrichment

3. **conftest.py** (2 additions)
   - +`_ensure_event_loop()` función
   - +`_ensure_event_loop_per_test()` fixture autouse

4. **pytest.ini** (1 removal)
   - Removido `--timeout=15` de `addopts`

5. **operator_local/** (renamed from operator/)
   - Directory rename para evitar shadowing stdlib

6. **tests/test_operator_switch_hermes_flow.py** (1 fix)
   - Actualizado mock path en `test_operator_intent_proxy`

7. **tests/test_pnp_and_integration.py** (reference only)
   - No cambios; test ahora pasa con campos agregados

## Próximos Pasos (P1+)

- [ ] Playwright MCP integration (opcional, sidecar)
- [ ] Hermes discovery Tier 2/3 (web search, HF)
- [ ] 2 test models download + registration
- [ ] Warmup/rotation smoke test
- [ ] Canonical DB generation (<500MB)
- [ ] CLI concentrator scoring (copilot-first)
- [ ] Production readiness report

## Timestamp
- Inicio: 2025-12-15 ~21:00
- Término: 2025-12-15 ~22:30
- Duración: ~1.5 horas

---
**Status: PHASE 2A COMPLETE ✅**
