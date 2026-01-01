# VX11 CORE WIRING — FASE B: CABLEADO VERIFICADO + GAPS

**Fecha**: 2026-01-01T04:30:38Z  
**Ingeniero**: Copilot (paranoico)  
**Estado**: PHASE B COMPLETE (Verificado, identificadas brechas)

---

## HALLAZGOS CRÍTICOS

### ✅ CORE OPERATIVO: tentaculo_link → madre (fallback)

```
POST /operator/chat
  ↓ (token: vx11-test-token)
  ↓ clients.route_to_switch() → FALLA (switch offline en solo_madre)
  ↓ FALLBACK: clients.route_to_madre_chat() → EXITOSO
  ↓
MADRE /madre/chat
  ↓ FallbackParser.parse(message) → genera plan MADRE
  ↓ Planner genera steps
  ↓
RESPUESTA 200 OK con payload útil
```

**Evidencia real**:
```json
{
  "response": "Plan executed. Mode: MADRE. Status: DONE",
  "session_id": "1f5ca9af-fb3b-4d6b-9481-df1e62a631a0",
  "status": "DONE",
  "mode": "MADRE",
  "provider": "fallback_local",
  "warnings": []
}
```

---

### ✅ DEFAULT SOLO_MADRE FUNCIONA

Sin intervención:
- `/operator/chat` NO devuelve "connection refused" opaco
- Devuelve 200 OK con respuesta útil (fallback a madre)
- **Policy está implementada**: Switch offline por defecto

---

### ❌ GAP-1: ENDPOINTS POWER WINDOWS EN TENTACULO_LINK

**Estado**: NO IMPLEMENTADO

- `POST /operator/power/window/open` → 404 Not Found
- `POST /operator/power/window/close` → 404 Not Found  
- Existe en `/api/window/*` (rutas incluidas) pero NO en `/operator/power/window/*`
- En `main_v7.py` línea 892-905 está marcado como **TODO — Phase 2**

**Impacto**: No se puede abrir ventana temporal desde tentaculo_link
- Workaround: Llamar directamente a madre: `POST http://madre:8001/madre/power/window/open`

---

### ⚠️ GAP-2: `/operator/power/policy/solo_madre/status` DEVUELVE 500 ERROR

**Síntoma**: 
```json
{"status":"error","code":500}
HTTP 200
```

**Rootcause**: Probablemente madre está devolviendo error al acceder a `/madre/power/policy/solo_madre/status`

**Verificación**: 
```bash
curl -H "X-VX11-Token: vx11-test-token" http://madre:8001/madre/power/policy/solo_madre/status
```

---

### ⚠️ GAP-3: SWITCH OFFLINE (circuit_open)

**Estado**: Todos los servicios OFF en solo_madre (esperado)

**Módulos detectados DOWN**:
- switch (circuit_open)
- hermes (circuit_open)
- hormiguero (circuit_open)
- spawner (circuit_open)
- mcp (circuit_open)
- shub (circuit_open)

**UP**:
- madre ✅
- operator-backend ✅
- tentaculo_link ✅

---

## CORE WIRING STATUS

| Componente | Estado | Evidencia |
|-----------|--------|-----------|
| **Single Entrypoint (8000)** | ✅ OK | `/health` devuelve 200 |
| **Token Auth** | ✅ OK | Rechaza 401/403, acepta con token válido |
| **tentaculo_link → madre** | ✅ OK | `/operator/chat` devuelve 200 OK |
| **Fallback (no switch)** | ✅ OK | MADRE responde con plan fallback_local |
| **Default SOLO_MADRE** | ✅ OK | Sin acción, switch OFF, no connection refused |
| **Policy Detection** | ⚠️ PARTIAL | `/operator/power/policy/solo_madre/status` → 500 |
| **Window Open API** | ❌ MISSING | `/operator/power/window/open` → 404 |
| **Window Close API** | ❌ MISSING | `/operator/power/window/close` → 404 |

---

## DEFINICIÓN DE HECHO (DoD) PROGRESS

✅ **Cumplido**:
1. Single entrypoint (8000) - TODO acceso SOLO por tentaculo_link
2. Default SOLO_MADRE - Switch OFF sin intervención
3. OFF_BY_POLICY claro - NO "connection refused" opaco
4. Token auth - X-VX11-Token required, 401/403 correctos
5. Fallback funcional - Madre chat SIN switch disponible

❌ **Faltante**:
1. Endpoints power/window/* en tentaculo_link
2. Endpoint para ABRIR ventana desde tentaculo_link
3. Policy status query (500 error)

---

## RECOMENDACIONES FASE C

### Opción A: IMPLEMENTAR VENTANAS (Full DoD)

Necesaría agregar en `tentaculo_link/main_v7.py`:
```python
@app.post("/operator/power/window/open")
async def power_window_open(req: PowerWindowOpenRequest, _: bool = Depends(token_guard)):
    """Open power window via madre"""
    clients = get_clients()
    madre = clients.get_client("madre")
    if not madre:
        raise HTTPException(status_code=503, detail="madre_unavailable")
    
    result = await madre.post("/madre/power/window/open", payload=req.dict())
    write_log("tentaculo_link", "power_window_open")
    return result

@app.post("/operator/power/window/close")
async def power_window_close(window_id: str, _: bool = Depends(token_guard)):
    """Close power window via madre"""
    # similar...
```

**Effort**: ~30 min (2 endpoints simples, proxy pattern)

### Opción B: USAR ENDPOINTS EXISTENTES (Mínimo)

Ya existen en madre:
- `POST /madre/power/window/open`
- `POST /madre/power/window/close`
- `GET /madre/power/state`

Documentar como:
- No exponer en tentaculo_link (respeta single-entrypoint)
- Acceso DIRECTO a madre para test/debug

---

## PRÓXIMOS PASOS

1. **Investigar 500 error** en `/operator/power/policy/solo_madre/status`
2. **Decidir**: ¿Implementar ventanas en tentaculo_link o usar madre directamente?
3. **FASE C**: Crear pruebas reproducibles + commit atómico

---

**Audit Trail**: docs/audit/20260101T042401Z_core_wiring/
