# VX11 Secrets Rotation Notice

Generated: 2025-12-30T03:31:33Z

## Summary
Detected tracked environment files containing token-like patterns and removed them from version control.

## Files Removed from Git Tracking
- `.env`
- `.env.deepseek`

## Required Actions (No Secrets Included)
1. Rotate any secrets previously stored in `.env` or `.env.deepseek`.
2. Store new secrets in your secure secret manager (Vault/CI secrets).
3. Recreate local `.env` files from `.env.example` with **real values** outside git.
4. Ensure `DEEPSEEK_API_KEY`, `VX11_TENTACULO_LINK_TOKEN`, and `VX11_GATEWAY_TOKEN` are set via env/secret manager.

## Validation
- Confirm `.env` and `.env.deepseek` remain untracked.
- Confirm `.env.example` contains placeholders only.

