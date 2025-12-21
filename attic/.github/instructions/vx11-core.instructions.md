# VX11 Core Modules — Path-Specific Instructions

**Scope:** `tentaculo_link/`, `madre/`, `switch/`, `hermes/`, `hormiguero/`, `spawner/`, `shubniggurath/`

## Reglas Obligatorias

### 1. Estructura de Módulos
- **NO duplicados** de módulos. Cada módulo tiene puerto único (8000–8008).
- **NO imports cruzados** entre módulos. Usa HTTP + `settings.{module}_url` siempre.
- **Async-first**: todos los endpoints son `async def`.
- **Token obligatorio**: header `X-VX11-Token` en todas las solicitudes.

### 2. Cambios Permitidos en Módulos
- ✅ Lógica dentro de endpoints (mantener namespacing)
- ✅ Agregar nuevos endpoints con versión (`/modulo/v{N}/...`)
- ✅ Optimizar queries a BD
- ❌ Cambiar puertos en docker-compose.yml
- ❌ Mover o renombrar módulos raíz
- ❌ Usar imports directos de otros módulos

### 3. Llamadas HTTP Inter-Módulo
```python
import httpx
from config.settings import settings
from config.tokens import get_token

VX11_TOKEN = get_token("VX11_GATEWAY_TOKEN") or settings.api_token
AUTH_HEADERS = {settings.token_header: VX11_TOKEN}

async def call_switch(prompt: str):
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.switch_url}/switch/route-v5",
            json={"prompt": prompt, "task_type": "chat"},
            headers=AUTH_HEADERS
        )
        resp.raise_for_status()
        return resp.json()
```

### 4. Bases de Datos
- **Use `config.db_schema.get_session("vx11")`** — BD unificada `data/runtime/vx11.db`
- **SIEMPRE `db.close()` en finally** — evita memory leaks
- **NO ALTER TABLE destructiva** — solo INSERT/SELECT existentes
- **Tablas canónicas**: ver [config/db_schema.py](../../config/db_schema.py)

### 5. Logging y Forensics
```python
import logging
from config.forensics import write_log

log = logging.getLogger(__name__)
log.info("evento")
write_log("mi_modulo", "evento", level="INFO")
```

### 6. Testing
- Tests en `tests/` con prefijo `test_`
- Usa pytest + pytest-asyncio
- Mock de HTTP: `httpx.AsyncClient` con responder
- **NO dejar containers corriendo** después de tests

## Control de Recursos (Low-Power)

- **MAX 2 módulos corriendo a la vez** durante desarrollo
- Usa `docker compose ps` antes de levantar nuevos
- Si >2 corriendo: apaga primero con `docker compose stop`
- Timeouts: 15s máximo para inter-módulo calls

## Red Intra-Módulo

- Usa DNS de Docker: `http://madre:8001`, `http://switch:8002`, etc.
- Fallback a localhost si Docker DNS falla (ver `config.dns_resolver.py`)
- Nunca hardcodees IPs o puertos en lógica

## Auditoría y Versionado

- Cambios significativos: actualiza `config/VERSION.txt` → commit etiquetado
- Si agregan tabla: documentar en `docs/audit/`
- Forensics: logs en `forensic/{modulo}/logs/`
- Hashes: en `forensic/{modulo}/hashes/`

---

**Última actualización:** 2025-12-16  
**Responsable:** Copilot Agent VX11
