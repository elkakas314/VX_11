# IMPORT AUDIT – VX11

## Resumen ejecutivo (máx 15 líneas)
- Estado general: Código fuertemente acoplado alrededor del paquete `config` (DB, tokens, settings, forensics) y del módulo `switch` (incluyendo `switch.hermes`). Muchos servicios (tentaculo_link, madre, mcp, spawner, switch) dependen de esas piezas centrales.
- Riesgos críticos: dependencia implícita del esquema DB (`config/db_schema.py`) y de `config/tokens.py` — moverlos rompe la mayoría de servicios. Presencia de importación del SDK `docker` y de `playwright` en scripts sin declaración clara en `requirements.txt` principal.
- Módulos seguros: utilidades pequeñas y scripts aislados bajo `scripts/` que solo usan stdlib o sqlite/json (pueden aislarse fácilmente).
- Módulos frágiles: `switch/` (especialmente `main.py`), `switch/hermes/`, `madre/` y `tentaculo_link/` — contienen lógica orquestal y múltiples cruces con DB y tokens.

## Mapa de dependencias por módulo
### switch/
- depende de: `config.settings`, `config.tokens`, `config.forensics`, `config.db_schema`, `httpx`, `fastapi`, `sqlalchemy`, `httpx`, `asyncio`, `psutil`.
- es usado por: tests (p. ej. `tests/test_switch_*`), `madre/` (calls into `switch`), `scripts/*` (e2e helpers), otros submódulos `switch.hermes`, `switch.fluzo`, `switch.cli_concentrator`.
- riesgo: Alto — `switch/main.py` es un punto de integración DB/tokens/servicios; mover rompe rutas de import y la inicialización central.

### switch/hermes/
- depende de: `config.db_schema`, `config.settings`, `config.tokens`, `httpx`, `sqlalchemy`, `asyncio`, módulos locales (`.cli_registry`, `.local_scanner`, `.hf_scanner`, `.cli_metrics`).
- es usado por: `switch/main.py`, tests (`tests/test_hermes_*`), `scripts` y consumidores internos del enrutamiento de IA.
- riesgo: Alto — múltiples imports relativos internos; contiene inicializadores y factories que deben permanecer con `switch`.

### tentaculo_link/
- depende de: `config.settings`, `config.forensics`, `config.tokens`, `fastapi`, `httpx`, `asyncio`.
- es usado por: rutas y la capa gateway (importado por tests y por `docker-compose` servicios). Varios módulos reexportan la app (`tentaculo_link/__init__.py`).
- riesgo: Muy alto — gateway, no mover.

### mcp/
- depende de: `config.settings`, `config.tokens`, `config.db_schema`, `fastapi`, `httpx`, `requests`, `sqlalchemy`.
- es usado por: integraciones externas y tests; actúa sobre la DB (sandbox/exec), no es aislable sin refactor.
- riesgo: Alto.

### madre/
- depende de: `config.settings`, `config.tokens`, `config.forensics`, `config.db_schema`, `spawner` (ej. `spawner.ephemeral_v2.apply_patch_operations`), `manifestator`.
- es usado por: orquestación de tareas (core orchestration); versiones legacy usan `docker` SDK (`import docker`) y por tanto dependencia no presente en el `requirements.txt` principal.
- riesgo: Muy alto — capa orquestal con múltiples cruces internos y llamadas externas.

### spawner/
- depende de: `config.settings`, `config.db_schema`, `psutil`, `subprocess`, `signal`, `shutil`.
- es usado por: `madre/` (p. ej. `bridge_handler.py`), scripts, y tests (`tests/test_spawner_*`).
- riesgo: Alto — contiene control de procesos y operaciones de runtime (no mover sin adaptar runtime hooks).

### models/ (nota)
- no contiene módulos Python ejecutables detectados; el código que define modelos ORM está en `config/db_schema.py` y `config/models.py`.
- riesgo: `config/db_schema.py` es central y no movible.

## Dependencias cruzadas críticas
- `switch/main.py` → `config.db_schema` (ej. [switch/main.py]) — impacto: mover rompe accesos a tablas y modelos; requiere reconfigurar acceso DB y fixtures.
- `switch/main.py` → `switch.hermes` (ej. `from switch.hermes import ...`) — impacto: mover `switch.hermes` descompone selectors/CLI fusion.
- `madre/bridge_handler.py` → `spawner/ephemeral_v2.py` (`apply_patch_operations`) — impacto: madre asume que spawner queda disponible localmente; mover rompe coordinación de despliegue/ephemeral.
- `tentaculo_link/main_v7.py` → `config.tokens` / `config.db_schema` — impacto: gateway depende de tokens y DB para autorización/registro.
- `mcp/main.py` → `config.db_schema`, `config.tokens` — impacto: mover afecta ejecución de sandboxes y logs.

## Archivos NO movibles (lista explícita)
- `config/db_schema.py` — motivo: define el esquema ORM usado por casi todos los servicios.
- `config/settings.py` — motivo: parámetros globales (paths, puertos, flags) consumidos en arranque.
- `config/tokens.py` — motivo: carga y reexporta tokens críticos; usado por todos los servicios para auth.
- `switch/main.py` — motivo: punto de entrada y orquestación central del motor de ruteo.
- `switch/hermes/__init__.py` y `switch/hermes/main.py` — motivo: inicializadores y factories para CLIs y modelos.
- `tentaculo_link/main_v7.py` — motivo: gateway HTTP principal.
- `madre/main.py` y `madre/main_legacy.py` — motivo: orquestación madre; referencias a `spawner` y `config`.
- `spawner/ephemeral_v2.py` — motivo: control de procesos y API para aplicar parches/ephemeral containers.
- `mcp/main.py` — motivo: ejecución de sandboxes y dependencia DB/auditoría.

## Archivos movibles con refactor
- `switch/cli_concentrator/*` — cambio requerido: convertir imports relativos en API pública y minimizar acople con `switch.main`.
- `switch/fluzo/*` — cambio requerido: encapsular cliente FLUZO en una interfaz independiente y aislar configuración de DB.
- `scripts/*` (algunos) — cambio requerido: mover a paquete `tools` y codificar dependencias en `pyproject`/requirements específicos.
- `operator_backend/backend/browser.py` (usa `playwright`) — cambio requerido: extraer adaptador de browser y declarar `playwright` en dependencias de desarrollo.

## Archivos aislables
- `scripts/generate_db_map.py` — utilidad de extracción, usa sqlite/json; aislable.
- `scripts/repo_inventory_and_readmes.py` — utilidad IO, aislable.
- `tools/diagnostics.py` — herramientas de diagnóstico basadas en psutil.
- `scripts/hermes_download_test_models.py` — gestor de descargas; puede aislarse como tarea cron/worker.

## Recomendación estructural (SIN ejecutar)
- estructura objetivo propuesta:
  - `core/`: `config/`, `data/`, `db_schema` y componentes imprescindibles para arranque.
  - `services/`: cada servicio independiente como `switch/`, `tentaculo_link/`, `madre/`, `mcp/`, `spawner/`, `manifestator/` con una API mínima entre ellos (clients/adapters).
  - `tools/` o `scripts/`: utilidades y scripts fuera del runtime principal.
- qué quedaría en core: `config/*`, `config/db_schema.py`, `config/tokens.py`, `config/settings.py`, `config/forensics.py`.
- qué quedaría en modules: `switch/` (incluye `switch/hermes`), `tentaculo_link/`, `mcp/`, `madre/`, `spawner/`, `manifestator/`.
- qué queda apagado pero preservado: `madre/main_legacy.py` (legacy orchestration) y scripts experimentales que dependen de `docker` o `playwright` — conservar para análisis forense/rollback.

---
### Observaciones adicionales (hallazgos técnicos)
- Paquetes externos usados y declarados en `requirements.txt`: `fastapi`, `uvicorn`, `pydantic`, `httpx`, `sqlalchemy`, `psutil`, `requests`, `numpy`, `playwright` **no aparece** en `requirements.txt` principal aunque se importa en `scripts/*` y `operator_backend/backend/browser.py` (ver `playwright.async_api`).
- SDK `docker` se importa en `madre/main_legacy.py` (`import docker`) pero no está listado en el `requirements.txt` principal.
- Uso de import dinámico y condicionales: muchos módulos hacen `from config.db_schema import ...` solo dentro de funciones (import tardío). Esto crea acoplamiento runtime y complica mover archivos sin reordenar inicialización.
- Presencia de imports relativos internos frecuentes en `switch/hermes/` (p. ej. `from .cli_registry import ...`) — indica paquete bien organizado, pero dependiente de mantener paquete `switch` intacto.
- Múltiples tests asumen importabilidad de apps (p. ej. `from switch.main import app`) — mover romperá test harnesses.

---
*Este informe es solo análisis de imports y acoplamientos; no he realizado cambios en el repositorio ni ejecutado comandos destructivos.*
