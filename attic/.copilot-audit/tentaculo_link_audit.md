# Auditoría Técnica: Tentáculo Link v7.0

## Resumen Ejecutivo

**Tentáculo Link** es el gateway central de VX11 que actúa como proxy autenticado, orquestador de rutas y centro de contexto. Expone ~12 endpoints HTTP + 1 WS (stub), autentica con `X-VX11-Token` header, aplica rate-limiting en memoria y maneja el seguimiento de sesiones CONTEXT-7 sin IA. Todos los módulos internos se conectan vía HTTP async con fallback a DNS hostname (no hardcoded localhost).

## Flujo de Conexión

```
Frontend (Operator React)
  → VITE_OPERATOR_BASE_URL=http://operator_backend:8011 (/operator/chat, /operator/system/status, etc.)
  → VITE_LINK_BASE_URL=http://tentaculo_link:8000 (agregación de estado /vx11/status)
  ↓
Tentáculo Link (Gateway 8000)
  ├─ Auth Guard (X-VX11-Token header)
  ├─ Rate Limiter (60 req/min per key)
  ├─ CONTEXT-7 Middleware (session tracking, no IA)
  ├─ Async HTTP Clients (madre, switch, hermes, hormiguero, mcp, shub, spawner, operator)
  ↓
Backend Modules (porta 8001-8008, 8011)
  └─ DB (SQLite single-writer: data/runtime/vx11.db)
```

## Endpoints Críticos

### Autenticación y Estado
- **GET `/health`** — Sin auth. Health check simple. Respuesta: `{"status":"ok","module":"tentaculo_link","version":"7.0"}`
- **GET `/vx11/status`** — Con auth. Agregación paralela de salud de todos los módulos. Incluye ports, module names, resumen de healthy/unhealthy.

### Chat y Operador
- **POST `/vx11/operator/chat`** — Con auth. Chat unificado con CONTEXT-7 tracking. Ruta interna a madre:8001 `/madre/chat`.
  - Request: `{message, session_id, user_id, metadata}`
  - Mantiene historial de conversación en CONTEXT-7 (BD SQLite)
- **POST `/operator/chat`** — Alias legacy para `/vx11/operator/chat`
- **GET `/operator/session/{session_id}`** — Recupera historial CONTEXT-7 de una sesión.

### Intents y DSL
- **POST `/vx11/intent`** — Ruta de intents estructurados (VX11::TASK, VX11::QUERY, VX11::DIAGNOSTIC, VX11::CLEANUP) hacia Madre para planificación.
- **POST `/vx11/dsl`** — Proxy DSL (texto natural) hacia Madre (/madre/dsl).

### Agregación y Recursos
- **GET `/vx11/overview`** — Resumen agregado de módulos (health, summary, counts).
- **GET `/resources`** — Recursos Hermes (CLI tools + local models).
- **GET `/shub/dashboard`** — Info Shub (audio).

### Hormiguero (Incidentes)
- **GET `/hormiguero/queen/status`** — Estado de la reina Hormiguero.
- **GET `/hormiguero/report`** — Reporte de incidentes recientes (limit param).

### WebSocket (Stub)
- **WebSocket `/ws`** — Real-time updates (actual WS usado por Operator es en operator_backend:8011).
  - Emite heartbeats + echo de mensajes.
  - Client ID via query param (default: "anonymous").

## Patrones Críticos Observados

### ✅ Fortalezas
1. **Sin hardcoding de localhost** — Usa `settings.madre_url or f"http://madre:{settings.madre_port}"` para URLs internas.
2. **Token resolution centralizado** — `config.tokens.load_tokens()` + fallback a env vars.
3. **Async HTTP clients** — Una sesión per módulo, reutilizable, error handling.
4. **Rate limiting in-memory** — RateLimiter por IP/user_id (60 req/min default).
5. **CONTEXT-7 sessions** — Ligero (sin IA), solo tracker de mensajes + DB.
6. **Forensics logging** — `write_log()` para auditoría de operaciones.

### ⚠️ Puntos de Atención
1. **WS endpoint (/ws) es un stub** — No debería ser usado por frontend en producción; el WS real está en operator_backend:8011.
2. **Rate limiting en memoria** — Si se reinicia tentaculo_link, se pierde historial de rate-limit. Considerar Redis en producción.
3. **CORS habilitado ampliamente** — `allow_origins=settings.allowed_origins, allow_methods=["*"]`. Revisar whitelist en settings.py.
4. **No TLS/mTLS entre módulos** — HTTP plain text en docker network (aceptable en local, pero considerar WSS/TLS en producción).
5. **Session history sin límite temporal** — CONTEXT-7 mantiene máximo 50 msgs por sesión, pero sesiones nunca se expiran. Considerar TTL.

## Recomendaciones para Centralización y Refuerzo

### Fase 1: Seguridad Inmediata
1. **Rotar VX11_GATEWAY_TOKEN** a valor aleatorio (no hardcoded "vx11-local-token") en producción.
2. **Validar allowed_origins** en settings.py — debe ser lista explícita de dominios (no `["*"]`).
3. **Implementar WSS (WebSocket Secure)** si tentaculo_link se expone públicamente.
4. **Añadir X-Request-ID** header para trazabilidad en logs.

### Fase 2: Escalabilidad
1. **Migrar RateLimiter a Redis** para persistencia y distribución (si hay múltiples instancias).
2. **Implementar circuit breaker** en ModuleClient para fallos cascada (ej: madre no responde → fallback response).
3. **Cachear /vx11/status** por 5s (agregación paralela puede ser costosa).

### Fase 3: Convergencia de Rutas
1. **Unificar prefijos de endpoint** — Actualmente mezcla `/vx11/*`, `/operator/*`, `/shub/*`, `/hormiguero/*`. Proponer: `/api/v1/*` como base única.
2. **Centralizar routing logic** — Crear router table (intent_type → endpoint mapping) para evitar hardcoding en main_v7.py.
3. **Session affinity** — Si Tentáculo Link se replica, necesita sticky sessions o session store en Redis.

### Fase 4: Observabilidad
1. **Métricas Prometheus** — Latencia por módulo, error rates, RPS.
2. **Tracing distribuido (Jaeger/Zipkin)** — Seguir request desde frontend → tentaculo → madre → spawner.
3. **Alertas** — Si módulo no responde en 5s, disparar alerta.

## Archivos Relacionados (Orden de Inspección)

1. **config/settings.py** — Fuente de verdad para URLs, ports, tokens, allowed_origins.
2. **config/tokens.py** — Carga env vars, resolución de tokens.
3. **config/db_schema.py** — ORM + session management.
4. **config/forensics.py** — Logging y auditoría.
5. **operator_backend/frontend/src/config.ts** — Constantes frontend (OPERATOR_BASE_URL, LINK_BASE_URL, WS_BASE_URL).
6. **operator_backend/frontend/src/services/api.ts** — Cliente HTTP frontend.
7. **docker-compose.yml** — Configuración servicios, ports, networks.

## Impacto en Frontend

El frontend (Operator) asume:
- **OPERATOR_BASE_URL** apunta a operator_backend:8011 (NO a tentaculo_link).
- Usa tentaculo_link:8000 SOLO para `/vx11/status` (agregación health).
- WS real es operator_backend:8011/ws (tentaculo /ws es ignorado).

**Implicación:** Cambios en tentaculo_link routing NO afectan frontend operacional directo, salvo que cambies `/vx11/status` contract.

## Checklist de Validación Pre-Refactor

- [ ] Todos los endpoints en /vx11/* requieren X-VX11-Token auth.
- [ ] Rate limit por IP/user_id funciona en stress test.
- [ ] CONTEXT-7 sessions persisten en BD.
- [ ] Fallback en ModuleClient para módulos offline (circuit breaker).
- [ ] Logs forensics registran todas las rutas proxy.
- [ ] CORS whitelist es explícito (no `["*"]`).
- [ ] WSS disponible en producción.
- [ ] Documentación de contrato HTTP actualizada (OpenAPI/Swagger recomendado).

## Conclusión

Tentáculo Link es un proxy robusto pero minimalista. Principales mejoras:
1. **Seguridad**: WSS, mTLS, token rotation.
2. **Escalabilidad**: Redis para session/rate-limit store, circuit breaker, caching.
3. **Convergencia**: Router table centralizado, prefijos unificados.
4. **Observabilidad**: Prometheus + Jaeger.

El refactor es viable sin breaking changes si mantienes compatibilidad con contratos HTTP existentes.
