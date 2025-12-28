# TASK A — P11 P1 BASELINE AUDIT: FINDINGS

**Timestamp**: 2025-12-28T212500Z  
**Status**: BASELINE CAPTURED + RIESGOS IDENTIFICADOS

## ESTADO ACTUAL (SNAPSHOT)

### Git/Docker/Chat Health
✓ HEAD: 36c9f29 (P10 FINAL)  
✓ Services: madre + redis + tentaculo_link UP  
✓ Chat: Working (deepseek_api fallback, 3748 chars response)  
✓ DB: quick_check=ok

## 10 RIESGOS P1 IDENTIFICADOS

1. **API Key Rotation** — CRITICAL — Old key still in container; TASK B enables hot-rotation
2. **Env Injection Model** — HIGH — docker-compose.override.yml missing env_file
3. **Rate Limiting** — HIGH — No rate limiting on /operator/api/chat
4. **Message Size Cap** — MEDIUM — No max length (4000 chars proposed)
5. **Caching** — MEDIUM — No cache on repeated queries (60s TTL proposed)
6. **Secrets Detection** — CRITICAL — No pre-commit/CI scanning (TASK D adds)
7. **Pre-Commit Hook** — MEDIUM — No local secret detection
8. **GitHub Actions** — HIGH — No CI-level secret scanning
9. **.env.local Tracking** — MEDIUM — Not in .gitignore yet
10. **Timeout Hardcoding** — MEDIUM — deepseek_client.py has hardcoded 30s timeout

## ARCHIVOS A MODIFICAR (PLAN)

| Task | File | Change | Impact |
|------|------|--------|--------|
| B | .gitignore | Add `.env.local`, `.env.*.local` | Prevent accidental commits |
| B | docker-compose.override.yml | Add `env_file: .env.local` | Enable hot key rotation |
| C | main_v7.py | Rate limit + cache in /operator/api/chat | Prevent spam + reduce costs |
| C | deepseek_client.py | Add message validation + timeout config | Prevent payload explosions |
| D | .pre-commit-config.yaml | Create with trufflehog + detect-secrets | Local secret detection |
| D | .github/workflows/secret-scan.yml | Create with TruffleHog action | CI-level security |

## POLICY COMPLIANCE

✅ SOLO_MADRE maintained  
✅ Single entrypoint (localhost:8000)  
✅ No hardcoded secrets (P10 fixed)  
✅ Chat always works (with guardrails in P1)

## READINESS

**✅ READY FOR TASKS B-D** — No blockers, all changes non-breaking.

Timeline: B (15 min) + C (45 min) + D (20 min) = ~80 min total.

