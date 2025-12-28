# PROMPT 13 Implementation Status

**Date**: 2025-12-28  
**Status**: PHASES 1-3 COMPLETE (FASES 4-5 PLANNED)

---

## FASE 0: BASELINE ✓

**Snapshot**:
- Git: Clean working tree, HEAD fa1c344 (P12 complete)
- Docker: SOLO_MADRE active (4 services: madre, redis, tentaculo_link, switch)
- DB: All PRAGMA checks OK (integrity, quick, foreign_key)
- Token sources: `/home/elkakas314/vx11/tokens.env` ✓

**Output**: docs/audit/P13_*/baseline/
- snapshot.txt (git status + log + docker ps)
- db_checks.txt (PRAGMA results)
- token_sources.txt (file availability)

---

## FASE 1: DEEPSEEK R1 SMOKE TEST ✓

**Smoke Test Result**:
```
HTTP Status: 200
Model: deepseek-reasoner
Reasoning tokens: 95
Total tokens: 117
Response: Valid JSON with reasoning_content ✓
```

**Output**: 
- deepseek_smoke.log (full request/response)
- deepseek_smoke_response.json (sanitized metadata)

**Conclusion**: DeepSeek R1 API functional and ready for co-dev integration.

---

## FASE 2: DEEPSEEK R1 CO-DEV ENDPOINT ✓

**New Code**:
- `tentaculo_link/deepseek_r1_client.py` (294 lines)
  - Class: `DeepSeekR1Client`
  - Methods: `invoke()`, `_check_rate_limit()`, `_post_with_retries()`
  - Features: rate limiting (10/hour), max_tokens (2000), retry logic, sanitized logging
  - Singleton: `get_deepseek_r1_client()`

**New Endpoints in tentaculo_link/main_v7.py**:
1. `POST /operator/api/assist/deepseek_r1` (manual co-dev)
   - Purpose enum: plan | patch | review | risk_assessment
   - Rate limit: 10 requests/hour
   - Max tokens: 2000 (cost control)
   - Optional opt-in: VX11_OPERATOR_CODEV_ENABLED=1
   - Response: reasoning_content + response + metadata

2. `GET /operator/api/assist/deepseek_r1/status`
   - Returns: enabled/disabled status + config
   - Safe: no secrets leaked

**Policy**: 
- PROHIBIDO: DeepSeek como fallback automático en chat (P12 contract)
- PERMITIDO: Manual opt-in en panel co-dev (separado)
- REQUERIDO: DB logging + rate limits + budget cap

---

## FASE 3: POWER WINDOWS REAL (START/STOP SWITCH + TTL) ✓

**Infrastructure**:
- docker.sock: Already mounted in madre container (docker-compose.yml line 71) ✓
- WindowManager: Exists in madre/power_windows.py ✓
- Docker functions: docker_compose_up(), docker_compose_stop() implemented in madre/routes_power.py ✓

**New Proxy Endpoints in tentaculo_link (tentaculo_link/main_v7.py)**:
1. `POST /operator/api/chat/window/open`
   - Opens temporal window for Switch service
   - Default TTL: 600s (10 minutes)
   - Proxies to madre internal /power/window/open
   - Response: window_id + deadline + ttl_remaining_sec

2. `POST /operator/api/chat/window/close`
   - Closes active window (manual)
   - Proxies to madre internal /power/window/close
   - Response: services_stopped + closed_at

3. `GET /operator/api/chat/window/status`
   - Returns current window state
   - Response: status (open|none) + ttl_remaining_sec + active_services

**TTL Handling**:
- Phase 1 (completed): WindowManager metadata + expiry detection
- Phase 2 (needed): Background scheduler in madre to auto-close expired windows
- Recommendation: async task in madre startup to poll check_expired_windows() every 30s

---

## FASE 4: SWITCH ENFORCE FREE-MODELS-ONLY (PLANNED)

**Requirement**: Chat runtime ONLY allows free models (gpt-4o, gpt-5-mini, grok-code-fast-1, etc.)

**Design**:
1. In switch/main.py: Add model allowlist validation
   - Whitelist: Free tier models only
   - Blacklist check: Reject premium models
   - Policy violation logging to DB (audit_logs)

2. Update `/operator/api/chat` in tentaculo_link:
   - If Switch unavailable AND DeepSeek disabled: do NOT fallback
   - UI suggestion: "Open chat window (10 min)" instead of silent fallback
   - Error response: 503 "Chat temporarily unavailable"

**Spec Location**: Will be documented in P13_DESIGN_FASE_4_5.md

---

## FASE 5: OPERATOR UI (WINDOW + CO-DEV PANEL) (PLANNED)

**ChatView Updates**:
- Current: Simple message input
- New: Window status badge (CLOSED/OPEN with countdown)
- New: Button "Open 10 min" → POST /operator/api/chat/window/open
- New: Auto-disable chat input if window CLOSED
- Policy: Never fallback to DeepSeek (error instead)

**New Co-Dev Panel**:
- Location: Sidebar or new tab "Co-Dev (R1)"
- Controls:
  - Purpose selector (plan/patch/review/risk)
  - Text input (prompt)
  - "Execute" button
  - Budget display (tokens used today / limit)
  - Warning: "Uses DeepSeek API credits"
- Output: Markdown rendering + latency badge

**Theme**: Dark mode (consistent with current design)

**Spec Location**: Will be documented in P13_DESIGN_FASE_4_5.md

---

## INVARIANTS MAINTAINED ✓

1. **Single entrypoint**: All access via tentaculo_link:8000 ✓
2. **Default solo_madre**: Power windows are opt-in only ✓
3. **Hermes catalog-only**: No changes to routing ✓
4. **Secrets out of repo**: Tokens from .env only ✓
5. **DB logging**: All actions will be logged (implementation in FASE 2+ complete)

---

## NEXT STEPS

1. **FASE 4 Implementation**: Switch model allowlist validation (1-2 hours)
2. **FASE 5 Implementation**: Operator UI window + co-dev panel (3-4 hours)
3. **Testing**: Smoke tests + E2E verification
4. **Final commit**: Atomic commits FASE 4 + FASE 5 + evidence

**Target**: Complete P13 by EOD 2025-12-28
