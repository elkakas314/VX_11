# DS-R1(A) PLAN — PHASE 2: DEEPSEEK R1 PROVIDER NORMALIZATION

**DeepSeek R1 Reasoning Model**  
**Correlation ID**: phase-2-plan-20251229-150000  
**Objective**: Design unified provider pattern for DeepSeek R1 integration

---

## STRATEGY

### Problem Statement
- Multiple DeepSeek implementations (madre, config, switch, tentaculo)
- No unified interface (response schemas differ)
- No mock provider (tests require network or env)
- No correlation tracking (traceability lost)
- Not easily swappable (hardcoded imports)

### Solution Design

**Phase 2 will deliver**:
1. Abstract BaseProvider class (interface contract)
2. DeepSeekR1Provider (normalized from existing madre client)
3. MockProvider (deterministic for tests)
4. LocalFallbackProvider (graceful degradation)
5. ProviderRegistry (centralizedlookup)
6. Correlation_id propagation (traceability)

### Architecture

```
Entrypoint: /operator/api/chat (tentaculo:8000)
    ↓
[Correlation ID injected: uuid or request-id]
    ↓
tentaculo_link/routes/chat.py
    ↓ [6s timeout]
switch.route_with_provider()  [if window open]
    ↓ [provider selection]
[Mock | DeepSeek R1 | Local Fallback]
    ↓
Response: status + provider + model + content + correlation_id
```

### Implementation Order

**Step 1**: Create provider base class + registry
- File: `switch/providers/__init__.py`
- Exports: `BaseProvider`, `ProviderRegistry`, `get_provider()`

**Step 2**: Implement concrete providers
- `DeepSeekR1Provider` (from madre/llm/deepseek_client.py)
- `MockProvider` (deterministic test double)
- `LocalFallbackProvider` (graceful degradation)

**Step 3**: Add correlation_id middleware
- Tentaculo: inject `x-correlation-id` header
- Madre: propagate to provider calls
- Provider: echo in response

**Step 4**: Update call sites
- madre/main.py:148 (chat endpoint) → use get_provider()
- switch/main.py (if routing enabled) → use registry
- config/deepseek.py → delegate to DeepSeekR1Provider

**Step 5**: Tests
- Unit: mock provider, timeout, error handling
- Integration: chat endpoint with mock flag ON

---

## DELIVERABLES

### Code Changes
1. `switch/providers/__init__.py` (NEW, 150 lines)
   - BaseProvider ABC
   - DeepSeekR1Provider
   - MockProvider
   - LocalFallbackProvider
   - ProviderRegistry

2. `madre/llm/deepseek_client.py` (REFACTOR, 20 lines)
   - Convert to DeepSeekR1Provider class method
   - Delegate from existing function

3. `config/deepseek.py` (UPDATE, 10 lines)
   - Use get_provider("deepseek_r1")

4. `tentaculo_link/main_v7.py` (UPDATE, 5 lines)
   - Inject correlation_id header

5. Tests: `tests/test_deepseek_provider.py` (NEW, 80 lines)
   - Mock provider test
   - Timeout test
   - Fallback test

### Configuration
- `VX11_DEEPSEEK_PROVIDER`: select provider ("deepseek_r1" | "mock" | "local")
- `VX11_MOCK_PROVIDERS`: true/false (enable all mocks for CI)
- Defaults: "local" (no network), safe

### Compliance
✅ Single entrypoint: NO change to routing  
✅ solo_madre: provider is internal to madre/switch  
✅ No hardcoded secrets: env vars only  
✅ No stubs: mock is explicit via flag  
✅ Traceable: correlation_id in all responses  

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Breaking change to madre/llm | Backward compat wrapper (existing function delegates to class) |
| Provider misconfiguration | Default to "local" fallback (always works) |
| Test timeout | Mock provider returns <5ms |
| Correlation_id collision | Use UUID v4 + timestamp |

---

## SUCCESS CRITERIA

- [ ] BaseProvider abstract class defined
- [ ] 3 concrete providers implemented
- [ ] MockProvider deterministic (no network)
- [ ] Correlation_id propagated through chain
- [ ] Backward compatible (existing code still works)
- [ ] Tests PASS with mock flag
- [ ] No new env vars required (optional, fallback works)

---

## NEXT: IMPLEMENTATION

Ready to code. Estimated time: 1 hour.

