Auditoría FASE 0 — Switch & Hermes (Realidad del repositorio)

Resumen corto
- Objetivo: mapear código de `Switch` y `Hermes`, detectar duplicados/errores y proponer ubicación canónica para `Hermes` antes de cualquier refactor.
- Recomendación inmediata: mantener `Hermes` como `switch/hermes/` (mínimo cambio) y corregir `switch/hermes/__init__.py` que actualmente contiene un fence de código y rompe importaciones. Migración a top-level `hermes/` sólo si se acepta refactor mayor.

Hallazgos

- Ubicaciones encontradas:
  - `switch/` — implementación completa del Switch (router IA). Archivo principal: `switch/main.py`.
  - `switch/hermes/` — implementación de Hermes (módulos: `cli_selector.py`, `cli_metrics.py`, `cli_registry.py`, `hermes_core.py`, `hf_scanner.py`, `local_scanner.py`, etc.).
  - `config/db_schema.py` — tablas unificadas referenciadas por Switch/Hermes (`model_registry`, `cli_registry`, `switch_queue_v2`, `ia_decisions`, `model_usage_stats`).

- Import / runtime issues detectadas:
  - `switch/hermes/__init__.py` contiene delimitadores de bloque de código (```python) y no es un módulo Python válido. Esto causa fallos de import (por ejemplo, `from switch.hermes import CLISelector` fallará si se ejecuta el paquete). Reproducible abriendo `switch/hermes/__init__.py`.
  - `switch/main.py` importa `switch.hermes` y depende de clases `CLISelector`, `CLIFusion`, `ExecutionMode` y `get_metrics_collector` — por lo tanto la importación rota impacta el startup de Switch.
  - No se detectaron otras copias evidentes de la lógica de Hermes en otros directorios; la implementación principal vive bajo `switch/hermes/`.

Consumo de colas / tablas
- `switch/main.py` usa `TaskQueue` (tabla `task_queue`) como cola persistente; también actualiza `SystemState` y lee `ModelRegistry` y `CLIRegistry`.
- `config/db_schema.py` expone la tabla `switch_queue_v2` en el esquema unificado y existen referencias en docs y backups (canónico extraído). No se halló código separado que actúe como consumidor alternativo de `switch_queue_v2` fuera de `switch/`.

Riesgos y prioridades
- R1 (alta): `switch/hermes/__init__.py` rompe imports → impide iniciar `switch` y cualquier módulo que dependa de `hermes`.
- R2 (media): Si se decide mover `hermes/` a top-level habrá que actualizar imports (`from switch.hermes import ...` → `from hermes import ...`), `docker-compose` (dependencias/healthchecks) y rutas de configuración (`settings.hermes_url`) — es un refactor mayor.
- R3 (baja): Posible limpieza/normalización de nombres y exports en `switch/hermes/` (p. ej. `ExecutionPlan` vs `ExecutionMode`) para consistencia.

Recomendación (única y priorizada)
- Mantener `Hermes` en su ubicación actual: `switch/hermes/`.
  - Motivos: mínima superficie de cambio, Switch ya importa desde `switch.hermes`, la base de código está agrupada; moverlo requeriría actualizar muchos imports y Docker/configs.
  - Acción inmediata requerida: corregir `switch/hermes/__init__.py` para que exporte correctamente símbolos (quitar fences ``` y dejar el listado de imports/ __all__ estándar). Esta corrección es de bajo riesgo y reversible.

Pasos siguientes sugeridos (desplegables)
1. Corregir `switch/hermes/__init__.py` (Quitar los fences y asegurar que las importaciones referenciadas existen). Test: `python -c "import switch.hermes; print(dir(switch.hermes))"`.
2. Ejecutar `python -m switch.main` o levantar el contenedor `switch` en entorno dev y validar `/health` y endpoints `/switch/*`.
3. Después de pasar FASE 0, si se decide un refactor mayor, planear: mover `switch/hermes/` → top-level `hermes/` en una sola PR con scripts de reemplazo de imports y actualización de `docker-compose.yml` + tests.

Evidencia mínima (paths)
- Código Switch: [switch/main.py](switch/main.py)
- Hermes package: [switch/hermes/__init__.py](switch/hermes/__init__.py)
- Hermes selector: [switch/hermes/cli_selector.py](switch/hermes/cli_selector.py)
- Hermes metrics: [switch/hermes/cli_metrics.py](switch/hermes/cli_metrics.py)
- DB schema: [config/db_schema.py](config/db_schema.py)
- Canónico (extractor outputs): `data/backups/vx11_CANONICAL_STATE.json`, `data/backups/canonical.table_catalog.json.new`

Si quieres, aplico el cambio mínimo ahora (editar `switch/hermes/__init__.py` removiendo los fences y dejando las imports limpias) y ejecuto la verificación local. Confírmame si procedo con esa corrección y la posterior prueba de arranque del módulo `switch`.
