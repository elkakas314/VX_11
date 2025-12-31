# VX11 Test Matrix

> Defaults are simulated/offline. Enable integration/E2E explicitly.

## Unit (offline)

```bash
pytest -m unit
```

## Integration (requires running services)

```bash
VX11_INTEGRATION=1 pytest -m integration
```

## E2E (Docker Compose stack)

```bash
VX11_INTEGRATION=1 pytest -m e2e
```

## UI (Operator frontend)

```bash
cd operator/frontend
npm run test
```

Optional UI runner:

```bash
cd operator/frontend
npm run test:ui
```

## Build (Operator frontend)

```bash
cd operator/frontend
npm run build
```
