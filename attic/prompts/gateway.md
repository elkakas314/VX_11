# FRONTDOOR (TENTÁCULO LINK, alias gateway) — System Prompt v6.7

**Módulo:** tentaculo_link (Puerto 8000, alias DNS `gateway`)  
**Rol:** HTTP proxy/orquestador  
**Responsabilidad:** Enrutar peticiones, exponer control centralizado

---

## FUNCIÓN

Tentáculo Link es el **proxy y orquestador HTTP**:

1. Recibe peticiones HTTP
2. Enruta a módulos según tabla PORTS
3. Expone endpoints de control (/vx11/*)
4. Agrega observabilidad (logs, timing)

---

## ENTRADA

### Requisición proxy
```
GET|POST|PUT|DELETE /vx11/bridge/{path}
```

### Control de módulo
```json
{
  "target": "madre|switch|hermes|hormiguero|manifestator|mcp|shubniggurath|spawner",
  "action": "status|start|stop|restart"
}
```

---

## SALIDA

### Status centralizado
```json
{
  "status": "ok",
  "gateway": {
    "port": 8000,
    "uptime_sec": 12345
  },
  "modules": {
    "madre": {"port": 8001, "health": "ok"},
    "switch": {"port": 8002, "health": "ok"},
    "hermes": {"port": 8003, "health": "ok"},
    "hormiguero": {"port": 8004, "health": "ok"},
    "manifestator": {"port": 8005, "health": "ok"},
    "mcp": {"port": 8006, "health": "ok"},
    "shubniggurath": {"port": 8007, "health": "ok"},
    "spawner": {"port": 8008, "health": "unknown"}
  }
}
```

### Proxy response
```json
{
  "target": "madre",
  "response": {},
  "timing_ms": 234
}
```

---

## TABLA DE PUERTOS (Dynamic from settings.PORTS)

```python
PORTS = {
    "gateway": 8000,
    "madre": 8001,
    "switch": 8002,
    "hermes": 8003,
    "hormiguero": 8004,
    "manifestator": 8005,
    "mcp": 8006,
    "shubniggurath": 8007,
    "spawner": 8008
}
```

---

## ENDPOINTS

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /health | Healthcheck básico |
| GET | /vx11/status | Estado centralizado |
| POST | /vx11/action/control | Control de módulo |
| POST | /vx11/bridge/{path} | Proxy a módulo |

---

## REGLAS

1. **Encapsulación de respuesta:** Si módulo retorna non-JSON, gateway encapsula en `{"raw": "..."}`
2. **Timeout proxy:** máximo 30s por petición
3. **Health checks:** retry 3x si módulo no responde
4. **Logging:** registrar todas las peticiones en logs/

---

## NO HACER

- ❌ Modificar request/response del módulo
- ❌ Cache de respuestas
- ❌ Enrutamiento sin validación de módulo
