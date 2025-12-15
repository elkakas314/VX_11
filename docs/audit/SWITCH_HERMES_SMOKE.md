SWITCH + HERMES — FASE 1 Smoke Checks

Resumen rápido
- `switch/hermes/__init__.py` saneado para evitar efectos en import.
- Comprobaciones realizadas (local): compilación de paquete y verificaciones de import.

Comandos ejecutados
```
python3 -m compileall switch/hermes
python3 -c "import switch.hermes as h; print('hermes_pkg_ok', getattr(h,'CLISelector',None) is not None)"
python3 -c "from switch.main import app; print('switch_app_ok')"
pytest -q -c /dev/null  # colección de tests con configuración limpia
```

Resultados relevantes
- `python3 -m compileall switch/hermes` → no errores de sintaxis tras corrección.
- Import checks:
  - `import switch.hermes` → OK (`hermes_pkg_ok True`).
  - `from switch.main import app` → OK (`switch_app_ok`).
- `pytest` (sin `pytest.ini`) mostró muchos errores relacionados con la ausencia del plugin `pytest_timeout` en el entorno, pero NO se detectaron errores de import relacionados con `switch.hermes` o `switch.main`.

Notas
- Estado actual: FASE 1 (corrección mínima y saneamiento de imports) completada. El repo aún tiene fallos en la suite completa por dependencias de entorno de test (plugins), no por los cambios realizados a Hermes.

Archivos modificados/creados
- `switch/hermes/__init__.py` — limpio, exporta símbolos sin efectos secundarios.
- `docs/audit/SWITCH_HERMES_REALITY.md` — informe FASE 0 añadido.

Siguiente paso automático: añadir consumidor de cola minimal y tests unitarios (FASE 2/3 groundwork).
