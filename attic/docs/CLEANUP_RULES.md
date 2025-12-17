# CLEANUP RULES (VX11) — Reglas para limpieza controlada

Principios básicos

- Ningún archivo se borra o mueve sin documento previo y aprobación humana.
- Las acciones de limpieza deben ejecutarse en seco (inventario), revisarse, aprobarse y luego ejecutarse paso-a-paso.

Reglas obligatorias

1. `node_modules/` nunca versionados
   - `node_modules/` puede existir localmente en cada paquete para desarrollo o en builder images. Debe estar en `.gitignore` en la raíz y en cada subpaquete.
   - CI debe usar `npm ci` o `pnpm install` para reproducir instalaciones.

2. `dist/`, `build/`, `.vite/`, `.cache/`, `*.log` nunca versionados
   - Artefactos de build son reproducibles y no se deben commitear.

3. Documentación canónica
   - Solo `docs/` contiene documentación canónica.
   - Archivar auditorías y snapshots en `docs/archive/`.

4. Auditorías
   - Auditorías activas (recientes) deben estar en `docs/audit/`.
   - Output generados por Copilot deben revisarse y moverse a `docs/audit/` o `docs/archive/` según aplique.

5. Archivos temporales
   - `.autosync.log`, `.tmp_copilot/`, y similares deben agregarse a `.gitignore`.

6. Proceso de limpieza
   - Inventario (FASE 1) → Revisión humana → Aprobación → Backup → Ejecución incremental en PRs pequeñas → Observación 48h → Merge final.

Checklist mínimo antes de cualquier borrado

- [ ] `docs/REPO_LAYOUT.md` presente y aprobada
- [ ] `docs/CLEANUP_RULES.md` presente
- [ ] Inventarios (node_modules, build artifacts, docs drift) generados y revisados
- [ ] Backup creado (tag o branch)
- [ ] CI verde en PR de limpieza (build y tests)

---

Fecha: 2025-12-14
