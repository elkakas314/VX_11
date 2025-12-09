# VX11 v6.0 — Operación Continua y Mantenimiento

**Versión:** 6.0  
**Modo:** Mantenimiento Autónomo  
**Log:** `logs/architect.log`

---

## Responsabilidades del Mantenimiento

### 1. **Diagnóstico Continuo** (automático cada ciclo)

Ejecuto verificaciones de:
- ✓ Health endpoints de los 9 módulos (8000-8008)
- ✓ Imports válidos (0 referencias a archivos legacy)
- ✓ Hardcoded ports (0 en código productivo)
- ✓ Integridad de BD unificada (36 tablas, registros válidos)
- ✓ Tests críticos (5/5 test_db_schema.py PASS)

**Indicador de fallo:** Si alguno falla, se registra en `logs/alerts.log`

### 2. **Correcciones Mínimas** (cuando se detecten issues)

Solo corrijo:
- Imports rotos → eliminar/actualizar referencia
- Endpoints faltantes → agregar al módulo correspondiente
- BD incoherencia → revisar y reparar
- Hardcodes → reemplazar con settings.PORTS
- Legacy references → eliminar (como se hizo con operador_autonomo)

**Regla:** Una línea, un cambio, una tarea = un log entry

### 3. **Sincronización Prompts ↔ Código** (auditoría continua)

Cada prompt en `prompts/` define exactamente:
- Entrada (JSON schema)
- Salida (JSON schema)
- Endpoints esperados
- Reglas de negocio
- Integraciones

El código debe implementar **exactamente** esto. Si no coincide:
1. Actualizo el código para match el prompt
2. Documento en `logs/architect.log`
3. Registro como "SYNC CORRECTION"

### 4. **Health Monitoring** (cron job ready)

Script disponible: `scripts/health_monitor.sh`

Para monitoreo automático cada 5 minutos:
```bash
*/5 * * * * cd /home/elkakas314/vx11 && ./scripts/health_monitor.sh >> logs/health_monitor.log 2>&1
```

Genera:
- `logs/health_monitor.log` → eventos de health check
- `logs/alerts.log` → solo alertas críticas

### 5. **Regeneración de Documentación** (solo si cambia arquitectura)

Regenero documentación **solo si**:
- Se añaden/remuevan módulos (no esperado)
- Cambia `settings.PORTS` estructura (improbable)
- Cambios en BD schema (improbable)

En caso normal: mantener docs.md tal como están.

---

## Estructura de Logs

### `logs/architect.log` (principal)

```
[2025-12-01T18:33:45Z] DIAGNOSTIC: Checking all module health endpoints...
[2025-12-01T18:33:45Z]   ✓ gateway:8000 → healthy
[2025-12-01T18:34:12Z] ANALYSIS: Scanning imports and hardcoded references...
[2025-12-01T18:34:12Z]   ✓ No hardcoded ports found in production code
[2025-12-01T18:35:30Z] MAINTENANCE CYCLE COMPLETE
```

**Formato:** `[ISO-8601-timestamp] EVENT: message`

### `logs/health_monitor.log` (opcional, para cron)

```
[2025-12-01T19:00:00Z] Health check cycle started
[2025-12-01T19:00:00Z]   ✓ gateway:8000
...
[2025-12-01T19:00:05Z] Health check PASSED: All 9/9 services responding
```

### `logs/alerts.log` (solo alertas)

```
[2025-12-01T19:05:00Z] ALERT: madre:8001 is not responding
[2025-12-01T19:05:05Z] ALERT: Health check FAILED: 1/9 services not responding
```

---

## Acciones Automáticas Permitidas

| Acción | Condición | Registro |
|--------|-----------|----------|
| Corregir import | Referencia legacy detectada | "IMPORT CLEANUP" |
| Eliminar hardcode | Puerto en código | "HARDCODE REMOVAL" |
| Sync prompt ↔ código | Endpoint faltante en módulo | "SYNC CORRECTION" |
| Backup BD | Cambio en schema | "BD BACKUP" |
| Restart servicio | Health check fail × 3 | "SERVICE RESTART" |
| Update test | BD schema cambió | "TEST UPDATE" |

---

## Acciones Prohibidas

❌ **NO HACER:**
- Mover/renombrar carpetas
- Crear nuevos archivos sin necesidad
- Duplicar código
- Cambiar settings.PORTS sin auditoría
- Modificar BD schema sin backup
- Crear nuevos módulos sin documentar
- Corregir "por si acaso" (solo cuando sea necesario)

---

## Estado Actual (Baseline)

**Registrado en:** `FINAL_VERIFICATION.txt`

```
Services:        9/9 ✓
DB unified:      ✓ (36 tables)
Hardcoded ports: 0 (productivo)
Legacy refs:     0
Tests passing:   5/5 BD schema
Imports:         100% valid
Docs:            Complete
```

---

## Escalabilidad (Guardrails)

Sistema diseñado para crecer sin romper:

1. **Nuevos módulos:** Usar `config/module_template.py`
2. **Nuevos puertos:** Agregar a `config/settings.py` PORTS dict
3. **Nuevas tablas:** Extender `config/db_schema.py` con SQLAlchemy
4. **Nuevo runner:** `scripts/run_all_dev.sh` tiene función `start_service()`
5. **Nuevos endpoints:** Copiar patrón de módulos existentes

---

## Checklists de Operación

### Daily Maintenance (automático)
- [ ] Health check all 9 services
- [ ] Verify no hardcoded ports
- [ ] Check BD integrity
- [ ] Run test_db_schema.py
- [ ] Log all findings

### Weekly Maintenance
- [ ] Review architect.log for patterns
- [ ] Verify prompt ↔ code sync
- [ ] Check BD backup status
- [ ] Run full pytest suite
- [ ] Update any documentation if needed

### Monthly Maintenance
- [ ] Audit entire codebase for drift
- [ ] Performance review (memory, CPU)
- [ ] Security review (no hardcoded secrets)
- [ ] Backup all DBs
- [ ] Verify deployment readiness

---

## Recuperación ante Fallo

**Si un servicio falla:**

1. Health monitor lo detecta
2. Se registra en `logs/alerts.log`
3. Revisar último estado en `logs/{service}_dev.log`
4. Reiniciar: `./scripts/run_all_dev.sh`
5. Validar health: `curl http://127.0.0.1:{port}/health`

**Si BD tiene issue:**

1. Verificar integridad: `python config/db_schema.py`
2. Si falla: restaurar backup desde `data/backups/`
3. Ejecutar migración: `python scripts/migrate_databases.py`

**Si importa falla:**

1. Buscar en codebase: `grep -r "legacy_module" --include="*.py"`
2. Remover referencia
3. Re-ejecutar pytest
4. Log el cambio

---

## Contacto y Escalation

**Sistema en crisis:**
1. Revisar `logs/architect.log` últimas 50 líneas
2. Revisar `logs/alerts.log` para patrones
3. Ejecutar diagnóstico: Ciclo de mantenimiento manual
4. Si no se resuelve: Verificar en `DEPLOYMENT_CHECKLIST.md` sección troubleshooting

---

## Autoridades y Responsabilidades

| Componente | Responsable | Log |
|------------|-------------|-----|
| Health monitoring | architect (automático) | architect.log |
| Service restart | healthmonitor.sh | health_monitor.log |
| Alerts | architect + monitor | alerts.log |
| BD maintenance | architect | architect.log |
| Code corrections | architect | architect.log |
| Docs updates | architect (solo si necesario) | architect.log |

---

**Sistema:** VX11 v6.0  
**Modo:** Operación Continua  
**Status:** ✓ Operational  
**Last Check:** 2025-12-01T18:35:30Z

Mantengase vigilante. Sistema lista para 24/7 operation.

