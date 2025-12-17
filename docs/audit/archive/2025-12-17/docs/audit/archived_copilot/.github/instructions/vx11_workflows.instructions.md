---
applyTo: ".github/workflows/**/*"
---
# VX11 Workflows Instructions
- No duplicar workflows. Reutiliza y ajusta los existentes.
- Añade/usa un job “dbmap_guard” cuando tenga sentido para asegurar que DB_MAP/DB_SCHEMA están actualizados.
- Evita commits automáticos desde CI salvo que ya sea política existente; prioriza “fail con instrucción de ejecutar /vx11_dbmap local”.
