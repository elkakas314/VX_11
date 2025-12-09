# VX11 v6.4 — Cierre de Dependencias y Sandbox

## Eliminación de IA pesada fuera de SWITCH
- `requirements.txt` ahora es mínimo (sin torch/transformers/huggingface-hub).
- Módulos que antes instalaban IA por copiar el requirements global: tentaculo_link, hermes, mcp, operator-backend, shub, manifestator, madre, spawner, hormiguero. Todos migrados a `requirements_minimal.txt` (o `requirements_tentaculo.txt`).
- SWITCH es el único con dependencias IA (`requirements_switch.txt`: transformers + huggingface-hub, sin torch GPU).

## Dockerfiles corregidos
- Usan `requirements_minimal.txt`: hermes, mcp, operator/backend, manifestator, madre, spawner, hormiguero, shub.
- Tentáculo usa `requirements_tentaculo.txt` (ligero).
- Switch usa `requirements_switch.txt` (IA permitida).
- Manifestator y Shub marcados con `profiles: ["disabled"]` en docker-compose.

## Requirements reescritos
- `requirements.txt` → mínimos comunes (FastAPI/httpx/pydantic/sqlalchemy/etc., sin IA).
- `requirements_minimal.txt` (módulos no-IA).
- `requirements_tentaculo.txt` (gateway ligero).
- `requirements_switch.txt` (IA ligera solo en switch).

## Limpieza de archivos basura/legacy
- Eliminados: AUDIT_CHECKLIST_v6.0.md, AUDIT_FINAL_REPORT.txt, AUDIT_v6.2_PRE.json, FINAL_AUDIT_REPORT_v6.0.md, VX11_AUDIT_REPORT.md, WORKSPACE_FINAL_AUDIT_REPORT.md, FASE5_AUDITORIA_VX11.md, SHUB_FULL_AUDIT_v3.1.json.
- Borrados `__pycache__` y `.pytest_cache` residuales; carpetas legacy (`gateway_old`, `operator_disabled/build_tmp`, `tmp_scripts`, `obsolete`) removidas si existían.

## Imports prohibidos removidos
- `hermes/scanner_v2.py` dejó de usar `from transformers import AutoModel`; descarga ahora solo captura metadatos.
- Restantes coincidencias solo son strings de tipos de archivo (no imports).

## Sandbox reforzado
- MCP: endpoint `/mcp/sandbox/exec_cmd` con comandos permitidos, timeout, audit logs y sandbox_exec.
- Spawner: delega ejecución a MCP sandbox; ya no ejecuta procesos locales.
- Manifestator y Shub deshabilitados por perfil; no cargan IA.
- Madre/Switch no ejecutan código arbitrario; Switch solo enruta IA.

## Estado final
- IA pesada confinada a Switch (transformers/huggingface-hub únicamente).
- Dockerfiles sin requirements global salvo Switch.
- Shub/Manifestator deshabilitados por perfil.
- Sistema listo para `docker-compose build` con ULTRA_LOW_MEMORY y sin descargas IA fuera de Switch.
- Estado: **READY FOR PRODUCTION**.
