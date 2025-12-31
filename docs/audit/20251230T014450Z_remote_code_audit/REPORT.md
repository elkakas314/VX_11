# VX11 Remote Code Audit Report (Phase 0)

Timestamp (UTC): 2025-12-30T01:44:50Z
Scope: repo scan for core modules, entrypoint routing, solo_madre policy, operator routes, correlation IDs, and secret exposure.

## Evidence bundle
All raw command outputs captured under:
- `docs/audit/20251230T014450Z_remote_code_audit/`

Key evidence files:
- `repo_top_level.txt`, `repo_top_level_dirs.txt`
- `docker-compose.yml.txt`, `docker-compose.override.yml.txt`
- `docker_compose_profiles_rg.txt`, `docker_compose_ports_rg.txt`
- `tentaculo_link_main_v7.lines.txt`
- `operator_backend_main.lines.txt`
- `operator_frontend_api.lines.txt`
- `madre_routes_power.lines.txt`, `madre_power_windows.lines.txt`, `madre_main.lines.txt`
- `operator_api_off_by_policy_rg.txt`, `madre_power_routes_rg.txt`
- `secrets_rg.txt`

## 1) Top-level modules (tree summary)
Source: `repo_top_level_dirs.txt`
- Core modules present: `tentaculo_link/`, `madre/`, `switch/` (+ `switch/hermes/`), `spawner/`, `operator/`, `hormiguero/`.
- Other modules present: `manifestator/`, `shubniggurath/`, `mcp/`.

## 2) Docker Compose profiles & external ports
Source: `docker-compose.yml.lines.txt`, `docker_compose_profiles_rg.txt`, `docker_compose_ports_rg.txt`

### Observed profiles
- `switch`, `hermes`, `hormiguero`, `mcp`, `spawner` are under `profiles: ["core"]`.
- `operator-backend` under `profiles: ["operator"]`.
- `manifestator` under `profiles: ["disabled", "maintenance"]`.

### Observed port publications (host-level exposure)
`docker-compose.yml` currently publishes:
- `tentaculo_link` → `8000:8000` (expected).
- `madre` → `8001:8001` (external exposure).
- `switch` → `8002:8002` (external exposure).
- `hermes` → `8003:8003` (external exposure).
- `hormiguero` → `8004:8004` (external exposure).
- `manifestator` → `8005:8005` (profiled but still published when enabled).
- `mcp` → `8006:8006` (external exposure).
- `spawner` → `8008:8008` (external exposure).
- `redis` → `6379:6379` (external exposure).

## 3) solo_madre policy & window controls (Madre)
Source: `madre_routes_power.lines.txt`, `madre_power_windows.lines.txt`, `madre_main.lines.txt`

### Window + policy endpoints
- `POST /madre/power/window/open`
- `POST /madre/power/window/close`
- `GET /madre/power/state`
- `POST /madre/power/policy/solo_madre/apply`
- `GET /madre/power/policy/solo_madre/status`

### Default mode
`madre/main.py` sets default `mode = "solo_madre"` in status payload logic, with heuristic to detect active services (see `madre_main.lines.txt`).

## 4) Operator routes (external via tentaculo_link)
Source: `tentaculo_link_main_v7.lines.txt`, `operator_backend_main.lines.txt`

### tentaculo_link operator proxy
- Middleware proxies `/operator/api/*` to operator backend `/api/v1/*`.
- For `/operator/api/v1/*`, upstream path becomes `/api/v1/*`.
- For `/operator/api/*` (legacy), upstream path becomes `/api/v1/*`.
- Injects/echoes `X-Correlation-Id` and enforces token guard.

### Operator backend endpoints
Defined under `/operator/api/*` and aliased to:
- `/api/v1/*` (public, documented)
- `/api/*` (legacy, hidden from schema)

Key routes include:
- `/operator/api/status`, `/operator/api/modules`, `/operator/api/topology`
- `/operator/api/chat`, `/operator/api/chat/window/open|close|status`
- `/operator/api/events`, `/operator/api/events/stream`
- `/operator/api/metrics`, `/operator/api/scorecard`
- `/operator/api/audit`, `/operator/api/audit/runs`
- `/operator/api/rails`, `/operator/api/rails/lanes`
- `/operator/api/health`, `/operator/api/healthz`

## 5) Correlation ID support
Source: `tentaculo_link_main_v7.lines.txt`, `operator_backend_main.lines.txt`
- tentaculo_link injects `X-Correlation-Id` on operator proxy responses.
- operator backend middleware accepts `X-Correlation-Id` or generates a UUID, and echoes it in JSON response payloads.

## 6) OFF_BY_POLICY response
Source: `tentaculo_link_main_v7.lines.txt`, `operator_backend_main.lines.txt`, `operator_frontend_api.lines.txt`
- tentaculo_link operator proxy returns JSON 403 with `status: OFF_BY_POLICY` on upstream failure.
- operator backend has `_off_by_policy()` helper for 403 JSON canonical payload.
- operator frontend expects `status: OFF_BY_POLICY` to surface policy message.

## 7) Secrets scan
Source: `secrets_rg.txt`
- No literal production tokens detected in the scan.
- **However** multiple files contain hardcoded default tokens such as `vx11-local-token` and `vx11-redis-local` in compose/scripts/examples.
- `.env.example` includes placeholder keys (e.g., `DEEPSEEK_API_KEY=sk-your-actual-api-key-from-deepseek-platform`).

## Risks & Findings

### P0 (must fix)
1) **Single-entrypoint violated by Docker compose port exposure**
   - `docker-compose.yml` publishes ports for `madre`, `switch`, `hermes`, `hormiguero`, `mcp`, `spawner`, and `redis`, allowing direct external access (violates invariant #1).
   - Evidence: `docker-compose.yml.lines.txt` (ports in services definitions).

2) **Default runtime exposes internal services externally**
   - Even with `solo_madre` default behavior, `madre` and `redis` are exposed on host ports by default.
   - Evidence: `docker-compose.yml.lines.txt`.

### P1 (should fix)
1) **Hardcoded default tokens in compose/scripts**
   - `docker-compose.yml` and scripts reference `vx11-local-token` and other token defaults, which conflicts with the “no secrets in repo” requirement.
   - Evidence: `secrets_rg.txt`, `docker-compose.yml.lines.txt`.

2) **Operator proxy uses fixed upstream mapping only to `/api/v1`**
   - For legacy `/operator/api/*`, the proxy maps to `/api/v1/*` (not `/api/*`). This is compatible with current aliases but should be verified if legacy `/api/*` semantics differ.
   - Evidence: `tentaculo_link_main_v7.lines.txt`.

### P2 (track)
1) **Documentation references internal ports directly**
   - Some docs mention direct access to `madre:8001` and others; should be aligned with single-entrypoint policy (if still present).
   - Evidence: `operator_api_off_by_policy_rg.txt` (docs hits).

## GAP List (file + line)

### P0
- `docker-compose.yml` publishes non-entrypoint services on host ports.
  - Example lines: `madre` port `8001:8001`, `switch` port `8002:8002`, `redis` port `6379:6379`.
  - Evidence: `docker-compose.yml.lines.txt`.

### P1
- Hardcoded default tokens in docker-compose environment entries.
  - Evidence: `docker-compose.yml.lines.txt`, `secrets_rg.txt`.

### P2
- Docs mention internal ports (potentially misleading for single-entrypoint-only policy).
  - Evidence: `operator_api_off_by_policy_rg.txt`.

## Next step (Phase 1)
Proceed to surgical fixes focusing on:
- Compose overlays/profiles to ensure only `tentaculo_link` publishes ports by default.
- Token exposure cleanup (remove hardcoded tokens, ensure env-based injection).
- Ensure operator proxy/off_by_policy behavior remains canonical.
