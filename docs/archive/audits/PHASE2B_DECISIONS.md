# VX11 Phase 2B — Decisions Log

**Date:** 2025-12-15  
**Phase:** Phase 2B Closure (Production Readiness)  
**Decision Authority:** Automatic execution per mandate

---

## Key Decisions Made

### 1. Model Selection for Testing

**Decision:** TinyLlama 1B + Llama2 7B (Q4_0 quantization)

**Rationale:**
- TinyLlama: 608MB, fast warmup (~20ms), ideal for quick regression tests
- Llama2: 3.6GB, production-grade LLM, suitable for comprehensive scenarios
- Q4_0: balances speed vs quality better than larger quantizations for local testing
- Both available without authentication issues (verified via HF API)

**Status:** ✅ ACCEPTED

---

<!-- Full decisions document archived; original remains in docs/audit/PHASE2B_DECISIONS.md -->
