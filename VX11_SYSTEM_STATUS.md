# VX11 System Status & Synchronization State

**Last Updated:** 2025-12-12 16:45 UTC

---

## Current State Summary

### Repository Synchronization
- **Local Repo:** `/home/elkakas314/vx11`
- **Remote:** `vx_11_remote` → `https://github.com/elkakas314/VX_11.git`
- **Current Branch:** `feature/ui/operator-advanced`
- **Sync Status:** ✅ PERFECT (0 commits ahead/behind)
- **Last Sync:** 2025-12-12 15:19:50 UTC (commit d14c2e8)

### Pending Changes (Local Only)
```
M  .github/copilot-instructions.md       (Sección B actualizada)
?? docs/AUTOSYNC_SYSTEMD_DESIGN.md       (Diseño systemd — referencia)
?? scripts/systemd/vx11-autosync.service (Diseño systemd — NO INSTALADO)
?? scripts/systemd/vx11-autosync.timer   (Diseño systemd — NO INSTALADO)
?? switch/ga_population.json             (Pre-existente sin rastrear)
```

### GitHub CLI & Authentication
- **CLI Version:** 2.4.0+dfsg1
- **Authenticated User:** elkakas314
- **Token Type:** Fine-Grained PAT (`github_pat_11BN5...`)
- **Status:** ✅ ACTIVE & WORKING

### Autosync Script Status
- **Script Location:** `/home/elkakas314/vx11/tools/autosync.sh`
- **Size:** 1560 bytes
- **Permissions:** `-rwxrwxr-x` (executable)
- **Last Execution:** 2025-12-12 15:19:50 UTC
- **Execution Mode:** ❌ MANUAL (no cron, timer, or background process)

### Systemd Autosync Design (NOT INSTALLED)
- **Service Template:** `/home/elkakas314/vx11/scripts/systemd/vx11-autosync.service`
- **Timer Template:** `/home/elkakas314/vx11/scripts/systemd/vx11-autosync.timer`
- **Design Doc:** `/home/elkakas314/vx11/docs/AUTOSYNC_SYSTEMD_DESIGN.md`
- **Interval:** 5 minutes (if/when installed)
- **Randomization:** ±30 seconds
- **Lock Mechanism:** `.autosync.lock`
- **Status:** ✅ DESIGNED, ❌ NOT INSTALLED

---

## Key Instructions (IMMUTABLE)

See `.github/copilot-instructions.md` **SECCIÓN A** for canonical rules:

1. **Never break synchronization** — Local and remote must always align
2. **Use autosync.sh only** — Official commit path
3. **Docker governs** — systemd is legacy
4. **Tentaculo_link is gateway** — Not gateway.deprecated
5. **No file duplication** — One source of truth
6. **Respect VX11 structure** — 10 modules in place
7. **Immutable section** — A cannot change; B is editable per session
8. **Read-only tools only** — No destructive terminal commands

---

## Operational Notes (Per-Session)

### For Next Chat Sessions

1. **Update Section B** in `.github/copilot-instructions.md` with:
   - Current git status (ahead/behind)
   - Any new pending changes
   - Detected issues/failures
   - Session-specific notes

2. **Check before modifying:**
   - `git status --porcelain`
   - `git rev-list --left-right --count HEAD...@{u}`
   - `.github/copilot-instructions.md` integrity (Sección A must be untouched)

3. **Never:**
   - Commit manually (use autosync.sh)
   - Install systemd artifacts without authorization
   - Modify Section A of instructions
   - Touch tokens.env (read-only only)
   - Break the 10-module structure

---

## Docker Module Status

As of 2025-12-12 15:25 UTC:

| Module | Port | Docker Status | Issue |
|--------|------|---------------|-------|
| tentaculo-link | 8000 | ✅ Healthy | — |
| madre | 8001 | ✅ Healthy | — |
| switch | 8002 | ✅ Healthy | — |
| hermes | 8003 | ❌ Restarting | `NameError: 'time' not defined` |
| hormiguero | 8004 | ❌ Restarting | `ModuleNotFoundError: 'tools'` |
| manifestator | 8005 | ⚠️ Unhealthy | (depends on others) |
| mcp | 8006 | ✅ Healthy | — |
| shubniggurath | 8007 | ❌ Restarting | `ModuleNotFoundError: 'numpy'` |
| spawner | 8008 | ✅ Healthy | — |
| operator-backend | 8011 | ✅ Healthy | — |

---

## When to Run Autosync

**Manual execution:**
```bash
cd /home/elkakas314/vx11
./tools/autosync.sh feature/ui/operator-advanced
```

**Expected behavior:**
1. Stash local changes
2. Fetch from remote
3. Rebase onto remote/feature/ui/operator-advanced
4. Apply stashed changes
5. Commit WIP if changes exist
6. Push to remote

**Logs:** Check console output or `journalctl` if running via systemd (when installed)

---

## Installation of Systemd Artifacts (Future Authorization Only)

When approved, to activate autonomous synchronization:

```bash
# Copy templates
sudo cp scripts/systemd/vx11-autosync.service /etc/systemd/system/
sudo cp scripts/systemd/vx11-autosync.timer /etc/systemd/system/

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable vx11-autosync.timer
sudo systemctl start vx11-autosync.timer

# Verify
sudo systemctl status vx11-autosync.timer
sudo journalctl -u vx11-autosync.service -f
```

---

## Files You SHOULD NOT Touch

- `tokens.env` (credentials only)
- `tokens.env.master` (sensitive)
- `.github/copilot-instructions.md` **SECCIÓN A** (immutable)
- `tools/autosync.sh` (core logic)
- Any module folder structure
- `docker-compose.yml` ports/services

---

## Files That CAN Change

- `.github/copilot-instructions.md` **SECCIÓN B** (per-session updates)
- Module code (with care, respecting sync)
- Configuration files (outside credentials)
- Documentation in docs/
- Design templates in scripts/systemd/

---

## Reference Links

- Main Instructions: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- Autosync Script: [tools/autosync.sh](tools/autosync.sh)
- Systemd Design: [docs/AUTOSYNC_SYSTEMD_DESIGN.md](docs/AUTOSYNC_SYSTEMD_DESIGN.md)
- Service Template: [scripts/systemd/vx11-autosync.service](scripts/systemd/vx11-autosync.service)
- Timer Template: [scripts/systemd/vx11-autosync.timer](scripts/systemd/vx11-autosync.timer)

---

**Status:** VX11 v7.0 architecture stable, synchronization functional, systemd design ready for future deployment.
