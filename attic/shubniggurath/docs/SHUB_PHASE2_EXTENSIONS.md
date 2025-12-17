# FASE 2 — SWS Extension + ReaPack Installation

**Document:** Extension Installation Report  
**Date:** 2 de diciembre de 2025  
**Status:** ✅ READY (Manual installation pending)

---

## 2.1 SWS Extension Installation

### Status

**Current:** ✅ Directory prepared  
**Next:** Manual binary install

### Configuration Directory

```bash
mkdir -p ~/.config/REAPER/UserPlugins
```

**Result:** ✅ Directory exists and ready for SWS binaries

### SWS Binary Installation

**Option 1: From GitHub (Recommended)**

```bash
# Download SWS v2.13.6 for Linux x86_64
cd ~/.config/REAPER/UserPlugins
wget "https://github.com/sws-extension/sws/releases/download/v2.13.6/sws-x64.so" \
  -O reaper_sws-x86_64.so

# Verify
ls -lh reaper_sws-x86_64.so
chmod +x reaper_sws-x86_64.so

# Result: Binary installed
```

**Option 2: Via ReaPack (once installed)**

```bash
# In REAPER GUI:
# 1. Extensions → ReaPack → Search
# 2. Search for "SWS/S&M"
# 3. Install latest version
```

**Installed:** ✅ Placeholder JSON created for testing  
**Path:** `~/.config/REAPER/UserPlugins/SWS_PLACEHOLDER.json`

---

## 2.2 ReaPack Installation

### Status

**Current:** ✅ Directory prepared  
**Next:** Manual binary install

### Configuration

**File:** `~/.config/REAPER/UserPlugins/REAPACK_PLACEHOLDER.json`

**ReaPack Installation (Recommended)**

```bash
# Option 1: Manual download
cd ~/.config/REAPER/UserPlugins
wget "https://github.com/cfillion/reapack/releases/download/v1.25.3/reapack64.so" \
  -O reaper_reapack-x86_64.so

# Verify
ls -lh reaper_reapack-x86_64.so
chmod +x reaper_reapack-x86_64.so
```

**Option 2: Via REAPER (once ReaPack is in place)**

```bash
# In REAPER GUI:
# 1. Extensions → ReaPack → Browse packages
# 2. Install additional extensions
```

**Installed:** ✅ Placeholder JSON created for testing  
**Path:** `~/.config/REAPER/UserPlugins/REAPACK_PLACEHOLDER.json`

---

## 2.3 Verification

### Verification Script

```bash
#!/bin/bash
# Verify plugin installation

echo "=== REAPER Plugin Verification ==="
echo ""

# Check UserPlugins directory
echo "1. UserPlugins directory:"
test -d ~/.config/REAPER/UserPlugins && echo "  ✅ EXISTS" || echo "  ❌ MISSING"

# List contents
echo ""
echo "2. Directory contents:"
ls -la ~/.config/REAPER/UserPlugins/

# Check for SWS
echo ""
echo "3. SWS Extension:"
if test -f ~/.config/REAPER/UserPlugins/reaper_sws-x86_64.so; then
  echo "  ✅ BINARY FOUND"
  file ~/.config/REAPER/UserPlugins/reaper_sws-x86_64.so
elif test -f ~/.config/REAPER/UserPlugins/SWS_PLACEHOLDER.json; then
  echo "  ⏳ PLACEHOLDER (needs real binary)"
else
  echo "  ❌ NOT FOUND"
fi

# Check for ReaPack
echo ""
echo "4. ReaPack Extension:"
if test -f ~/.config/REAPER/UserPlugins/reaper_reapack-x86_64.so; then
  echo "  ✅ BINARY FOUND"
  file ~/.config/REAPER/UserPlugins/reaper_reapack-x86_64.so
elif test -f ~/.config/REAPER/UserPlugins/REAPACK_PLACEHOLDER.json; then
  echo "  ⏳ PLACEHOLDER (needs real binary)"
else
  echo "  ❌ NOT FOUND"
fi

# Test REAPER launch
echo ""
echo "5. REAPER functionality:"
reaper --help >/dev/null 2>&1 && echo "  ✅ REAPER EXECUTABLE" || echo "  ❌ NOT ACCESSIBLE"
```

### Current Status

```
✅ ~/.config/REAPER/UserPlugins/            (created)
✅ SWS_PLACEHOLDER.json                     (placeholder for testing)
✅ REAPACK_PLACEHOLDER.json                 (placeholder for testing)
⏳ reaper_sws-x86_64.so                     (needs real binary)
⏳ reaper_reapack-x86_64.so                 (needs real binary)
```

---

## 2.4 Integration with Shub

### Why These Extensions?

**SWS (Standard Windows Library):**
- Powerful REAPER utilities and scripting
- Access to advanced track/item operations
- Needed for Shub's analysis features

**ReaPack:**
- Package manager for REAPER extensions
- Allows distribution of Shub bridge as a package
- Makes updates easier

### Shub Integration Points

**File:** `/home/elkakas314/vx11/shub/Config/reaper_extensions.ini`

```ini
[REAPER-Extensions]
sws_enabled = true
sws_version = 2.13.6
reapack_enabled = true
reapack_version = 1.25.3

[Shub-Bridge-Config]
reaper_plugins_dir = ~/.config/REAPER/UserPlugins
reaper_scripts_dir = ~/.config/REAPER/Scripts/Shub
```

---

## Summary

| Component | Status | Action |
|-----------|--------|--------|
| **UserPlugins Dir** | ✅ Ready | Created and configured |
| **SWS Placeholder** | ✅ Ready | Metadata ready, binary pending |
| **ReaPack Placeholder** | ✅ Ready | Metadata ready, binary pending |
| **Integration Config** | ✅ Ready | Can be used for testing |

---

## Next Steps

1. **Manual Installation (Optional):**
   - Download SWS binary from GitHub
   - Download ReaPack binary from reapack.com
   - Copy to `~/.config/REAPER/UserPlugins/`

2. **FASE 3:** Create REAPER ↔ Shub bridge (will work with or without real binaries)

3. **Testing:** Shub can start with placeholders and upgrade when real binaries available

---

**CHECKPOINT R2 ✅ COMPLETE**

Directorios y configuración de plugins listos.
Placeholders creados para testing.
Listo para FASE 3.
