# Archived: operator_backend (2025-12-28)

## Decision
**ARCHIVED AND REMOVED** — operator_backend service is UNUSED and INACTIVE in production.

## Audit Findings
- **Active Operators**: tentaculo_link:8000 (single entrypoint)
- **operator_backend References**: Only in docker-compose.yml (profile="operator", OFF-by-default)
- **Code References**: None in active codebase
- **Dependencies**: operator_backend service does NOT proxy to tentaculo_link; independent HTTP server
- **Single Entrypoint Invariant**: Operator UI now served via tentaculo_link:8000/operator/ui/ (StaticFiles mount)

## Changes
1. Archived full operator_backend tree to: docs/audit/ARCHIVED_OPERATOR_BACKEND_20251228_170000/
2. Removed from docker-compose.yml (service + profile)
3. Removed operator_backend/ folder from repository

## Rationale
- UI is now statically served via tentaculo_link (single entrypoint)
- No loss of functionality (UI + API routing centralized)
- Reduced complexity: 1 service (tentaculo_link) instead of 2
- Maintains SOLO_MADRE_CORE invariant (only madre + tentaculo_link required)

## Verification
```bash
# Confirm removal
ls -la operator_backend/  # Should return: No such file or directory

# Confirm UI still works
curl http://localhost:8000/operator/ui/  # 200 HTML
```

## Artifacts
- Timestamp: 2025-12-28 17:00 UTC
- Commit: [see commit message]
- Evidence: This file + operator_backend tree snapshot
