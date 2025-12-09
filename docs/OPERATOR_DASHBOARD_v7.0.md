# Operator Dashboard v7.0

Flujos visibles desde el frontend (8020) y backend (8011).

## Endpoints clave
- Tentáculo Link (8000): `/vx11/health-aggregate` expone health real de los módulos VX11.
- Operator backend (8011):
  - `/ui/status`: proxy a health-aggregate para la UI.
  - `/ui/events`: últimos eventos (intents/chat) en memoria.
  - `/intent/chat`: chat/mix/sistema con metadata enriquecida.
- Frontend consume:
  - `LINK_BASE_URL=http://tentaculo_link:8000`
  - `OPERATOR_BASE_URL=http://operator-backend:8011`

## Flujo
1. **Estado**: Frontend → `/ui/status` (operator-backend) → Tentáculo Link → módulos.
2. **Chat/Mix**: Frontend → `/intent/chat` (operator-backend) → Switch/Hermes → Madre/Spawner según modo.
3. **Eventos**: Frontend hace polling a `/ui/events` y WebSocket (si disponible) para listar intents recientes.

## Servicios monitorizados
- tentaculo_link, madre, switch, hermes, hormiguero, manifestator, mcp, spawner, operator-backend.

## Tokens
- Header `X-VX11-Token: vx11-local-token` en todas las llamadas internas.
