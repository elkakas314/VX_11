# VX11 Cleanup Framework - Verification Checklist

**Date**: 2026-01-03  
**Status**: ✅ READY TO VERIFY

Use this checklist to verify all deliverables are in place.

---

## Files Verification

### Documentation

- [ ] `docs/README.md` - Centralized entry point (100+ LOC)
  ```bash
  test -f docs/README.md && wc -l docs/README.md
  ```

- [ ] `docs/runbooks/ops_process_cleanup.md` - Runbook (250+ LOC)
  ```bash
  test -f docs/runbooks/ops_process_cleanup.md && wc -l docs/runbooks/ops_process_cleanup.md
  ```

- [ ] `docs/canon/SWITCH_HERMES_RUNTIME.md` - Runtime spec (580+ LOC)
  ```bash
  test -f docs/canon/SWITCH_HERMES_RUNTIME.md && wc -l docs/canon/SWITCH_HERMES_RUNTIME.md
  ```

- [ ] `docs/status/FASE_4_E2E_HIJAS_TEST_REAL.md` - E2E tests (390+ LOC)
  ```bash
  test -f docs/status/FASE_4_E2E_HIJAS_TEST_REAL.md && wc -l docs/status/FASE_4_E2E_HIJAS_TEST_REAL.md
  ```

- [ ] `docs/status/FASE_5_6_DEEPSEEK_REASONING.md` - Design decisions (80+ LOC)
  ```bash
  test -f docs/status/FASE_5_6_DEEPSEEK_REASONING.md && wc -l docs/status/FASE_5_6_DEEPSEEK_REASONING.md
  ```

- [ ] `docs/status/COMPLETION_SUMMARY_CLEANUP_FRAMEWORK_FASE_7.md` - Summary (280+ LOC)
  ```bash
  test -f docs/status/COMPLETION_SUMMARY_CLEANUP_FRAMEWORK_FASE_7.md && wc -l docs/status/COMPLETION_SUMMARY_CLEANUP_FRAMEWORK_FASE_7.md
  ```

### Automation Scripts

- [ ] `scripts/vx11_rotate_audits.sh` - Executable (120 LOC)
  ```bash
  test -f scripts/vx11_rotate_audits.sh && test -x scripts/vx11_rotate_audits.sh && echo "✓ Executable"
  ```

- [ ] `Makefile` - Unified commands (139 LOC)
  ```bash
  test -f Makefile && wc -l Makefile
  ```

### GitHub Workflows

- [ ] `.github/workflows/vx11-smoke-tests.yml` - Smoke tests (125 LOC)
  ```bash
  test -f .github/workflows/vx11-smoke-tests.yml && wc -l .github/workflows/vx11-smoke-tests.yml
  ```

- [ ] `.github/workflows/vx11-hygiene.yml` - Hygiene checks (305 LOC)
  ```bash
  test -f .github/workflows/vx11-hygiene.yml && wc -l .github/workflows/vx11-hygiene.yml
  ```

---

## Git Commits Verification

All 6 commits should be present in `vx_11_remote/main`:

```bash
git log --oneline -6
```

Expected output:
```
d298356 vx11: cleanup-framework-summary: executive summary
1dd141b vx11: fase-7-completion: cleanup framework 7-fase report
346cf43 vx11: fase-4-6: e2e-tests + hermes-spec + github-ci-automation
13d2ac4 vx11: fase-3-makefile: unified operations commands
c42bf15 vx11: fase-2-audit-rotation: automated archival script
57b2fa2 vx11: fase-1-runbook: process cleanup procedures + doc structure
```

Verify all pushed:
```bash
git log --oneline vx_11_remote/main -6
```

---

## Functionality Verification

### 1. Makefile Works

```bash
make help          # Should show all targets
make up-core       # Should start solo_madre
make status        # Should show current status
make smoke         # Should run health checks
```

### 2. Audit Rotation Script Works

```bash
bash scripts/vx11_rotate_audits.sh --dry-run    # Should show plan without changes
bash scripts/vx11_rotate_audits.sh --help       # Should show options
```

### 3. Documentation is Readable

```bash
cat docs/README.md | head -20        # Should show entry point
grep -i "makefile\|runbook" docs/README.md    # Should find references
```

### 4. GitHub Workflows are Valid YAML

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/vx11-smoke-tests.yml'))" && echo "✓ Valid YAML"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/vx11-hygiene.yml'))" && echo "✓ Valid YAML"
```

---

## Invariants Verification

### 1. Single Entrypoint (:8000)

```bash
grep -r "8002\|8003\|8008\|8009" docs/canon/ | grep -v "never\|internal" && echo "⚠️ Direct port references found" || echo "✓ No direct internal port calls"
```

### 2. solo_madre Default

```bash
grep -i "solo_madre\|default" docs/README.md && echo "✓ solo_madre documented"
```

### 3. Token Security

```bash
grep -i "X-VX11-Token\|token.*required" docs/canon/*.md && echo "✓ Token enforcement documented"
```

### 4. DB Integrity

```bash
grep -i "PRAGMA\|integrity_check" docs/status/FASE_4_E2E_HIJAS_TEST_REAL.md && echo "✓ DB checks included"
```

### 5. No Breaking Changes

```bash
git log --oneline --name-status 57b2fa2..d298356 | grep "^D" && echo "⚠️ Files deleted" || echo "✓ No deletions (100% additive)"
```

---

## Summary Verification

Total files: Should be 10+
```bash
find docs/runbooks docs/canon docs/status -name "*.md" -newer /tmp 2>/dev/null | wc -l
```

Total LOC: Should be 2,000+
```bash
wc -l docs/runbooks/ops_process_cleanup.md docs/README.md docs/canon/SWITCH_HERMES_RUNTIME.md docs/status/FASE_4_E2E_HIJAS_TEST_REAL.md scripts/vx11_rotate_audits.sh Makefile .github/workflows/vx11-*.yml | tail -1
```

---

## Final Checks

- [ ] All files present and readable
- [ ] All commits pushed to vx_11_remote/main
- [ ] Makefile targets work (at least `make help`)
- [ ] No hardcoded secrets (pre-commit passed)
- [ ] Invariants verified (all 5 checks pass)
- [ ] Documentation is comprehensive (500+ LOC)
- [ ] GitHub workflows are valid YAML
- [ ] Git status is clean

---

## Sign-Off

**Verification Date**: _______________  
**Verified By**: _______________  
**Status**: [ ] PASS / [ ] FAIL

If all checks pass: Framework is ready for production.

---

**Questions?** See `docs/README.md` or contact: Copilot (VX11 Agent)
