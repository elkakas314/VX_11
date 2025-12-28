# INEE Extended - Feature Matrix & Endpoints Reference

**Generated**: 2024-12-28  
**Status**: Dormant Package (All features OFF by default)

---

## Feature Matrix

| Feature | Module | Endpoint | Flag | Status | Implementation |
|---------|--------|----------|------|--------|-----------------|
| Builder (Patchset) | builder.py | POST /operator/inee/builder/patchset | HORMIGUERO_BUILDER_ENABLED | Dormant | create_patchset() → INTENT only, no execution |
| Builder (Prompt) | builder.py | POST /operator/inee/builder/prompt-pack | HORMIGUERO_BUILDER_ENABLED | Dormant | create_prompt_pack() |
| Colony Register | builder.py | POST /operator/inee/colony/register | VX11_INEE_ENABLED | Dormant | register_colony() → egg state |
| Colony Lifecycle | builder.py | POST /operator/inee/colony/lifecycle/advance | VX11_INEE_ENABLED | Dormant | advance_lifecycle() → egg→larva→adult |
| Colony Heartbeat | builder.py | POST /operator/inee/colony/heartbeat | VX11_INEE_ENABLED | Dormant | heartbeat() tracking |
| Envelope (HMAC) | builder.py | POST /operator/inee/colony/envelope | VX11_INEE_REMOTE_PLANE_ENABLED | Dormant | create_envelope() → SHA256 signed + nonce protected |
| Rewards Account | builder.py | POST /operator/inee/rewards/account/{account_id} | VX11_REWARDS_ENABLED | Dormant | get_account() |
| Rewards Transaction | builder.py | POST /operator/inee/rewards/transaction | VX11_REWARDS_ENABLED | Dormant | add_transaction() |
| Rewards Status | builder.py | GET /operator/inee/rewards/status | VX11_REWARDS_ENABLED | Dormant | rewards_status() |
| Manifestator Patches | builder.py | POST /operator/inee/manifestator/patch-plan | VX11_INEE_ENABLED | Dormant | generate_patch_plan() |
| Manifestator Prompts | builder.py | POST /operator/inee/manifestator/prompt-pack | VX11_INEE_ENABLED | Dormant | generate_manifestator_prompts() |
| INEE Status | builder.py | GET /operator/inee/status | VX11_INEE_ENABLED | Dormant | inee_extended_status() |

---

## Proxy Routes (Tentaculo Link → Hormiguero)

All routes token-guarded (x-vx11-token header required).

### Builder Routes

```
POST /operator/inee/builder/patchset
  Proxy to: POST /hormiguero/inee/extended/builder/patchset
  Body: {spec_id, description, parameters}
  Response: {status, patchset_id, intent_id, changes}
  
POST /operator/inee/builder/prompt-pack
  Proxy to: POST /hormiguero/inee/extended/builder/prompt-pack
  Query: ?patchset_id=...
  Response: {status, pack_id, prompts}
```

### Colony Routes

```
POST /operator/inee/colony/register
  Proxy to: POST /hormiguero/inee/extended/colony/register
  Body: {colony_id, remote_url}
  Response: {status, colony_id, state, registered_at}
  
POST /operator/inee/colony/lifecycle/advance
  Proxy to: POST /hormiguero/inee/extended/colony/lifecycle/advance
  Query: ?colony_id=... &new_state=...
  Response: {status, colony_id, old_state, new_state}
  
POST /operator/inee/colony/heartbeat
  Proxy to: POST /hormiguero/inee/extended/colony/heartbeat
  Query: ?colony_id=...
  Response: {status, colony_id, heartbeat_at}
  
POST /operator/inee/colony/envelope
  Proxy to: POST /hormiguero/inee/extended/colony/envelope
  Body: {colony_id, payload}
  Response: {envelope_id, nonce, hmac_signature, payload}
  Note: Only active if VX11_INEE_REMOTE_PLANE_ENABLED=1
```

### Rewards Routes

```
GET /operator/inee/rewards/status
  Proxy to: GET /hormiguero/inee/extended/rewards/status
  Response: {status, top_accounts, total_points_in_circulation}
  
POST /operator/inee/rewards/account/{account_id}
  Proxy to: POST /hormiguero/inee/extended/rewards/account/{account_id}
  Response: {status, account_id, balance, transactions_count}
  
POST /operator/inee/rewards/transaction
  Proxy to: POST /hormiguero/inee/extended/rewards/transaction
  Body: {account_id, amount, reason}
  Response: {status, transaction_id, balance_after}
```

### Manifestator Routes

```
POST /operator/inee/manifestator/patch-plan
  Proxy to: POST /hormiguero/inee/extended/manifestator/patch-plan
  Body: {modules, patch_type}
  Response: {status, plan_id, patches, risk_level}
  
POST /operator/inee/manifestator/prompt-pack
  Proxy to: POST /hormiguero/inee/extended/manifestator/prompt-pack
  Body: {context}
  Response: {status, pack_id, prompts}
```

### Status Routes

```
GET /operator/inee/status
  Proxy to: GET /hormiguero/inee/extended/status
  Response: {
    status: "ok",
    enabled: false|true,
    remote_plane_enabled: false|true,
    execution_enabled: false|true,
    colonies_count: 0,
    pending_intents: 0,
    builder_available: false|true,
    rewards_available: false|true
  }
```

---

## Feature Flags Reference

### VX11_INEE_ENABLED
- **Default**: 0 (disabled)
- **Controls**: INEE router mounting, general INEE functionality
- **Impact**: If 0, /operator/inee/* endpoints return 503 or "disabled"
- **Set in**: .env or docker-compose environment

### HORMIGUERO_BUILDER_ENABLED
- **Default**: 0 (disabled)
- **Controls**: Patchset generation (Builder service)
- **Impact**: If 0, Builder endpoints return {"status": "disabled"}
- **Key**: Builder NEVER executes directly; only creates INTENT

### VX11_INEE_REMOTE_PLANE_ENABLED
- **Default**: 0 (disabled)
- **Controls**: External remote colony API exposure
- **Impact**: If 0, /operator/inee/colony/envelope returns 503
- **Note**: Single entrypoint must be true even if remote plane disabled

### VX11_INEE_EXECUTION_ENABLED
- **Default**: 0 (disabled)
- **Controls**: Madre-authorized execution of intents
- **Impact**: If 0, no intents are processed for execution
- **Status**: Currently not used (Spawner delegates separately)

### VX11_REWARDS_ENABLED
- **Default**: 0 (disabled)
- **Controls**: Rewards engine (scoring, accounting)
- **Impact**: If 0, rewards endpoints return {"status": "disabled"}
- **Use**: Internal economy for priority scheduling

### VX11_INEE_WS_ENABLED
- **Default**: 0 (disabled)
- **Controls**: WebSocket integration
- **Impact**: If 0, WebSocket routes not mounted
- **Status**: Not yet implemented

---

## Safety Constraints

### 1. No Direct Execution
- Builder.create_patchset() returns INTENT_ID only
- Actual execution delegated to Spawner (separate service)
- No code execution in hormiguero service

### 2. Single Entrypoint
- All requests must go through tentaculo_link:8000
- No direct calls to hormiguero:8004 from external clients
- Proxy routes enforce this via fastapi routing

### 3. Token Validation
- All endpoints require x-vx11-token header
- Missing token → 401/403 (token_guard dependency)
- Token checked in tentaculo_link before proxy

### 4. HMAC Envelope Protection
- All remote colony messages HMAC-SHA256 signed
- Nonce replay protection enabled
- Replay attack → {"status": "rejected"} or similar

### 5. Additive-Only Changes
- No existing tables modified
- No existing endpoints removed or changed
- All new tables have IF NOT EXISTS clause
- Safe to re-run DB bootstrap

### 6. Dormant by Default
- All flags OFF at startup
- Services return "disabled" status when flags OFF
- No background processing until explicitly enabled
- SOLO_MADRE_CORE power windows unaffected

---

## DB Tables Added

**36 Idempotent Tables** (CREATE TABLE IF NOT EXISTS):

### INEE Internal Plane
- inee_colonies: Remote colony registry
- inee_agents: Agent instances within colonies
- inee_intents: Created intents (Builder output)
- inee_audit: Audit log

### Remote Colony Support
- colony_eggs: Beta queens in incubation
- colony_lifecycle: Lifecycle state tracking
- colony_envelopes: HMAC-signed messages

### Builder Support
- builder_specs: Spec definitions
- builder_patchsets: Generated patchsets
- builder_prompt_packs: LLM prompts

### Rewards Support
- reward_accounts: Account registry
- reward_transactions: Transaction log
- reward_scoring: Scoring rules

### Manifestator Support
- manifestator_patches: Patch metadata
- manifestator_prompts: Prompt templates
- manifestator_diagrams: Diagram definitions (reserved)

### 6 Performance Indices
- idx_inee_colonies_status: Fast status queries
- idx_colony_lifecycle_state: Lifecycle filtering
- idx_builder_patchsets_correlation: Correlation tracking
- idx_reward_accounts_balance: Account queries
- idx_inee_intents_pending: Pending intent queries
- idx_colony_envelopes_nonce: Nonce lookups

---

## Test Coverage

### P0 Tests (Dormant Verification)
- ✅ Flags OFF → endpoints return 503/"disabled"
- ✅ Token validation (missing token → 401/403)
- ✅ Builder dormant (HORMIGUERO_BUILDER_ENABLED=0)
- ✅ Remote plane OFF (VX11_INEE_REMOTE_PLANE_ENABLED=0)
- ✅ Status shows enabled=false
- ✅ Direct hormiguero endpoint dormant

### P1 Tests (Semantics)
- ✅ Builder endpoint reachable
- ✅ Builder returns patchset_id (INTENT mode)
- ✅ No execution traces in response
- ✅ Envelope has HMAC signature field
- ✅ Nonce field present (replay protection)

### DB Tests (Schema)
- ✅ inee_colonies, inee_intents, colony_lifecycle, colony_envelopes exist
- ✅ builder_patchsets, reward_accounts exist
- ✅ DB integrity check OK (PRAGMA integrity_check)
- ✅ FK constraints satisfied
- ✅ 6+ performance indices
- ✅ INEE-related table count > 0

---

## Activation Steps

To enable INEE Extended in production:

```bash
# 1. Set feature flags in .env
export VX11_INEE_ENABLED=1
export HORMIGUERO_BUILDER_ENABLED=1
export VX11_INEE_REMOTE_PLANE_ENABLED=1  # if needed
export VX11_REWARDS_ENABLED=1

# 2. Restart services
docker-compose restart hormiguero

# 3. Verify status
curl -H "x-vx11-token: vx11-local-token" \
  http://localhost:8000/operator/inee/status

# Expected response:
# {
#   "status": "ok",
#   "enabled": true,
#   "remote_plane_enabled": true,
#   "execution_enabled": false,
#   "colonies_count": 0,
#   "pending_intents": 0,
#   "builder_available": true,
#   "rewards_available": true
# }
```

---

## Version Info

| Component | Version | Status |
|-----------|---------|--------|
| FastAPI | 0.104.1 | ✅ Active |
| Pydantic | 2.4.2 | ✅ Active |
| SQLAlchemy | 2.0.23 | ✅ Prepared (not yet used) |
| SQLite | Standard | ✅ Active |
| HMAC-SHA256 | stdlib | ✅ Active |
| UUID | stdlib | ✅ Active |

---

## Notes

- All code is **dormant by default** (feature flags OFF)
- **No breaking changes** to existing functionality
- **Single entrypoint** enforced via proxy in tentaculo_link
- **No direct execution** (Builder creates INTENT, Spawner executes)
- **Token-guarded** all endpoints (x-vx11-token required)
- **HMAC-protected** remote communication
- **Additive-only** DB schema (IF NOT EXISTS clauses)
- **Production-ready** when flags enabled

---

## References

- Canonical Spec: docs/canon/VX11_INEE_OPTIONAL_CANONICAL_v1.0.0.json
- DB Schema: hormiguero/hormiguero/core/db/schema_inee_extended.py
- Models: hormiguero/hormiguero/inee/models.py
- Services: hormiguero/hormiguero/inee/builder.py
- Endpoints: hormiguero/hormiguero/inee/api/routes_extended.py
- Proxy: tentaculo_link/main_v7.py (lines 1022-1101)
- Tests: tests/test_inee_p0_dormant.sh, test_inee_p1_builder_intent.sh, test_inee_db_schema.sh
