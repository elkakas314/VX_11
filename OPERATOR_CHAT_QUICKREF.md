# OPERATOR CHAT P0+P1 QUICK REFERENCE

**Status**: Production Ready (P10 + P11 complete)

---

## API ENDPOINT

```
POST http://localhost:8000/operator/api/chat
```

### Request
```json
{
  "message": "Your question here (max 4000 chars)",
  "session_id": "optional_session_id"
}
```

### Response
```json
{
  "message_id": "msg_abc123",
  "session_id": "session_123",
  "response": "Answer from DeepSeek or switch service",
  "model": "deepseek-chat",
  "fallback_source": "deepseek_api|switch|degraded",
  "degraded": false,
  "cache_hit": false
}
```

### Headers (Required)
```
x-vx11-token: vx11-local-token
Content-Type: application/json
```

### Error Codes

| Code | Reason | Resolution |
|------|--------|-----------|
| 200 | OK | Normal response |
| 429 | Rate limited (>10 req/min) | Wait 60 seconds |
| 413 | Message too long (>4000 chars) | Reduce message size |
| 401 | Missing/invalid token | Check x-vx11-token header |
| 500 | Server error | Check container logs |

---

## P1 GUARDRAILS

### Rate Limiting
- **Limit**: 10 requests per minute per session_id
- **Exceeded**: Returns 429 Too Many Requests + retry_after: 60
- **Backend**: Redis-backed (or in-memory fallback if Redis down)

### Message Size Cap
- **Max**: 4000 characters
- **Exceeded**: Returns 413 Payload Too Large
- **Bypass**: Not possible (security guardrail)

### Caching
- **TTL**: 60 seconds
- **Key**: `operator_chat_cache:{session_id}:{message_hash}`
- **Benefit**: Repeated queries return instantly (no DeepSeek call)

### Timeouts
- **Total timeout**: 15 seconds
- **Switch timeout**: 4 seconds (fails quickly if down)
- **DeepSeek timeout**: 15 seconds (reduced from 30s)

---

## DEPLOYMENT

### Local Development
```bash
# Copy .env.example to .env.local
cp .env.example .env.local

# Set your DeepSeek API key
echo "DEEPSEEK_API_KEY=sk-your-key" >> .env.local

# Start services (SOLO_MADRE: madre + redis + tentaculo_link only)
docker compose up -d

# Test endpoint
curl -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","session_id":"test"}' \
  http://localhost:8000/operator/api/chat
```

### Key Rotation (No Restart Required)
```bash
# Update .env.local
echo "DEEPSEEK_API_KEY=sk-new-key" > .env.local

# docker-compose.override.yml loads env_file automatically
# Next request uses new key (no container restart needed)
```

### Pre-Commit Setup (Recommended)
```bash
pip install pre-commit
pre-commit install
pre-commit run -a  # Test before pushing
```

---

## MONITORING

### Health Check
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
docker compose logs -f tentaculo_link

# Watch for these markers:
# chat_cache_hit: Query returned from cache
# chat_rate_limit_exceeded: Rate limit triggered
# chat_message_too_long: Message cap enforced
# chat_deepseek_fallback_success: DeepSeek worked
# chat_switch_failed: Switch unavailable (using DeepSeek)
```

### Database Check
```bash
sqlite3 data/runtime/vx11.db \
  "SELECT COUNT(*) FROM operator_message;"
```

---

## SECURITY

### Secrets Protection
- ✅ No hardcoded keys in code
- ✅ .env* files gitignored
- ✅ Pre-commit hooks check for secrets
- ✅ GitHub Actions CI scans for secrets

### Before Pushing
```bash
# Local check (must pass)
pre-commit run -a

# Should output:
# - Detect secrets: no issues
# - TruffleHog: no high-entropy strings
# - Ruff: no linting issues
```

---

## FALLBACK CHAIN

1. **Primary**: switch service (4s timeout)
   - High quality responses, faster
   
2. **Fallback**: DeepSeek API (15s timeout)
   - Always works (if API key set + network available)
   
3. **Degraded**: Echo + apology
   - Last resort (both above unavailable)
   - Response: `[DEGRADED MODE] Services unavailable...`

---

## SOLO_MADRE POLICY

### Allowed Services (Auto-Start)
- ✅ madre (port 8001) — planning + maintenance
- ✅ redis (port 6379) — cache + rate limiter
- ✅ tentaculo_link (port 8000) — gateway

### Off-By-Policy Services (Manual Only)
- ⏸️ switch — optional, disabled by policy
- ⏸️ hermes — optional, disabled by policy
- ⏸️ hormiguero — optional, disabled by policy
- ⏸️ spawner — optional, disabled by policy

### Start Optional Service (If Needed)
```bash
docker compose up -d switch
# Then chat will use switch (4s), then DeepSeek (15s), then degraded
```

---

## TROUBLESHOOTING

### Chat returns degraded response
1. Check DeepSeek API key: `grep DEEPSEEK_API_KEY .env.local`
2. Check container logs: `docker compose logs -f tentaculo_link | grep deepseek`
3. Verify internet connection to api.deepseek.com

### Rate limit keeps triggering
- Limit is 10 req/min per session_id
- Use different session_id for different clients
- Or wait 60 seconds before retrying

### Cache always misses
- Cache key includes message_hash
- Identical messages hit cache (within 60s window)
- Different messages = different cache entries

### Message cap blocks valid requests
- Check message length: `echo -n "your message" | wc -c`
- Max is 4000 characters
- Reduce message size or split into multiple requests

---

## API EXAMPLE (Python)

```python
import requests
import json

url = "http://localhost:8000/operator/api/chat"
headers = {
    "x-vx11-token": "vx11-local-token",
    "Content-Type": "application/json"
}

payload = {
    "message": "What is VX11?",
    "session_id": "session_123"
}

resp = requests.post(url, json=payload, headers=headers)
print(json.dumps(resp.json(), indent=2))
```

---

## MORE DOCUMENTATION

- **Full P10 Report**: OPERATOR_P10_FINAL_EVIDENCE.md
- **Full P11 Report**: OPERATOR_P11_P1_HARDENING_COMPLETE.md
- **Architecture**: VX11_CONTEXT.md
- **Database Schema**: docs/audit/DB_SCHEMA_v7_FINAL.json
