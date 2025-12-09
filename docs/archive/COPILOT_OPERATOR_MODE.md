# Copilot Operator Mode v6.2 - Guía de Operación

## Estado Actual: ⏸️ DESACTIVADO

El modo operador de Copilot está **PREPARADO** pero **DESACTIVADO** en v6.2. Esta documentación define cómo funcionará cuando se active.

---

## 1. Conceptos Fundamentales

### Dos Modos de Operación

#### Modo Normal (Actual - Predeterminado)
```
Copilot → [Asistente local VS Code]
          ↓
          (NO interactúa con VX11)
          ↓
          Respuesta desde Copilot, sin contexto VX11
```

**Uso:** Ayuda general de programación, refactoring, debugging local

**Limitaciones:** No acceso a estado de VX11, tareas, engines

---

#### Modo Operador VX11 (Futuro - Requiere Activación)
```
Copilot → [Operador VX11 (preparado)]
          ↓
          [Validación + Seguridad]
          ↓
          [Bridge seguro]
          ↓
          VX11 Gateway (/vx11/chat)
          ↓
          [Respuesta contextualizada]
          ↓
          Copilot
```

**Uso:** Consultas sobre tareas, engines, status de VX11, optimización

**Limitaciones:** Solo lectura + acciones preaprobadas

---

## 2. Arquitectura del Puente

```
Copilot
   ↓
config/copilot_operator.py
   ├─ operator_mode: "disabled" | "vx11_operator"
   ├─ allowed_actions: [lista blanca]
   ├─ blocked_actions: [lista negra]
   └─ OperatorRoles: viewer | operator | admin
   ↓
config/orchestration_bridge.py
   ├─ build_operator_payload(message, context7)
   ├─ validate_operator_request(req)
   └─ safe_route_to_vx11(message, context7)
   ↓
config/copilot_bridge_validator.py
   ├─ validate_message_length
   ├─ validate_metadata_format
   ├─ validate_mode_flag
   ├─ validate_security_constraints
   └─ sanitize_payload
   ↓
gateway/main.py
   └─ /vx11/chat (cuando se active)
```

---

## 3. Payload Canónico

Cuando el modo operador esté activo, Copilot enviará:

```json
{
  "source": "copilot",
  "session_id": "uuid-del-copilot",
  "message": "What is the current status of VX11?",
  "metadata": {
    "file_path": "/home/user/project/src/main.py",
    "language_id": "python",
    "editor_context": "selection|file|edit",
    "timestamp": "2025-12-01T22:30:00Z"
  },
  "context7": {
    "layer1_user": {
      "user_id": "copilot_operator",
      "language": "en",
      "verbosity": "normal"
    },
    "layer2_session": {
      "session_id": "uuid-session",
      "channel": "copilot",
      "start_time": "2025-12-01T22:00:00Z"
    },
    "layer3_task": {
      "task_id": "copilot_query",
      "task_type": "query",
      "priority": "normal"
    },
    "layer4_environment": {
      "os": "linux",
      "vx_version": "6.2",
      "cpu_load": 0.5
    },
    "layer5_security": {
      "auth_level": "operator",
      "sandbox": true,
      "allowed_tools": [
        "vx11/status",
        "vx11/chat",
        "switch/query"
      ],
      "ip_whitelist": ["127.0.0.1"]
    },
    "layer6_history": {
      "recent_commands": ["vx11/status"],
      "successes_count": 1
    },
    "layer7_meta": {
      "explain_mode": true,
      "debug_trace": false,
      "mode": "balanced",
      "trace_id": "uuid-trace"
    }
  }
}
```

---

## 4. Restricciones de Seguridad (PERMANENTES)

### ✅ PERMITIDO (cuando operador activo)

```python
allowed_actions = [
    # Query operations (read-only)
    "vx11/status",           # Estado del gateway
    "vx11/chat",             # Chat conversacional
    "switch/query",          # Scoring de engines
    "hermes/list-engines",   # Listar engines disponibles
    "madre/get-task",        # Obtener detalles de tarea
    "hormiguero/ga/summary", # Resumen GA
    
    # Safe state changes (limitadas)
    "switch/pheromone/update",   # Actualizar feromona
    "hormiguero/ga/optimize",    # Ejecutar GA
    
    # Validation
    "vx11/validate/copilot-bridge",  # Validar puente
]
```

### ❌ BLOQUEADO (SIEMPRE - nunca se permitirá)

```python
blocked_actions = [
    # Process operations
    "spawn", "spawn_daughters", "exec", "system", "shell", "bash", "sh", "cmd",
    
    # File operations
    "delete", "rm", "mv", "cp", "rename", "chmod", "chown",
    
    # System operations
    "root", "sudo", "reboot", "shutdown", "systemctl", "docker", "kubectl",
    
    # Database operations
    "drop", "truncate", "alter", "grant", "revoke",
    
    # Network operations
    "curl", "wget", "nc", "nmap", "ssh", "telnet",
]
```

---

## 5. Validación de Requests

Todo request pasa por validación ESTRICTA:

1. **Tamaño máximo:** 16 KB (protección contra DoS)
2. **Estructura mínima:** `message` + `context7` requeridos
3. **Detección de shell:** Rechaza indicadores como `bash`, `exec`, `popen`
4. **Rutas seguras:** Rechaza `/etc/`, `/root/`, `/sys/`, `C:\`
5. **Lista negra:** Valida contra `blocked_actions`
6. **Context-7:** Debe estar presente y válido

### Ejemplo de Request VÁLIDO

```json
{
  "message": "What engines are available?",
  "context7": { ... }
}
```

### Ejemplo de Request RECHAZADO

```json
{
  "message": "bash -c 'rm -rf /'",  ← BLOQUEADO: shell command
  "context7": { ... }
}
```

```json
{
  "message": "Delete /etc/config",  ← BLOQUEADO: archivo sistema
  "context7": null  ← ERROR: context-7 falta
}
```

---

## 6. Roles y Permisos

### Rol: `viewer` (Por defecto para Copilot)

- **Lectura:** ✅ Sí
- **Escritura:** ❌ No
- **Concurrentes:** 1 operación
- **Rate limit:** 30 req/min

**Acciones permitidas:**
- `vx11/status`
- `vx11/chat` (solo queries)
- `hermes/list-engines`
- `hormiguero/ga/summary`

---

### Rol: `operator`

- **Lectura:** ✅ Sí
- **Escritura:** ✅ Sí (limitada)
- **Concurrentes:** 5 operaciones
- **Rate limit:** 100 req/min

**Acciones permitidas:**
- Todas las de `viewer` +
- `switch/pheromone/update`
- `hormiguero/ga/optimize`

---

### Rol: `admin`

- **Lectura:** ✅ Sí
- **Escritura:** ✅ Sí (completo)
- **Concurrentes:** 20 operaciones
- **Rate limit:** 300 req/min

**⚠️ NO RECOMENDADO para Copilot**

---

## 7. Estados de Activación

### Estado Actual (v6.2)

```python
# config/copilot_operator.py
operator_mode = "disabled"
```

**Efectos:**
- Copilot NO interactúa con VX11
- Validadores preparados pero no activos
- Bridge preparado pero no enruta
- Los tests están comentados

---

### Activación (Futuro)

Para activar en versiones posteriores:

```python
# config/copilot_operator.py
operator_mode = "vx11_operator"  # Cambiar esto
```

**Efectos:**
- Copilot puede enviar queries a `/vx11/chat`
- Bridge valida y enruta requests
- Logs de "operator_bridge" se generan
- Fallback a modo normal si validación falla

---

## 8. Flujo de Ejecución (cuando esté activo)

```
1. Copilot genera query
   └─ "What is the current status?"

2. Editor captura metadata
   ├─ file_path: /home/user/src/main.py
   ├─ language_id: python
   └─ editor_context: selection

3. build_operator_payload()
   └─ Construye payload canónico con context-7

4. validate_operator_request()
   ├─ Tamaño: ✓ < 16KB
   ├─ Shell commands: ✓ Ninguno detectado
   ├─ Rutas absolutas: ✓ Ninguna detectada
   ├─ Context-7: ✓ Presente y válido
   └─ → VÁLIDO

5. safe_route_to_vx11()
   ├─ Verifica is_operator_active()
   ├─ Verifica validate_operator_action()
   └─ Enruta a gateway/main.py

6. gateway enruta a madre
   └─ Retorna respuesta contextualizada

7. Copilot recibe response
   └─ Integra con sugerencias locales
```

---

## 9. Logging y Auditoría

Todos los eventos del operador se registran como `"operator_bridge"`:

```
[operator_bridge] route_attempt:mode=inactive
[operator_bridge] operator_inactive:request_rejected
[operator_bridge] validation_failed:errors=2
[operator_bridge] action_not_allowed:delete_file
[operator_bridge] safe_route_prepared:message_len=45
```

**Ubicación:** `logs/` y `forensic/operator_bridge/`

---

## 10. Instrucciones para Activar (Futuro)

### Paso 1: Editar configuración

```bash
nano config/copilot_operator.py
```

Cambiar:
```python
operator_mode = "disabled"
```

A:
```python
operator_mode = "vx11_operator"
```

### Paso 2: Verificar cambios

```bash
python3 -c "from config.copilot_operator import is_operator_active; print(is_operator_active())"
# Output: True
```

### Paso 3: Reiniciar servicios

```bash
./scripts/run_all_dev.sh
```

### Paso 4: Validar bridge

```bash
curl http://127.0.0.1:52111/vx11/validate/copilot-bridge
```

### Paso 5: Probar desde Copilot

En VS Code con Copilot:
```
@vx11 What is the current status?
```

---

## 11. Troubleshooting

### "Copilot operator mode is disabled"

**Causa:** `operator_mode = "disabled"` en copilot_operator.py

**Solución:**
```bash
# Editar config/copilot_operator.py
operator_mode = "vx11_operator"
```

---

### "Request validation failed: errors=[...]"

**Causa:** Request contenía comando bloqueado o estructura inválida

**Solución:** Revisar payload, eliminar comandos shell, incluir context-7

---

### "Action not allowed for Copilot operator"

**Causa:** Acción no está en `allowed_actions`

**Solución:** Solo queries de lectura permitidas. Contactar admin para whitelist.

---

## 12. Resumen

| Aspecto | Estado v6.2 | Estado Futuro |
|--------|-----------|--------------|
| Modo operador | ⏸️ Desactivado | ▶️ Activable |
| Archivos | Preparados | En uso |
| Validadores | Listos | Activos |
| Bridge | Estructurado | Enrutando |
| Tests | Listos | Ejecutándose |
| Seguridad | Definida | Aplicada |

---

**Versión:** 6.2  
**Estado:** Preparado - No Activo  
**Última actualización:** 2025-12-01
