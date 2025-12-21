# Shubniggurath (Shub) v6.7

Motor de tareas pesadas (audio/ML) y pipeline de modelos.

## Docker (compose)

- **Puerto:** 8007
- **Health:** `GET /health` (en compose el healthcheck actual es permisivo)
- **Volúmenes:** `./models` → `/app/models`, `./data/runtime` → `/app/data/runtime`

## Rol

- Ejecuta tareas de análisis/procesamiento (p.ej. fases de Shub).
- Consume la BD unificada para registrar proyectos/tareas/eventos cuando aplica.

