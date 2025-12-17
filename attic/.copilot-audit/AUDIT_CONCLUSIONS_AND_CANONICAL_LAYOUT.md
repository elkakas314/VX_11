# AUDIT: CONCLUSIONES Y LAYOUT CANÓNICO PROPUESTO

Objetivo: presentar conclusiones consolidando hallazgos y proponer layout canónico del repo para la Fase de reorganización controlada.

1) Conclusión corta

- El backend de Operator está correctamente ubicado en `operator_backend/backend/` y debe permanecer allí.
- El frontend de producción que se usa en Docker es `operator_backend/frontend/` — se recomienda designarlo como `frontend canónico en producción`.
- La carpeta `operator/` actualmente actúa como sandbox/dev. Decidir: conservar como "dev only" o consolidar en `operator_backend/frontend/`.

2) Layout canónico propuesto (sin mover archivos automáticamente)

```
/ (repo root)
├─ operator_backend/
│  ├─ backend/                # FastAPI operator backend (CANONICAL)
│  └─ frontend/               # Operator frontend (PRODUCTION build) (CANONICAL)
├─ tentaculo_link/
├─ madre/
├─ switch/
├─ hermes/
├─ hormiguero/
├─ manifestator/
├─ mcp/
├─ shubniggurath/
├─ spawner/
├─ docs/                     # Documentación canónica
│  ├─ architecture.md
│  ├─ api_reference.md
│  └─ audit/                  # Auditorías consolidadas
├─ scripts/                   # Build, cleanup, CI helpers
├─ data/                      # runtime DB, models (volumes)
└─ .copilot-audit/            # Auditorías generadas por Copilot (review)
```

3) Acciones recomendadas (fases, no automatizar)

Fase 0 — Preparación (solo documentos)
- Crear `docs/REPO_LAYOUT.md` y `docs/CLEANUP.md`.
- Decidir frontend canónico (documentar decisión).

Fase 1 — Limpieza (manual supervisado)
- Archivar o mover (manual) los md legacy a `docs/archive/`.
- Eliminar `dist/` y `node_modules/` local de control de versiones si se incluyen en git.

Fase 2 — Reorganización controlada
- Si se consolida `operator/` dentro de `operator_backend/frontend/`, plan de migración: copiar, validar, CI y luego eliminar `operator/` con PR y periodo de observación.

Fase 3 — Validación y CI
- Añadir jobs CI para build frontend (desde `operator_backend/frontend`) y backend.
- Tests e2e: mock Switch para `/operator/chat`.

4) Riesgos y puntos de parada

- Riesgo alto: manipular `node_modules` versionados o borrar artefactos sin validar CI.
- Procedimiento: si detectas `node_modules` tracked por git — STOP, documentar y coordinar PR de limpieza.

---
Fecha: 2025-12-14
