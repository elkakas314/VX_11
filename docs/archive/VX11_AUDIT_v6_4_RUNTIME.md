# VX11 v6.4 – Auditoría Runtime (parcial)

Fecha: (auto) durante sesión Codex  
Estado: No completado – builds interrumpidos por timeout, contenedores incompletos.

## Resumen rápido
- `docker-compose up -d` inició pero se detuvo por timeouts de build (switch/hermes/hormiguero/otros no levantados).
- Contenedores en ejecución al momento del corte:
  - `vx11-spawner`: healthy, `/health` respondió `{"status":"ok","module":"spawner","active":0}`.
  - `vx11-mcp`: unhealthy, `/health` devolvió `auth_required` (bypass de health no efectivo).
  - `vx11-tentaculo-link`: reiniciando (no estable).
- Resto de servicios (madre, switch, hermes, hormiguero, operator-backend) no estaban levantados por build inconcluso.

## Puertos / health (curl)
- 8000: sin respuesta (tentáculo reiniciando)
- 8001/8002/8003/8004/8011: sin respuesta (servicios no activos)
- 8006 (mcp): `{"detail":"auth_required"}` → health protegido
- 8008 (spawner): OK

## Observaciones y pendientes
- Reintentar `docker-compose up -d` (build largo >120s). Puede requerir `docker-compose up --build` con más tiempo.
- Ajustar MCP para que `/health` sea realmente público (actualmente depende de auth).
- Revisar por qué tentaculo_link reinicia (logs de contenedor).
- Ejecutar validaciones previstas (switch queue, hermes list, madre plans, operator endpoints, BD schema) una vez que todos los servicios estén arriba.

## Próximos pasos sugeridos
1) Ejecutar `docker-compose up --build` con timeout amplio y verificar `docker-compose ps` hasta ver todos en healthy (excepto shub/manifestator deshabilitados).  
2) Revalidar healths: `for p in 8000 8001 8002 8003 8004 8006 8008 8011; do curl -s http://127.0.0.1:$p/health; done`.  
3) Si MCP sigue pidiendo auth en health, mover el bypass antes del dependency global o quitar dependencia en /health.  
4) Revisar logs de tentaculo_link para reinicios (`docker logs vx11-tentaculo-link`).  
5) Completar checklist de endpoints (tentáculo status/WS, operator/system, switch queue/route, hermes list/cli, madre plans, spawner spawn via MCP, BD schema).
