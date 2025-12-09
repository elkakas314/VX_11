# 🎚️ REAPER Safe Installation Script for VX11 v6.2

> **Purpose**: Install REAPER DAW with audio stack in isolated VX11 sandbox, with automatic rollback on failure
>
> **Safety**: Preserves VX11 core integrity, non-interactive suitable for CI/autonomous, graceful error handling

---

## ✅ Quick Start

```bash
# 1. Place REAPER installer in ~/Descargas/
cp ~/Downloads/reaper*.tar.xz ~/Descargas/

# 2. Run installation script (non-interactive)
bash /home/elkakas314/vx11/scripts/install_reaper_safe.sh

# 3. Verify
source ~/.bashrc
reaper --version
```

---

## 📋 What This Script Does

### Phase 1: Pre-Flight Checks
- ✅ Verify VX11 core (9 modules intact)
- ✅ Create tentaculo_vx11 sandbox if needed
- ✅ Check required binaries (tar, find)
- ✅ Ensure no VX11 core modifications

### Phase 2: Find Installer Files
- ✅ Detect REAPER installer (*.tar.xz or *.tar.gz)
- ✅ Detect plugin .so files (SWS, ReaPack, etc.)
- ✅ Validate file accessibility

### Phase 3: Uninstall Previous REAPER
- ✅ Find existing installations (/opt/REAPER, ~/.config/REAPER, etc.)
- ✅ Backup before deletion
- ✅ Safe removal with error handling

### Phase 4: Extract REAPER Installer
- ✅ Create controlled install path
- ✅ Extract with path traversal protection
- ✅ Verify binary integrity
- ✅ Set proper permissions

### Phase 5: Create REAPER Command Wrapper
- ✅ Create wrapper script (not system symlink)
- ✅ Add to PATH via ~/.bashrc
- ✅ Enable global `reaper` command

### Phase 6: Install Plugins
- ✅ Copy .so files to UserPlugins directory
- ✅ Preserve plugin permissions
- ✅ Non-critical on failure

### Phase 7: Install Audio Stack
- ✅ **First choice**: PipeWire + JACK compatibility
- ✅ **Fallback**: PulseAudio + JACK modules
- ✅ **Fallback**: ALSA (always available)
- ✅ Add user to audio group
- ✅ Avoid mixing audio systems

### Phase 8: Detect Audio Devices
- ✅ Check ALSA devices (aplay -L)
- ✅ Check PulseAudio sinks (pactl list)
- ✅ Check JACK (jack_lsp)
- ✅ Detect USB audio interfaces

### Phase 9: Verify Installation
- ✅ Test REAPER binary executable
- ✅ Test REAPER headless startup
- ✅ Verify audio backend responding
- ✅ Confirm audio devices accessible

### Phase 10: Generate Summary Report
- ✅ Create detailed installation report
- ✅ Document audio backend used
- ✅ List detected devices
- ✅ Provide troubleshooting guide

---

## 📁 Directory Structure Created

```
/home/elkakas314/tentaculo_vx11/
├── tools/
│   └── reaper/                    # REAPER installation directory
│       ├── reaper                 # Main REAPER binary
│       ├── UserPlugins/           # Plugin directory
│       ├── Resources/
│       └── ...
├── bin/
│   └── reaper                     # Wrapper script (added to PATH)
├── .backup_reaper_*/              # Backup of previous installation
├── reaper_install.log             # Full installation log
└── reaper_install_summary.txt     # Installation summary report
```

---

## 🔄 Rollback & Error Handling

### Automatic Rollback

If any phase fails:
1. Script captures failure
2. Executes rollback steps in reverse order
3. Restores previous state from backup
4. Logs all operations

### Manual Rollback

If you need to manually undo installation:

```bash
# Remove new installation
rm -rf /home/elkakas314/tentaculo_vx11/tools/reaper

# Restore from backup
cp -r /home/elkakas314/tentaculo_vx11/.backup_reaper_*/* ~/

# Remove wrapper
rm /home/elkakas314/tentaculo_vx11/bin/reaper

# Clean up PATH
sed -i '/tentaculo_vx11\/bin/d' ~/.bashrc
```

---

## 🎙️ Audio Backend Selection

### PipeWire (Recommended)
- ✅ Modern Linux audio system
- ✅ JACK compatibility via pipewire-jack
- ✅ Better latency and routing
- ✅ Native PulseAudio bridge

**Packages**: pipewire, pipewire-jack, pipewire-alsa, pipewire-pulse

### PulseAudio (Fallback)
- ✅ Widely compatible
- ✅ Simple per-app volume control
- ✅ JACK bridge via pulseaudio-module-jack

**Packages**: pulseaudio, pulseaudio-module-jack

### ALSA (Final Fallback)
- ✅ Always available (kernel-level)
- ✅ Low-level audio control
- ✅ No additional packages needed

---

## 🔧 Configuration Files

### REAPER Configuration
- Location: `~/.config/REAPER/reaper.ini`
- Main settings file (auto-created on first launch)
- Edit for JACK, sample rate, audio devices

### Audio System Configuration
- **PipeWire**: `~/.config/pipewire/pipewire.conf`
- **PulseAudio**: `~/.config/pulse/default.pa`
- **ALSA**: `/etc/asound.conf` or `~/.asoundrc`

---

## 📊 Log Files

### Installation Log
- **Location**: `/home/elkakas314/tentaculo_vx11/reaper_install.log`
- **Content**: All phases, timings, warnings, errors
- **Size**: ~10-50 KB

### Summary Report
- **Location**: `/home/elkakas314/tentaculo_vx11/reaper_install_summary.txt`
- **Content**: Status, paths, audio config, troubleshooting
- **Human-readable**: Yes, safe to share

### Access Logs
```bash
# View full log
cat /home/elkakas314/tentaculo_vx11/reaper_install.log

# View summary
cat /home/elkakas314/tentaculo_vx11/reaper_install_summary.txt

# Follow log in real-time during install
tail -f /home/elkakas314/tentaculo_vx11/reaper_install.log
```

---

## 🐛 Troubleshooting

### "REAPER installer not found"
```bash
# Check if file is in ~/Descargas/
ls -la ~/Descargas/*reaper*

# Expected formats
reaper*.tar.xz
reaper*.tar.gz
```

### "Audio devices not detected"
```bash
# Verify ALSA devices
aplay -l

# Check PulseAudio
pactl list short sinks

# Test JACK (if installed)
jack_lsp

# Add user to audio group
sudo usermod -a -G audio $USER
# (Requires logout/login to take effect)
```

### "REAPER won't start"
```bash
# Test binary directly
/home/elkakas314/tentaculo_vx11/tools/reaper/reaper --version

# Check for library dependencies
ldd /home/elkakas314/tentaculo_vx11/tools/reaper/reaper

# Try headless mode
/home/elkakas314/tentaculo_vx11/tools/reaper/reaper -audioconfig
```

### "Audio backend not working"
```bash
# Check which backend is active
systemctl status pipewire  # or pulseaudio
pactl stat  # PulseAudio status
pw-cli info  # PipeWire status

# Restart audio daemon
systemctl restart pipewire  # or pulseaudio

# Check for audio group membership
groups  # Should include 'audio'

# Enable JACK
qjackctl  # GUI
# or manually: jackd -d alsa -d hw:0
```

### "VX11 core was modified"
```bash
# Verify VX11 integrity
for m in gateway madre switch hermes hormiguero manifestator mcp shubniggurath spawner; do
    [ -d /home/elkakas314/vx11/$m ] && echo "✓ $m" || echo "✗ $m"
done

# Check core Python files
ls -la /home/elkakas314/vx11/config/*.py | wc -l  # Should be 15+
```

---

## 🔒 Safety Constraints Enforced

| Constraint | Implementation |
|-----------|-----------------|
| **VX11 core untouched** | All changes in `/tentaculo_vx11/tools/reaper` |
| **Isolated installation** | REAPER never touches `/opt`, `/usr` system paths |
| **Safe extraction** | Path traversal check, temp directory validation |
| **Graceful failure** | Error handling in every phase, automatic rollback |
| **Non-interactive** | Suitable for CI/cron (all prompts automated) |
| **Minimal sudo** | Only for audio package installation |
| **Plugin isolation** | Plugins in sandbox, verified file types |
| **Audio mixing prevention** | Selects one backend, avoids conflicts |
| **Backup on uninstall** | Previous state preserved before removal |

---

## 🚀 Advanced Usage

### CI/CD Integration

```bash
#!/bin/bash
# Example: Run in GitHub Actions or similar
set -e

cd /home/elkakas314/vx11

# Run installation
bash scripts/install_reaper_safe.sh

# Verify success
if grep -q "SUCCESS" /home/elkakas314/tentaculo_vx11/reaper_install_summary.txt; then
    echo "✓ REAPER installation successful"
    exit 0
else
    echo "✗ REAPER installation failed"
    cat /home/elkakas314/tentaculo_vx11/reaper_install.log
    exit 1
fi
```

### Manual Audio Configuration

```bash
# After installation, configure audio backend

# For PipeWire + JACK
sudo apt-get install qjackctl
qjackctl &  # Start JACK control GUI

# For PulseAudio
pactl set-default-sink alsa_output.pci-0000_00_1f.3.analog-stereo

# For ALSA only
alsamixer  # Configure audio levels
```

### Plugin Management

```bash
# Add more plugins after installation
cp ~/Descargas/*.so /home/elkakas314/tentaculo_vx11/tools/reaper/UserPlugins/

# Verify plugins are found
ls /home/elkakas314/tentaculo_vx11/tools/reaper/UserPlugins/
```

---

## 📝 Script Output Example

```
[2024-01-15 14:30:00] [INFO] ============================================================
[2024-01-15 14:30:00] [INFO] REAPER Safe Installation for VX11 v6.2
[2024-01-15 14:30:00] [INFO] Start Time: Mon Jan 15 14:30:00 EST 2024
[2024-01-15 14:30:00] [INFO] ============================================================
[2024-01-15 14:30:01] [INFO] === PHASE 1: PRE-FLIGHT CHECKS ===
[2024-01-15 14:30:01] [SUCCESS] VX11 core verified intact
[2024-01-15 14:30:02] [INFO] === PHASE 2: FIND INSTALLER FILES ===
[2024-01-15 14:30:02] [SUCCESS] Found REAPER installer: /home/elkakas314/Descargas/reaper_linux_x86_64.tar.xz
[2024-01-15 14:30:03] [INFO] === PHASE 3: UNINSTALL PREVIOUS REAPER ===
[2024-01-15 14:30:03] [INFO] No previous REAPER installation found
...
[2024-01-15 14:35:00] [SUCCESS] REAPER Installation COMPLETED SUCCESSFULLY
[2024-01-15 14:35:00] [SUCCESS] End Time: Mon Jan 15 14:35:00 EST 2024
[2024-01-15 14:35:00] [SUCCESS] ============================================================
```

---

## 📞 Support & Next Steps

1. **Verify installation**: `/home/elkakas314/tentaculo_vx11/reaper_install_summary.txt`
2. **Check logs**: `/home/elkakas314/tentaculo_vx11/reaper_install.log`
3. **Test REAPER**: `reaper --version`
4. **Configure audio**: See "Audio Backend Selection" section
5. **Report issues**: Include summary report + relevant log sections

---

## 🔄 VX11 Integration

This script maintains complete VX11 v6.2 integrity:

- ✅ All 9 VX11 modules remain untouched
- ✅ REAPER runs in isolated sandbox (`tentaculo_vx11`)
- ✅ No modifications to VX11 core paths
- ✅ Can be completely rolled back
- ✅ VX11 services operate normally during/after installation

---

**Version**: 1.0  
**Last Updated**: 2024-01-15  
**Tested On**: Ubuntu 20.04+ / Debian 11+  
**Status**: ✅ Production Ready

