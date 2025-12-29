# PHASE 2 — DEEPSEEK R1 PROVIDER INTEGRATION (BASELINE)

**Timestamp**: 2025-12-29T15:00:00Z  
**Objective**: Normalize DeepSeek R1 as provider pattern; add mock + correlation_id; make testable

---

## BASELINE STATE

### Existing DeepSeek Integration

**Files found**:
1. `madre/llm/deepseek_client.py` (132 lines) — sync/async client with fallback
2. `config/deepseek.py` (280 lines) — wrapper with local fallback
3. `switch/deepseek_r1_provider.py` (118 lines) — audio analysis provider (incomplete)
4. `tentaculo_link/deepseek_client.py` — duplicate/variant
5. `tentaculo_link/deepseek_r1_client.py` — variant

### Current State Analysis

**madre/llm/deepseek_client.py**:
- ✅ Reads API key from env (DEEPSEEK_API_KEY priority)
- ✅ Async support
- ✅ Fallback on missing token
- ❌ No mock provider
- ❌ No correlation_id
- ❌ Response schema varies (status/provider/model keys mixed)

**config/deepseek.py**:
- ✅ Feature flag integration
- ✅ Deterministic fallback (local echo)
- ✅ Settings-based control
- ❌ No mock mode
- ❌ No provider pattern (just functions)

**switch/deepseek_r1_provider.py**:
- ⚠️  Audio-specific (not generic routing provider)
- ❌ Missing integration with switch router
- ❌ No registry pattern

### Issue

**Problem**: Multiple DeepSeek implementations, no unified provider pattern, no mock mode for tests

**Impact**: 
- Test suite requires network or env vars
- Hard to swap providers
- Correlation tracking missing

---

## SPECIFICATION (PHASE 2)

### Provider Pattern (Normalized)

```python
class BaseProvider(ABC):
    @abstractmethod
    async def __call__(
        self,
        prompt: str,
        correlation_id: str,
        timeout_seconds: int = 15
    ) -> ProviderResponse:
        """
        Returns:
        {
            "status": "success" | "degraded" | "error",
            "provider": "deepseek" | "local" | "mock",
            "model": "deepseek-reasoner" | None,
            "content": str,
            "reasoning": str (optional, for R1),
            "correlation_id": str (echoed),
            "latency_ms": int,
            "error": str (if status=error)
        }
        """
```

### Registry Pattern

```python
# In switch/providers/__init__.py
PROVIDER_REGISTRY = {
    "deepseek_r1": DeepSeekR1Provider(),
    "mock": MockProvider(),
    "local": LocalFallbackProvider(),
}

def get_provider(name: str) -> BaseProvider:
    return PROVIDER_REGISTRY.get(name, PROVIDER_REGISTRY["local"])
```

### Mock Provider (for tests)

```python
class MockProvider:
    async def __call__(self, prompt, correlation_id, timeout_seconds=15):
        return {
            "status": "success",
            "provider": "mock",
            "model": "mock-reasoner",
            "content": f"[MOCK] Analyzed: {prompt[:50]}...",
            "reasoning": "[Mock reasoning]",
            "correlation_id": correlation_id,
            "latency_ms": 5,
        }
```

### Activation Pattern

```python
# Environment variables
VX11_DEEPSEEK_PROVIDER="mock" | "deepseek_r1" | "local"  # default: local
VX11_MOCK_PROVIDERS=true  # global test flag
```

---

## IMPLEMENTATION TASKS

1. ✅ Baseline analysis (DONE — this document)
2. Create provider base class + registry
3. Normalize madre/llm/deepseek_client.py → DeepSeekR1Provider
4. Create MockProvider
5. Add correlation_id propagation (tentaculo → madre → provider)
6. Unit tests (mock mode, timeout, fallback)
7. Integration test (switch window → provider)
8. Commit + review

