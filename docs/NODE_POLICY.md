# NODE_MODULES & JS DEPENDENCIES POLICY

Propósito

Definir reglas para el manejo de dependencias Node.js y `node_modules` en VX11.

Reglas

1. `node_modules/` nunca debe ser comiteado en el repositorio.
2. Cada paquete con `package.json` puede tener su `node_modules/` localmente para desarrollo.
3. CI debe usar `npm ci` o `pnpm install --frozen-lockfile` en cada paquete para reproducibilidad.
4. El root `package.json` sólo se usará si hay scripts globales; si no, evaluar eliminarlo.
5. Dockerfiles deben usar multi-stage builds: instalar dependencias en builder y copiar solo `dist/` al stage final.

Procedimiento de verificación

- Ejecutar `git ls-files | grep node_modules` para detectar node_modules versionados.
- Si se detecta, crear issue y PR de limpieza con backup y pasos detallados.

---
Fecha: 2025-12-14
