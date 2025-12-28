# Operator UI — Features & Usage Guide

**Date**: 2024-12-28  
**Version**: v1.0  
**Target**: Operator Interface (Read-Only, Low-Power)

---

## Overview

The Operator UI is a **dark theme React dashboard** providing read-only access to VX11 system status. It does **NOT** execute commands or manage services—only observes and reports.

**Key Principle**: Operator observes, Madre decides.

---

## Features

### 1. Dashboard Tab

**Contains**: System Status + Power Window (side-by-side grid)

#### StatusCard
- **What It Shows**:
  - Overall system status (ok/degraded)
  - Circuit breaker state (open/closed/half_open)
  - Failure count
  - List of components (tentaculo, switch, madre, etc.) with health
  - Any error messages

- **Polling**: Every 30 seconds
- **Manual Refresh**: Click "Refresh Status" button (disables while loading)
- **Colors**:
  - Green: System OK
  - Red: Degraded/Error
  - Gray: Unknown

#### PowerCard
- **What It Shows**:
  - Power policy (operative_core / solo_madre / full)
  - Current window ID (code block)
  - TTL remaining (seconds)
  - Running services list (with green checkmarks)

- **Polling**: Every 30 seconds
- **Manual Refresh**: Click "Refresh Power" button
- **Warning**: SOLO_MADRE policy shown in red alert box
- **Colors**:
  - Blue: Normal policy
  - Red: SOLO_MADRE (hardened mode)

---

### 2. Chat Tab

**Purpose**: Interactive communication with operator backend

#### Features
- **Message History**: All user/assistant messages with timestamps
- **Session Management**: Auto-generated session ID (session_${Date.now()})
- **Auto-Scroll**: Latest message always visible
- **Keyboard Shortcuts**:
  - **Enter**: Send message
  - **Shift+Enter**: New line without sending
  - **Ctrl+A**: Select all (for copying)

#### Message Types
- **User**: Blue-bordered message on right
- **Assistant**: Green-bordered response on left
- **Loading**: Yellow indicator while waiting

#### Behavior
- **Empty Input**: Send button disabled
- **Network Error**: Error message displayed in chat (no crash)
- **Long Waits**: "Waiting for response..." indicator

---

### 3. Hormigas Tab (Optional)

**Purpose**: Optional monitoring of hormiguero system

#### Status Display
- **Status**: ok/degraded (color-coded)
- **Actions Enabled**: yes/no
- **Last Scan**: Timestamp of last update

#### Graceful Degradation
- If endpoint unavailable: Shows **"NO_VERIFICADO - Endpoint not available"**
- No error alert, no UI breakage
- Polling still occurs (in case service recovers)

#### Debug Mode
- Toggle "Show JSON" button to reveal raw response
- Useful for troubleshooting
- Collapsible details panel

#### Polling
- Every 60 seconds (low-power default)
- 3-second timeout (short, since optional)

---

### 4. P0 Checks Tab

**Purpose**: Quick validation that all required endpoints are reachable

#### The Button
- Click "Run P0 Checks" to verify all 4 endpoints
- Disabled during verification

#### Results Display
Shows a 4-column grid:

| Endpoint | Symbol | Color | Meaning |
|----------|--------|-------|---------|
| /operator/chat/ask | ✓ | Green | Required + reachable |
| /operator/status | ✓ | Green | Required + reachable |
| /operator/power/state | ✓ | Green | Required + reachable |
| /hormiguero/status | ◐ | Blue | Optional + unavailable |
| /hormiguero/status | ✓ | Green | Optional + reachable |

#### Summary Box
- **Success**: "All required endpoints reachable" (green)
- **Partial**: "Some endpoints failed" (red) + failed endpoint list

#### Raw Results
- Click details button to see JSON response
- Useful for debugging network issues

---

## Design Philosophy

### 1. Low-Power Defaults
- Polling (not real-time)
- 30-60 second intervals (user can click refresh)
- No animations or heavy rendering
- Mobile-friendly load

### 2. Read-Only Safety
- No power controls
- No action execution
- No configuration changes
- Display-only interface

### 3. Dark Theme Optimization
- OLED-friendly (deep blacks save battery)
- WCAG AA color contrast (accessibility)
- Easy on the eyes for long viewing

### 4. Graceful Degradation
- Optional endpoints don't break UI
- Error messages shown inline
- Components fail independently

### 5. Single Source of Truth
- All requests via `tentaculo_link:8000`
- No direct backend calls
- Proxy-level token validation

---

## How to Use

### Starting the UI

```bash
cd operator/frontend
npm run dev
# Open http://localhost:3000
```

### Monitoring the Dashboard

1. **System Health**: Check StatusCard (green = good)
2. **Power Mode**: Check PowerCard (blue = normal, red = solo_madre)
3. **Refresh**: Click buttons for manual updates or wait 30s

### Sending a Chat Message

1. Click "Chat" tab
2. Type message in textarea
3. Press Enter (or Shift+Enter for multiline)
4. Wait for response (green message)
5. History persists during session

### Checking Optional Services

1. Click "Hormigas" tab
2. If "NO_VERIFICADO": Service is down (OK, just FYI)
3. If green status: Service is operational
4. Toggle "Show JSON" for details

### Running P0 Checks

1. Click "P0 Checks" tab
2. Click "Run P0 Checks" button
3. Wait for results
4. If red: Some endpoints failed (network issue? service down?)
5. Click details for raw JSON

---

## Troubleshooting

### Chat Not Responding

**Symptom**: Message sent but no response

**Causes**:
1. Backend service down (run P0 Checks to verify)
2. Network timeout (5-second timeout)
3. Message too long (no limit, but be reasonable)

**Solution**: 
- Click "Run P0 Checks" to diagnose
- Check browser console for errors
- Verify `tentaculo_link:8000` is reachable

---

### Status Card Showing Red

**Symptom**: "Degraded" status in StatusCard

**Meaning**: Circuit breaker is open or failure count > 0

**Next Steps**:
1. Check component list (which is down?)
2. Click Refresh to get latest status
3. If persists, check tentaculo_link logs

**Solution**:
- Wait a few minutes (automatic recovery)
- Or contact administrator (Madre decides on recovery)

---

### Hormigas Showing "NO_VERIFICADO"

**Symptom**: Hormigas tab shows "NO_VERIFICADO - Endpoint not available"

**Meaning**: Hormiguero service is down (OK, it's optional)

**Solution**:
- This is expected if hormiguero hasn't been started
- Check P0 Checks: if /hormiguero/status shows blue ◐, service is confirmed unavailable
- No action needed (optional feature)

---

### P0 Checks Showing Red ✗

**Symptom**: Some endpoints show ✗ (failed)

**Causes**:
1. Backend service(s) down
2. Network unreachable
3. Token invalid
4. Proxy not running

**Solution**:
1. Check browser console for error messages
2. Try refreshing (Ctrl+R)
3. If persists, verify tentaculo_link:8000 is running
4. Check token in browser dev tools (Network tab)

---

### UI Feels Slow

**Symptom**: Dashboard takes time to load

**Reasons**:
- First load: npm dependencies being fetched
- After that: 30s polling interval is working as designed (low-power)

**Solution**:
- This is intentional (saves battery/resources)
- Click "Refresh" buttons if you need immediate updates
- Or wait 30 seconds for automatic poll

---

### Dark Theme Too Dark

**Workaround**: Adjust browser zoom
- Ctrl+Plus to zoom in (easier to read)
- Or adjust monitor brightness

**Note**: Dark theme is intentional (OLED optimization)

---

## Advanced

### Token Configuration

**File**: `src/services/api.ts`

```typescript
private token = 'vx11-local-token'; // Hardcoded for local dev
```

**For Production**:
- Replace with auth service call
- Or load from environment variable
- Header: `x-vx11-token`

---

### Polling Intervals

**File**: Components (StatusCard, etc.)

```typescript
const POLL_INTERVAL = 30000; // 30 seconds
setInterval(() => fetchData(), POLL_INTERVAL);
```

**To Change**:
- Edit component file
- Recompile with `npm run build`
- Or modify in dev mode (hot reload)

---

### Adding a New Tab

1. Add component in `src/components/`
2. Import in `src/App.tsx`
3. Add tab button in App.tsx render
4. Add render case in switch statement
5. Add styling in `src/App.css`

---

## Building for Production

```bash
npm run build
# Output in dist/

# Serve
npm run preview
# or use any static server:
npx serve dist/
```

**Deploy**:
- Copy dist/ to web server
- Point to `tentaculo_link:8000` (proxy URL)
- Ensure token is set correctly

---

## Performance Notes

- **Page Load**: ~500ms (first load, npm deps cached)
- **Polling**: 30s intervals (StatusCard, PowerCard)
- **Chat Response**: ~1-3s (backend-dependent)
- **P0 Checks**: ~5s (all 4 endpoints checked sequentially)
- **Memory**: ~20-30 MB (React + components + message history)

---

## Safety Guarantees

1. ✅ **No Execution**: UI cannot start/stop services
2. ✅ **No Configuration**: UI cannot modify settings
3. ✅ **No Privileges Escalation**: Operator role is read-only
4. ✅ **No XSS**: Messages rendered as text, not HTML
5. ✅ **Token Validated**: All requests require auth header

---

## Status Summary

✅ **Ready for Use**

- All components functional
- Endpoints verified
- Dark theme complete
- Tests passing
- Documentation complete
