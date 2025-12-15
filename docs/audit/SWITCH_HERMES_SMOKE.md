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

## Docker build (2025-12-15) — Resultado

Resumen: intento de `docker-compose build switch` falló durante la fase de COPY.

Extracto relevante del log:

```
COPY sitecustomize.py /app/
COPY failed: file not found in build context or excluded by .dockerignore: stat sitecustomize.py: file does not exist
ERROR: Service 'switch' failed to build : Build failed
```

Impacto: el build no finalizó; por eso no se pudo levantar el servicio `switch` para comprobar `/health`.

Próximos pasos sugeridos:
- Verificar que `sitecustomize.py` está presente en el contexto de build y no está excluido por `.dockerignore`.
- Ajustar `docker-compose.yml` o `Dockerfile` si la ruta esperada difiere del layout del repo.
- Reintentar `docker-compose build switch` una vez corregido.

Acciones inmediatas: revisaré `sitecustomize.py` y `.dockerignore` en el repositorio.

## Rebuild tras corrección (.dockerignore) — 2025-12-15

Acción: eliminé `sitecustomize.py` de `.dockerignore` para incluirlo en el contexto de build, luego ejecuté `docker-compose build switch`.

Resultados:

- El build de la imagen `vx11-switch` finalizó correctamente y la imagen fue etiquetada como `vx11-switch:v6.7`.
- `docker-compose up` falló al recrear el servicio por un error interno de `docker-compose` ('ContainerConfig'). Para sortearlo, arranqué la imagen directamente con `docker run`.

Respuesta `/health` obtenida (JSON):

```
{"status":"ok","module":"switch","active_model":"general-7b","warm_model":"audio-engineering","queue_size":0}
```

Observaciones:
- El servicio Uvicorn arrancó y respondió el endpoint `/health` correctamente.
- En los logs se observan repetidos intentos de conexión a proveedores locales/CLIs (`local_gguf_small`, `ollama_local`, `deepseek_r1`, `cli_registry`) que fallaron con "All connection attempts failed" — esto es esperado en un entorno de CI/local sin providers configurados y no impide que `/health` responda.

Próximo paso recomendado: investigar y ajustar la integración con los proveedores locales (o mockearlos en pruebas) y reintentar `docker-compose up` (o migrar a `docker compose` con buildx si se prefiere BuildKit más moderno).
\
Acción tomada: habilité modo mock (`VX11_MOCK_PROVIDERS=1`) para evitar llamadas de red en warm-up y reconstruí/ejecuté la imagen.

Resultados posteriores:

- Contenedor `vx11-switch-mock` arrancó correctamente con `VX11_MOCK_PROVIDERS=1`.
- `/health` respondió: `{"status":"ok","module":"switch","active_model":"general-7b","warm_model":"audio-engineering","queue_size":0}`.

Notas: el mock reduce ruido en logs y evita fallos por proveedores no configurados; es adecuado para pruebas locales y CI. Para producción, desactivar `VX11_MOCK_PROVIDERS` y asegurar proveedores accesibles.

