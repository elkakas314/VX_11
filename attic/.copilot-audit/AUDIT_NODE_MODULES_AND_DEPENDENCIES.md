# AUDIT: node_modules Y DEPENDENCIAS

Objetivo: listar y justificar cada `node_modules` presente, evaluar impacto y proponer acciones de limpieza.

1) Ubicaciones encontradas

- `/home/elkakas314/vx11/node_modules` — raíz
- `/home/elkakas314/vx11/operator/node_modules` — frontend developer
- `/home/elkakas314/vx11/operator_backend/frontend/node_modules` — backend-frontend build/dev

2) Por qué existen

- `operator/node_modules`: contiene dependencias del frontend `operator/` (React, Vite, plugins). Es necesario para desarrollo local y `npm run dev` allí.
- `operator_backend/frontend/node_modules`: contiene dependencias del UI integrado con `operator_backend` (probablemente la versión canónica usada por Dockerfile en `operator_backend/frontend`). Es necesario para build/provisión del contenedor `operator-frontend`.
- `node_modules` en la raíz: muy pequeño (solo `@types/` y `csstype/` listados). Probablemente creado por un `npm install` en la raíz (hay un `package.json` en la raíz). Puede ser necesario si la raíz define herramientas JS/mono-repo scripts; sin embargo actualmente la raíz `package.json` existe y podría justificar este `node_modules`.

3) Quién usa cada uno

- `operator/node_modules`: desarrolladores que trabajan en `operator/` (dev server, vite).
- `operator_backend/frontend/node_modules`: CI/CD y Docker build para `operator-frontend` (build step `npm run build` en `operator_backend/frontend`).
- raíz `node_modules`: scripts en la raíz (si existen) o residuo de instalación global; revisar `package.json` en la raíz para confirmar.

4) ¿Están bien ubicadas?

- Sí para `operator/` y `operator_backend/frontend/` si ambos frontends se mantienen. Preferible: un único frontend canónico para evitar duplicación.
- Raíz: revisar si `package.json` necesita dependencias; si no, borrar `node_modules` en la raíz (local dev) y añadir `node_modules/` a `.gitignore` (si no está).

5) ¿Deben eliminarse o moverse?

- Eliminar de control de versiones: todos `node_modules` deben ignorarse. Si hay paquetes comiteados por error, deben limpiarse (manual).
- Consolidación recomendada: elegir un frontend canónico y mantener `node_modules` solo en ese paquete para builds; o usar root monorepo (pnpm/workspaces) si se desea multi-frontend gestionado.

6) ¿Están contaminando el repo?

- Posible: si `node_modules` fue comiteado en algún lugar o si `dist/`/`build/` contenga artefactos. Actualmente `operator/node_modules` y `operator_backend/frontend/node_modules` existen localmente (no indica si se cometieron). Revisar `.gitignore` y `git status` para confirmar no tracked.

7) Recomendaciones (acciones propuestas)

- Verificar con `git ls-files | grep node_modules` si se versionó. Si hay archivos `node_modules/` en git, plan de limpieza (borrar y reescribir historial si necesario).
- Añadir reglas claras en `.gitignore` en la raíz:
  - `/operator/node_modules/`
  - `/operator_backend/frontend/node_modules/`
  - `/node_modules/`
  - `/operator/dist/` (artefactos de build)
- Documentar en `docs/CLEANUP.md` el procedimiento: `rm -rf` local, `npm ci` en cada paquete, CI limpio y caching por carpeta.

---
Fecha: 2025-12-14
