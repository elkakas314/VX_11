---
name: vx11_dbmap
description: "VX11: Ejecuta DBMAP (rotate backups, integrity check, regenerate docs/audit, tests)."
agent: "VX11 Builder"
tools: ["search/codebase"]
---
Eres VX11 Builder. Ejecuta el flujo DBMAP usando el runner existente.

Pasos:
1) Confirmar root (pwd/ls) + git status.
2) Abrir y leer scripts/vx11_workflow_runner.py para confirmar el comando exacto DBMAP.
3) Ejecutar DBMAP con ese comando.
4) Verificar que se han regenerado docs/audit/DB_MAP* y docs/audit/DB_SCHEMA* (y META si aplica).
5) Ejecutar tests mínimos existentes (pytest o el runner si lo integra).
6) Dejar el repo limpio: sin basura, sin duplicados. Reportar cambios: lista de archivos tocados + comandos ejecutados + resultado final.
