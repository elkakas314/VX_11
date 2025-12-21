# VX11 Autosync Systemd Design — REFERENCE (NOT INSTALLED)

**Status:** Design document only. These artifacts are **NOT INSTALLED** in the system.
**When to install:** Only upon explicit authorization from the user.

---

## Overview

This document outlines the systemd service and timer design for autonomous VX11 repository synchronization. The design uses:

1. **vx11-autosync.service** — One-shot service that runs the autosync script
2. **vx11-autosync.timer** — Timer that triggers the service every 5 minutes
3. **.autosync.lock** — Lockfile to prevent concurrent executions

---

## Design Rationale

### Why 5-minute interval?
- Balances between rapid change detection and system overhead
- Allows repository changes to propagate to remote within predictable window
- Reduces risk of multiple concurrent syncs while keeping latency reasonable

### Why randomized delay (±30 seconds)?
- Prevents "thundering herd" if multiple VX11 instances are running
- Avoids collision with other scheduled tasks
- Distributes load across time window

### Why root user?
- Required for SSH key access if using key-based git auth
- Allows write permissions to `.autosync.lock`
- Consistent with VX11 Docker orchestration model

### Why lockfile (.autosync.lock)?
- Prevents infinite loop if service/timer logic fails
- Simple, reliable anti-race mechanism
- Can be inspected with `ls -la .autosync.lock`
- Automatically cleaned up by ExecStopPost

---

## Installation Instructions (FUTURE USE)

### Step 1: Copy files to systemd
```bash
sudo cp scripts/systemd/vx11-autosync.service /etc/systemd/system/
sudo cp scripts/systemd/vx11-autosync.timer /etc/systemd/system/
```

### Step 2: Reload and enable
```bash
sudo systemctl daemon-reload
sudo systemctl enable vx11-autosync.timer
sudo systemctl start vx11-autosync.timer
```

### Step 3: Verify
```bash
sudo systemctl status vx11-autosync.timer
sudo systemctl list-timers vx11-autosync.timer
sudo journalctl -u vx11-autosync.service -f
```

---

## Verification & Debugging

### Check service status
```bash
systemctl status vx11-autosync.service
systemctl status vx11-autosync.timer
```

### View recent executions
```bash
sudo journalctl -u vx11-autosync.service -n 50
sudo journalctl -u vx11-autosync.service --since="1 hour ago"
```

### Monitor in real-time
```bash
sudo journalctl -u vx11-autosync.service -f
```

### Check for lockfile
```bash
ls -la /home/elkakas314/vx11/.autosync.lock
```

### Manual trigger (for testing)
```bash
sudo systemctl start vx11-autosync.service
```

### Disable (if needed)
```bash
sudo systemctl stop vx11-autosync.timer
sudo systemctl disable vx11-autosync.timer
```

---

## Troubleshooting

### "Timer is not running"
```bash
sudo systemctl enable vx11-autosync.timer
sudo systemctl start vx11-autosync.timer
```

### "Service failed with exit code 1"
Check logs:
```bash
sudo journalctl -u vx11-autosync.service -n 100
```

### "Lockfile stuck"
Safe manual cleanup (only if absolutely sure service is not running):
```bash
# First, verify no process is using the lock
ps aux | grep autosync | grep -v grep

# If safe, remove lock
rm /home/elkakas314/vx11/.autosync.lock
```

### "Changes not synced after 5 minutes"
- Check git status: `cd /home/elkakas314/vx11 && git status`
- Check for uncommitted changes: `git status --porcelain`
- Review service logs: `sudo journalctl -u vx11-autosync.service -n 50`

---

## Architectural Notes

- **Service Type:** `oneshot` — Executes script once and exits
- **Restart Policy:** None (timer handles re-execution)
- **Dependency Chain:** Timer → Service → autosync.sh script
- **Lock Mechanism:** File-based (simple, reliable, no external DB needed)
- **Git Integration:** Uses existing `vx_11_remote` remote configuration

---

## Security Considerations

- Runs as root (required for git operations)
- Uses public SSH key authentication (configured in system)
- No passwords stored in unit files
- Lockfile permissions: World-readable (not sensitive data)
- Logs written to systemd journal (restricted to root/systemd by default)

---

## Future Enhancements

1. **Conditional sync** — Only commit if actual changes detected
2. **Notification webhook** — Alert on sync failure
3. **Rollback capability** — Store pre-sync commit hash
4. **Metrics collection** — Track sync success rate, duration
5. **Conflict resolution** — Auto-stash on rebase conflicts

---

## Related Files

- `/home/elkakas314/vx11/tools/autosync.sh` — Main sync script
- `/home/elkakas314/vx11/.github/copilot-instructions.md` — VX11 canonical instructions
- `/home/elkakas314/vx11/scripts/systemd/` — Other VX11 service templates

---

**Last Updated:** 2025-12-12
**Status:** DESIGN ONLY — NOT INSTALLED
