**SWITCH & HERMES — Production Ready**

Resumen:
- **Objetivo:** Documentar la corrección que garantiza la persistencia confiable de `ia_decisions` desde `/switch/task` y del consumidor `switch_queue_v2`, dejar el módulo listo para producción y listar verificaciones y comandos de aceptación.

Causa raíz:
- **Problema principal:** Inserciones fallidas en `ia_decisions` debido a errores de serialización/metadata y manejo silencioso de excepciones en el camino de respuesta de `/switch/task`.
- **Efecto:** Algunas llamadas devolvían `200` al cliente pero la persistencia en BD fallaba sin traza clara, por lo que el contador de decisiones no se incrementaba.

Cambios aplicados:
- **Tolerancia de serialización:** añadido manejo seguro de `meta_json` y `prompt` antes de `json.dumps` para evitar `TypeError`/`ValueError`.
- **Logging forense y fallos visibles:** se añadió `write_log(...)` en casos de éxito y logging con traceback en errores, además de `record_crash` fallback en el módulo forense.
- **Compatibilidad de contratos:** se añadió alias `cost` en `RoutingResult` y `GARouter.record_execution_result` acepta `tokens_used` (mapeado a `tokens`) para no romper clientes existentes.
- **Consumer real probado:** `switch/workers/queue_consumer.py` ejecuta `run_once()` y procesa filas de `switch_queue_v2` invocando localmente `/switch/task`.

Archivos relevantes:
- [switch/main.py](switch/main.py)
- [switch/intelligence_layer.py](switch/intelligence_layer.py)
- [switch/ga_router.py](switch/ga_router.py)
- [switch/workers/queue_consumer.py](switch/workers/queue_consumer.py)
- [scripts/fill_ia_from_switch_queue.py](scripts/fill_ia_from_switch_queue.py)

Comandos de verificación (local / entorno de desarrollo):
- **Estado DB (conteo decisiones):**
  - `python3 - <<'PY'\nimport sqlite3, os\np=os.path.join('data','runtime','vx11.db')\nconn=sqlite3.connect(p)\ncur=conn.cursor()\ncur.execute('SELECT count(*) FROM ia_decisions')\nprint(cur.fetchone()[0])\nconn.close()\nPY`
- **Probar endpoint directo:**
  - `curl -X POST http://127.0.0.1:8002/switch/task -H 'Content-Type: application/json' -H 'X-VX11-Token: vx11-local-token' -d '{"task_type":"chat","payload":{"text":"prueba persistencia ia_decision"}}'`
- **Ejecutar consumer una vez:**
  - `python3 -c "from switch.workers.queue_consumer import QueueConsumer; print(QueueConsumer().run_once())"`
- **Insertar fila de prueba en queue (sqlite):**
  - `sqlite3 data/runtime/vx11.db "INSERT INTO switch_queue_v2 (source,priority,task_type,payload_hash,payload,status,created_at) VALUES ('local',5,'chat','testhash','{}','queued',datetime('now'))"`

Evidencia (ejecución actual en repo):
- `ia_decisions` total actual: **449** (host DB `./data/runtime/vx11.db`).
- Última fila insertada en `ia_decisions` (ejemplo): id **449**, `prompt_hash` = `bb69ab706d888e59767521a5769571b4483b5e8915cadd3509c43c02c421a40f`, provider `gpt4`, task_type `approval`, timestamp `2025-12-15 19:13:51.784888`.

Pruebas de aceptación propuestas:
- Ejecutar las tres verificaciones de arriba: conteo antes, `POST /switch/task`, `QueueConsumer.run_once()`, y confirmar que el conteo aumenta.
- Correr `scripts/validate_switch_hermes_db_contract.py` para validar contrato DB y reportar discrepancias.
- Ejecutar `scripts/generate_canonical_v2.py` y adjuntar artefactos en `data/backups` como prueba de estado canonizado.

Siguientes pasos recomendados:
- Completar y revisar tests unitarios en CI (resolver dependencia/plugin `pytest` si aparece).
- Añadir un monitoreo simple que alerte si `ia_decisions` no crece tras N llamadas (podría indicar regresión silenciosa).
- Documentar en `docs/` la política de manejo de metadatos para `meta_json` (qué tipos aceptamos) y añadir ejemplos de payload aceptables.

Contacto / rollback rápido:
- Para revertir, use el historial git en la rama de trabajo (revertir commit específico que aplicó parches en `switch/`).
- Si detecta inserciones fallidas en producción, ejecutar `scripts/fill_ia_from_switch_queue.py` para backfill seguro.

Fin del documento.
