# Contrato del Agente VX11 (modo cirujano)

## Regla de oro
No me preguntes entre pasos. Ejecuta en lotes.

## Solo pregunta si vas a:
1) borrar archivos (rm/rmdir) o vaciar carpetas
2) mover/renombrar fuera de docs/audit/ o fuera de la estructura canónica
3) tocar docker-compose*.yml o algo que levante/pare contenedores
4) hacer cambios masivos (muchos archivos) sin evidencia forense

## Antes de CADA acción (obligatorio)
- `pwd` y `realpath` del archivo objetivo
- `git status -sb`
- localizar y leer el DB_MAP y DB_SCHEMA "FINAL" en docs/audit (fuente de verdad)

## Evidencia / Forense (siempre)
- Todo output y reportes: `docs/audit/`
- No crees informes duplicados con nombres nuevos: actualiza los existentes
- Si haces inventario/limpieza: actualiza `docs/audit/COPILOT_CONFIG_FINAL.md`

## Limpieza
- Cero duplicados
- Si un archivo ya existe y sirve, se actualiza (no se clona)
- No meter secretos en el repo
