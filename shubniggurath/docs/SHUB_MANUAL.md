# Shub-Niggurath Ultimate v3.0 — Manual de Integración

**Versión:** 3.0  
**Fecha:** 2 de diciembre de 2025  
**Estatus:** Completado y validado  
**Contexto:** Integración con VX11 v6.2 sin modificaciones  

---

## Visión General

Shub-Niggurath Ultimate v3.0 es un sistema de asistencia de audio impulsado por IA, diseñado para integrar con VX11 v6.2 sin modificar su arquitectura core ni sus puertos de operación.

### Características Clave

- **Conversational AI:** Asistente inteligente basado en comandos de estudio
- **Pipeline Modular 0→100:** Procesamiento de audio en etapas
- **Integración VX11:** Bridges seguros con Switch, Madre, MCP
- **BD Avanzada:** Schema especializado para audio + análisis
- **API REST completa:** 7 routers (assistant, analysis, mixing, mastering, preview, headphones, maintenance)
- **Cluster Interno:** Docker compose independiente

---

## Estructura de Archivos

```
/home/sam/vx11/shub/
├── shub_core_init.py              # Núcleo: ShubAssistant, Pipeline, Context
├── shub_routers.py                # API REST (7 routers)
├── shub_db_schema.py              # Schema BD + migraciones
├── shub_vx11_bridge.py            # Cliente VX11 (Switch, Madre, MCP)
├── shub_copilot_bridge_adapter.py # Entry point Copilot→Shub
├── main.py                        # App FastAPI principal
├── docker/
│   ├── shub_compose.yml           # Cluster interno
│   ├── Dockerfile.api
│   ├── Dockerfile.engine
│   └── .env.shub
├── db/
│   └── migrations_shub.sql        # Migraciones
├── tests/
│   └── test_shub_core.py          # Suite de tests
└── docs/
    ├── SHUB_ROUTES.md
    ├── SHUB_VX11_INTEGRATION.md
    └── API_SPEC.md
```

---

## Puertos y Configuración

### Puertos Shub (Independientes de VX11)

- API principal: `9000`
- Conversational engine: `9001` (interno)
- Spectral analyzer: `9002` (interno)
- Headphone engine: `9003` (interno)
- Maintenance agent: `9004` (interno)
- AI processor: `9005` (interno)
- Drum doctor: `9006` (interno)

### Integración VX11 (NO conflictivos)

- Gateway VX11: `8000` (referencia solo)
- Madre VX11: `8001` (referencia solo)
- Switch VX11: `8002` (referencia solo)
- MCP VX11: `8006` (referencia solo)

---

## Flujos de Integración

### 1. Entrada Copilot→Shub (Conversacional)

```
Copilot
  ↓
POST /v1/assistant/copilot-entry
  ↓
StudioCommandParser (analiza comando)
  ↓
├─ Si comando simple → procesa localmente
├─ Si requiere orquestación → route_to_madre
└─ Si mensaje libre → route_to_mcp
  ↓
Response con session_id + actions_taken
```

### 2. Análisis Shub→VX11 (Distribuido)

```
Shub /v1/analysis/analyze
  ↓
VX11FlowAdapter.shub_analysis_to_vx11()
  ↓
Switch (routing inteligente)
  ↓
Resultado
  ↓
Caché en analysis_cache
```

### 3. Maestría Shub (Local)

```
Mix session → Mastering pipeline
  ↓
Goal LUFS normalización
  ↓
Resultado en mastering_sessions
```

---

## Instanciación y Uso

### Crear Asistente

```python
from shub_core_init import ShubAssistant

assistant = ShubAssistant(name="Shub-Niggurath")
msg = assistant.add_message("user", "analyze the mix")
result = await assistant.process_command("analyze", {"mode": "full"})
```

### Usar Bridges VX11

```python
from shub_vx11_bridge import get_vx11_client, VX11FlowAdapter

client = get_vx11_client()
await client.health_check()  # Verificar VX11

adapter = VX11FlowAdapter(client)
result = await adapter.shub_analysis_to_vx11("spectra", "project_id_123")
```

### Entry Point Copilot

```python
from shub_copilot_bridge_adapter import get_copilot_bridge, CopilotEntryPayload

bridge = get_copilot_bridge()
payload = CopilotEntryPayload("mix track=1", require_action=True)
result = await bridge.handle_copilot_entry(payload)
```

---

## BD y Migraciones

### Crear BD

```bash
sqlite3 /app/data/shub_niggurath.db < db/migrations_shub.sql
```

### Tablas Principales

- `project_audio_state` — Proyectos
- `reaper_tracks` — Tracks REAPER
- `reaper_item_analysis` — Items analizados
- `analysis_cache` — Caché rápido
- `assistant_sessions` — Sesiones conversacionales
- `mixing_sessions` — Sesiones de mezcla
- `mastering_sessions` — Sesiones de maestría

---

## Tests

```bash
# Validación básica (sin pytest)
python3 -m py_compile shub_*.py

# Con pytest (después de instalar)
pytest tests/test_shub_core.py -v
```

---

## Seguridad y Restricciones

✅ **PERMITIDO:**
- Crear tablas en BD propia
- Usar puertos 9000+
- Llamar a endpoints VX11 via bridge
- Procesar comandos locales

❌ **PROHIBIDO:**
- Modificar DB de VX11
- Tocar puertos 8000-8008
- Cambiar docker-compose VX11
- Activar operator_mode
- Alterar archivos fuera de `/shub/`

---

## Desactivación/Limpieza

### Detener Shub

```bash
docker-compose -f shub/docker/shub_compose.yml down
```

### Remover volúmenes

```bash
docker volume rm shub_data shub_logs
```

### Remover completamente

```bash
rm -rf /home/sam/vx11/shub/
```

---

## Roadmap v3.1+

- [ ] Soporte multi-proyecto
- [ ] Integración REAPER nativa
- [ ] Machine learning para beat detection
- [ ] Streaming en vivo (headphones)
- [ ] Colaboración distribuida

---

**Mantenedor:** GitHub Copilot  
**Contacto:** VX11 System Issues  
**Licencia:** MIT (compatible con VX11)
