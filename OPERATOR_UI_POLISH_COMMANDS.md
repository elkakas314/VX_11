# 🎨 VX11 Operator UI Polish - Command Reference

## 📋 Copy-Paste Ready Commands

### 1️⃣ Setup & Preparation
```bash
cd /home/elkakas314/vx11
source tokens.env
export GITHUB_TOKEN=$GITHUB_FINEGRAND_PAT
git status
```

### 2️⃣ Create Feature Branch
```bash
git checkout main
git pull vx_11_remote main
git checkout -b operator-ui-polish
```

### 3️⃣ Complete Validation (All-in-One)
```bash
cd /home/elkakas314/vx11
bash vx11-ui-polish-validator.sh
```

Or manually:

```bash
# 3a. Run frontend validator
python3 scripts/validate-frontend.py

# 3b. Build frontend
cd operator/frontend
npm ci
npm run build

# 3c. Test health
curl -s http://localhost:8000/health | grep tentaculo_link && echo "✅ Health OK"

# 3d. Test API with token
source tokens.env
curl -s -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/status | grep status && echo "✅ API OK"

# 3e. Test SSE (quick test)
timeout 2 curl -s -N "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true" | head -1 && echo "✅ SSE OK"
```

### 4️⃣ Review Changes
```bash
cd /home/elkakas314/vx11
git status
git diff operator/frontend/
```

### 5️⃣ Commit Changes
```bash
cd /home/elkakas314/vx11
git add operator/frontend/
git commit -m "vx11(operator-ui): visual polish (layout/typography/components) — no wiring changes

Files touched:
- operator/frontend/src/components/*.tsx
- operator/frontend/src/layouts/*.tsx
- operator/frontend/src/styles/*.css

Validation:
- validate-frontend.py: ✅ PASS
- npm run build: ✅ PASS
- Health check: ✅ OK
- API status: ✅ OK

No wiring/auth/networking changes. UI-only polish."
```

### 6️⃣ Push to Remote
```bash
git push -u vx_11_remote operator-ui-polish
```

### 7️⃣ Create Pull Request (Option A: GitHub CLI)
```bash
gh auth status
gh pr create \
  --base main \
  --head operator-ui-polish \
  --title "vx11: Operator UI visual polish (no wiring changes)" \
  --body "## Overview
Frontend visual improvements: spacing, typography, components, status badges.

## Type
- [x] UI/Styling
- [ ] Feature
- [ ] Bugfix

## Changes
- Consistent spacing scale (4/8/16px)
- Typography system improvements
- Status badge component
- Layout refinements

## Validation
- ✅ validate-frontend.py PASSED
- ✅ npm run build succeeded
- ✅ /health OK
- ✅ /operator/api/status OK
- ✅ SSE stream OK

## No Changes To
- Networking/auth logic
- API routes/endpoints
- Backend code
- Secrets/tokens

UI-only polish."
```

### 7️⃣ Create Pull Request (Option B: Web UI)
```bash
# Get the link to create PR
echo "https://github.com/elkakas314/VX_11/compare/main...operator-ui-polish"
# Paste in browser and fill form
```

### 8️⃣ Monitor PR Status
```bash
# View PR details
gh pr view operator-ui-polish

# Open PR in browser
gh pr view operator-ui-polish --web

# Wait for CI/checks to pass, then merge (if authorized)
gh pr merge operator-ui-polish --auto --squash
```

---

## 🔍 Validation-Only Commands

### Quick Validator (without full build)
```bash
cd /home/elkakas314/vx11
python3 scripts/validate-frontend.py
```

### Build Only
```bash
cd /home/elkakas314/vx11/operator/frontend
npm ci && npm run build
```

### Smoke Tests Only
```bash
# Test 1: Health
curl -s http://localhost:8000/health | head -c 50

# Test 2: API (needs token)
source /home/elkakas314/vx11/tokens.env
curl -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/status | head -c 50

# Test 3: SSE
timeout 2 curl -s -N "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true"
```

---

## 🎯 DeepSeek Integration

### Step 1: Get Design Critique
Ask Copilot to invoke DeepSeek:

```
Use DeepSeek R1 to analyze the Operator frontend typography and propose a consistent system.

Files to review:
- operator/frontend/src/components/AgentCard.tsx
- operator/frontend/src/layouts/MainLayout.tsx
- operator/frontend/src/styles/theme.css

Propose:
1. Font size scale (h1, h2, body, small, mono)
2. Line-height for readability
3. Letter-spacing for titles
4. CSS custom properties for reusability
5. Responsive adjustments

Return only presentational code, no logic changes.
```

### Step 2: Design Status Badge
```
Use DeepSeek R1 to design a status badge component for VX11 agents.

States: RUNNING (blue), COMPLETED (green), FAILED (red), PENDING (gray)

Requirements:
- Consistent with Material Design 3
- Icon + label support
- Small/medium/large sizes
- Hover/focus states
- Accessible (WCAG AA)
- CSS-only animations (no JS logic)

Return component code (TSX + CSS).
```

### Step 3: Layout Grid Review
```
Use DeepSeek R1 to review this layout for spacing consistency:
[paste current MainLayout.tsx]

Suggest improvements using:
- CSS Grid with consistent gap (8px or 16px)
- Margin/padding scale: 4, 8, 16, 24, 32px
- Responsive breakpoints (mobile, tablet, desktop)
- Visual hierarchy (colors, sizes, weights)

Return only presentational changes.
```

---

## ✨ Example Workflow (Full Session)

```bash
# 1. Setup
cd /home/elkakas314/vx11
source tokens.env
git checkout -b operator-ui-polish

# 2. Edit files (using DeepSeek as design advisor)
# - Improve MainLayout spacing
# - Add StatusBadge component
# - Update typography tokens

# 3. Quick validate
python3 scripts/validate-frontend.py

# 4. If validation passes, build
cd operator/frontend && npm ci && npm run build

# 5. Test
cd ..
curl -s http://localhost:8000/health | grep tentaculo_link && echo "✅"

# 6. Review & commit
git status
git diff operator/frontend/
git add operator/frontend/
git commit -m "vx11(operator-ui): visual polish (layout/typography/components) — no wiring changes"

# 7. Push
git push -u vx_11_remote operator-ui-polish

# 8. Create PR
gh pr create --base main --head operator-ui-polish --title "vx11: Operator UI visual polish" --body "UI improvements..."

# 9. Done!
echo "✅ Submitted PR for review"
```

---

## 🚨 If Something Fails

### validate-frontend.py fails
```bash
# See what's wrong
python3 scripts/validate-frontend.py
# Fix violations (likely hardcoded port), then retry
```

### Build fails
```bash
cd operator/frontend
rm -rf node_modules package-lock.json dist
npm ci
npm run build
# If still fails: check TypeScript errors
npm run typecheck
```

### API test fails
```bash
# Check services are running
docker-compose -f docker-compose.full-test.yml ps
# Check logs
docker-compose -f docker-compose.full-test.yml logs tentaculo_link | tail -20
```

### gh pr create fails
```bash
# Check auth
gh auth status
# Re-auth if needed
gh auth login --with-token < <(echo $GITHUB_FINEGRAND_PAT)
```

---

## 📊 Checklist Before Saying "Done"

```bash
# In terminal, run all these and confirm ✅:

[ ] git status shows only operator/frontend changes
[ ] python3 scripts/validate-frontend.py returns 0
[ ] npm run build succeeds
[ ] curl http://localhost:8000/health succeeds
[ ] curl -H "X-VX11-Token: vx11-test-token" http://localhost:8000/operator/api/status succeeds
[ ] Commit message describes UI changes (no "fixed bug" or "refactored logic")
[ ] git push -u vx_11_remote operator-ui-polish succeeds
[ ] gh pr create succeeds or https://github.com/elkakas314/VX_11 has new PR
```

---

## 🎨 File Editing Tips

### Finding Components to Improve
```bash
find operator/frontend/src -name "*.tsx" -type f | grep -v node_modules | head -20
```

### Checking Current Styles
```bash
find operator/frontend/src -name "*.css" -type f | xargs ls -lh
```

### Viewing TypeScript Issues
```bash
cd operator/frontend
npm run typecheck 2>&1 | head -20
```

---

## 📚 Related Files

- **Prompt Guide**: `OPERATOR_UI_POLISH_PROMPT.md` (full role/scope/validation)
- **Validator Script**: `vx11-ui-polish-validator.sh` (all-in-one check)
- **Frontend**: `operator/frontend/` (your editing area)
- **Validate Script**: `scripts/validate-frontend.py` (hardcoded port checker)
- **GitHub API**: `docs/GITHUB_API_SETUP.md` (for gh CLI setup)

---

## 🎯 Success = Green Lights

**When you see all these, you're done:**

```
✅ Frontend validator PASSED
✅ Frontend build PASSED
✅ Health check PASSED
✅ API status check PASSED
✅ SSE stream check PASSED
✅ Git commit created
✅ Git push succeeded
✅ PR created or link shared
```

**Then celebrate! 🎉**

