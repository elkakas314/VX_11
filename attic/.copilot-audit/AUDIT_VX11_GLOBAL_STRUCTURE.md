# AUDIT: VX11 — ESTRUCTURA GLOBAL

Resumen breve

Esta auditoría mapea la estructura del repo VX11, identifica duplicados, basura y zonas de mejora para permitir una reorganización controlada. No se realizan cambios — solo recomendaciones.

1) ¿Qué existe (alto nivel)

- Módulos principales en la raíz: `tentaculo_link`, `madre`, `switch`, `hermes`, `hormiguero`, `manifestator`, `mcp`, `shubniggurath`, `spawner`, `operator`, `operator_backend`.
- DB runtime en `data/runtime/vx11.db`.
- Orquestación: `docker-compose.yml` (servicios 8000..8008 + 8011 + frontend 8020).
- Dos frontends Operator: `operator/` y `operator_backend/frontend/` (duplicación relevante).
- Múltiples docs en raíz (README.md, docs/*, AUDITORIA_*). Gran cantidad de archivos de auditoría y reportes.

2) Qué está mal (síntesis)

- Duplicación de frontends: `operator/` y `operator_backend/frontend/` ambos contienen UI React/Vite. Riesgo: drift entre versiones, confusión en CI/CD y Docker builds.
- Estructura híbrida: frontend de producción (docker-compose) apunta a `operator_backend/frontend`, pero `operator/` existe como dev-sandbox. Falta claridad canónica.
- Carpeta `node_modules/` presente en varios niveles (root minimal, `operator/`, `operator_backend/frontend/`) provoca peso y contaminación del repo si se versiona por error.
- Mucha documentación legacy en la raíz (archivos `AUDITORIA_*`, `REPORTE_*`, `PLAN_*`) sin clasificación, dificulta encontrar la documentación canónica.
- Archivos temporales y builds en `build/` y `operator/dist/` pueden estar mezclados con artefactos de CI.

3) Qué está fuera de sitio

- `operator/` como carpeta independiente junto a `operator_backend/` (ambos con frontends) — provocar confusión sobre cuál es el UI canónico.
- `docs/` contiene documentación, pero hay muchos md en raíz que replican información (`RESUMEN_*`, `AUDITORIA_*`) y deberían moverse a `docs/archived/` o `docs/audit/`.
- `node_modules/` en la raíz no es típico salvo si la raíz tiene un package.json (existe package.json en root) — revisar propósito.

4) Qué sobra (candidatos)

- `operator/dist/` si es un artefacto build (debe agregarse a .gitignore si no está ya). Recomendación: no trackear dist
- Archivos `.tmp_copilot/`, `.autosync.log` y otros logs temporales deben ir a `.gitignore` o `forensic/` según política.
- Documentos duplicados: consolidar todos los `AUDITORIA_*` dispersos bajo `docs/audit/`.

5) Qué falta

- Mapa canónico: un `docs/REPO_LAYOUT.md` que indique claramente qué es canónico (servicios, frontends, dónde vivir el backend de Operator).
- Política de builds/ci: `ci/` o `scripts/` con pasos claros para construir operator frontend (dev vs prod) y para construir `operator_backend`.
- Limpieza de node_modules en CI y `.gitignore` más estricta.

6) Recomendaciones (no destructivas)

- Declarar canonical UI: elegir `operator_backend/frontend` como fuente de producción (porque docker-compose lo usa) o justificar mantener `operator/` y cambiar docker-compose.
- Consolidar docs en `docs/` y mover auditorías a `docs/audit/`.
- Añadir `CLEANUP.md` con lista de carpetas a ignorar o eliminar manualmente por el mantenedor.
- Evitar node_modules en repo (añadir reglas en `.gitignore`, limpiar repositorio si hay artefactos comiteados).


---

Fecha: 2025-12-14
Auditor: Copilot (agente de análisis)
