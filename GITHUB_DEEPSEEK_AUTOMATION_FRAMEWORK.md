# VX11 GitHub + DeepSeek Security & Automation Framework

**Status**: ✅ FULLY HARDENED  
**Date**: 2026-01-03  
**Commits**: 7 (security + workflow docs)

---

## 📋 Summary: 3 Layers of Security

### Layer 1: Token Security (Incident Response)
**Goal**: Prevent token leaks in documentation and git history

| Component | File | Status |
|-----------|------|--------|
| **Documentation cleaned** | `docs/GITHUB_API_SETUP.md` | ✅ No real tokens (placeholders only) |
| **Incident report** | `docs/audit/GITHUB_API_SECURITY_INCIDENT_20260103.md` | ✅ Detailed timeline |
| **User rotation guide** | `GITHUB_SECURITY_FIX_COPY_PASTE.md` | ✅ 3-step quickstart |
| **Rotation script** | `scripts/github-token-rotation.sh` | ✅ Guided + safe |

**Commit**: `b96b12d` (docs(github): remove leaked tokens...)

---

### Layer 2: Pre-Commit Protection (Prevention)
**Goal**: Block tokens BEFORE they reach git

| Feature | Location | Status |
|---------|----------|--------|
| **Pre-commit hook** | `.git/hooks/pre-commit` | ✅ Executable (chmod +x) |
| **Token pattern detection** | `ghp_*`, `github_pat_*` | ✅ Blocks at commit time |
| **API key detection** | `sk-*`, `sk_live_*` | ✅ Prevents DeepSeek leaks |
| **Private key detection** | `*.pem`, `*.key`, `id_rsa` | ✅ Security hardening |
| **tokens.env staging block** | Warns if committed | ✅ Prevents accidents |

**Commit**: `740ec78` (docs(github): enhance API setup + add pre-commit...)

---

### Layer 3: Workflow Hardening (Process Safety)
**Goal**: Enable automation while preventing mistakes

| Pattern | File | Safety Features |
|---------|------|-----------------|
| **GitHub API** | `docs/GITHUB_API_SETUP.md` | ✅ Bearer auth, `gh api` examples, anti-patterns |
| **UI Polish + DeepSeek** | `OPERATOR_UI_POLISH_DEEPSEEK_WORKFLOW.md` | ✅ Hard invariants, validation, red flags |

**Commit**: `0deaaa2` (docs: add UI Polish workflow with DeepSeek...)

---

## 🔐 Security Checklist (For Users & Teams)

### Before First Use

- [ ] **Rotate GitHub tokens** (old → new in tokens.env)
- [ ] **Verify .gitignore** includes `tokens.env`
- [ ] **Pre-commit hook** is executable:
  ```bash
  ls -lh .git/hooks/pre-commit  # Should show -rwx------
  ```
- [ ] **Test hook** by trying to commit a token (should fail)

### During Development

- [ ] **Load tokens from env**:
  ```bash
  source tokens.env
  ```
- [ ] **Never echo tokens**:
  ```bash
  # ✅ SAFE
  echo "First 20 chars: ${GITHUB_FINEGRAND_PAT:0:20}..."
  
  # ❌ UNSAFE
  echo $GITHUB_FINEGRAND_PAT
  ```
- [ ] **Use `gh api`** for most operations (safer)
- [ ] **For scripts**: Load from `tokens.env`, not hardcoded

### Before Committing

- [ ] **Pre-commit hook runs** (automatic, blocks if needed)
- [ ] **Verify no tokens in diff**:
  ```bash
  git diff --cached | grep -E "ghp_|github_pat_|sk-"
  # Should return nothing
  ```
- [ ] **For documentation**: Use placeholders:
  ```bash
  # ✅ CORRECT
  GITHUB_TOKEN=${GITHUB_FINEGRAND_PAT}
  
  # ❌ WRONG
  GITHUB_TOKEN=github_pat_11BN5ARTA0iURN705UlKWd_...
  ```

---

## 📚 Documentation Map

### Security & Token Management
| Document | Purpose | Audience |
|----------|---------|----------|
| `GITHUB_SECURITY_FIX_SUMMARY.md` | Executive summary | Team leads |
| `GITHUB_SECURITY_FIX_COPY_PASTE.md` | Step-by-step rotation | Users (5 min) |
| `docs/GITHUB_API_SETUP.md` | API reference (safe patterns) | Developers |
| `docs/audit/GITHUB_API_SECURITY_INCIDENT_20260103.md` | Incident details | Auditors |
| `scripts/github-token-rotation.sh` | Interactive guide | Users (optional) |

### Automation Workflows
| Document | Purpose | Audience |
|----------|---------|----------|
| `OPERATOR_UI_POLISH_DEEPSEEK_WORKFLOW.md` | UI polish with DeepSeek | Designers/Devs |
| `.git/hooks/pre-commit` | Automated token detection | All (runs automatically) |

---

## 🚀 Using This Framework

### For GitHub API Automation

```bash
# 1. Load tokens (from secure location)
source tokens.env

# 2. Use gh CLI (recommended)
gh api --paginate /user/repos --jq '.[] | .name'

# OR use curl with proper headers
curl -sS \
  -H "Authorization: Bearer ${GITHUB_FINEGRAND_PAT}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/user | jq .

# 3. Check rate limit
gh api rate_limit --jq '.rate_limit | {limit, remaining}'
```

### For UI Polish with DeepSeek

```bash
# 1. Read the workflow guide
cat OPERATOR_UI_POLISH_DEEPSEEK_WORKFLOW.md

# 2. Create branch
git checkout -b operator-ui-polish-deepseek

# 3. Get design recommendations from DeepSeek using prompts in guide

# 4. Apply changes (ONLY in operator/frontend/src/)

# 5. Validate (all checks must pass)
python3 scripts/validate-frontend.py --verbose
cd operator/frontend && npm run build && cd ../..
bash vx11-ui-polish-validator.sh

# 6. Commit (single, clean)
git commit -m "vx11(operator-ui): visual polish — ..."

# 7. Create PR
gh pr create --base main --head operator-ui-polish-deepseek
```

---

## 🛡️ What's Protected

| Threat | Layer | Mechanism |
|--------|-------|-----------|
| Token in documentation | Layer 1 | Removed real tokens, use placeholders |
| Token in git history | Layer 1 | Incident report + rotation guide |
| Token in commit | Layer 2 | Pre-commit hook blocks `ghp_*` patterns |
| API key exposure | Layer 2 | Pre-commit hook blocks `sk_*` patterns |
| Wiring changes during UI polish | Layer 3 | Hard invariants + validation checks |
| Hardcoded ports in UI | Layer 3 | `validate-frontend.py` + `vx11-ui-polish-validator.sh` |

---

## ✅ Validation Status

| Check | Status | Command |
|-------|--------|---------|
| No tokens in docs | ✅ PASS | `grep -E "github_pat_|ghp_" docs/GITHUB_API_SETUP.md` (no output) |
| Pre-commit hook exists | ✅ PASS | `ls -x .git/hooks/pre-commit` |
| All commits pushed | ✅ PASS | `git log vx_11_remote/main --oneline -7` |
| Build succeeds | ✅ PASS | `cd operator/frontend && npm run build` |
| Health check responds | ✅ PASS | `curl http://localhost:8000/health` |

---

## 🔄 Next Steps (Team)

### Immediate (Today)
- [ ] Read `GITHUB_SECURITY_FIX_COPY_PASTE.md`
- [ ] Rotate GitHub tokens (3 steps, 5 minutes)
- [ ] Test pre-commit hook:
  ```bash
  echo "test: ghp_fake1234567890123456789012" > test.txt
  git add test.txt
  git commit -m "test"  # Should FAIL
  rm test.txt
  git reset HEAD
  ```

### Short-term (This Week)
- [ ] Deploy pre-commit hook to team (copy `.git/hooks/pre-commit` to shared locations)
- [ ] Brief team on new security patterns
- [ ] Enable GitHub Push Protection (Settings → Code security)

### Long-term (Monthly)
- [ ] Rotate tokens quarterly
- [ ] Review `docs/audit/` for any new incidents
- [ ] Update DeepSeek prompts based on UI feedback
- [ ] Monitor pre-commit hook logs for patterns

---

## 📞 Support

### Token Issues
→ Read: `GITHUB_SECURITY_FIX_COPY_PASTE.md`  
→ Run: `bash scripts/github-token-rotation.sh`

### GitHub API Questions
→ Read: `docs/GITHUB_API_SETUP.md` (anti-patterns section)

### UI Polish with DeepSeek
→ Read: `OPERATOR_UI_POLISH_DEEPSEEK_WORKFLOW.md`

### Security Incident
→ Report: Create issue with label `security`  
→ Audit: `docs/audit/GITHUB_API_SECURITY_INCIDENT_20260103.md`

---

## 🎯 Key Takeaway

**You now have a hardened automation framework** that allows:
- ✅ Safe GitHub API usage (via `gh` CLI or curl with proper headers)
- ✅ AI-assisted UI design with DeepSeek (while preventing wiring changes)
- ✅ Automated token leak prevention (pre-commit hook)
- ✅ Clear documentation of what's secure vs unsafe

**Everything is production-ready. Just complete the token rotation and you're done.**
