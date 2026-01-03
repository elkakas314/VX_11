# VX11 Security & Automation Cheatsheet

## 🔐 Token Management (DO THIS FIRST)

```bash
# 1. Rotate GitHub tokens
https://github.com/settings/tokens  # Revoke old
https://github.com/settings/tokens/new  # Create new

# 2. Update environment
nano tokens.env
# GITHUB_FINEGRAND_PAT=github_pat_<new-token>
# DEEPSEEK_API_KEY=sk_live_<new-key>  (optional)

# 3. Reload
source tokens.env
gh auth status  # Verify
```

---

## 🛠️ GitHub API (Safe Patterns)

### Using `gh` CLI (Recommended - No Token Exposure)

```bash
# Repos
gh api --paginate /user/repos --jq '.[] | .name'

# Issues
gh api /repos/elkakas314/VX_11/issues -f state=open --jq '.[] | {number, title}'

# Create issue
gh api /repos/elkakas314/VX_11/issues -X POST \
  -f title="Title" -f body="Description"

# Pull requests
gh pr list
gh pr create --title "Title" --body "Body" --base main

# Rate limit check
gh api rate_limit --jq '.rate_limit | {limit, remaining, reset}'
```

### Using `curl` + Headers (For Scripts)

```bash
source tokens.env

AUTH="Authorization: Bearer ${GITHUB_FINEGRAND_PAT}"
ACCEPT="Accept: application/vnd.github+json"
VER="X-GitHub-Api-Version: 2022-11-28"

# Get user
curl -sS -H "$AUTH" -H "$ACCEPT" -H "$VER" \
  https://api.github.com/user | jq .login

# Create issue with jq (safe)
ISSUE=$(jq -n --arg t "Title" --arg b "Body" \
  '{title: $t, body: $b}')
curl -sS -X POST -H "$AUTH" -H "$ACCEPT" -H "$VER" \
  -d "$ISSUE" \
  https://api.github.com/repos/elkakas314/VX_11/issues | jq '{number, title}'
```

---

## ✨ DeepSeek for UI Design (Safe Workflow)

```bash
# 1. Create branch
git checkout -b operator-ui-polish-deepseek

# 2. Edit ONLY operator/frontend/src/
#    (components/, layouts/, styles/)

# 3. Get design from DeepSeek using prompts in:
#    cat OPERATOR_UI_POLISH_DEEPSEEK_WORKFLOW.md

# 4. Validate (ALL must pass)
python3 scripts/validate-frontend.py --verbose
cd operator/frontend && npm ci && npm run build && cd ../..
bash vx11-ui-polish-validator.sh

# 5. Commit (single, clean)
git commit -m "vx11(operator-ui): visual polish — typography/spacing/components"

# 6. Create PR
gh pr create --base main --head operator-ui-polish-deepseek \
  --title "Operator UI polish" \
  --body "UI-only: typography/spacing. No wiring changes. All validation PASS."
```

---

## 🚫 Anti-Patterns (NEVER DO THIS)

```bash
# ❌ Token in URL
# git clone https://<token>@github.com/...
# ✅ Instead
git clone git@github.com:elkakas314/VX_11.git
# or
gh repo clone elkakas314/VX_11

# ❌ Token in script
export TOKEN="ghp_xxx..."
# ✅ Instead
source tokens.env
# Use ${GITHUB_FINEGRAND_PAT}

# ❌ Token in docs
GITHUB_TOKEN=github_pat_11BN5ARTA0...
# ✅ Instead
GITHUB_TOKEN=${GITHUB_FINEGRAND_PAT}

# ❌ Classic token with full scope
# ✅ Instead
# Fine-grained token, repo VX_11 only, minimal scopes

# ❌ Never rotate tokens
# ✅ Rotate quarterly (3-month calendar reminder)
```

---

## 🔒 Pre-Commit Hook (Auto-Runs on `git commit`)

Automatically blocks:
- `ghp_*` (GitHub classic tokens)
- `github_pat_*` (GitHub fine-grained tokens)
- `sk_*`, `sk_live_*` (DeepSeek/OpenAI keys)
- `*.pem`, `*.key`, `id_rsa` (Private keys)
- Warns if `tokens.env` staged (should not commit)

**If blocked**:
```bash
# Fix the file, then:
git reset HEAD <file>  # Unstage
# (edit to remove secret)
git add <file>  # Re-stage
git commit -m "..."  # Retry
```

---

## 📋 Security Checklist (Before Committing)

- [ ] `tokens.env` is in `.gitignore` ✓
- [ ] Token loaded from `tokens.env` (not hardcoded)
- [ ] Never echo full token: `echo "${VAR:0:20}..."`
- [ ] Pre-commit hook passed (automatic)
- [ ] No token patterns in diff:
  ```bash
  git diff --cached | grep -E "ghp_|github_pat_|sk_" || echo "CLEAN"
  ```
- [ ] Documentation uses placeholders only
- [ ] No backend/wiring changes in UI polish
- [ ] All validations pass (python script, build, curl checks)

---

## 📚 Documentation Map

| Need | File |
|------|------|
| Token rotation (3 steps) | `GITHUB_SECURITY_FIX_COPY_PASTE.md` |
| API reference | `docs/GITHUB_API_SETUP.md` |
| UI polish workflow | `OPERATOR_UI_POLISH_DEEPSEEK_WORKFLOW.md` |
| Full overview | `GITHUB_DEEPSEEK_AUTOMATION_FRAMEWORK.md` |
| Incident details | `docs/audit/GITHUB_API_SECURITY_INCIDENT_20260103.md` |
| This cheatsheet | `GITHUB_SECURITY_CHEATSHEET.md` |

---

## 🚨 Emergency: Token Exposed

```bash
# 1. REVOKE immediately
# https://github.com/settings/tokens → Delete

# 2. Generate new token
# https://github.com/settings/tokens/new

# 3. Update tokens.env
nano tokens.env
source tokens.env

# 4. Notify team
# "Rotated GitHub token. Old token revoked."

# 5. For CI/CD: Update secrets
# GitHub Settings → Secrets and variables → Update GITHUB_TOKEN
```

---

## ✅ Validation Commands (Copy-Paste)

```bash
# All-in-one validation
python3 scripts/validate-frontend.py --verbose && \
  cd operator/frontend && npm run build && cd ../.. && \
  bash vx11-ui-polish-validator.sh && \
  echo "✅ ALL VALIDATION PASSED"

# No tokens in docs
grep -E "github_pat_|ghp_" docs/GITHUB_API_SETUP.md || echo "✅ CLEAN"

# Pre-commit hook exists
test -x .git/hooks/pre-commit && echo "✅ HOOK EXISTS"

# No hardcoded ports
grep -r "800[0-9]" operator/frontend/src || echo "✅ NO PORTS"

# Health check
curl -H "X-VX11-Token: vx11-test-token" http://localhost:8000/health | jq .

# Rate limit
gh api rate_limit --jq '.rate_limit'
```

---

## 🎯 Common Tasks

### Create GitHub Issue
```bash
gh api /repos/elkakas314/VX_11/issues -X POST \
  -f title="Bug: ..." -f body="..." -f labels=bug
```

### List PRs
```bash
gh pr list --state open
```

### Comment on PR
```bash
gh pr comment 42 --body "Looks good!"
```

### Merge PR
```bash
gh pr merge 42 --merge
```

### Check rate limit
```bash
gh api rate_limit --jq '.rate_limit | {limit, remaining}'
```

### Clone without tokens
```bash
gh repo clone elkakas314/VX_11
```

---

## 📞 Support

| Issue | Action |
|-------|--------|
| Token rotation | Read: `GITHUB_SECURITY_FIX_COPY_PASTE.md` |
| Pre-commit blocked | See: Emergency section above |
| UI validation fails | Check: `docs/GITHUB_API_SETUP.md` anti-patterns |
| DeepSeek design | Use: `OPERATOR_UI_POLISH_DEEPSEEK_WORKFLOW.md` |
| API error | Check rate limit + docs/GITHUB_API_SETUP.md |

---

## 🔑 Key Takeaways

1. **Load tokens from env** (`source tokens.env`), never hardcode
2. **Use `gh api`** for most operations (safer)
3. **Validate before commit** (script + build + tests)
4. **Pre-commit hook blocks secrets** (automatic)
5. **Rotate tokens quarterly** (3-month reminder)
6. **For UI polish**: Use DeepSeek prompts from workflow guide
7. **Hard invariants**: Single entrypoint, auth preserved, no wiring

---

**Status**: Production Ready | Last Updated: 2026-01-03 | See GITHUB_DEEPSEEK_AUTOMATION_FRAMEWORK.md for complete overview
