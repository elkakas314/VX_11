# VX11 Secret Rotation Guide (No Values)

**Scope**: This guide provides rotation steps without embedding any credentials.

## When to rotate
- Any accidental secret exposure in git history.
- Any suspect access to .env, tokens.env, or CI/CD secrets.
- Scheduled rotation for production keys (e.g., monthly/quarterly).

## What to rotate
- `DEEPSEEK_API_KEY`
- `VX11_TENTACULO_LINK_TOKEN` / `VX11_GATEWAY_TOKEN`
- `VX11_OPERATOR_TOKEN` / `VX11_LOCAL_TOKEN`
- Any other provider API keys referenced via env vars.

## Rotation steps (generic)
1. **Issue new credentials** in the provider dashboard.
2. **Update secrets storage** (local `.env` or vault/CI secrets). Do **not** commit.
3. **Restart services** that read env vars at startup (e.g., `tentaculo_link`, `operator-backend`).
4. **Revoke old credentials** in the provider dashboard.
5. **Validate** via single-entrypoint (tentaculo_link) health and operator status endpoints.

## Post-rotation validation (examples)
```bash
curl -sS http://127.0.0.1:8000/health
curl -sS -H "X-VX11-Token: $VX11_TOKEN" http://127.0.0.1:8000/operator/api/v1/status
```

## Notes
- Keep `.env` and `tokens.env` out of git.
- Prefer environment variables in production deployments.
