# VX11 Remote Megarelease Report (20251230T040512Z)

## Alcance
Núcleo solicitado:
- tentaculo_link (single entrypoint)
- madre (power manager + ventanas)
- switch/hermes (router + catálogo)
- spawner (hijas)
- operator (frontend+backend) sin bypass

## Matriz PASS/FAIL/NO_VERIFIED
| Control | Estado | Evidencia |
| --- | --- | --- |
| Single entrypoint (prod compose expone solo 8000) | PASS (config) | `docker-compose.production.yml` expone solo `8000:8000` (ver `docs/audit/20251230T040512Z_remote_megarelease/compose_ports_context.txt`). |
| Runtime default solo_madre | PASS (code) | `tentaculo_link/main_v7.py` declara `policy: solo_madre` por defecto y reporta OFF_BY_POLICY (`rg_solo_madre_endpoints.txt`). |
| OFF_BY_POLICY responde 403 JSON canónico | PASS (code) | `tentaculo_link/main_v7.py` y `operator/backend/main.py` generan 403 con payload OFF_BY_POLICY (`tentaculo_link_main_off_by_policy.txt`, `operator_backend_off_by_policy.txt`). |
| Operator NO bypass (sin llamadas a puertos internos) | PASS (scan) | `operator` no contiene `localhost:8001/8002/8003/8004/8006/8008` (`rg_operator_internal_ports.txt`). |
| Secrets versionados | PASS (after fix) | `.env*` removidos del repo; quedan solo `.env.example` y `attic/.env.example` (`env_files_after.txt`). |
| Gate: /health 200 via 8000 | NO_VERIFIED | No se ejecutó `curl http://127.0.0.1:8000/health` en este run. |
| Gate: auth 401/403 sin token, 200/403 con token | NO_VERIFIED | No se ejecutaron curls autenticados. |
| DB integrity (quick_check/integrity_check/foreign_key_check) | NO_VERIFIED | No se ejecutó `sqlite3 ... PRAGMA ...`. |
| Operator build (npm/pnpm) | NO_VERIFIED | No se ejecutó build de frontend. |

## Endpoints reales (con fuente)
### tentaculo_link
- `GET /health` — `tentaculo_link/main_v7.py:344` (`rg_health_endpoints.txt`)
- `GET /operator/power/policy/solo_madre/status` — `tentaculo_link/main_v7.py:746` (`rg_solo_madre_endpoints.txt`)
- `POST /operator/power/policy/solo_madre/apply` — `tentaculo_link/main_v7.py:758` (`rg_solo_madre_endpoints.txt`)

### madre
- `GET /health` — `madre/main.py:132` (`rg_health_endpoints.txt`)
- `POST /madre/power/policy/solo_madre/apply` — `madre/power_manager.py:998` (`rg_solo_madre_endpoints.txt`)
- `GET /madre/power/policy/solo_madre/status` — `madre/power_manager.py:1033` (`rg_solo_madre_endpoints.txt`)

### switch
- `GET /health` — `switch/main.py:759` (`rg_health_endpoints.txt`)
- `POST /switch/chat` — `switch/main.py:1432` (`switch_routes.txt`)
- `GET /switch/providers` — `switch/main.py:799` (`switch_routes.txt`)

### hermes
- `GET /health` — `switch/hermes/main.py:293` (`rg_health_endpoints.txt`)
- `POST /hermes/exec` — `switch/hermes/main.py:80` (`hermes_routes.txt`)
- `GET /hermes/catalog/summary` — `switch/hermes/main.py:609` (`hermes_routes.txt`)

### spawner
- `GET /health` — `spawner/main.py:563` (`rg_health_endpoints.txt`)
- `POST /spawner/spawn` — `spawner/main.py:766` (`spawner_routes.txt`)

### operator (backend)
- `GET /operator/api/status` — `operator/backend/main.py:300` (`operator_backend_routes_generic.txt`)
- `POST /operator/api/chat` — `operator/backend/main.py:443` (`operator_backend_routes_generic.txt`)
- `GET /operator/api/health` — `operator/backend/main.py:275` (`operator_backend_routes_generic.txt`)

## Riesgos
### P0
- **NINGUNO detectado tras fixes locales.**

### P1
- **Tokens por defecto “vx11-local-token”** en compose/código. No son secretos reales, pero deben **sobrescribirse** en producción con valores rotados. Ver `rg_vx11_local_token.txt`.

### P2
- **Gates no verificados en runtime** (health/auth/DB/build) por no ejecutar contenedores/tests en este run. Ver matriz NO_VERIFIED.

## Cambios aplicados en este run
- Eliminados `.env`, `.env.deepseek`, `.env.phase5` versionados.
- Nuevo `docs/audit/ROTATION.md` con guía de rotación sin valores.
- Operator frontend ahora usa base relativa en prod (sin URL absoluta por defecto).

## GAPS / NO_DATA
- No se ejecutó descubrimiento OpenAPI en runtime (NO_VERIFIED).
- No se levantó `docker compose` para validar gates de puertos, auth y health.
