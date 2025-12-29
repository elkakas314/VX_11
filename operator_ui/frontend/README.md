# VX11 Operator UI

Dark theme dashboard for VX11 Operator. Read-only interface that consumes only `tentaculo_link:8000`.

## Features

- **Dashboard**: System status + Power window state
- **Chat**: Interactive chat with session history
- **Hormigas**: Read-only monitoring panel (optional, shows NO_VERIFICADO if unavailable)
- **P0 Checks**: Quick verification of all endpoints

## Architecture

```
┌─ React/Vite Frontend (port 3000) ─┐
│  - StatusCard                      │
│  - PowerCard                       │
│  - ChatPanel                       │
│  - HormigueroPanel                 │
│  - P0ChecksPanel                   │
└────────────────┬────────────────────┘
                 │
                 ↓ (HTTP, x-vx11-token)
        ┌─ Tentaculo Link:8000 ─┐
        │ (Single Entrypoint)   │
        └────────────┬──────────┘
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
   Backend Services      (Hormiguero optional)
```

## Development

```bash
# Install dependencies
npm install

# Run dev server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Run tests with UI
npm run test:ui
```

## Configuration

### Environment Variables

- `VITE_API_BASE_URL`: Backend URL (default: `http://localhost:8000`)
- `VITE_TOKEN`: Auth token (default: `vx11-local-token`)

### Feature Flags

All endpoints checked by P0 suite:
- ✅ `/operator/chat/ask` (required)
- ✅ `/operator/status` (required)
- ✅ `/operator/power/state` (required)
- ◐ `/hormiguero/status` (optional, shows NO_VERIFICADO if unavailable)

## Design

- **Dark theme** (OLED-friendly colors)
- **Low-power UI**: Polling (30s for status/power, 60s for hormiguero) + manual refresh
- **No real-time**: Polling only, no WebSockets by default
- **Read-only**: No power controls or actions from UI
- **Minimal JS**: No heavy frameworks, vanilla fetch API

## Testing

### P0 Tests

Quick validation of all required endpoints:

```bash
# In UI: Click "Run P0 Checks" button
# Shows: ✓ OK / ✗ FAIL for each endpoint
```

### Unit Tests

```bash
npm run test
```

Tests verify:
- Component rendering
- API call mocking
- P0 checks behavior

## Troubleshooting

### "NO_VERIFICADO - Endpoint not available"

Hormiguero panel shows this when:
- `/hormiguero/status` endpoint not available
- Hormiguero service (port 8004) not running
- Network timeout (3s default)

This is normal in low-power mode. The panel is optional.

### Buttons not responding

- Check browser console for errors
- Verify `tentaculo_link:8000` is running
- Check token: `x-vx11-token: vx11-local-token` (default)

### Chat not working

- Check `/operator/chat/ask` endpoint (run P0 Checks)
- Verify switch service is running
- Look for errors in browser console

## Production Build

```bash
npm run build
# Output: dist/

# Serve with any static server
python -m http.server --directory dist 8080
```

Then navigate to `http://localhost:8080`

## License

VX11 Project
