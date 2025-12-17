# COMPOSE_PORT_MAP_BEFORE

Generated: 2025-12-16

From `docker-compose.yml` (summary):

- tentaculo_link: container_port=8000, host_port=8000, health=/health, depends_on=null
- madre: container_port=8001, host_port=8001, health=/health, depends_on=tentaculo_link
- switch: container_port=8002, host_port=8002, health=/health, depends_on=tentaculo_link
- hermes: container_port=8003, host_port=8003, health=/health, depends_on=tentaculo_link
- hormiguero: container_port=8004, host_port=8004, health=/health, depends_on=tentaculo_link
- manifestator: container_port=8005, host_port=8005, health=/health, depends_on=tentaculo_link (profile: disabled)
- mcp: container_port=8006, host_port=8006, health=/health, depends_on=tentaculo_link
- shubniggurath: container_port=8007, host_port=8007, health: CMD-SHELL true, depends_on=tentaculo_link
- spawner: container_port=8008, host_port=8008, health=/health, depends_on=tentaculo_link
- operator-backend: container_port=8011, host_port=8011, health=/health, depends_on=tentaculo_link,switch
- operator-frontend: container_port=8020, host_port=8020, health=/ (HTTP), depends_on=operator-backend

Notes:
- `tentaculo_link` uses host port 8000 which matches canonical policy (8000–8008).
- Healthchecks call `http://localhost:<port>/health` inside container; ensure `health` endpoints exist and respond 200.
- `shubniggurath` healthcheck is a no-op (`true`) by design (profile disabled typically).

Next: compose reconciliation after gateway changes will be written to `COMPOSE_PORT_MAP_AFTER.md`.
