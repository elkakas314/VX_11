# Secrets Rotation Guide

## Scope
This guide covers rotating VX11 secrets and API tokens after removing tracked `.env*` files from Git.

## Steps
1. **Generate new secrets** in your secrets manager or vault for:
   - `VX11_TENTACULO_LINK_TOKEN`
   - `VX11_GATEWAY_TOKEN`
   - `DEEPSEEK_API_KEY`
   - Any other service-specific tokens used by `switch`, `madre`, or `operator`.
2. **Update deployment environment variables** (production and staging) with the new values.
3. **Update local developer environments** by setting secrets in a non-tracked `.env.local` or `tokens.env` file (kept out of Git).
4. **Restart services** to ensure the new secrets are loaded.
5. **Validate**:
   - `curl -sS -i http://127.0.0.1:8000/health`
   - Authenticate via the configured token header and verify 200 responses.
6. **Invalidate old secrets** in the secrets manager and audit logs.

## Notes
- Do **not** store secrets in Git. Keep `.env*` and `tokens.env` untracked.
- Use your organization’s standard rotation cadence and incident response procedures.
