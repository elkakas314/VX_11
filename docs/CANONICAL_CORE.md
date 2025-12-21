Canonical core modules

- `switch/` (includes `switch/hermes/`)
- `tentaculo_link/`
- `madre/`
- `mcp/`
- `data/runtime/` (runtime DB; DO NOT DELETE)

Levantar core (por defecto):

- En entorno con Docker Compose v2/`docker compose`:
  - `docker compose up -d --build`  # bring core services (non-core marked with profile "full")

Levantar todo (perfil full):

- `docker compose --profile full up -d --build`

Notas:
- Non-core services are marked with `profiles: ["full"]` in `docker-compose.override.yml`.
- `operator*` code has been archived to `attic/` to avoid stdlib collisions.
