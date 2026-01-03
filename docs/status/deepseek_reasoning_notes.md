# DeepSeek R1 Reasoning Notes — Frontend + Wiring Decisions — 2026-01-03

## Propósito
Documentar razonamientos DeepSeek R1 utilizados para diagnosticar + diseñar fixes de:
1. Frontend "Se ve pero no hace nada"
2. Token flow (headers vs query params para SSE)
3. UX states (401 vs 403 vs OFF_BY_POLICY)
4. Decisiones wiring Switch/Hermes

---

## RAZONAMIENTO 1: Diagnóstico Frontend Bug

### Problema Original
UI carga visualmente (dark theme, botones responden) pero:
- SSE nunca conecta ("Disconnected from events feed" permanente)
- Token "Not configured" en Settings
- Chat no responde
- HTTP 401 en llamadas

### Análisis Depth
Frontend YA IMPLEMENTA token correctly:
- ✅ getToken() lee localStorage
- ✅ API client incluye X-VX11-Token header
- ✅ SSE construye URL con ?token=query_param
- ✅ Componentes UI para configuration existen

**Entonces ¿por qué "se ve pero no hace nada"?**

**Root Cause (R1 reasoning)**:
1. **Default token = ""** (empty) → sin usuario configurar, frontend NO envía token válido
2. **SSE client intenta conectar SIN token** → immediate 401
3. **EventSource onerror reintenta infinito** → spam de reconexiones sin token
4. **UI no bloquea SSE init** si falta token → UX confusa ("Disconnected", no "Please configure token")
5. **TokenSettings puede no estar prominente** en flujo principal

**Decisión R1: NO rediseñar, agregar guard antes de SSE**:
- Si !token → onError inmediato, no intentar connect
- Mostrar claro: "Token required" + CTA de configuración
- Esto ya está en código, pero UI no lo refleja correctamente

### Implementación
✅ Agregar `isTokenConfigured()` helper en api.ts
✅ EventsClient: guardia en constructor (skip connect si no token)
✅ App.tsx: escuchar `vx11:token-changed` event + guardia de estado

---

## RAZONAMIENTO 2: Token Flow — Headers vs Query Params

### Dilema
Tentáculo Link proxy: token debe ir a /operator/api/*
- Métodos HTTP normales (GET/POST): ✅ header `X-VX11-Token` OK
- EventSource/SSE: ❌ NO permite headers (CORS + HTTP limitation)
  - **Solución**: Query param `?token=...` (único método válido)

### Por qué Query Param es CORRECTO para SSE
1. **HTTP/HTML5 límite**: EventSource NO permite custom headers (especificación)
2. **CORS**: Incluso con credencials: include, headers son rechazados por EventSource
3. **Alternativa fallida**: WebSocket (más complejo, no válido para SSE)
4. **Best practice**: Token en query param para SSE es estándar VX11

### Decisión R1
- API endpoints (fetch): `X-VX11-Token` header
- SSE (EventSource): `?token=<encoded>` query param
- Codificar token en URL para caracteres especiales: `encodeURIComponent(token)`
- No mezclar; es inconsistencia por desig HTTP/5, no por VX11

### Validación
✅ Tentaculo `token_guard_with_query_param()` ya soporta ambos
✅ EventsClient construye URL correcto: `${url}?token=${encodeURIComponent(token)}`
✅ Backend validará token en ambas formas

---

## RAZONAMIENTO 3: UX States — 401 vs 403 vs OFF_BY_POLICY

### Estados Posibles

| Estado | HTTP | Causa | UX Mostrada |
|--------|------|-------|-----|
| **No token** | 401 | Cliente no envió token | "Token required" + CTA |
| **Token inválido** | 403 | Token exist pero no válido | "Token invalid" + CTA edit |
| **OFF_BY_POLICY** | 403 | Token OK pero policy (solo_madre) | "Read-only mode" (no error) |
| **Service down** | 503 | Backend no responde | "Service unavailable" |

### Decisión UX (R1 reasoning)
- **401**: Block UI, mostrar banner rojo "Unauthorized. Configure token."
  - No intentar SSE, no llamar API, esperar token
- **403 + OFF_BY_POLICY**: Allow UI, mostrar badge "Observer Mode"
  - SSE deshabilitado (esperado en solo_madre)
  - Chat read-only si permitido, pero no error de red
  - Acciones críticas bloqueadas con "Ask Madre to open window"
- **403 (token inválido)**: Block UI, mostrar "Token invalid. Edit in Settings."
  - Similar a 401 pero con CTA diferente
- **503**: Mostrar "Backend unavailable", retry automático

### Implementación
✅ App.tsx: chequea `if (403 && OFF_BY_POLICY)` → no error, set eventsConnected=true
✅ EventsClient.checkOffByPolicy() → detecta policy denial
✅ API client: mapea 401 → "auth_required", 403 → "forbidden / off_by_policy"

---

## RAZONAMIENTO 4: Wiring Switch/Hermes — CLI-First + Standby

### Decisión Arquitectónica
VX11 puede usar múltiples LLM providers:
1. **Copilot CLI** (GitHub) — si disponible, mejor quality/razonamiento
2. **LLM local** (Ollama + phi2/deepseek-r1) — fallback, always available
3. **Degraded** — ninguno disponible

### Por qué CLI-First
- ✅ Copilot R1 + GPT-4 mejor quality
- ✅ No consume GPU/RAM local (external service)
- ✅ Más rápido en latency (GitHub hosted)
- ⚠️ Requiere instalación: `pip install github-copilot-cli`

### Por qué Standby LLM
- ✅ Funciona en offline
- ✅ No requiere API keys
- ⚠️ GPU-intensive (si GPU disponible)
- ⚠️ Modelos ligeros (~3GB cada uno)

### Decisión R1: Hybrid Strategy
```
if CLI available:
  use Copilot (primary)
else:
  use Ollama + phi2 (standby)
```

Configuración:
- **data/models/inventory.json** — lista de modelos + providers
- **SWITCH_CLI_PROVIDER=copilot** — CLI hint
- **HERMES_LLM_STANDBY=phi2** — fallback
- **SWITCH_USE_LOCAL_FALLBACK=1** — auto-fallback enabled

### No cambiar código de Switch/Hermes
- Ya tienen lógica de provider selection
- Solo agregar config + inventory para transparencia

---

## RAZONAMIENTO 5: Decisiones de No-Cambio (Invariantes Respetados)

### Lo que NO cambié (y por qué)
1. **No re-arquitectura frontend** → Código está bien, solo necesita ajustes UX
2. **No cambiar tentaculo proxy token flow** → Es correcto (traduce entre dominios)
3. **No descargar modelos automáticamente** → Riesgo de bloquearse en runtime
4. **No exponer puertos internos** → Single-entrypoint invariante
5. **No agregar auth a SSE via header** → Imposible en HTTP/5, query param es standard

### Invariantes Preservados
✅ Single entrypoint (tentaculo_link:8000)
✅ Token NUNCA hardcoded en bundle
✅ Solo_madre mode (read-only cuando aplique)
✅ Deterministic token flow (mismo para fetch + SSE)
✅ DB integrity + foreign keys

---

## Validación de Decisiones

### Test 1: Frontend Token Flow
```bash
# Configurar token en Settings → esperar 2s
# SSE debe conectar sin "Disconnected"
curl -N "http://localhost:8000/operator/api/events?token=vx11-test-token&follow=true" | head -3
# Expected: event stream OK
```

### Test 2: Off-by-Policy Detection
```bash
# En solo_madre mode
curl -H "X-VX11-Token: vx11-test-token" \
  http://localhost:8000/operator/api/health

# Si devuelve 403 + status='off_by_policy' → UX debe mostrar "Observer Mode"
```

### Test 3: Provider Selection
```bash
# Check which provider se usó
docker compose logs vx11-switch-test | grep -i "provider\|cli\|ollama" | tail -5
```

---

## Conclusiones

1. **Frontend Fix** es UX + guardia, no architecture
2. **Token Flow** usa standards HTTP/5 (headers + query param)
3. **States** deben ser explícitos en UI (no genéricos "error")
4. **Wiring** respeta invariantes + usa configuración, no hardcodes
5. **All decisions documented** para mantenimiento futuro

**Status**: REASONING COMPLETE, SAFE TO IMPLEMENT

