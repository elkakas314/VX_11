# VX11 Operator UI Polish with DeepSeek (Safe Workflow)

## ROLE: UI Polisher (Zero Wiring Changes)

You are enhancing the Operator frontend **presentation layer ONLY**. 
- ✅ Typography, spacing, layout, component visuals, responsive design
- ❌ Backend wiring, API routes, auth logic, networking, events

---

## HARD INVARIANTS (NEVER CHANGE)

- **Single Entrypoint**: All requests via `tentaculo_link:8000` ONLY
- **Vite Base Path**: `/operator/ui/` (exact, cannot change)
- **Auth Pattern**: `X-VX11-Token` header (preserved as-is)
- **No Hardcoded Ports**: If you see `8001`/`8002`/`8011` anywhere → DELETE it
- **No Secrets in Code**: No tokens, keys, credentials anywhere

---

## ALLOWED SCOPE (What You CAN Touch)

```
operator/frontend/src/
  ├── components/**         ✅ Presentation only
  ├── layouts/**            ✅ Visual structure
  ├── styles/**             ✅ CSS / design tokens / themes
  ├── App.tsx               ✅ JSX/TSX markup (no logic changes)
  └── index.css             ✅ Global styles
```

---

## FORBIDDEN SCOPE (Never Touch These)

```
operator/frontend/src/
  ├── services/**           ❌ API clients, auth handlers
  ├── lib/events-client.ts  ❌ EventSource/SSE wiring
  ├── hooks/**              ❌ Data fetching logic
  └── utils/auth*           ❌ Token validation logic

Backend (ANY):
  ├── tentaculo_link/       ❌ API gateway
  ├── madre/                ❌ System controller
  ├── switch/               ❌ Routing logic
  ├── spawner/              ❌ Task execution
  └── docker-compose.*      ❌ Service orchestration
```

---

## WORKFLOW (STEP-BY-STEP)

### 1. Create Branch

```bash
git checkout -b operator-ui-polish-deepseek
```

### 2. Make Visual Changes (Using DeepSeek for Design Advice)

**Prompt DeepSeek with**:

```
You are a UI/UX expert for a technical dashboard (VX11 Operator).
The interface manages distributed services and API endpoints.

Current state: Components use basic styling, inconsistent spacing, unclear hierarchy.

Design a plan for:
1. Typography scale (headings, body, labels) based on Material Design 3
2. Spacing system (4px grid, consistent gaps, padding)
3. Status badge component (healthy/unhealthy/warning states)
4. Responsive grid for service cards
5. Color tokens for light/dark modes

Output: Concrete CSS changes + component examples (TSX/JSX).
Constraints:
- NO backend logic changes
- Keep EventSource/API client calls unchanged
- NO new libraries (use what's already in package.json)
- Target modern CSS (CSS Grid, Flexbox, CSS Variables)
```

**Apply DeepSeek's output to**:
- `operator/frontend/src/styles/` (design tokens)
- `operator/frontend/src/components/` (visual markup)
- `operator/frontend/src/layouts/` (page structure)

### 3. Validate (Strict Checks)

```bash
# [1/3] No hardcoded ports
python3 scripts/validate-frontend.py --verbose

# Output should show: ✅ No hardcoded ports (8001-8011)

# [2/3] Build succeeds
cd operator/frontend
npm ci
npm run build
cd ../..

# Output: build/ folder created, no TypeScript errors

# [3/3] Service health checks pass
bash vx11-ui-polish-validator.sh

# Output: All 5 checks pass
#   [1/5] Validation script: PASS
#   [2/5] Build: PASS
#   [3/5] /health: PASS
#   [4/3] /operator/api/status: PASS
#   [5/5] EventSource stream: PASS
```

### 4. Safety Verification (Before Commit)

```bash
# No hardcoded ports anywhere
grep -RInE "localhost:800[0-9]|:800[0-9]|process.env.PORT" operator/frontend/src operator/frontend/dist 2>/dev/null && echo "❌ FAIL: Found hardcoded port" && exit 1 || echo "✅ PASS: No hardcoded ports"

# No secrets/tokens
grep -RInE "ghp_|github_pat_|sk-|sk_live_" docs operator/frontend/src 2>/dev/null && echo "❌ FAIL: Found secret pattern" && exit 1 || echo "✅ PASS: No secrets"

# No backend changes
git diff --name-only | grep -E "tentaculo_link|madre/|switch/|spawner/" && echo "❌ FAIL: Backend files changed" && exit 1 || echo "✅ PASS: Backend untouched"
```

### 5. Single Clean Commit

```bash
git add operator/frontend/src

git commit -m "vx11(operator-ui): visual polish — typography, spacing, components

CHANGES:
- Typography scale: consistent h1-h6, body sizes per Material Design 3
- Spacing system: 4px grid, consistent padding/margin
- Component updates: status badges, service cards, layout grids
- Responsive design: mobile/tablet/desktop breakpoints
- Color tokens: light/dark mode ready

VALIDATION:
✅ scripts/validate-frontend.py PASS
✅ npm build PASS
✅ vx11-ui-polish-validator.sh PASS
✅ No hardcoded ports, no secrets, no backend changes

INVARIANTS PRESERVED:
✅ Vite base: /operator/ui/
✅ Auth: X-VX11-Token header
✅ API: /operator/api/* unchanged
✅ EventSource: events?token=... unchanged
✅ Single entrypoint: tentaculo_link:8000"
```

### 6. Push & Create PR

```bash
git push -u vx_11_remote operator-ui-polish-deepseek

gh pr create \
  --base main \
  --head operator-ui-polish-deepseek \
  --title "Operator UI polish: typography, spacing, components" \
  --body "**Type**: UI-only visual enhancements

**What Changed**:
- Typography scale (Material Design 3)
- Spacing system (4px grid)
- Component styling (badges, cards, grids)
- Responsive design

**What Didn't Change**:
✅ No API/auth/wiring changes
✅ Entrypoint: tentaculo_link:8000
✅ Base path: /operator/ui/
✅ No hardcoded ports
✅ No secrets in code

**Validation**:
✅ validate-frontend.py
✅ npm build
✅ vx11-ui-polish-validator.sh
✅ All checks passed

**DeepSeek Used For**: UI/UX design recommendations (typography, spacing, components)"
```

---

## DEEPSEEK PROMPTS (Copy-Paste Ready)

### Prompt 1: Design System

```
You are a design system expert for a technical dashboard.
Based on Material Design 3, design a complete typography and spacing system for VX11 Operator UI.

Output format:
1. CSS custom properties (variables) for typography
2. CSS custom properties for spacing/breakpoints
3. Component examples (status badges, cards)
4. Light/dark mode support

Constraints:
- Use modern CSS (variables, grid, flexbox)
- No external libraries (Tailwind, Bootstrap)
- Must work with existing React setup
- Output should be copy-pasteable into operator/frontend/src/styles/
```

### Prompt 2: Component Polish

```
I have a React component that displays API status (healthy/unhealthy/warning).
Current HTML:
<div class="status-badge">
  <span>{status}</span>
</div>

Make it visually polished with:
1. Appropriate color per status
2. Icon representation
3. Animation (optional, smooth)
4. Accessible (aria-labels, roles)
5. Responsive sizing

Output: Complete TSX component + CSS, ready to integrate.
```

### Prompt 3: Responsive Layout

```
Design a responsive grid layout for service cards in VX11 Operator.
Each card shows:
- Service name
- Status (healthy/warning/error)
- Uptime %
- Last deployment

Requirements:
- Mobile (1 column)
- Tablet (2 columns)
- Desktop (3-4 columns)
- Touch-friendly spacing
- Accessibility (keyboard nav, labels)

Output: React component + CSS Grid, ready to use.
```

---

## VALIDATION COMMANDS (Copy-Paste)

```bash
# Test typography changes
npm run build  # Must succeed with no TypeScript errors

# Check no ports are hardcoded
grep -r "800[0-9]" operator/frontend/src && exit 1 || echo "PASS"

# Verify EventSource still works (no changes to events client)
curl -H "X-VX11-Token: vx11-test-token" \
  "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true" \
  --connect-timeout 2 | head -1

# Verify API status endpoint
curl -H "X-VX11-Token: vx11-test-token" \
  "http://localhost:8000/operator/api/status" | jq .

# Run full validation
bash vx11-ui-polish-validator.sh
```

---

## RED FLAGS (If You See These → STOP & FIX)

- ❌ Changes to `tentaculo_link/`, `madre/`, `switch/`, `spawner/`
- ❌ New API route definitions
- ❌ Token/secret values in code/docs
- ❌ Import of `EventSource` client (should already exist)
- ❌ Changes to `.env` / environment variables
- ❌ New npm packages (use existing ones only)
- ❌ Hardcoded ports like `8001`, `8011`
- ❌ Modifications to git hooks or workflow files

---

## SUCCESS CRITERIA

- ✅ Visual improvements are clear (typography, spacing, components)
- ✅ All validation scripts pass
- ✅ No backend/wiring changes
- ✅ No secrets in code
- ✅ PR description explains only UI changes
- ✅ Single clean commit
- ✅ Ready for human review + merge

---

## REFERENCES

- Material Design 3: https://m3.material.io/
- CSS Grid: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout
- Responsive Design: https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design
- React Best Practices: https://react.dev/learn
