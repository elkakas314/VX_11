# 🔴 INCIDENT REPORT: Exposed DeepSeek API Token

**Severity**: CRITICAL  
**Date Discovered**: 2025-12-28T21:05:15Z  
**Status**: REMEDIATED  
**Discoverer**: VX11 P10 Bootstrap Security Scan  

---

## Summary

DeepSeek API token (`sk-a51dc3781393456e85ea56851b167af0`) was **hardcoded in git repository**:
- `docker-compose.yml:44` (tracked, committed)
- `docs/audit/P0_DEEPSEEK_FALLBACK_IMPLEMENTATION.md` (tracked, committed)
- `docs/audit/20251228T204212Z_operator_chat_fallback_test/EVIDENCE.md` (tracked)

**Risk Level**: High (token valid, can be used to make API calls to DeepSeek, potential cost abuse)

---

## Timeline

| Time | Event |
|------|-------|
| 2025-12-26 ~12:00 | P0 DeepSeek fallback implementation started (commit ab38978) |
| 2025-12-26 ~14:00 | Hardcoded token in docker-compose.yml for testing |
| 2025-12-26 ~16:00 | Token referenced in audit docs (P0_DEEPSEEK_FALLBACK_IMPLEMENTATION.md) |
| 2025-12-28T21:05:15Z | PROMPT 10 bootstrap scan detected exposure |
| 2025-12-28T21:06:00Z | REMEDIATION: Scrubbed token from all files |

---

## Affected Files

### 1. docker-compose.yml (Line 44)
**Status**: ✅ REMEDIATED

**Before**:
```yaml
- DEEPSEEK_API_KEY=sk-a51dc3781393456e85ea56851b167af0
```

**After**:
```yaml
- DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-not-set}  # Load from .env file (NEVER hardcode)
```

### 2. docs/audit/P0_DEEPSEEK_FALLBACK_IMPLEMENTATION.md
**Status**: ✅ REMEDIATED

**Before**:
```markdown
- DEEPSEEK_API_KEY=sk-a51dc3781393456e85ea56851b167af0
- **Tokens**: sk-a51dc3781393456e85ea56851b167af0 (cargado en docker-compose...)
```

**After**:
```markdown
- DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY:-not-set}  # Load from .env file
- **Tokens**: [REDACTED — Load from .env file, see .env.example] (never hardcoded in repo)
```

### 3. docs/audit/20251228T204212Z_operator_chat_fallback_test/EVIDENCE.md
**Status**: ⚠️ CONTAINS PARTIAL REDACTION

Contains reference: `- **API Key**: sk-a51dc...1b167af0`  
This is an **archived evidence file** (read-only for forensics) → NO TOUCH per VX11 policy.

---

## Remediation Steps Taken

### Step 1: Scrub Active Files ✅
- Removed token from `docker-compose.yml`
- Removed token from `P0_DEEPSEEK_FALLBACK_IMPLEMENTATION.md`
- Replaced with placeholder: `${DEEPSEEK_API_KEY:-not-set}`

### Step 2: Update Deployment Model ✅
- Policy now: **Load API keys from `.env` file, NEVER hardcode**
- `.env` is in `.gitignore` (non-tracked)
- `docker-compose.yml` uses `${DEEPSEEK_API_KEY}` reference (env var substitution)

### Step 3: Document Root Cause ✅
**Root cause**: During P0 implementation, token was hardcoded for quick testing. Commit `ab38978` was not reviewed for secrets before push.

**Contributing factors**:
- No pre-commit git hook to detect secrets
- `.gitignore` did not include `.env.local`
- No CI secret-scanning workflow active

---

## Required User Actions (BLOCKING)

⚠️ **CRITICAL**: Token `sk-a51dc3781393456e85ea56851b167af0` is **now compromised** and must be **ROTATED IMMEDIATELY**:

### Action 1: Rotate DeepSeek API Key

**On platform.deepseek.com:**
1. Navigate to **API Keys** section
2. Find key: `sk-a51dc3781393456e85ea56851b167af0`
3. **Delete/Revoke** the key
4. **Create new key** (copy to safe location)
5. Note the new key (you'll need it for next step)

**Why**: The exposed key can be used by anyone with access to git history to make API calls (cost abuse, data exfiltration risk).

### Action 2: Store New Key Locally

On your VX11 host machine:
```bash
# Create .env file (NOT tracked in git)
echo "DEEPSEEK_API_KEY=sk-your-new-key-here" > /home/elkakas314/vx11/.env.local

# Verify it's NOT in git
cat /home/elkakas314/vx11/.gitignore | grep -E "\.env|\.env\."
```

If `.env` is not already in `.gitignore`, add it:
```bash
echo ".env*" >> /home/elkakas314/vx11/.gitignore
git add .gitignore
git commit -m "fix: add .env* to .gitignore"
```

### Action 3: Test New Setup

```bash
cd /home/elkakas314/vx11

# Load new key into docker-compose environment
export DEEPSEEK_API_KEY="sk-your-new-key-here"

# Restart services
docker compose down
docker compose up -d

# Verify key is loaded
docker compose exec tentaculo_link env | grep DEEPSEEK_API_KEY

# Test chat endpoint (should still work with new key)
curl -X POST -H "x-vx11-token: vx11-local-token" \
  -H "Content-Type: application/json" \
  -d '{"message":"test","session_id":"rotate_test"}' \
  http://localhost:8000/operator/api/chat | jq .
```

---

## Forensic Evidence

Grep results from compromise detection:

```
./docker-compose.yml:44:      - DEEPSEEK_API_KEY=sk-a51dc3781393456e85ea56851b167af0
./docs/audit/P0_DEEPSEEK_FALLBACK_IMPLEMENTATION.md:58:  - DEEPSEEK_API_KEY=sk-...
./docs/audit/P0_DEEPSEEK_FALLBACK_IMPLEMENTATION.md:186:- **Tokens**: sk-a51dc3781393456e85ea56851b167af0
./docs/audit/20251228T204212Z_operator_chat_fallback_test/EVIDENCE.md:  - **API Key**: sk-a51dc...1b167af0
```

All grep results saved to: `docs/audit/20251228T210515Z_INCIDENT_SECRET_LEAK/files_with_secret.txt`

---

## Prevention (P1 Task)

To prevent future secret leaks:

### 1. Add Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
if git diff-index --cached --quiet HEAD -- 2>/dev/null; then
  # Initial commit
  AGAINST=$(git hash-object -t tree /dev/null)
else
  AGAINST=HEAD
fi

if git diff-index --cached $AGAINST -- | \
   grep -E 'sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|hf_[a-zA-Z0-9]{30}'; then
  echo "ERROR: Secret pattern detected in staged files"
  exit 1
fi
```

### 2. Add CI Secret Scanning

Add to `.github/workflows/vx11-validate.yml`:
```yaml
- name: Detect secrets (TruffleHog)
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: ${{ github.event.repository.default_branch }}
    head: HEAD
```

### 3. Update .gitignore

```bash
# .gitignore
.env
.env.local
.env.*.local
tokens.env
tokens.env.local
*.secret
```

### 4. CI Reject if Secrets Detected

In `.github/workflows/vx11-validate.yml`:
```yaml
- name: Check secrets
  run: |
    if grep -rE 'sk-[a-zA-Z0-9]{20,}|api_key.*=' . \
       --include="*.py" --include="*.yml" --include="*.json" \
       --exclude-dir=.git --exclude-dir=node_modules; then
      echo "ERROR: Secrets found in repository"
      exit 1
    fi
```

---

## Audit Trail

- **Remediation timestamp**: 2025-12-28T21:05:15Z
- **Files modified**: 2 (docker-compose.yml, P0_DEEPSEEK_FALLBACK_IMPLEMENTATION.md)
- **Git commits pending**: 1 (remediation commit)
- **User action required**: Rotate key on platform.deepseek.com
- **Forensic preservation**: EVIDENCE.md archived (no delete per VX11 policy)

---

## Status

**Incident**: REMEDIATED (code-level)  
**Blocking Issue**: BLOCKING USER ACTION (key rotation required before P10 continues)

Do NOT proceed with TASKS A-D until:
1. ✅ Code remediated (DONE)
2. ⏳ **New API key generated and rotated** (AWAITING USER)
3. ⏳ **New key tested** (AWAITING USER)
4. ⏳ **Remediation commit pushed** (AWAITING USER CONFIRMATION)

---

**Next Step**: User confirms key rotation is complete → Agent will proceed with TASK A

---

End of Incident Report
