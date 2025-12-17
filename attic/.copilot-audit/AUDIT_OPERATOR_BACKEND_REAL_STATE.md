# AUDIT: OPERATOR BACKEND — ESTADO REAL

Ruta(s) encontradas:
- `/home/elkakas314/vx11/operator_backend/backend/` (contiene `main_v7.py`, servicios, Dockerfile)
- `/home/elkakas314/vx11/operator_backend/frontend/` (UI separada)

Resumen ejecutivo

`operator_backend` contiene un backend FastAPI completo (`main_v7.py`) con múltiples endpoints: `/operator/chat`, `/operator/session/{session_id}`, `/operator/vx11/overview`, `/operator/shub/dashboard`, `/operator/resources`, `/operator/browser/task`, `/operator/tool/call`, `/operator/switch/adjustment`, `/operator/switch/feedback` y un websocket `/ws/{session_id}` stub.

1) ¿Qué existe

- `main_v7.py`: implementación FastAPI con persistencia vía `config.db_schema` (usa `OperatorSession`, `OperatorMessage`, `OperatorBrowserTask`, `OperatorToolCall`, `OperatorSwitchAdjustment`).
- Integraciones locales: `browser.py` (BrowserClient stub), `switch_integration.py` (SwitchClient), `services/` con `operator_brain.py`, `clients.py`, `model_rotator.py`.
- Dockerfiles: `operator_backend/backend/Dockerfile` y `operator_backend/Dockerfile` (ambos presentes), `operator_backend/frontend/Dockerfile` para UI.
- `operator_backend/frontend` es una UI completa con su propio build y `nginx.conf`.

2) ¿Qué endpoints existen realmente

- `/operator/chat` — implementado y persiste mensajes en BD; consulta `SwitchClient.query_chat()` para obtener respuesta.
- `/operator/session/{session_id}` — obtiene historial guardado en BD.
- `/operator/browser/task` — endpoint que crea y ejecuta tareas de browser (usa BrowserClient).
- Varios endpoints auxiliares para recursos, shub dashboard, tool call tracking, switch feedback y websocket.

3) ¿Cuáles están rotos o incompletos

- WebSocket `/ws/{session_id}` es un stub que hace echo; no hay lógica de push real.
- Operaciones que dependen de `SwitchClient` o `BrowserClient` pueden fallar si esos clientes no están configurados o si Switch no responde. Hay manejo de errores, pero falta tests de integración.
- Algunos modelos de campos en `OperatorBrowserTask` y otros objetos parecen esperar columnas que no existen en la BD actual si el esquema no contiene esas propiedades (ver diferencias entre `db_schema.py`). Requiere verificación de consistencia con `config/db_schema.py`.

4) ¿Está fuera de sitio? ¿Dónde debería vivir el backend?

- Estado actual: el backend vive en `operator_backend/backend/` y está dockerizado; `docker-compose.yml` referencia `operator-backend` con build `operator_backend/backend/Dockerfile`.
- Conclusión obligatoria: **El backend de Operator debe vivir en `operator_backend/backend/` (como está ahora).**
  - Razonamiento: separación clara entre backend y frontend; ya está dockerizado; contiene integraciones con Switch y Browser; facilita CI/CD y dependencias Python.
  - Alternativa (no recomendada): mover backend dentro de `operator/` complicaría builds, mezclando Node y Python en un subpaquete y generando confusión en Docker.

5) ¿Debería el frontend de Operator vivir dentro del backend?

- Observación: `operator_backend/frontend` ya contiene una UI preparada para producción y un `Dockerfile` que el `docker-compose.yml` usa para el servicio `operator-frontend`.
- Recomendación: mantener `operator_backend/frontend` como la UI que se publica en Docker (actual topología). Consolidar `operator/` como sandbox/dev si se desea mantener para desarrolladores.

6) ¿Qué endpoints no son usados por el frontend actual?

- Varios endpoints administrativos (`/operator/tool/call`, `/operator/switch/adjustment`, `/operator/switch/feedback`) pueden estar reservados para telemetry o integraciones internas y no necesariamente llamados por `operator/src`.
- Verificar con trazas y llamadas de `src/services/*` para confirmar consumo real. Actualmente `operator/src/services/chat-api.ts` envía al `/operator/chat` únicamente.

7) Riesgos altos detectados

- Inconsistencias entre esquema DB esperado por `main_v7.py` y `config/db_schema.py` pueden provocar fallos en runtime. (Investigar tablas y columnas mencionadas: p.ej. campos adicionales en `OperatorBrowserTask` usados en main_v7.py.)
- Duplicación de frontends genera riesgo de desplegar UI desincronizada con el backend.

8) Recomendaciones (no destructivas)

- Mantener backend en `operator_backend/backend/` (canónico). Documentar en `docs/REPO_LAYOUT.md`.
- Añadir tests end-to-end que mockeen Switch y validen `/operator/chat` happy path y error cases.
- Revisar y sincronizar modelos ORM en `config/db_schema.py` con lo que `main_v7.py` espera; añadir migraciones o notes.
- Implementar cobertura mínima para WebSocket o documentar que es stub.

---
Fecha: 2025-12-14
