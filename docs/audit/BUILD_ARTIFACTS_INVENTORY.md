# INVENTARIO: Artefactos de build y logs (solo lectura)

Comandos ejecutados:
```
find /home/elkakas314/vx11 -type d \( -name dist -o -name build -o -name .vite -o -name .cache \)
find /home/elkakas314/vx11 -type f -name "*.log"
```

Resultados (2025-12-14):

Directorios `dist` / `build` / `.vite` detectados:

- /home/elkakas314/vx11/operator_backend/frontend/dist
  - UI build (production) generado por `operator_backend/frontend`.
  - `Dockerfile` en `operator_backend/frontend` probablemente copia `dist/` a nginx stage.

- /home/elkakas314/vx11/operator/dist
  - Artefacto build de `operator/` (sandbox/dev). Reproducible.

- /home/elkakas314/vx11/build
  - Carpeta root `build/` usada por scripts de CI o artifacts. Contiene `node_modules` en su interior.

- /home/elkakas314/vx11/operator/node_modules/.vite
  - Cache de Vite local (dev).

Logs detectados (ejemplos):
- /home/elkakas314/vx11/forensic/*/logs/*.log (varios) — logs forenses por módulo (mantener)
- /home/elkakas314/vx11/.autosync.log, .copilot-audit/frontend_npm_install.log — logs operativos temporales
- /home/elkakas314/vx11/operator_backend/frontend/node_modules/react-grid-layout/yarn-error.log — error log de instalación

Recomendaciones:
- `operator_backend/frontend/dist` y `operator/dist` deben estar en `.gitignore` si no se desea versionar build artifacts.
- Mantener `forensic/*/logs` como parte del sistema forense, pero rotar y archivar logs antiguos.
- Remover `build/node_modules` del control de versión si existe; usar builder stages en Docker.

---
Fecha: 2025-12-14
