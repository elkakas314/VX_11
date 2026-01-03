# 🎨 VX11 Operator UI Visual Polish Prompt
## Copy-Paste Guide for Copilot (DeepSeek + Frontend Enhancement)

**Date**: 2026-01-03  
**Version**: 1.0  
**Status**: Ready to Execute

---

## 📋 ROLE & GOAL

**ROLE**: VX11 Frontend Visual Polisher (NO-WIRING-CHANGES) + Release Engineer.

**GOAL**: Improve Operator UI visual quality (spacing/typography/components/status badges/layout) WITHOUT changing any network/auth wiring.

---

## 🛡️ HARD INVARIANTS (NON-NEGOTIABLE)

### 1️⃣ Single Entrypoint Only
- All requests via **tentaculo_link :8000**
- **NO direct calls** to internal ports (8001/8002/8003/8011)
- Validate with: `python3 scripts/validate-frontend.py`

### 2️⃣ Keep Vite Configuration Exact
- Base path: `base=/operator/ui/` (EXACT)
- Proxy behavior must remain unchanged
- Build must succeed: `npm run build`

### 3️⃣ Keep API Paths EXACT
- Valid prefixes ONLY:
  - `/operator/api/*`
  - `/operator/ui/*`
  - `/health`
  - `/v1/*`
  - `/vx11/*`
- Do NOT invent new endpoints
- Do NOT change buildApiUrl logic

### 4️⃣ Keep Auth Semantics Untouched
- **Header auth**: `X-VX11-Token` for fetch requests
- **Query param**: `token=...` for SSE/EventSource
- Do NOT modify token validation logic
- Do NOT change auth-related error handling

### 5️⃣ No Logic Refactoring
- Do NOT refactor events-client logic
- Do NOT change retry/backoff behavior
- Do NOT modify token storage behavior
- **ONLY** presentation/styling changes allowed

---

## 🧠 DEEPSEEK USAGE GUIDELINES

### When to Use DeepSeek
Use DeepSeek R1 (via Copilot environment) to:
- **Critique UI/UX** and propose presentational improvements
- Suggest **typography scale** consistency
- Design **layout grid** and spacing system
- Propose **component style** consistency
- Design "**status pill**" visuals
- Review **responsive behavior**
- Validate **accessibility** (WCAG AA compliance)

### When NOT to Use DeepSeek
- ❌ Never paste tokens or secrets
- ❌ Never add GITHUB_TOKEN, API keys, or credentials
- ❌ Never ask it to generate backend code
- ❌ Never ask it to refactor networking logic
- ❌ Never commit secrets to repo

### Example DeepSeek Prompts
```
"Analyze the current Operator frontend typography (src/components/...).
Propose a consistent scale (heading sizes, body text, small text, mono font).
Suggest CSS custom properties for reusability."

"Design a status badge component for agent states (RUNNING, COMPLETED, FAILED, PENDING).
Include colors, icons, animations, and hover states.
Return only the presentational code."

"Review operator/frontend/src/layouts/MainLayout.tsx for spacing consistency.
Suggest improvements using CSS Grid and consistent spacing tokens (4px, 8px, 16px, etc.)."
```

---

## ✅ ALLOWED SCOPE (ONLY These Changes)

### 1. Presentational Components
- File pattern: `operator/frontend/src/**/*.tsx`
- Changes allowed:
  - Layout improvements (Grid, Flex, margins, padding)
  - Typography styling (font-size, font-weight, line-height)
  - Component composition (Card, Badge, Button wrappers)
  - className/style prop adjustments
  - Responsive design (media queries)

### 2. Styling & Design Tokens
- File pattern: `operator/frontend/src/**/*.css`
- Changes allowed:
  - Add CSS custom properties (`--color-primary`, `--spacing-unit`, etc.)
  - Improve color consistency
  - Add consistent spacing scale
  - Update border-radius, shadows, transitions

### 3. Small UI Components (Presentational Only)
```tsx
// ✅ ALLOWED: New presentational component
export const StatusBadge = ({ status, label }) => (
  <span className={`badge badge-${status}`}>{label}</span>
);

// ✅ ALLOWED: Layout wrapper
export const SectionHeader = ({ title, subtitle }) => (
  <div className="section-header">
    <h2>{title}</h2>
    {subtitle && <p>{subtitle}</p>}
  </div>
);
```

### 4. Text/Labels Updates
- Update UI text for clarity (if helpful for UX)
- No logic changes
- Example: "Fetch Status" → "Stream Status"

---

## ❌ FORBIDDEN SCOPE (DO NOT CHANGE)

### 🚫 Networking & Wiring
- ❌ Do NOT modify `buildApiUrl`
- ❌ Do NOT change API route paths
- ❌ Do NOT add hardcoded hosts/ports
- ❌ Do NOT refactor fetch/EventSource logic

### 🚫 Authentication
- ❌ Do NOT change token header logic
- ❌ Do NOT modify auth validation
- ❌ Do NOT alter token query param behavior
- ❌ Do NOT change error handling for 401/403

### 🚫 Backend Integration
- ❌ Do NOT create new backend endpoints
- ❌ Do NOT refactor events-client logic
- ❌ Do NOT change retry/backoff strategies
- ❌ Do NOT modify token storage/caching

### 🚫 Secrets
- ❌ Do NOT commit tokens to repo
- ❌ Do NOT paste API keys anywhere
- ❌ Do NOT hardcode credentials

---

## 🔍 VALIDATION (MUST PASS BEFORE COMMIT)

### Step 1: Run Frontend Validator
```bash
cd /home/elkakas314/vx11
python3 scripts/validate-frontend.py
```

**Expected Output**:
```
✅ No hardcoded internal ports found
✅ Vite base path correct: /operator/ui/
✅ All API paths valid
✅ No auth logic changes detected
Exit code: 0
```

**If FAILS**: Exit code ≠ 0 → DO NOT commit. Fix violations first.

### Step 2: Build Frontend
```bash
cd /home/elkakas314/vx11/operator/frontend
npm ci  # Clean install
npm run build  # Must succeed
```

**Expected Output**:
```
vite v5.x build
✓ 123 modules transformed...
dist/ built in 2.34s
```

**If FAILS**: Build error → DO NOT commit. Fix issues first.

### Step 3: Smoke Tests

#### Test 1: Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","module":"tentaculo_link","version":"7.0"}
```

#### Test 2: API Status (401 without token)
```bash
curl http://localhost:8000/operator/api/status
# Expected: HTTP 401 {"detail":"auth_required"}
```

#### Test 3: API Status (200 with token)
```bash
source tokens.env
curl -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/status
# Expected: HTTP 200 with JSON response
```

#### Test 4: SSE Stream
```bash
curl -N "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true" &
sleep 2 && kill %1
# Expected: Streaming JSON events (no errors)
```

---

## 🚀 WORKFLOW: Complete Git + GitHub CLI

### Step 0: Prerequisites
```bash
cd /home/elkakas314/vx11
source tokens.env
export GITHUB_TOKEN=$GITHUB_FINEGRAND_PAT
```

### Step 1: Create Feature Branch
```bash
git checkout main
git pull vx_11_remote main
git checkout -b operator-ui-polish
```

### Step 2: Make UI Changes
```bash
# Edit your files:
# - operator/frontend/src/components/...
# - operator/frontend/src/layouts/...
# - operator/frontend/src/styles/...
# (Use DeepSeek as design advisor)
```

### Step 3: Validation (MANDATORY)
```bash
# 1. Run frontend validator
python3 scripts/validate-frontend.py
# Must exit with code 0

# 2. Build frontend
cd operator/frontend
npm ci
npm run build
# Must succeed

# 3. Quick smoke tests
cd /home/elkakas314/vx11
curl -s http://localhost:8000/health | grep -q "tentaculo_link" && echo "✅ Health OK"
source tokens.env
curl -s -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/status | grep -q "status" && echo "✅ API OK"
```

### Step 4: Git Commit
```bash
cd /home/elkakas314/vx11

# Review changes
git status
git diff operator/frontend

# Stage changes
git add operator/frontend/

# Commit with required message format
git commit -m "vx11(operator-ui): visual polish (layout/typography/components) — no wiring changes

Changes:
- Improved spacing consistency using 4px/8px/16px scale
- Typography system with reusable font sizes
- Status badge component with consistent styling
- Layout improvements in MainLayout and sections
- Responsive design refinements

Files touched:
- operator/frontend/src/components/*.tsx
- operator/frontend/src/layouts/*.tsx
- operator/frontend/src/styles/*.css

Validation:
- validate-frontend.py: ✅ PASS
- npm run build: ✅ PASS
- Health check: ✅ PASS
- API status: ✅ PASS
- SSE stream: ✅ PASS

No wiring/auth/networking changes. UI-only polish."
```

### Step 5: Push to Remote
```bash
git push -u vx_11_remote operator-ui-polish
```

**Expected Output**:
```
remote: Resolving deltas: 100% (N/N), done.
To https://github.com/elkakas314/VX_11.git
 * [new branch]      operator-ui-polish -> operator-ui-polish
Branch 'operator-ui-polish' set up to track 'vx_11_remote/operator-ui-polish'.
```

### Step 6: Create Pull Request (Optional but Recommended)
```bash
# Check gh CLI is authenticated
gh auth status
# Output: Logged in to github.com as elkakas314

# Create PR
gh pr create \
  --base main \
  --head operator-ui-polish \
  --title "vx11: Operator UI visual polish (no wiring changes)" \
  --body "## Overview
Frontend visual enhancements: spacing, typography, components, status badges.

## Type
- [x] UI/Styling
- [ ] Feature
- [ ] Bugfix

## Changes
- Consistent spacing scale (4/8/16px)
- Typography system improvements
- Status badge component
- Layout refinements
- Responsive design

## Validation
- ✅ validate-frontend.py PASSED
- ✅ npm run build succeeded
- ✅ Health check OK
- ✅ API auth OK
- ✅ SSE stream OK

## Notes
- No networking changes
- No auth logic changes
- No backend work
- UI-only polish

Closes: (if applicable)"
```

**Expected Output**:
```
Creating pull request for operator-ui-polish into main in elkakas314/VX_11

remote: Create a pull request for 'operator-ui-polish' on GitHub by visiting:
remote: https://github.com/elkakas314/VX_11/pull/123

https://github.com/elkakas314/VX_11/pull/123
```

### Step 7: Monitor CI/Checks (on GitHub)
1. Visit PR link
2. Wait for GitHub Actions to run
3. Verify all checks pass (build, tests, linting)
4. Request review or merge if authorized

---

## 🎯 COPILOT CHECKLIST (Before Saying "Done")

- [ ] **All changes are presentational** (spacing/typography/components only)
- [ ] **No hardcoded ports** in code (validate-frontend.py passed)
- [ ] **No auth logic modified** (still using X-VX11-Token header)
- [ ] **No API paths changed** (all under /operator/api or /operator/ui)
- [ ] **No secrets committed** (no tokens, API keys in files)
- [ ] **Build succeeds** (`npm run build` exit code 0)
- [ ] **Smoke tests pass** (health, API status, SSE)
- [ ] **validate-frontend.py passes** (exit code 0)
- [ ] **Commit message is clear** (describes UI changes, lists files, includes validation)
- [ ] **PR is created** (or commit is pushed with good message)

---

## 📚 Reference: File Structure

```
operator/
├── frontend/
│   ├── src/
│   │   ├── components/       ← ✅ Edit here (presentational)
│   │   ├── layouts/          ← ✅ Edit here (layout, spacing)
│   │   ├── hooks/            ← ⚠️  Only styling hooks, never auth
│   │   ├── services/         ← ❌ DO NOT TOUCH (auth, API, wiring)
│   │   ├── styles/           ← ✅ Edit here (CSS tokens, themes)
│   │   └── utils/            ← ❌ DO NOT TOUCH (buildApiUrl, auth)
│   ├── vite.config.ts        ← ✅ Review only (base path must stay /operator/ui/)
│   ├── package.json
│   └── tsconfig.json
├── backend/                  ← ❌ DO NOT TOUCH
└── docker-compose.yml        ← ❌ DO NOT TOUCH
```

---

## 🔧 Quick Command Reference

```bash
# Load tokens
source tokens.env
export GITHUB_TOKEN=$GITHUB_FINEGRAND_PAT

# Create & switch branch
git checkout -b operator-ui-polish

# Validate
python3 scripts/validate-frontend.py
(cd operator/frontend && npm ci && npm run build)

# Commit
git add operator/frontend/
git commit -m "vx11(operator-ui): visual polish ..."

# Push
git push -u vx_11_remote operator-ui-polish

# Create PR
gh pr create --base main --head operator-ui-polish --title "..." --body "..."

# Monitor PR
gh pr view operator-ui-polish --web  # Opens in browser
```

---

## 🚨 Common Mistakes to AVOID

| Mistake | ❌ DON'T | ✅ DO |
|---------|---------|-----|
| **Ports** | `fetch("http://localhost:8001/...")` | `fetch("/operator/api/...")` |
| **Auth** | Modify token validation | Use token in header/query only |
| **Secrets** | Commit `GITHUB_TOKEN` to code | Use environment variables |
| **Endpoints** | Invent `/custom/endpoint` | Use only documented API paths |
| **Refactor** | Change events-client retry logic | Change only styling/layout |
| **Vite** | Change `base=/` | Keep `base=/operator/ui/` |

---

## 📞 Troubleshooting

### validate-frontend.py FAILS
```bash
# Check output for violations
python3 scripts/validate-frontend.py

# Common issue: Hardcoded port found
# Fix: Replace `localhost:8001` with `/operator/api`
```

### npm run build FAILS
```bash
# Clear cache and reinstall
cd operator/frontend
rm -rf node_modules package-lock.json
npm ci
npm run build
```

### API returns 401
```bash
# Check token is set
echo $GITHUB_FINEGRAND_PAT
# Must be non-empty

# Test with curl
source tokens.env
curl -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/status
```

### gh pr create fails
```bash
# Check authentication
gh auth status
# If not logged in:
gh auth login --with-token < <(echo $GITHUB_FINEGRAND_PAT)
```

---

## ✨ Success Criteria

✅ **Task Complete When:**
1. Commit is pushed to vx_11_remote/operator-ui-polish
2. PR is created (or commit has excellent message)
3. All validation scripts pass (exit code 0)
4. UI improvements are visible and professional
5. No wiring/auth/networking changes were made
6. validate-frontend.py confirms no hardcoded ports

---

## 📝 Commit Message Template

```
vx11(operator-ui): visual polish (layout/typography/components) — no wiring changes

## Summary
Brief description of UI improvements (1-2 lines).

## Changes Made
- Change 1 (e.g., "Improved spacing consistency")
- Change 2 (e.g., "Added status badge component")
- Change 3 (e.g., "Typography system improvements")

## Files Modified
- operator/frontend/src/components/SomeComponent.tsx
- operator/frontend/src/layouts/MainLayout.tsx
- operator/frontend/src/styles/tokens.css

## Validation Results
- validate-frontend.py: ✅ PASS
- npm run build: ✅ PASS
- curl /health: ✅ OK
- curl /operator/api/status: ✅ OK (with token)
- SSE stream: ✅ OK

## No Changes To
- ❌ Networking/auth logic
- ❌ API routes/endpoints
- ❌ Backend code
- ❌ Secrets/tokens
```

---

**Ready to polish the Operator UI! 🎨**

Use this guide as your checkpoint. Copilot will validate at each step.
