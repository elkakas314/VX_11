# VX11 Token Rotation Log

## 2025-12-30
- Untracked local `.env`, `.env.deepseek`, and `.env.phase5` files from Git.
- Confirmed `.env` files are ignored via `.gitignore`.
- Reminder: rotate any developer-local tokens stored in untracked env files before production use.

## Procedure (summary)
1. Move secrets to local-only `.env` or secret store (never commit).
2. Rotate provider tokens in the vendor console.
3. Update local `.env` values and redeploy affected services.
4. Record rotation date + scope in this file.
