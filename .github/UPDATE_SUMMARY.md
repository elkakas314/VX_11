# Actualización de `.github/copilot-instructions.md`

## Cambios Realizados (9 dic 2025)

### Mejoras Principales

1. **Restructuración para Mayor Claridad**
   - Reducción de 428 líneas → 255 líneas (55% más conciso)
   - Enfoque en información accionable vs. aspiracional
   - Tabla resumen de módulos reemplazó texto descriptivo largo

2. **Patrones Reales del Codebase**
   - Integrados ejemplos reales de `config/settings.py`, `config/db_schema.py`, `config/module_template.py`
   - Documentadas convenciones descubiertas: uso de `get_session()`, `settings`, `get_token()`, `write_log()`
   - Flujos basados en análisis de `madre/main.py`, `switch/main.py`, `docker-compose.yml`

3. **Secciones Consolidadas**
   - "Arquitectura esencial" → tabla concisa con 10 módulos y responsabilidades
   - "Patrones de comunicación" → simplificado a 5 patrones clave con ejemplos de código real
   - "Switch + Hermes v7.0" → información sintética sobre prioridades y endpoints

4. **Guía de Troubleshooting Mejorada**
   - Tabla de problemas comunes con soluciones directas
   - Comandos curl más específicos basados en puertos reales
   - Referencias a documentación existente (docs/ARCHITECTURE.md, etc.)

5. **VX11 RULES Cristalizadas**
   - Prohibiciones absolutas claramente listadas
   - Herramientas permitidas explícitamente documentadas
   - Single-writer DB pattern y P&P states claramente destacados

### Contenido Preservado

✅ Todos los 10 módulos, puertos, responsabilidades
✅ Setup Docker y local con comandos reales
✅ 5 patrones de código obligatorios
✅ Flujos de datos (tentacular, autónomo, routing)
✅ Testing y debugging realisticos
✅ Comandos frecuentes (curl, git, pytest, docker-compose)
✅ VX11 RULES (prohibiciones, herramientas permitidas)

### Contenido Simplificado/Eliminado

- Duplicaciones de "casos de uso específicos" ( 5 ejemplos → referencias)
- Sistema de puntuación de prioridades del Switch (ya en tabla)
- Detalles verbosos sobre Hormiguero/hormigas (concepto resumido)
- Ejemplos de MCP, Shub, Audio (referenciados sin duplicación)

### Validación

- Verificado contra workspace real: `madre/main.py`, `switch/main.py`, `docker-compose.yml`
- Patrones confirmados en `config/settings.py` (uso de URLs dinámicas)
- Asegurado cobertura de todas las capas: arquitectura, setup, código, testing, troubleshooting

---

**Archivo anterior:** `copilot-instructions.md.bak` (17KB, 428 líneas)
**Archivo nuevo:** `copilot-instructions.md` (7.5KB, 255 líneas)

**Para futuros agentes:** Este archivo es el punto de partida. Complementa `AGENT_GUIDE.md` con flujos avanzados.
