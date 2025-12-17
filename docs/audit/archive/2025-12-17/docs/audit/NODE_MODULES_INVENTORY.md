# INVENTARIO: node_modules (solo lectura)

Comando ejecutado:
```
find /home/elkakas314/vx11 -type d -name node_modules
```

Resultados (2025-12-14):

- /home/elkakas314/vx11/operator_backend/frontend/node_modules
  - ¿Quién lo usa?: `operator_backend/frontend` (UI canónica para producción, Docker build)
  - `package.json` asociado: `/home/elkakas314/vx11/operator_backend/frontend/package.json` (sí)
  - ¿Está en .gitignore?: verificar manual (recomendado). Riesgo de borrado: bajo si se reconstruye con `npm ci`.

- /home/elkakas314/vx11/operator/node_modules
  - ¿Quién lo usa?: `operator/` (sandbox/dev UI)
  - `package.json` asociado: `/home/elkakas314/vx11/operator/package.json` (sí)
  - ¿Está en .gitignore?: verificar manual. Riesgo de borrado: bajo (dev rebuildable).

- /home/elkakas314/vx11/build/node_modules
  - ¿Quién lo usa?: artefactos build; posiblemente residuo de scripts de build
  - `package.json` asociado: revisar `build/` (posible builder env). Riesgo: medio — confirmar antes de borrar.

- /home/elkakas314/vx11/node_modules
  - ¿Quién lo usa?: raíz `package.json` (si existe). Riesgo: medio — confirmar si root package.json necesita deps.

- Varias subcarpetas `node_modules` dentro de `operator_backend/frontend/node_modules/*/node_modules` (resolución de paquetes). Son dependencias internas y no se tocan.

Recomendación:
- No borrar nada automáticamente. Añadir a `.gitignore` si falta. Ejecutar `git ls-files | grep node_modules` para detectar si algo está versionado.
- Documentar en `docs/NODE_POLICY.md` (siguiente paso).

---
Fecha: 2025-12-14
