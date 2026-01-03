# VX11 Documentation Index

**Last Updated**: 2026-01-03  
**Purpose**: Single entry point for all VX11 documentation.

---

## 📚 Main Sections

### 🚀 Quick Start
- [Quick Start Guide](../status/QUICK_START_GUIDE.md) - Setup & first steps
- [Operator UI Guide](../status/QUICK_START_GUIDE.md#token-configuration) - Token config & troubleshooting

### 📖 Runbooks (Operations)
- [Process Cleanup & Troubleshooting](../runbooks/ops_process_cleanup.md) - Zombies, watchers, Docker
- [Operator Runbook](../RUNBOOK_OPERATOR_V7.md) - Full operations manual

### 🏗️ Architecture
- [Core Architecture](../ARCHITECTURE.md) - System design & components
- [Canonical Specs](./canon/) - Living specifications (see below)
- [Power Windows Spec](../POWER_WINDOWS_SPEC.md) - Policy windows

### 🔐 Security & API
- [Token Usage Guide](../TOKEN_USAGE_GUIDE.md) - Token management & flow
- [GitHub API Setup](../GITHUB_API_SETUP.md) - OAuth & webhooks

### 🧪 Testing & Validation
- [E2E Matrix](../TEST_MATRIX.md) - Test scenarios
- [Run E2E Locally](../RUN_E2E_LOCAL.md) - Commands to run tests

### 📦 Status & Audits
- [Latest Status](./status/) - Current operational state (rotated regularly)
- [Audit Reports](./audit/) - Historical audits (SCORECARD.json, latest outdir only)

---

## 📋 Directory Structure

```
docs/
├── README.md                    ← YOU ARE HERE
├── ARCHITECTURE.md              (Core design)
├── TOKEN_USAGE_GUIDE.md         (Auth patterns)
├── RUNBOOK_OPERATOR_V7.md       (Operations manual)
├── POWER_WINDOWS_SPEC.md        (Policy windows)
├── TEST_MATRIX.md               (Testing reference)
├── RUN_E2E_LOCAL.md             (Test execution)
│
├── canon/                       (Living specs)
│   ├── README.md
│   ├── CANONICAL_CORE.md
│   └── [other specs]
│
├── runbooks/                    (How-to guides)
│   ├── README.md
│   ├── ops_process_cleanup.md
│   └── [other runbooks]
│
├── status/                      (Current state - rotated)
│   ├── QUICK_START_GUIDE.md
│   ├── DOCUMENTATION_INDEX.md
│   ├── COMPLETION_SUMMARY_*
│   ├── FASE_*.md
│   └── [latest 3-5 fases]
│
└── audit/                       (Historical - archived)
    ├── SCORECARD.json           (Latest metrics)
    ├── DB_SCHEMA_v7_FINAL.json  (DB schema snapshot)
    ├── DB_MAP_v7_FINAL.md
    ├── <LATEST_OUTDIR>/
    ├── <PREV_OUTDIR>/
    ├── <PREV_OUTDIR>/
    └── archive/                 (Rotated-out evidence)
```

---

## 🔄 Document Lifecycle

### 🟢 Living Documents (Always Updated)
- `docs/canon/*.md` - Specifications that evolve with VX11
- `docs/runbooks/*.md` - Operational procedures
- `docs/status/QUICK_START_GUIDE.md` - User guide

**Rotation Policy**: Never deleted, versioned if breaking changes.

### 🟡 Status Documents (Short-Lived)
- `docs/status/COMPLETION_SUMMARY_*.md` - Phase reports
- `docs/status/FASE_*.md` - Phase documentation

**Rotation Policy**: Keep latest 3-5 phases. When new phase added, move oldest to `archive/` if >6 months old.

### 🔴 Audit Evidence (Archived After Use)
- `docs/audit/<OUTDIR>/` - Timestamped audit runs
- `docs/audit/SCORECARD.json` - Metrics snapshot (latest only)

**Rotation Policy**:
- Keep: `SCORECARD.json` (latest), `DB_SCHEMA_v7_FINAL.json`, DB_MAP files
- Archive after 1 week: Old OUTDIR runs → `docs/audit/archive/<DATE>.tar.gz`
- Cleanup: Run weekly; remove archives >3 months old

---

## 🎯 How to Use This Index

### For New Users
1. Start: [Quick Start Guide](../status/QUICK_START_GUIDE.md)
2. Troubleshoot: [Process Cleanup Runbook](../runbooks/ops_process_cleanup.md)
3. Learn: [Architecture](../ARCHITECTURE.md)

### For Operators
1. Quick reference: [Operator Runbook](../RUNBOOK_OPERATOR_V7.md)
2. Troubleshoot: [Process Cleanup Runbook](../runbooks/ops_process_cleanup.md)
3. Verify: [Test Matrix](../TEST_MATRIX.md)

### For Developers
1. Specs: [Architecture](../ARCHITECTURE.md) + [Canon](./canon/)
2. API: [Token Usage Guide](../TOKEN_USAGE_GUIDE.md)
3. Testing: [Run E2E Locally](../RUN_E2E_LOCAL.md)

### For DevOps / CI-CD
1. Automation: [GitHub API Setup](../GITHUB_API_SETUP.md)
2. Policy: [Power Windows Spec](../POWER_WINDOWS_SPEC.md)
3. Cleanup: [Process Cleanup Runbook](../runbooks/ops_process_cleanup.md)

---

## 🔗 Key Invariants (See Architecture)

1. **Single Entrypoint**: All external access via `tentaculo_link:8000`
2. **Default Policy**: `solo_madre` (read-only, no spawner)
3. **Token Security**: Never in code/logs, always env/localStorage/vault
4. **No Internal Port Exposure**: 8001 (Madre), 8002 (Switch), etc. not public
5. **Policy Windows**: Temporary elevation via `POST /madre/window/open`

---

## 📊 Status Dashboard

| Component | Status | Reference |
|-----------|--------|-----------|
| Frontend | ✅ Operational | [Quick Start](../status/QUICK_START_GUIDE.md) |
| Backend | ✅ Running | Check `/health` endpoint |
| Spawner | ✅ Ready | [Power Windows](../POWER_WINDOWS_SPEC.md) |
| Token Auth | ✅ Enforced | [Token Guide](../TOKEN_USAGE_GUIDE.md) |
| Docs | ✅ Indexed | (this file) |

**Last Verification**: 2026-01-03

---

## 📝 Maintenance Tasks

### Daily
- [ ] Monitor `/health` endpoint (alert if 5xx)
- [ ] Check logs for zombies: `ps -eo stat | grep Z`

### Weekly
- [ ] Rotate `docs/status/` (move old FASE files to archive if >1 week)
- [ ] Compress & move old audit dirs: `docs/audit/archive/`
- [ ] Run smoke tests: [Run E2E Local](../RUN_E2E_LOCAL.md)

### Monthly
- [ ] Update `SCORECARD.json`
- [ ] Clean audit archive (>3 months)
- [ ] Verify `.gitignore` (no generated files tracked)

---

## ✅ Checklist: Before Pushing

- [ ] No `docs/audit/` directories >30 days old in root (use archive/)
- [ ] `docs/status/` has ≤5 active FASE files
- [ ] `.gitignore` excludes: `outdir/`, `audit/archive/*.tar.gz`, `*.log`
- [ ] `docs/canon/` has current specs (no duplicates)
- [ ] README.md + ARCHITECTURE.md are in sync

---

**Generated**: 2026-01-03  
**For updates**: Edit this file or respective sections above.
