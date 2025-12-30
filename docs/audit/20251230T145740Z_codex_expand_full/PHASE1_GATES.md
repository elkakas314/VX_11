# PHASE 1 — Hard Gates (Production)

## Commands executed
1. `docker compose -f docker-compose.production.yml down --remove-orphans`
2. `docker compose -f docker-compose.production.yml up -d --build`
3. `curl http://127.0.0.1:8000/health`
4. `EXTRA_PORTS=0` check reference in `docs/audit/CORE_GATES_PACK.md`
5. sqlite integrity checks (skipped; DB path missing)

## Results
- Docker compose commands failed: `docker` binary unavailable in environment.
- Health check returned HTTP `000` (service not running).
- `data/runtime` directory not found → skipped sqlite integrity checks.

## Evidence
- `phase1_down.txt`
- `phase1_up.txt`
- `phase1_health_http_code.txt`
- `phase1_data_runtime_ls.txt`
- `phase1_extra_ports_rg.txt`
