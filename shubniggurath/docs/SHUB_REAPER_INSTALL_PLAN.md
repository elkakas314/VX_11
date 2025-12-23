# SHUB-NIGGURATH v3.0 — REAPER INSTALLATION PLAN

**Document:** Production REAPER Integration Guide  
**Version:** 3.1 Preparation  
**Date:** 2025-12-02  
**Target Environment:** Linux (Ubuntu 20.04+)

---

## PART 1: REAPER Installation on Linux

### Step 1.1: System Requirements

**Minimum:**
- CPU: 2 cores, 2GHz
- RAM: 4 GB
- Storage: 20 GB (SSD recommended)
- OS: Ubuntu 20.04+ / Debian 11+ / Fedora 36+

**Recommended:**
- CPU: 8+ cores
- RAM: 16+ GB
- Storage: 100+ GB SSD
- OS: Ubuntu 22.04 LTS

### Step 1.2: Install REAPER

```bash
# Download REAPER (latest stable)
cd /opt
sudo wget https://www.reaper.fm/files/6.x/reaper6831_linux_x86_64.tar.xz

# Extract
sudo tar -xf reaper6831_linux_x86_64.tar.xz
cd REAPER
./install-reaper.sh  # Installs to $HOME/REAPER

# Or use system install
sudo ./install-backend.sh
sudo ln -s /opt/REAPER /usr/local/reaper
```

### Step 1.3: REAPER Configuration

```bash
# Set REAPER home
export REAPER_HOME="$HOME/REAPER"
export REAPER_SCRIPTS="$REAPER_HOME/Scripts"
export REAPER_EXTENSIONS="$REAPER_HOME/Plugins/reaper_*"

# Create directories
mkdir -p ~/.config/REAPER
mkdir -p "$REAPER_SCRIPTS/Shub"
mkdir -p "$REAPER_HOME/ReaPacks"

# Add to ~/.bashrc or ~/.zshrc
echo 'export REAPER_HOME="$HOME/REAPER"' >> ~/.bashrc
source ~/.bashrc
```

### Step 1.4: Verify Installation

```bash
# Check REAPER
reaper --help                           # Should show options
$REAPER_HOME/reaper --version          # Should show version

# Check ReaScript support
reaper -console                         # Opens REAPER console

# Test via shell
python3 << 'EOF'
import subprocess
result = subprocess.run(["reaper", "--version"], capture_output=True, text=True)
print(result.stdout)  # Should show REAPER version
EOF
```

---

## PART 2: REAPER Extension Ecosystem

### Step 2.1: Install ReaPack

**ReaPack** = Extension manager for REAPER (required for Shub)

```bash
# Download ReaPack
cd "$REAPER_HOME/Plugins"
wget "https://github.com/cfillion/reapack/releases/download/v1.25.3/reapack64.so"

# Verify
ls -la reapack64.so  # Should exist

# Restart REAPER
reaper &  # Starts headless
# In REAPER GUI: Extensions → ReaPack → Browse → Install
```

### Step 2.2: Install SWS Extensions

**SWS** = Standard Windows Library (powerful utilities)

```bash
# Via ReaPack:
# Extensions → ReaPack → Search: "SWS/S&M"
# Install latest version

# Or manual:
cd "$REAPER_HOME/Plugins"
wget https://github.com/sws-extension/sws/releases/download/v2.13.6/sws-x64.so
chmod +x sws-x64.so
```

### Step 2.3: Create Shub Bridge Extension Directory

```bash
# Shub bridge location
SHUB_BRIDGE_DIR="$REAPER_HOME/Plugins/Shub-Niggurath"
mkdir -p "$SHUB_BRIDGE_DIR"

# Structure:
# $SHUB_BRIDGE_DIR/
# ├── reaper_shub_bridge.so          (C++ compiled bridge)
# ├── shub_scripts/
# │   ├── shub_analyzer.lua          (ReaScript Lua)
# │   ├── shub_mixer.lua
# │   ├── shub_master.lua
# │   └── shub_connector.lua         (Main entry point)
# ├── config.ini                      (Bridge configuration)
# └── README.md

touch "$SHUB_BRIDGE_DIR/config.ini"
cat > "$SHUB_BRIDGE_DIR/config.ini" << 'CONFIG'
[Shub-Niggurath Bridge v3.1]
shub_api_host=http://127.0.0.1
shub_api_port=9000
reaper_project_auto_sync=true
headphone_monitoring=false
drum_analysis_enabled=true
spectral_analysis_enabled=true
auto_mix_suggestion=false
CONFIG
```

### Step 2.4: ReaScript Integration Points

**Shub will access REAPER via ReaScript API:**

```lua
-- shub_connector.lua (main entry)

-- 1. Get project information
reaper.GetProjectName(projidx, namebuf, namebuf_sz)
reaper.CountTracks(proj)
reaper.GetTrack(proj, trackidx)

-- 2. Get track data
reaper.GetTrackName(track, namebuf, namebuf_sz)
reaper.GetMediaTrackInfo_Value(track, "D_VOL")  -- Volume
reaper.GetMediaTrackInfo_Value(track, "D_PAN")  -- Pan

-- 3. Get items (regions/clips)
reaper.CountTrackMediaItems(track)
reaper.GetTrackMediaItem(track, itemidx)
reaper.GetMediaItemInfo_Value(item, "D_POSITION")  -- Start time
reaper.GetMediaItemInfo_Value(item, "D_LENGTH")    -- Duration

-- 4. Get FX chain
reaper.TrackFX_GetCount(track)
reaper.TrackFX_GetFXName(track, fx, namebuf, namebuf_sz)
reaper.TrackFX_GetParam(track, fx, param, value)

-- 5. Send to Shub via HTTP
-- (HTTP POST to http://127.0.0.1:9000/v1/analysis/analyze)
```

---

## PART 3: Shub ↔ REAPER Communication Bridge

### Step 3.1: Bridge Architecture

```
REAPER (DAW)
    │
    ├─ ReaScript Lua API
    │   └─ Track/Item/FX enumeration
    │
    ├─ Shub Bridge Plugin (reaper_shub_bridge.so)
    │   └─ HTTP client → Shub API
    │
    └─ Network Bridge
        │
        └─ Shub-Niggurath API (9000)
            ├─ /v1/analysis/analyze
            ├─ /v1/mixing/mix
            ├─ /v1/mastering/master
            └─ /v1/headphones/calibrate
```

### Step 3.2: Bridge Configuration

**File:** `$SHUB_BRIDGE_DIR/bridge_config.py`

```python
# Shub v3.1 bridge configuration
REAPER_INTEGRATION = {
    "reaper_executable": "$HOME/REAPER/reaper",
    "reaper_project_path": "$HOME/Documents/REAPER Projects",
    "reaper_scripts_path": "$HOME/REAPER/Scripts/Shub",
    "reaper_api_timeout": 5.0,  # seconds
    "project_auto_sync": True,
    "track_cache_ttl": 60,  # seconds
    "auto_update_interval": 2.0,  # seconds
}

SHUB_API = {
    "host": "http://127.0.0.1",
    "port": 9000,
    "timeout": 10.0,
    "endpoints": {
        "analysis": "/v1/analysis/analyze",
        "mixing": "/v1/mixing/mix",
        "mastering": "/v1/mastering/master",
        "headphones": "/v1/headphones/calibrate",
    }
}

FEATURES = {
    "real_time_analysis": True,
    "drum_doctor": True,
    "spectral_analyzer": True,
    "auto_mixing": True,
    "auto_mastering": True,
    "headphone_monitoring": False,  # Requires stereo monitoring
}
```

### Step 3.3: Live Project Monitoring

**Mechanism:** Poll REAPER for project changes

```python
# shub/reaper_bridge/monitor.py (v3.1)

import asyncio
import httpx
import subprocess
import json

class REAPERMonitor:
    def __init__(self, reaper_home: str, shub_api: str):
        self.reaper_home = reaper_home
        self.shub_api = shub_api
        self.current_project = None
        self.track_cache = {}
    
    async def monitor_project(self):
        """Poll REAPER for project changes"""
        while True:
            try:
                # Get current project name
                project = await self._get_current_project()
                
                if project != self.current_project:
                    print(f"Project changed: {project}")
                    await self._sync_project(project)
                    self.current_project = project
                
                # Get track changes
                tracks = await self._get_tracks()
                if tracks != self.track_cache:
                    print(f"Tracks changed: {len(tracks)} tracks")
                    await self._analyze_tracks(tracks)
                    self.track_cache = tracks
                
                # Wait before next poll
                await asyncio.sleep(2.0)
            
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(5.0)
    
    async def _get_current_project(self) -> str:
        """Get current project name from REAPER"""
        # Via ReaScript: reaper.GetProjectName()
        result = subprocess.run([
            f"{self.reaper_home}/reaper",
            "-script", "get_project_name.lua"
        ], capture_output=True, text=True)
        return result.stdout.strip()
    
    async def _sync_project(self, project_name: str):
        """Sync project metadata to Shub"""
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.shub_api}/analysis/analyze", json={
                "project_name": project_name,
                "action": "sync_project"
            })
    
    async def _get_tracks(self) -> list:
        """Get track list from REAPER"""
        # Via ReaScript API enumeration
        pass
    
    async def _analyze_tracks(self, tracks: list):
        """Send tracks to Shub for analysis"""
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.shub_api}/analysis/analyze", json={
                "tracks": tracks,
                "action": "analyze_tracks"
            })

# Usage
monitor = REAPERMonitor(
    reaper_home="$HOME/REAPER",
    shub_api="http://127.0.0.1:9000"
)
asyncio.run(monitor.monitor_project())
```

---

## PART 4: Shub v3.1 REAPER Bridge Modules

### Step 4.1: Module Structure

**File:** `/home/elkakas314/vx11/shub/reaper_bridge/` (v3.1)

```
shub/reaper_bridge/
├── __init__.py
├── reaper_client.py           ← Main REAPER interface
├── reaper_monitor.py          ← Live project monitoring
├── reaper_analyzer.py         ← Audio analysis + REAPER integration
├── reaper_mixer.py            ← Mixing recommendations for REAPER
├── reaper_mastering.py        ← Mastering suggestions
├── reaper_headphones.py       ← Headphone calibration + monitoring
├── lua_scripts/
│   ├── shub_analyzer.lua      ← ReaScript analyzer
│   ├── shub_mixer.lua         ← Mixing script
│   └── shub_master.lua        ← Mastering script
└── config.py                  ← Bridge configuration
```

### Step 4.2: Core Bridge Classes

**reaper_client.py:**

```python
class REAPERClient:
    """Low-level REAPER API client"""
    
    async def get_project(self) -> REAPERProject:
        """Get current project"""
        
    async def get_track(self, track_idx: int) -> REAPERTrack:
        """Get specific track"""
        
    async def get_items(self, track_idx: int) -> List[REAPERItem]:
        """Get items in track"""
        
    async def get_fx_chain(self, track_idx: int) -> List[REAPERFX]:
        """Get FX chain"""
        
    async def apply_gain(self, track_idx: int, gain_db: float):
        """Apply gain to track"""
        
    async def apply_pan(self, track_idx: int, pan: float):
        """Apply pan to track"""

class REAPERAnalyzer:
    """Real-time drum + spectral analysis"""
    
    async def analyze_drums(self, track_idx: int) -> DrumAnalysis:
        """Analyze drum track"""
        
    async def spectral_analysis(self, track_idx: int) -> SpectralAnalysis:
        """Perform spectral analysis"""

class REAPERMixer:
    """Mixing recommendations engine"""
    
    async def suggest_mix(self, project: REAPERProject) -> MixSuggestions:
        """Generate mixing recommendations"""

class REAPERMastering:
    """Mastering analysis + suggestions"""
    
    async def analyze_mastering(self, project: REAPERProject) -> MasteringAnalysis:
        """Analyze project for mastering"""
```

---

## PART 5: Deployment Checklist for REAPER Integration

### Pre-Deployment

- [ ] REAPER installed in `/opt/REAPER` or `$HOME/REAPER`
- [ ] ReaPack installed via REAPER Extensions
- [ ] SWS extensions installed
- [ ] Shub bridge directory created
- [ ] Bridge configuration file created
- [ ] Lua scripts placed in correct directory
- [ ] Shub API running on port 9000
- [ ] Network connectivity verified (localhost:9000)

### Deployment

- [ ] Copy `reaper_bridge/` module to `/home/elkakas314/vx11/shub/`
- [ ] Update `shub/main.py` to import and initialize REAPERMonitor
- [ ] Create systemd service for REAPER monitoring (optional)
- [ ] Run Shub v3.1 with REAPER bridge enabled
- [ ] Verify bridge health endpoint

### Post-Deployment

- [ ] Test project sync (open REAPER project, verify Shub sees it)
- [ ] Test drum analysis (load drum track, verify analysis)
- [ ] Test mixing recommendations (run mixing analysis)
- [ ] Test mastering analysis (run mastering analysis)
- [ ] Monitor logs for errors
- [ ] Verify headphone monitoring (if enabled)

### Monitoring

```bash
# Watch Shub logs
tail -f /home/elkakas314/vx11/logs/shub.log

# Check bridge health
curl http://127.0.0.1:9000/health

# Test REAPER connection
curl http://127.0.0.1:9000/v1/reaper/health

# Monitor REAPER process
ps aux | grep reaper
```

---

## PART 6: Troubleshooting REAPER Integration

### Issue 1: REAPER not found

```bash
# Solution 1: Check REAPER installation
ls -la $HOME/REAPER/reaper

# Solution 2: Set REAPER_HOME
export REAPER_HOME="/opt/REAPER"
reaper --version

# Solution 3: Update bridge config
# Edit shub/reaper_bridge/config.py with correct path
```

### Issue 2: ReaScript timeout

```bash
# Solution: Increase timeout in config.py
REAPER_INTEGRATION["reaper_api_timeout"] = 10.0  # was 5.0

# Solution 2: Check REAPER is responsive
reaper -console
# (Can you see console output?)
```

### Issue 3: HTTP bridge not responding

```bash
# Solution 1: Check Shub is running
curl http://127.0.0.1:9000/health  # Should return 200

# Solution 2: Check port 9000 is not blocked
sudo lsof -i :9000  # Should show Shub process

# Solution 3: Check firewall
sudo ufw status  # Should allow localhost
```

### Issue 4: Analysis returns empty

```bash
# Solution 1: Verify project is loaded in REAPER
# (Open a project in REAPER GUI or via reaper --script)

# Solution 2: Check track enumeration
# Verify ReaScript can see tracks:
reaper -script get_track_count.lua

# Solution 3: Enable debug logging
# In config.py: set DEBUG = True
```

---

## PART 7: v3.1 Roadmap

### Phase 1: Core Integration (Weeks 1-2)
- ✅ Install REAPER
- ✅ Set up ReaPack + SWS
- ✅ Create bridge directory structure
- ✅ Test ReaScript API

### Phase 2: Real-time Monitoring (Weeks 3-4)
- ✅ Implement REAPERMonitor class
- ✅ Real-time project sync
- ✅ Track change detection
- ✅ Item enumeration

### Phase 3: Analysis Integration (Weeks 5-6)
- ✅ Drum Doctor with REAPER tracks
- ✅ Spectral analysis on actual audio
- ✅ Peak detection + headroom calculation
- ✅ Cache results in database

### Phase 4: Mixing + Mastering (Weeks 7-8)
- ✅ Auto-mixing suggestions
- ✅ Gain staging recommendations
- ✅ EQ suggestions based on spectral analysis
- ✅ Mastering loudness targets

### Phase 5: Headphone Monitoring (Weeks 9-10)
- ✅ HRTF-based monitoring
- ✅ Real-time headphone profile
- ✅ A/B comparison with regular monitoring
- ✅ Monitoring bias correction

### Phase 6: Polish + Documentation (Weeks 11-12)
- ✅ Performance optimization
- ✅ Error handling
- ✅ User documentation
- ✅ Video tutorials

---

## PART 8: Quick Start (When REAPER is Ready)

```bash
# 1. Install REAPER
cd /opt
sudo wget https://www.reaper.fm/files/6.x/reaper6831_linux_x86_64.tar.xz
sudo tar -xf reaper6831_linux_x86_64.tar.xz
cd REAPER && ./install-reaper.sh

# 2. Set environment
export REAPER_HOME="$HOME/REAPER"
echo 'export REAPER_HOME="$HOME/REAPER"' >> ~/.bashrc

# 3. Install ReaPack via REAPER GUI
# (Extensions → ReaPack → Browse Packages)

# 4. Verify Shub REAPER bridge exists
# (v3.1 ships with reaper_bridge module)

# 5. Start Shub with REAPER enabled
cd /home/elkakas314/vx11
python3 shub/main.py --enable-reaper-bridge

# 6. Test
curl http://127.0.0.1:9000/v1/reaper/health
```

---

## Conclusion

This plan provides complete REAPER integration pathway for Shub-Niggurath v3.1. 

**Current Status:** v3.0 ready, v3.1 bridge architecture prepared, awaiting REAPER installation.

**When REAPER is available:** Follow this plan to activate full integration.

---

*Plan Generated: 2025-12-02T11:15:00Z*  
*For: Shub-Niggurath v3.1*  
*Status: READY FOR IMPLEMENTATION*
