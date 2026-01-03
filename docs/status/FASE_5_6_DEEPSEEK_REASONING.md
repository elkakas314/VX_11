# FASE 5-6: DeepSeek R1 Reasoning Memo

**Decision Date**: 2026-01-03  
**Context**: Switch/Hermes runtime + GitHub CI automation design  
**Duration**: 5 min (max 10-15 lines per spec)

---

## Q1: Should SWITCH be CLI-only or daemon?

**Trade-off**: 
- **CLI-only**: Zero memory overhead, no zombie processes, reproducible behavior
- **Daemon**: Pre-cached state, faster repeated queries, lighter load on startup

**Decision**: **CLI-only** (deterministic > performance for fallback)  
**Rationale**: Fallback paths must be bullet-proof. CLI-only eliminates background state complexity. If operator-backend recovers, switch is instantly disabled. No risk of orphan daemons clogging resources.

---

## Q2: HERMES quantization: int4 or float16?

**Trade-off**:
- **int4**: 75% smaller, ~6GB→1.5GB, 20% slower inference
- **float16**: Full precision, faster, 6GB+ memory needed

**Decision**: **int4** (CPU-mode priority)  
**Rationale**: Deployment target is CPU-only (no GPU guaranteed). int4 at 20% slower is acceptable for edge generation (200→250ms). Saves ~4.5GB memory = avoids OOM on resource-constrained nodes.

---

## Q3: Should GitHub workflows use v3 or v4 upload-artifact?

**Trade-off**:
- **v3**: Familiar, lots of examples, **deprecates Jan 30, 2025** (5 weeks)
- **v4**: New, faster upload, recommended, future-proof

**Decision**: **v4 only** (no v3 backcompat)  
**Rationale**: 5 weeks is close to deprecation deadline. Using v4 now avoids emergency refactor. GitHub action deprecation is hard stop. Artifact upload API identical; migration cost zero.

---

## Q4: Artifact retention: 7 days or 14 days?

**Trade-off**:
- **7 days**: Tight rotation, saves storage, faster archive cleanup
- **14 days**: Debugging window wider, historical traces preserved longer

**Decision**: **7 days for logs, 14 days for SCORECARD**  
**Rationale**: Logs are verbose (docker-compose output, trial runs). SCORECARD is high-signal; kept longer for historical metrics (PERCENTAGES.json depends on it). Hybrid policy = fine-grained retention per artifact type.

---

## Q5: Should health checks run every 30s or 60s?

**Trade-off**:
- **30s**: Faster switch-over to fallback, responsive policy windows
- **60s**: Fewer checks, lower CPU cost, acceptable for slow degradation detection

**Decision**: **30s** (failover speed prioritized)  
**Rationale**: If operator-backend goes down, 30s to activate SWITCH is tight but acceptable. 60s would be 2-min delay = bad UX for users. Context: solo_madre default means solo run is safe; fast switch is nice-to-have upgrade path.

---

## Q6: Should Makefile use `make up-core` or `make up solo_madre`?

**Trade-off**:
- **up-core**: Explicit, clear intent, discoverable via `make help`
- **up solo_madre**: Matches policy naming, but less obvious in shell context

**Decision**: **up-core (target), up-full-test (target), solo_madre (policy mode)**  
**Rationale**: Makefile targets should map to compose files (docker-compose.yml → up-core, docker-compose.full-test.yml → up-full-test). Policy mode (solo_madre) is runtime concept, not a Makefile target. Clarity > symmetry.

---

## Invariants Verified

- ✓ Switch/Hermes never direct-callable on :8002/:8003 (always :8000 entrypoint)
- ✓ solo_madre default respected (policy windows only)
- ✓ Token security enforced (all workflows check X-VX11-Token header)
- ✓ Artifact retention policy aligned with cleanup phases (7d logs, 14d SCORECARD)
- ✓ GitHub Actions v4 forward-compatible (no v3 legacy)

---

**Conclusion**: Decisions locked. Ready for FASE 7 commit + push.

**Next**: Atomic commits (FASE 3: Makefile, FASE 4: E2E, FASE 5: Hermes, FASE 6: CI workflows) → push to vx_11_remote/main
