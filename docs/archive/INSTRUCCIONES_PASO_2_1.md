# 🎯 INSTRUCCIONES PARA PRÓXIMA SESIÓN — VX11 v7.1

**Documento:** Guía de continuación  
**Estado Actual:** 🟢 PRODUCCIÓN READY (95%)  
**Siguiente:** PASO 2.1 — Integración SIL en Switch

---

## 📍 PUNTO DE PARTIDA

Tú estás aquí:
```
✅ Análisis completo
✅ Intelligence Layer creada  
✅ GA Router creada
✅ Plan documentado
➡️ PRÓXIMO: Integrar en Switch
```

---

## ⚡ PASO 2.1 — INTEGRACIÓN DE SIL EN /SWITCH/CHAT (1 hora)

### Objetivo
`/switch/chat` endpoint debe usar `SwitchIntelligenceLayer` para todas las decisiones de routing.

### Cambios a hacer

**Archivo:** `switch/main.py` (líneas ~925-1050)

#### 1. Importar Intelligence Layer (después de línea 37)
```python
# Agregar después de: from switch.shub_forwarder import get_switch_shub_forwarder

from switch.intelligence_layer import (
    get_switch_intelligence_layer,
    RoutingContext,
    RoutingDecision,
)
from switch.ga_router import get_ga_router
```

#### 2. Inicializar en startup (en `_startup_consumer()`, después de línea 536)
```python
# Después de: asyncio.create_task(warm_up_engine.warmup_periodic())

# Inicializar Intelligence Layer y GA Router
log.info("Inicializando Intelligence Layer...")
sil = get_switch_intelligence_layer()

log.info("Inicializando GA Router...")
ga_router = get_ga_router(ga_optimizer)
```

#### 3. Reemplazar lógica en `/switch/chat` (lineas 925-1050)

**VIEJO CÓDIGO (a reemplazar):**
```python
@app.post("/switch/chat")
async def switch_chat(req: ChatRequest):
    provider_hint = (req.provider_hint or req.provider or "").strip().lower() or None
    task_type = req.metadata.get("task_type", "").strip().lower() if req.metadata else ""
    
    # Detectar tarea de sistema → delegar a Madre
    if task_type == "system" or provider_hint == "madre":
        # ... código viejo ...
```

**NUEVO CÓDIGO (reemplazar TODO el endpoint):**
```python
@app.post("/switch/chat")
async def switch_chat(req: ChatRequest):
    """
    Chat mejorado: usa Intelligence Layer para routing inteligente.
    
    Flujo:
    1. Crear RoutingContext con metadata completa
    2. Consultar SwitchIntelligenceLayer
    3. Ejecutar con fallbacks
    4. Registrar en GA metrics
    """
    
    start_time = time.monotonic()
    sil = get_switch_intelligence_layer()
    ga_router = get_ga_router(ga_optimizer)  # ga_optimizer es global
    
    try:
        # Extraer metadata
        task_type = req.metadata.get("task_type", "general").strip().lower() if req.metadata else "general"
        source = req.metadata.get("source", "operator").strip().lower() if req.metadata else "operator"
        provider_hint = (req.provider_hint or "").strip().lower() or None
        
        prompt_text = req.messages[0].content if req.messages else ""
        
        # PASO 1: Crear contexto de routing
        context = RoutingContext(
            task_type=task_type,
            source=source,
            messages=[m.model_dump() for m in req.messages],
            metadata=req.metadata or {},
            provider_hint=provider_hint,
            max_tokens=req.metadata.get("max_tokens", 4096) if req.metadata else 4096,
            require_streaming=req.metadata.get("require_streaming", False) if req.metadata else False,
        )
        
        # PASO 2: Consultar Intelligence Layer para decisión
        routing_decision = await sil.make_routing_decision(context)
        
        logger.info(f"Routing decision: {routing_decision.decision}, engine: {routing_decision.primary_engine}")
        
        # PASO 3: Ejecutar según decisión
        latency_ms = 0
        result = None
        success = False
        
        if routing_decision.decision == RoutingDecision.MADRE:
            result, latency_ms, success = await _execute_madre_task(prompt_text, req.metadata or {})
        
        elif routing_decision.decision == RoutingDecision.MANIFESTATOR:
            result, latency_ms, success = await _execute_manifestator_task(prompt_text, req.metadata or {})
        
        elif routing_decision.decision == RoutingDecision.SHUB:
            result, latency_ms, success = await _execute_shub_task(prompt_text, req.metadata or {})
        
        else:  # CLI, LOCAL, HYBRID, FALLBACK
            result, latency_ms, success = await _execute_hermes_task(
                engine_name=routing_decision.primary_engine,
                prompt=prompt_text,
                metadata=req.metadata or {}
            )
        
        # PASO 4: Registrar en GA metrics
        ga_router.record_execution_result(
            engine_name=routing_decision.primary_engine,
            task_type=task_type,
            latency_ms=latency_ms,
            success=success,
            cost=0.0,
            tokens=req.metadata.get("tokens_used", 0) if req.metadata else 0,
        )
        
        return {
            "status": "ok" if success else "partial",
            "provider": routing_decision.primary_engine,
            "decision": routing_decision.decision.value,
            "content": result.get("content", "") if isinstance(result, dict) else str(result),
            "latency_ms": latency_ms,
            "reasoning": routing_decision.reasoning,
        }
    
    except Exception as exc:
        latency_ms = int((time.monotonic() - start_time) * 1000)
        write_log("switch", f"chat_error:{exc}", level="ERROR")
        
        return {
            "status": "error",
            "provider": "fallback",
            "content": f"Error: {str(exc)}",
            "latency_ms": latency_ms,
        }
```

#### 4. Agregar helpers (después del endpoint /switch/chat)

```python
async def _execute_madre_task(prompt: str, metadata: Dict) -> Tuple[Dict, int, bool]:
    """Ejecutar tarea en Madre."""
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0, headers=AUTH_HEADERS) as client:
            resp = await client.post(
                f"{settings.madre_url.rstrip('/')}/madre/route-system",
                json={"messages": [{"role": "user", "content": prompt}], "metadata": metadata},
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                result = resp.json()
                latency_ms = int((time.monotonic() - start) * 1000)
                return result, latency_ms, True
    except Exception as e:
        logger.error(f"Madre task error: {e}")
    
    return {"content": "Error en Madre"}, int((time.monotonic() - start) * 1000), False


async def _execute_manifestator_task(prompt: str, metadata: Dict) -> Tuple[Dict, int, bool]:
    """Ejecutar tarea en Manifestator."""
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0, headers=AUTH_HEADERS) as client:
            resp = await client.post(
                f"{settings.manifestator_url.rstrip('/')}/detect-drift",
                json={"messages": [{"role": "user", "content": prompt}], "metadata": metadata},
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                result = resp.json()
                latency_ms = int((time.monotonic() - start) * 1000)
                return result, latency_ms, True
    except Exception as e:
        logger.error(f"Manifestator task error: {e}")
    
    return {"content": "Error en Manifestator"}, int((time.monotonic() - start) * 1000), False


async def _execute_shub_task(prompt: str, metadata: Dict) -> Tuple[Dict, int, bool]:
    """Ejecutar tarea en Shub."""
    start = time.monotonic()
    try:
        forwarder = get_switch_shub_forwarder()
        result = await forwarder.route_to_shub(query=prompt, context=metadata)
        latency_ms = int((time.monotonic() - start) * 1000)
        return result, latency_ms, result.get("status") in ("ok", "skip")
    except Exception as e:
        logger.error(f"Shub task error: {e}")
    
    return {"content": "Error en Shub"}, int((time.monotonic() - start) * 1000), False


async def _execute_hermes_task(engine_name: str, prompt: str, metadata: Dict) -> Tuple[Dict, int, bool]:
    """Ejecutar tarea en Hermes o CLI."""
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=30.0, headers=AUTH_HEADERS) as client:
            resp = await client.post(
                f"{settings.hermes_url.rstrip('/')}/hermes/execute",
                json={"engine": engine_name, "prompt": prompt, "metadata": metadata},
                headers=AUTH_HEADERS,
            )
            if resp.status_code == 200:
                result = resp.json()
                latency_ms = int((time.monotonic() - start) * 1000)
                return result, latency_ms, True
    except Exception as e:
        logger.error(f"Hermes task error: {e}")
    
    return {"content": "Error en Hermes"}, int((time.monotonic() - start) * 1000), False
```

### Verificación

Después de hacer los cambios:

```bash
# 1. Compilar
python3 -m compileall switch/main.py -q

# 2. Verificar imports
grep -E "from switch.(intelligence_layer|ga_router)" switch/main.py

# 3. Test básico (opcional)
python3 -c "from switch.main import app; print('✅ Switch importable')"
```

---

## ⚡ PASO 2.2 — INTEGRACIÓN EN /SWITCH/TASK (30 min)

Similar a PASO 2.1, pero en el endpoint `/switch/task` (líneas ~1050-1200).

**Cambios similares:**
1. Importar SIL + GA Router
2. Crear RoutingContext
3. Consultar SIL
4. Registrar en GA

---

## 🧪 TESTS DESPUÉS DE INTEGRAR

```bash
# Test 1: Compilación
python3 -m compileall switch/ -q

# Test 2: Endpoints existen
curl -X POST http://localhost:8002/switch/chat \
  -H "X-VX11-Token: test" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "test"}]}'

# Test 3: GA está activo
curl -X GET http://localhost:8002/switch/ga/status \
  -H "X-VX11-Token: test"
```

---

## 📋 CHECKLIST PARA PRÓXIMA SESIÓN

```
[ ] Leer este documento
[ ] Abrir switch/main.py
[ ] Agregar imports (Intelligence Layer + GA Router)
[ ] Agregar inicialización en startup
[ ] Reemplazar /switch/chat endpoint
[ ] Agregar helper functions
[ ] Compilar ✅
[ ] Test básico ✅
[ ] Commit: "✅ PASO 2.1: SIL integrada en /switch/chat"
[ ] Pasar a PASO 2.2
```

---

## 🎓 NOTAS IMPORTANTES

1. **SwitchIntelligenceLayer** SIEMPRE consulta Hermes → respeta prioridades tentaculares
2. **GA Router** registra CADA ejecución → feedback loop activo
3. **RoutingContext** centraliza metadata → decisiones más inteligentes
4. **No remover código viejo** hasta verificar que todo funciona
5. **Tests primero** → cambios después

---

## 📞 CONTACTO

Si hay dudas durante la implementación:
1. Leer PLAN_TENTACULAR_FINAL_v7_1.md
2. Revisar archivos de ejemplo (intelligence_layer.py, ga_router.py)
3. Compilar + testear después de cada cambio

---

**STATUS:** Listo para comenzar PASO 2.1

**TIEMPO ESTIMADO:** 1.5 horas para completar PASOS 2.1 + 2.2

**RESULTADO:** Switch 100% inteligente con feedback loop GA activo

