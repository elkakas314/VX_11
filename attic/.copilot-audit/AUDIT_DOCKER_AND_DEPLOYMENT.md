# AUDIT: DOCKER Y DESPLIEGUE

Archivo principal inspeccionado: `/home/elkakas314/vx11/docker-compose.yml`

Resumen

El `docker-compose.yml` orquesta los módulos canónicos (tentaculo_link, madre, switch, hermes, hormiguero, manifestator, mcp, shubniggurath, spawner) y añade servicios para `operator-backend` (8011) y `operator-frontend` (8020). Las imágenes se construyen desde `operator_backend/backend/Dockerfile` y `operator_backend/frontend/Dockerfile`.

1) Topología actual (resumen)

- `operator-backend` service (8011) — build context: `operator_backend/backend/Dockerfile` — depende de `tentaculo_link` y `switch`.
- `operator-frontend` service (8020) — build context: `operator_backend/frontend/Dockerfile` — depende de `operator-backend`.
- Volúmenes: `./data:/app/data` para operator-backend; `./models:/app/models` compartido.
- Variables de entorno por servicio: tokens (VX11_*), ULTRA_LOW_MEMORY, LOG_LEVEL.

2) ¿Operator Backend está correctamente dockerizado?

- Sí: `operator_backend/backend/Dockerfile` existe y `docker-compose.yml` lo construye y publica en el puerto 8011.
- El servicio define healthcheck para `http://localhost:8011/health` y mounts correctos para `data` y `models`.

3) ¿Está duplicado? ¿Se despliega donde debe?

- No duplicado en despliegue: docker-compose usa `operator_backend` para backend y su `frontend` para la UI. Sin embargo, existe `operator/` (otro frontend) que no forma parte del build docker-compose — es un duplicado local de desarrollo.
- La decisión de desplegar desde `operator_backend/frontend` es coherente con la separación backend/frontend en un mismo módulo.

4) Volúmenes y rutas montadas

- `/data` y `/models` se montan en `operator-backend` y otros servicios. Esto es coherente para compartir modelos y runtime.
- `build/artifacts/logs` mapeado a `/app/logs` en múltiples servicios: útil para centralizar logs, pero requiere permisos y política de rotación.

5) Dockerfiles y CI

- `operator_backend/frontend/Dockerfile` y `operator_backend/backend/Dockerfile` existen.
- Revisar `Dockerfile` para asegurar que `npm ci` y `npm run build` no incluyan `node_modules` no deseados y que se use multi-stage builds para minimizar tamaño.

6) Riesgos y observaciones

- Si se mantiene `operator/` para desarrollo, el proceso de generación de imágenes debe dejar claro que la fuente canónica es `operator_backend/frontend`.
- Healthchecks y memory limits (512m) están establecidos uniformemente — verificar que `operator-backend` requiere dicho límite (Playwright/browser tasks podrían necesitar más memoria en ciertos casos).

7) Recomendaciones (sin cambios automáticos)

- Documentar en `docs/DEPLOYMENT.md` el flujo: desarrollo vs production, explicación de por qué el build usa `operator_backend/frontend`.
- Añadir CI job que buildée `operator_backend/frontend` y `operator_backend/backend` y publique imágenes con tags `vx11-operator-backend:v7.0`.
- Revisar Dockerfiles para multi-stage y remover `node_modules` de la imagen final (use npm ci && npm run build en builder stage y sólo copie `dist/` a nginx).

---
Fecha: 2025-12-14
