- Modo cirujano: ejecutar en lotes sin preguntar.
- Antes de tocar BD o estructura: validar DB_MAP/DB_SCHEMA FINAL en docs/audit.
- Mantener evidencias y reportes en docs/audit/.

- Antes de ejecutar flujos de cleanup/attic: cargar `docs/audit/CLEANUP_EXCLUDES_CORE.txt` y abortar si aparece un candidato CORE. Documentar el motivo en `docs/audit/`.
