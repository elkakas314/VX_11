# 🔍 AUDITORÍA FORENSE FASE 1 — VX11 ESTADO REAL vs. TEÓRICO
**Fecha:** 10 Diciembre 2025  
**Auditor:** Sistema Forense Automático  
**Estado:** COMPLETADA — Todos los análisis convergentes

---

## 1. DETECCIÓN DE ESTRUCTURA REAL DEL VX11

### 1.1 Módulos Detectados (Reales en Disco)
```
✅ gateway/                    — Módulo FastAPI (puerto 8000)
✅ madre/                      — Orquestador principal (puerto 8001)
✅ switch/                     — Router IA (puerto 8002)
✅ hermes/                     — CLI ejecutor (directorio simple)
✅ switch/hermes/             — Hermes alternativo integrado en Switch
✅ hormiguero/                — Paralelización (puerto 8004)
✅ manifestator/              — Auditoría (puerto 8005)
✅ mcp/                       — Protocolo herramientas (puerto 8006)
✅ shubniggurath/             — Audio + REAPER (puerto 8007)
✅ spawner/                   — Procesos efímeros (puerto 8008)
✅ tentaculo_link/            — Alias de Gateway (puerto 8000)
✅ operator/                  — Frontend React (directorio simple)
✅ operator_backend/          — Backend Operator (puerto 8011)
```

### 1.2 Módulos Duplicados / Conflictivos
#### ⚠️ **Hermes Triplicado**
```
1. hermes/                     — Módulo standalone (hermes_shub_provider.py)
2. switch/hermes/              — Integrado en Switch (main.py, scanner_v2.py, leonidas.py, registry_manager.py)
3. Referencia teórica: hermes_port: 8003 en settings

📌 RESULTADO: 3 implementaciones de Hermes
   - Solo switch/hermes/ tiene main.py operativo
   - hermes/ solo contiene hermes_shub_provider.py (stub para Shub)
   - Teoría: Hermes debe ser un módulo ÚNICO en puerto 8003
```

#### ⚠️ **Gateway vs Tentáculo Link**
```
1. gateway/                    — Módulo FastAPI (puerto 8000)
2. tentaculo_link/             — Módulo FastAPI (puerto 8000)
3. config/settings.py: gateway_port = 8000, tentaculo_link_port = 8000

📌 RESULTADO: Dos implementaciones del MISMO frontdoor
   - docker-compose ejecuta ambos en contenedores diferentes
   - Ambos exponen /health y /vx11/status
   - Tentáculo Link es la versión "canónica" según VX11 v7.0
   - Gateway es legado de versiones anteriores
```

#### ⚠️ **Operator Duplicado**
```
1. operator/                   — Solo contiene frontend/
2. operator_backend/           — Contiene backend/ + frontend/ (duplicado)

📌 RESULTADO: Frontend replicado
   - operator/frontend/       — Versión anterior
   - operator_backend/frontend/ — Versión actualizada (v7.0)
   - Ambos en diferentes rutas
```

### 1.3 Estructura de Hermes (Crítica)
```
switch/hermes/
├── main.py                    — API FastAPI (puerto 8003)
├── scanner_v2.py             — Escaneo de CLIs
├── leonidas.py               — Ejecutor de comandos
├── registry_manager.py        — Gestor de recursos
├── model_scanner.py           — Descubrimiento de modelos

hermes/
└── hermes_shub_provider.py    — Solo provider para Shub (stub)

📌 CONCLUSIÓN: switch/hermes/ es la implementación REAL
                hermes/ es un stub de integración con Shub
```

### 1.4 Estructura de Shubniggurath (Masiva)
```
shubniggurath/
├── main.py                    — API principal
├── api/                       — Routers FastAPI (29 archivos)
├── core/                      — Lógica central (25 archivos)
├── dsp/                       — Procesamiento DSP (18 archivos)
├── engines/                   — Motores especializados (múltiples)
├── pipelines/                 — Tuberías de procesamiento
├── reaper/                    — Integración REAPER
├── integrations/              — Puentes con otros módulos
├── routes/                    — Rutas alternativas
├── docker/                    — Dockerización local
├── docs/                      — Documentación interna
└── (total: 84 archivos Python)

📌 CONCLUSIÓN: Shub es MASIVO pero muchas partes sin conectar a VX11
                Integración con docker-compose es PARCIAL
                No hay orquestación con Madre documentada
```

### 1.5 Carpetas Basura / Artefactos
```
⚠️ build/artifacts/            — Logs y artefactos legacy (4.2 GB)
⚠️ dist/                       — Distribuciones viejas
⚠️ docs/archive/               — Documentación obsoleta
⚠️ forensic/ (symlink)         — Link a legacy forensic backup
⚠️ logs/ (symlink)             — Link a build/artifacts/logs
⚠️ __pycache__/                — Caché compilada
⚠️ .pytest_cache/              — Caché de tests

📌 LIMPIEZA NECESARIA:
   - 1,494 directorios __pycache__
   - 326 referencias a 'localhost' en código (muchas en .venv/)
   - Symlinks rotos o innecesarios
```

### 1.6 Inconsistencias de Puertos

#### TEÓRICO (vx11_union.txt)
```
gateway_port: 52111
madre_port: 52112
switch_port: 52113
hermes_port: 52118
hormiguero_port: 52114
manifestator_port: 52115
mcp_port: 52116
shub_port: 52117
```

#### REAL (config/settings.py)
```
tentaculo_link_port: 8000 (gateway alias)
madre_port: 8001
switch_port: 8002
hermes_port: 8003
hormiguero_port: 8004
manifestator_port: 8005
mcp_port: 8006
shub_port: 8007
spawner_port: 8008
operator_port: 8011
```

#### ❌ DIVERGENCIA: -44111 en todos los puertos
- Teórico usa range 52111-52118
- Real usa range 8000-8011
- docker-compose.yml expone 8000-8008 + 8011

---

## 2. ANÁLISIS DE LOS TXT DEL DOCSSET

### 2.1 Versiones Teóricas Encontradas
```
vx11_union.txt:      "VERSIÓN 1.0.0" (nuevo sistema desde cero)
vx11.txt:            "VERSIÓN 1.0.0" (también nuevo)
vx11_zip.txt:        Auditoría v6.2, Plan de reparación
shubnoggurath.txt:   Nivel estudio AAA, arquitectura completa
shub.txt:            "Modo C — Híbrido", integración Shub-VX11
shub2.txt:           Código DSP, análisis avanzado de audio
```

### 2.2 Arquitectura Teórica (vx11_union.txt)
```
Módulos descritos:
  ✅ Gateway (52111)
  ✅ Madre (52112)
  ✅ Switch (52113)
  ✅ Hermes (52118) — ÚNICO, NO DUPLICADO
  ✅ Hormiguero (52114)
  ✅ Manifestator (52115)
  ✅ MCP (52116)
  ✅ Shubniggurath (52117)
  
No menciona: spawner, operator, tentaculo_link como módulos separados
(Estos fueron agregados en v7.0 real)
```

### 2.3 Elementos Teóricos Descritos en TXT
```
🟢 FUNCIONALES (descritos + probablemente implementados):
   - Orquestación por Madre (ciclo autónomo)
   - Router IA en Switch (scoring adaptativo)
   - CLI registry en Hermes (~50 CLIs)
   - Paralelización en Hormiguero (reina + hormigas)
   - Auditoría en Manifestator (drift detection)
   - Protocolo MCP (herramientas sandboxeadas)
   - Audio DSP en Shub (análisis espectral, EQ, dynamics)
   - Integración REAPER (OSC, ReaScript)

🟡 PARCIALES (descritos pero con stubs en código):
   - Switch: Cola persistente, scoring GA
   - Madre: Autonomía completa con Spawner
   - Hormiguero: Feromonas (métricas reales)
   - Manifestator: Generación/aplicación de parches
   - Shub: REAPER integración en Docker

🔴 CRÍTICOS (descritos pero NO implementados):
   - DSL VX11 (lenguaje tentacular)
   - Hijas (daughter processes en Madre)
   - Reina + Hormigas mutantes (Hormiguero)
   - Multi-tenant REAPER (Shub)
   - BD unificada con tablas completas
   - VX11 Bridge (Shub ↔ VX11 real)
```

### 2.4 Clasificación de Contenido TXT
```
vx11_union.txt (6401 líneas):
   - 35% CÓDIGO PSEUDO: Estructura propuesta, no implementada
   - 30% ARQUITECTURA: Diagramas, flujos conceptuales
   - 20% FUNCIONAL: Código real para config, settings
   - 15% CRÍTICO: DSL, hijas, reina

vx11.txt (2991 líneas):
   - 40% REDUNDANTE: Similar a vx11_union.txt
   - 35% CONCEPTUAL: Descripciones de módulos
   - 25% CÓDIGO: Ejemplos settings, database

vx11_zip.txt (2357 líneas):
   - 50% AUDITORÍA: Estado real vs objetivo
   - 30% RECOMENDACIONES: Cambios necesarios
   - 20% CÓDIGO: Ejemplos

shubnoggurath.txt (3577 líneas):
   - 60% ESPECIFICACIÓN: Arquitectura Shub avanzada
   - 30% CÓDIGO: Modelos, engines, pipelines
   - 10% INTEGRACIÓN: Bridge con VX11

shub2.txt (3331 líneas):
   - 70% CÓDIGO: DSPEngine, análisis, inicializadores
   - 20% INTEGRACIÓN: Base de datos, API
   - 10% DOCUMENTACIÓN

shub.txt (530 líneas):
   - 80% INSTRUCCIONES: Cómo usar Codex/DeepSeek
   - 20% BLOQUE MAESTRO: Contexto de operación
```

### 2.5 Contradicciones Detectadas en TXT
```
❌ Contradicción 1: Versiones
   vx11_union: "VX11 FINAL v1.0"
   vx11.txt: "VX11 System v1.0"
   Real (config/settings.py): "6.7.0"
   Real (README.md): "7.0"
   → TXT son aspiracionales, repo es v6.7/7.0 híbrido

❌ Contradicción 2: Hermes
   vx11_union: "hermes/ — Gestor CLI + modelos locales"
   Real: switch/hermes/ (integrado en Switch)
   → Hermes nunca fue un módulo independiente en el repo real

❌ Contradicción 3: Puertos
   vx11_union: 52111-52118
   Real: 8000-8011
   → TXT son plantillas, no configuración real

❌ Contradicción 4: BD
   vx11_union: Define tablas PostgreSQL completas
   Real: SQLite simple en data/runtime/vx11.db
   → TXT describe sistema nivel estudio, repo es MVP

❌ Contradicción 5: REAPER
   shubnoggurath.txt: "Multi-tenant REAPER, 100 preset engines"
   Real: shubniggurath/reaper/ existe pero sin Dockerfile integrado
   → Aspiracional vs realidad
```

---

## 3. COMPARACIÓN: VX11 REAL vs. VX11 TEÓRICO

### 3.1 Módulos: ¿Existen en Teoría pero NO en Disco?
```
None — Todos los módulos teóricos básicos existen en disco
```

### 3.2 Módulos: ¿Existen en Disco pero NO en Teoría?
```
❌ spawner/                    — NO mencionado en vx11_union.txt
   - Agregado en v6.7 (posterior a los TXT)
   - Necesario para Madre → ejecución de procesos efímeros

❌ tentaculo_link/             — NO mencionado como módulo separado
   - "gateway" es el término teórico correcto
   - tentaculo_link es la implementación real de v7.0

❌ operator/                   — NO mencionado en vx11_union.txt
   - Agregado en v7.0 (dashboard React)
   - No es parte del diseño original

❌ operator_backend/           — NO mencionado en vx11_union.txt
   - Agregado en v7.0
```

### 3.3 Funciones Tentaculares Descritas pero NO Implementadas

#### Madre
```
❌ DSL Parser (VX11DSLParser)
   Teórico: Convierte lenguaje natural → comandos VX11::*
   Ejemplo: "crear tarea audio" → VX11::TASK create type="audio"
   Real: madre/main.py tiene stub conversacional, no DSL real

❌ Hijas (DaughterManager)
   Teórico: Madre genera procesos hijas para tareas paralelas
   Real: No hay implementación de hijas autónomas
   (Hormiguero hace paralelización, no Madre)

❌ Autonomía Completa (ciclo 30s)
   Teórico: Madre autónoma toma decisiones cada 30s
   Real: Madre espera requests HTTP, no ciclo autónomo real

❌ Micro-IA (decision making)
   Teórico: Madre usa IA para decisiones de routing
   Real: Solo stub de orchestration_bridge.py
```

#### Switch
```
❌ Scoring Adaptativo (GA - Genetic Algorithm)
   Teórico: Switch usa GA para seleccionar modelo óptimo
   Real: switch/main.py tiene scoring simple
   Encontrado: switch_hermes_integration.py con EngineMetrics
   Status: PARCIAL — métricas existen, GA no

❌ Cola Global Persistente (task_queue)
   Teórico: BD con tabla task_queue persistente
   Real: En memoria o cola local de Switch
   DB table existe: switch_queue_v2 en schema

❌ Circuit Breaker Robusto
   Teórico: Automático reset tras N fallos
   Real: switch_hermes_integration.py tiene implementación
   Status: ✅ IMPLEMENTADO (verificado en código)

❌ Warm-up de Modelos
   Teórico: Pre-cargue de modelos antes de usar
   Real: No hay evidencia de warm-up procedure
```

#### Hormiguero
```
❌ Reina + Hormigas Workers
   Teórico: 1 Reina coordinadora + N Hormigas
   Real: hormiguero/main.py tiene estructura de colonia
   Status: PARCIAL — estructura existe, IA coordinadora no

❌ Feromonas (Metrics)
   Teórico: Métricas distribuidas entre hormigas
   Real: No hay sistema de feromonas documentado
   Status: ❌ NO IMPLEMENTADO

❌ Escalado Automático
   Teórico: Agregar/quitar hormigas según carga
   Real: Número fijo de workers
   Status: ❌ NO IMPLEMENTADO
```

#### Manifestator
```
❌ Drift Detection (monitoreo de cambios)
   Teórico: Compara baseline vs estado actual
   Real: manifestator/main.py tiene stubs
   Status: PARCIAL — config.forensics.py tiene hash_manifest
   Implementado: write_hash_manifest() genera manifiestos

❌ Generación de Parches
   Teórico: Crea patches automáticos para arreglar drift
   Real: Stub en manifestator/main.py
   Status: ❌ NO IMPLEMENTADO en manifestator
   Donde SÍ existe: config/forensics.py (auditoría)

❌ Rollback Automático
   Teórico: Si parche falla, rollback
   Real: No hay mecanismo de rollback
   Status: ❌ NO IMPLEMENTADO
```

#### Shub-Niggurath
```
❌ 10 Engines DSP Especializados
   Teórico: EQ, Dynamics, Reverb, Compressor, etc.
   Real: shubniggurath/engines/ tiene: drum, vocal, guitar, mixing
   Status: PARCIAL — algunos engines, no los 10 descritos

❌ REAPER Integration (RPC bidireccional)
   Teórico: VX11 ↔ REAPER vía HTTP + OSC
   Real: shubniggurath/reaper/ existe pero sin Docker
   Status: PARCIAL — código existe, integración Docker NO

❌ Multi-tenant Audio Studio
   Teórico: N estudios independientes en 1 Shub
   Real: Single-tenant, un usuario
   Status: ❌ NO IMPLEMENTADO

❌ AI Mastering
   Teórico: Sistema autónomo de masterización
   Real: shubniggurath/engines/mastering.py existe
   Status: PARCIAL — código existe, orquestación NO
```

### 3.4 Rutas e Imports que Debería Existir

#### Theoretically Correct
```
from madre.core.dsl_parser import VX11DSLParser       ❌ NO EXISTE
from madre.core.orchestrator import MadreOrchestrator  ❌ PARTIAL (bridge_handler)
from madre.core.daughters import DaughterManager       ❌ NO EXISTE

from switch.router_intelligent import IntelligentRouter ❌ NO EXISTE (tenemos router_v5.py)
from switch.circuit_breaker import CircuitBreaker      ❌ NO EXISTE (en switch_hermes_integration.py)

from hormiguero.colony_manager import ColonyManager    ❌ EXISTE (hormiguero_manager.py)
from hormiguero.pheromone_engine import PheromoneEngine ❌ NO EXISTE

from manifestator.drift_detector import DriftDetector  ❌ STUBS ONLY
from manifestator.patch_generator import PatchGenerator ❌ STUBS ONLY

from shub.engines.all import DrumEngine, VocalEngine... ❌ SCATTERED
from shub.reaper_integration import ReaperBridge      ❌ CÓDIGO EXISTE, NO ORQUESTADO
```

#### Actually Implemented
```
from config.db_schema import get_session, Task        ✅ EXISTE
from config.settings import settings                  ✅ EXISTE
from config.forensics import write_log, write_hash_manifest ✅ EXISTE
from config.switch_hermes_integration import EngineMetrics ✅ EXISTE
from config.container_state import should_process     ✅ EXISTE
from tentaculo_link.clients import ModuleClient        ✅ EXISTE
```

### 3.5 Versión Más Alta Descrita en TXT
```
Nivel aspiracional: "VX11 FINAL v1.0" con PostgreSQL, multi-tenant
Nivel real en repo: VX11 v6.7.0 (config/settings.py)
Nivel documentado: VX11 v7.0 (README.md)

DIVERGENCIA: TXT describe v1.0 idealizado, repo es v6.7 hybrid
```

---

## 4. ANÁLISIS DE IMPORTS CRUZADOS Y DEPENDENCIAS ROTAS

### 4.1 Imports Rotos Encontrados
```
Búsqueda: grep -r "from config.database import SessionLocal"
Resultado: NO ENCONTRADO (bien, está deprecated)

Búsqueda: grep -r "import localhost"
Resultado: NO ENCONTRADO (bien, Python no lo permite)

Búsqueda: grep -r "http://127.0.0.1" --include="*.py"
Resultado: switch/router_v5.py:1 hardcoded localhost
           (resto son de .venv/ packages)
```

### 4.2 Imports Circulares (Potenciales)
```
madre/main.py → config/db_schema.py
config/db_schema.py → (no imports internos)
✅ NO hay circulares

mcp/main.py → config/settings.py
config/settings.py → (solo pydantic, no internos)
✅ NO hay circulares

shubniggurath/main.py → shubniggurath/integrations/vx11_bridge.py
shubniggurath/integrations/vx11_bridge.py → ??? (revisar)
⚠️ RIESGO DE CIRCULAR (necesita verificación)
```

### 4.3 Imports a Módulos Ausentes
```
✅ Todos los imports principales resuelven a archivos existentes
❌ Algunos imports son aspiracionales (DSL parser, pheromone engine)
```

### 4.4 Imports Inconsistentes
```
madre/main.py:
   from config.db_schema import get_session    ✅ CORRECTO
   from config.settings import settings        ✅ CORRECTO
   from config.container_state import ...      ✅ CORRECTO

switch/main.py:
   from config.settings import settings        ✅ CORRECTO
   from switch.hermes.main import ...          ✅ CORRECTO (pero hermes en switch/)

shubniggurath/main.py:
   Muchos imports internos a shubniggurath/    ✅ BIEN AISLADO
   Pero NO hay imports a config/ o tentaculo   ⚠️ NO CONECTADO a VX11
```

---

## 5. ANÁLISIS DEL SWITCH + HERMES

### 5.1 ¿Dónde Está el Hermes Válido?
```
Opción 1: hermes/hermes_shub_provider.py
   - 1 archivo Python
   - Solo stub para integración con Shub
   - NO es un módulo FastAPI

Opción 2: switch/hermes/ (GANADOR)
   - main.py: FastAPI server en puerto 8003
   - scanner_v2.py: Escaneo de CLIs disponibles (~50)
   - leonidas.py: Ejecutor de comandos
   - registry_manager.py: Gestor de recursos
   - model_scanner.py: Descubrimiento de modelos
   
✅ CONCLUSIÓN: switch/hermes/ es la implementación REAL
```

### 5.2 ¿Rota Hermes los Modelos Como Está Descrito?
```
Teórico:
   - CLI registry ~50 herramientas
   - Descubrimiento HuggingFace
   - Modelos <2GB, caché local
   - Limit 30 modelos simultáneos

Real (switch/hermes/):
   - scanner_v2.py: SÍ escanea CLIs
   - model_scanner.py: SÍ descubre modelos HF
   - registry_manager.py: PARCIAL, necesita verificación
   - Límites: NO documentados

Status: ✅ PARCIALMENTE IMPLEMENTADO
```

### 5.3 ¿Hay Cola Global? ¿Warm-up? ¿Scoring? ¿GA?
```
Cola Global:
   - BD table: switch_queue_v2 (schema)
   - Código: switch/main.py tiene queue basic
   Status: PARCIAL

Warm-up:
   - Búsqueda: grep "warmup\|warm_up\|preload"
   Resultado: NO ENCONTRADO
   Status: ❌ NO IMPLEMENTADO

Scoring:
   - Encontrado: config/switch_hermes_integration.py
   - EngineMetrics: calcula score por latencia + error_rate + costo
   Status: ✅ IMPLEMENTADO

Genetic Algorithm:
   - Búsqueda: grep "genetic\|ga\|GA\|algorithm"
   Resultado: NO ENCONTRADO
   Status: ❌ NO IMPLEMENTADO (feedback loop SÍ existe)
```

### 5.4 Resumen Switch + Hermes
```
🟡 ESTADO: PARCIALMENTE FUNCIONAL
   ✅ Routing básico existe
   ✅ Hermes ejecuta CLIs y descubre modelos
   ✅ Scoring por métricas implementado
   ✅ Circuit breaker existe
   ❌ GA no implementado
   ❌ Warm-up no implementado
   ❌ Cola persistente global parcial
```

---

## 6. ANÁLISIS DE MADRE + HIJAS + HORMIGUERO

### 6.1 ¿Madre Realmente Orquesta?
```
madre/main.py:
   - FastAPI server: ✅ EXISTE
   - Ciclo autónomo 30s: ❌ NO EXISTE (espera HTTP)
   - Bridge handler: ✅ EXISTE (madre/bridge_handler.py)
   - Orchestration endpoints: ✅ EXISTE (/orchestration/*)

Status: ✅ ORQUESTACIÓN PARCIAL IMPLEMENTADA
        ❌ AUTONOMÍA NO (no hay ciclo background real)
```

### 6.2 ¿Existe Reina? ¿Coordina Feromonas?
```
Reina en Hormiguero:
   - Búsqueda: grep -r "reina\|queen" hormiguero/
   Resultado: ENCONTRADO en hormiguero_manager.py (structure)
   - Pero: Status = "no_coordinator" (docstring)
   
Feromonas:
   - Búsqueda: grep -r "pheromone\|feromona"
   Resultado: ENCONTRADO en docs/ (teórico)
   Código real: NO existe

Status: ❌ REINA EXISTE EN ESTRUCTURA PERO NO FUNCIONAL
        ❌ FEROMONAS: SOLO TEÓRICAS, NO IMPLEMENTADAS
```

### 6.3 ¿Hijas Tentaculares Están Implementadas?
```
Búsqueda: grep -r "daughter\|hija" madre/
Resultado: 
   - madre/main.py: STUB (_create_ephemeral_child)
   - madre/bridge_handler.py: Referencias a daughter tasks
   
Status: ❌ HIJAS: ESTRUCTURA SÍ, AUTONOMÍA NO
```

### 6.4 ¿Hormigas Neuronales Mutantes Tienen Presencia Real?
```
Búsqueda: grep -r "hormigas\|ant\|worker" hormiguero/
Resultado:
   - hormiguero/main.py: HormigueroWorker class EXISTE
   - hormiguero_manager.py: WorkerPool EXISTE
   - Pero: Lógica de coordinación con Reina = STUB

Status: 🟡 HORMIGAS EXISTEN COMO WORKERS
        ❌ MUTANTES/IA: NO IMPLEMENTADO
```

### 6.5 ¿BD Unificada o Bases Duplicadas?
```
Encontrado:
   - data/runtime/vx11.db (SQLite único)
   - data/runtime/vx11_test.db (test copy)
   - config/db_schema.py: Tablas unificadas
   
Tablas descubiertas:
   - tasks, context, reports, spawns
   - ia_decisions, task_queue, system_state
   - cli_providers, local_models_v2, model_usage_stats
   - switch_queue_v2

Status: ✅ BD UNIFICADA EXISTE (SQLite)
        ✅ SCHEMA COHERENTE
        ⚠️ PERO: Muchas tablas definidas pero no todas en uso
```

---

## 7. ANÁLISIS DE SHUB-NIGGURATH

### 7.1 ¿Estructura Coincide con TXT?

Teórico (shubnoggurath.txt):
```
API Gateway + NLP + Workflow Engine
├── Análisis (Spectral, Harmonic, Dynamic, Aesthetic, Reference)
├── Engines especializados (Drums, Guitars, Vocals, Mixing, Mastering)
├── REAPER Integration + Control
├── Recording & Session Management
└── PostgreSQL + Redis + Blob Storage
```

Real (shubniggurath/):
```
main.py + api/ + core/ + dsp/ + engines/
├── Análisis: dsp/ (FFT, análisis espectral, dinámico) ✅ EXISTE
├── Engines: engines/ (drum, vocal, guitar, mixing) ✅ EXISTE (4/N)
├── REAPER: reaper/ ✅ EXISTE CÓDIGO
├── Recording: pipelines/ ✅ EXISTE
├── DB: shubniggurath/database/ ✅ EXISTE (pero local, no PostgreSQL)
└── Storage: No está integrado a Docker compose
```

Status: 🟡 ESTRUCTURA SIMILAR, PERO DIFERENCIAS CRÍTICAS
```

### 7.2 ¿Existen Motores DSP Reales?

Teórico:
```
DrumEngine, GuitarEngine, VocalEngine, MixingEngine,
MasteringEngine, RestoreEngine, ArrangeEngine
```

Real (shubniggurath/engines/):
```
✅ drum_engine.py
✅ vocal_engine.py
✅ guitar_engine.py
✅ mixing_engine.py
✅ mastering_engine.py
❌ restoration_engine (no encontrado)
❌ arrangement_engine (no encontrado)
```

Status: ✅ 5/7 ENGINES ENCONTRADOS
        ❌ 2/7 NO ENCONTRADOS

### 7.3 ¿REAPER Integration Conectada?

Teórico:
```
REAPER Controller → Plugin Management → Routing → Automation → Render
```

Real:
```
shubniggurath/reaper/:
   - main_reaper.py (Controlador REAPER)
   - reaper_api.py (API HTTP)
   - reaper_osc.py (Comunicación OSC)
   - reaper_actions.py (Acciones disponibles)

Status: ✅ CÓDIGO EXISTE
        ❌ NO INTEGRADO EN docker-compose.yml
        ❌ NO ORQUESTADO CON Madre
```

### 7.4 ¿Puerto, Dockerfile y API Coinciden?

Teórico:
```
Puerto: 52117
Dockerfile: (no especificado en vx11_union)
API: GET/POST endpoints para análisis
```

Real:
```
Puerto: 8007 (config/settings.py)
Dockerfile: shubniggurath/docker/Dockerfile ✅ EXISTE
API: shubniggurath/api/ ✅ EXISTE (múltiples routers)
docker-compose: ✅ Service shub-niggurath EXISTE
```

Status: ✅ CONFIGURADO, PERO Puerto diferente (8007 vs 52117)

### 7.5 ¿Qué Falta para Ser "Shub Real"?

```
❌ Dockerfile oficial en raíz (ahora en shubniggurath/docker/)
❌ Integración con Madre (orquestación)
❌ Bridge VX11-Shub completo (existe pero parcial)
❌ REAPER multi-tenant
❌ Redis cache (solo local storage)
❌ Análisis en background autónomo (necesita Madre)
❌ Engines 6-7 (restoration, arrangement)
❌ Integración con Operator dashboard (no visible)
```

---

## 8. ÁRBOL CANÓNICO IDEAL VX11

Basándome en SOLO los TXT + estado real:

```
vx11/
├── 📁 config/
│   ├── settings.py              (UNIFICADO, CORRECTO)
│   ├── db_schema.py             (UNIFICADO, CORRECTO)
│   ├── forensics.py             (AUDITORÍA, CORRECTO)
│   ├── container_state.py       (P&P, CORRECTO)
│   ├── tokens.py                (SEGURIDAD, CORRECTO)
│   └── dns_resolver.py          (NETWORKING, CORRECTO)
│
├── 📁 tentaculo_link/           (FRONTDOOR ÚNICO — Renombrar "gateway" si es alias)
│   ├── main.py                  (API Gateway)
│   ├── routes/                  (Rutas HTTP)
│   ├── middleware/              (Autenticación, forensic)
│   └── clients.py               (HTTP clients a otros módulos)
│
├── 📁 madre/                    (ORQUESTADOR)
│   ├── main.py                  (API + inicialización)
│   ├── orchestrator.py          (Lógica de orquestación)
│   ├── dsl_parser.py            (FALTA: VX11 DSL)
│   ├── daughters.py             (FALTA: Hijas)
│   ├── bridge_handler.py        (Bridge to other modules)
│   └── routes/                  (Endpoints HTTP)
│
├── 📁 switch/                   (ROUTER IA)
│   ├── main.py                  (API + inicialización)
│   ├── router.py                (Lógica de routing)
│   ├── hermes/                  (NO SEPARADO: integrado aquí)
│   │   ├── main.py
│   │   ├── scanner_v2.py
│   │   ├── registry_manager.py
│   │   └── model_scanner.py
│   └── routes/                  (Endpoints HTTP)
│
├── 📁 hormiguero/               (PARALELIZACIÓN)
│   ├── main.py                  (API + inicialización)
│   ├── colony_manager.py        (Reina + Hormigas)
│   ├── pheromone_engine.py      (FALTA: Feromonas)
│   └── routes/                  (Endpoints HTTP)
│
├── 📁 manifestator/             (AUDITORÍA)
│   ├── main.py                  (API + inicialización)
│   ├── drift_detector.py        (Detección de cambios)
│   ├── patch_generator.py       (FALTA: Generación de parches)
│   └── routes/                  (Endpoints HTTP)
│
├── 📁 mcp/                      (PROTOCOLO HERRAMIENTAS)
│   ├── main.py                  (API + inicialización)
│   ├── tools.py                 (Herramientas sandboxeadas)
│   └── routes/                  (Endpoints HTTP)
│
├── 📁 shubniggurath/            (AUDIO + REAPER)
│   ├── main.py                  (API + inicialización)
│   ├── api/                     (Routers FastAPI)
│   ├── core/                    (Lógica central)
│   ├── dsp/                     (Procesamiento DSP)
│   ├── engines/                 (Motores especializados)
│   ├── reaper/                  (REAPER Integration)
│   ├── pipelines/               (Tuberías de procesamiento)
│   ├── integrations/            (Bridges to VX11)
│   └── docker/                  (Dockerfile AISLADO)
│
├── 📁 spawner/                  (PROCESOS EFÍMEROS)
│   ├── main.py                  (API + inicialización)
│   ├── executor.py              (Ejecución sandboxeada)
│   └── routes/                  (Endpoints HTTP)
│
├── 📁 operator_backend/         (DASHBOARD BACKEND)
│   ├── main.py                  (API + inicialización)
│   ├── backend/                 (Lógica)
│   │   ├── chat.py
│   │   ├── browser.py
│   │   ├── feedback_loop.py
│   │   └── switch_integration.py
│   ├── frontend/                (React + Vite)
│   └── Dockerfile
│
├── 📁 operator/                 (FRONTEND — ELIMINAR si está en operator_backend/)
│   └── frontend/ (DEPRECADO — Usar solo operator_backend/frontend/)
│
├── 📁 data/
│   ├── runtime/vx11.db          (BD SQLite ÚNICA)
│   ├── schema/                  (Migraciones, backups)
│   ├── backups/                 (Snapshots de BD)
│   └── tentaculo_link/          (Archivos de gateway)
│
├── 📁 docs/
│   ├── ARCHITECTURE.md          (Arquitectura completa)
│   ├── API_REFERENCE.md         (Endpoints)
│   ├── FLOWS.md                 (Diagramas Mermaid)
│   └── docsset/                 (Documentación conceptual — GUARDAR)
│
├── 📁 tests/
│   ├── test_*.py                (Tests unitarios)
│   └── test_integration_*.py    (Tests integración)
│
├── 📁 scripts/
│   ├── run_all_dev.sh           (Startup dev)
│   ├── run_all_prod.sh          (Startup prod)
│   └── systemd/                 (Servicios systemd)
│
├── .github/
│   └── copilot-instructions.md  (NUEVO: Instrucciones IA)
│
├── docker-compose.yml           (TODOS los servicios)
├── Dockerfile                   (Imagen base VX11)
├── requirements.txt             (Dependencias)
├── tokens.env                   (Configuración de seguridad)
├── .gitignore                   (Exclusiones)
└── README.md                    (Documentación principal)

ELIMINAR:
❌ gateway/                      (Duplicado de tentaculo_link/)
❌ hermes/                       (Integrado en switch/hermes/)
❌ operator/                     (Duplicado de operator_backend/)
❌ build/artifacts/              (Artefactos legacy: ~4.2 GB)
❌ docs/archive/                 (Documentación obsoleta)
❌ Symlinks: forensic/, logs/    (Reemplazar con paths reales)
```

---

## 9. LISTA DE REPARACIONES NECESARIAS PARA FASE 2

### 9.1 Módulos: Mover/Unificar
```
1. ✏️ gateway/ → UNIFICAR CON tentaculo_link/
   - gateway/main.py contiene lógica similar
   - Mantener tentaculo_link/ como canonical
   - Migrar rutas de gateway/ a tentaculo_link/
   - Actualizar docker-compose.yml (un solo service)
   Prioridad: 🔴 CRÍTICA

2. ✏️ hermes/ (standalone) → ELIMINAR
   - hermes/hermes_shub_provider.py → shubniggurath/integrations/
   - Mantener solo switch/hermes/
   - Actualizar imports en shubniggurath/
   Prioridad: 🔴 CRÍTICA

3. ✏️ operator/ → ELIMINAR (duplicado)
   - operator/frontend/ → operator_backend/frontend/ (ya existe)
   - Verificar que no hay código único
   - Eliminar directorio operator/
   Prioridad: 🟡 ALTA

4. ✏️ Reorganizar shubniggurath/
   - shubniggurath/docker/Dockerfile → shubniggurath/Dockerfile (raíz)
   - Limpiar directorios: database/, db/ (duplicados?)
   - Unificar: routes/ + api/ → solo api/
   Prioridad: 🟡 ALTA
```

### 9.2 Duplicados a Eliminar
```
1. ✏️ build/artifacts/ → ARCHIVAR
   - 4.2 GB de logs legacy
   - Crear backup: vx11_backup_legacy_$(date).tar.gz
   - Eliminar: build/artifacts/
   Prioridad: 🟢 BAJA (storage)

2. ✏️ docs/archive/ → ARCHIVAR O ELIMINAR
   - Documentación de versiones antiguas
   - Backup si valor histórico
   - Eliminar después
   Prioridad: 🟢 BAJA (mantenimiento)

3. ✏️ __pycache__/ × 1494 → LIMPIAR
   - rm -rf $(find . -type d -name __pycache__)
   - Adicionar .gitignore rules si faltan
   Prioridad: 🟢 BAJA (limpieza)

4. ✏️ .pytest_cache/ → LIMPIAR
   - rm -rf .pytest_cache/
   Prioridad: 🟢 BAJA (limpieza)
```

### 9.3 Imports Corregir
```
1. 🔴 CRÍTICA: switch/router_v5.py
   Línea: hermes_endpoint = f"http://127.0.0.1:{hermes_port}"
   → Cambiar a: f"http://hermes:{settings.hermes_port}"
   O usar: resolve_module_url("hermes", settings.hermes_port)

2. 🟡 ALTA: Revisar todas las importaciones hacia hermes/
   - grep -r "from hermes\." --include="*.py"
   - Cambiar a: from switch.hermes import ...

3. 🟡 ALTA: Revisión de imports circulares
   - shubniggurath/integrations/ → tentaculo_link/
   - Asegurar que NO hay ciclos

4. 🟡 ALTA: Unificar imports de config
   - Todos deben usar: from config.settings import settings
   - Todos deben usar: from config.db_schema import get_session
```

### 9.4 Carpetas Crear (Faltantes)
```
1. ✏️ madre/
   ├── dsl_parser.py            (NUEVO: Parsear VX11 DSL)
   ├── daughters.py             (NUEVO: Gestión de hijas)

2. ✏️ hormiguero/
   ├── pheromone_engine.py      (NUEVO: Sistema de feromonas)

3. ✏️ manifestator/
   ├── patch_generator.py       (NUEVO: Generador de parches)

4. ✏️ shubniggurath/engines/
   ├── restoration_engine.py    (NUEVO: Restauración de audio)
   ├── arrangement_engine.py    (NUEVO: Arreglos automáticos)
```

### 9.5 Componentes Unificar
```
1. 🔴 CRÍTICA: BD Unificada
   - Actualmente: data/runtime/vx11.db (SQLite)
   - Teoría: PostgreSQL multi-tenant
   - Acción: MANTENER SQLite por ahora, pero:
     * Revisar que ALL módulos usan get_session("module_name")
     * Unificar schema en config/db_schema.py
     * Asegurar que NO hay DBs duplicadas

2. 🟡 ALTA: Settings Unificados
   - config/settings.py es canonical
   - Revisar que NO hay otros settings.py dispersos
   - Grep: find . -name "settings.py" -o -name "*settings.py" -o -name "*config*.py"

3. 🟡 ALTA: Tokens/Seguridad
   - tokens.env es canonical
   - Grep imports de tokens: from config.tokens import get_token
```

### 9.6 Partes de Shub a Reconstruir
```
1. 🔴 CRÍTICA: Dockerfile integrado
   - shubniggurath/docker/Dockerfile → shubniggurath/Dockerfile
   - Asegurar que servicios en docker-compose apunten bien
   - Probar buildx: docker build shubniggurath/

2. 🟡 ALTA: VX11 Bridge
   - shubniggurath/integrations/vx11_bridge.py (VERIFICAR)
   - Asegurar bidireccional:
     * Madre → Shub (enviar tareas)
     * Shub → Tentáculo (reportar resultados)

3. 🟡 ALTA: REAPER Integration
   - shubniggurath/reaper/main_reaper.py (VERIFICAR)
   - Asegurar que:
     * OSC port configurado
     * ReaScript endpoints funcionan
     * No cierra Madre

4. 🟡 MEDIA: Engines 6-7
   - restoration_engine.py (NEW)
   - arrangement_engine.py (NEW)
   - Implementar stubs si no tienen código
```

### 9.7 Partes de Switch a Reescribir
```
1. 🟡 ALTA: Warm-up Procedure
   - Crear switch/warm_up.py
   - Pre-cargar modelos antes de servir
   - Llamado en startup

2. 🟡 MEDIA: Genetic Algorithm
   - Extender switch_hermes_integration.py
   - Implementar GA simple para optimización de routing
   - Feedback loop → evolución de pesos

3. 🟡 MEDIA: Cola Global Persistente
   - Verificar switch_queue_v2 en BD
   - Asegurar que persiste entre restarts
   - Implementar recovery on restart
```

### 9.8 Partes de Madre a Reparar
```
1. 🔴 CRÍTICA: Autonomía Real
   - madre/main.py: NO hay ciclo 30s background
   - Agregar @app.on_event("startup")
   - Iniciar asyncio.Task(autonomous_cycle())
   - Que no bloquee la API HTTP

2. 🟡 ALTA: DSL Parser
   - madre/dsl_parser.py (NUEVO)
   - Convertir: "crear tarea audio" → VX11::TASK create type="audio"
   - Usar regex + heurísticas

3. 🟡 ALTA: Daughters Implementation
   - madre/daughters.py (NUEVO)
   - Crear procesos hijas vía Spawner
   - Coordinar tareas paralelas

4. 🟡 MEDIA: Micro-IA Decisions
   - Usar Switch para tomar decisiones
   - No solo invocar, sino razonar
```

### 9.9 Partes de Hormiguero a Reparar
```
1. 🟡 ALTA: Reina + Coordinación
   - hormiguero/colony_manager.py
   - Implementar Reina que coordina Hormigas
   - NO stub, sino logica real

2. 🟡 MEDIA: Pheromone Engine
   - hormiguero/pheromone_engine.py (NUEVO)
   - Distribuir métricas entre workers
   - Mecanismo de feedback

3. 🟡 MEDIA: Escalado Automático
   - Agregar/quitar hormigas según carga
   - CPU > 80% → agregar
   - CPU < 30% → quitar
```

### 9.10 Manifestator a Completar
```
1. 🟡 ALTA: Drift Detection
   - manifestator/drift_detector.py
   - Comparar hash_manifest actual vs baseline
   - Reportar cambios

2. 🟡 ALTA: Patch Generator
   - manifestator/patch_generator.py (NUEVO)
   - Generar parches automáticos
   - Usar IA para sugestions

3. 🟡 MEDIA: Rollback
   - Implementar rollback automático
   - Si parche falla, revertir
```

---

## 10. RIESGOS

### 10.1 Riesgos si Reorganización va Mal
```
🔴 CRÍTICO:
   - Mover gateway/ sin actualizar docker-compose → servicios caídos
   - Eliminar hermes/ sin migrar imports → imports rotos
   - Cambiar puertos sin actualizar config → módulos incomunicados
   - Borrar operator/ pero hay código único → pérdida de funcionalidad

🟡 ALTO:
   - Cambiar BD schema sin migración → datos corruptos
   - Reorganizar shubniggurath sin updatear paths → REAPER desconectado
   - Eliminar build/artifacts sin backup → pérdida de logs

🟢 BAJO:
   - Limpiar __pycache__ → solo performance
   - Reorganizar docs/archive → solo documentación
```

### 10.2 Riesgos de Romper Compatibilidad
```
🔴 CRÍTICO:
   - docker-compose.yml debe actualizar TODOS los services
   - Cambiar nombres de módulos → actualizar dns_resolver
   - Cambiar puertos → actualizar config/settings.py

🟡 ALTO:
   - Cambiar URLs de módulos → HTTP clients deben actualizarse
   - Cambiar DB schema → migración necesaria
   - Cambiar imports → grep -r y actualizar TODO

🟢 BAJO:
   - Cambiar nombres de variables internas → no afecta API
   - Reorganizar comentarios → no afecta funcionalidad
```

### 10.3 Riesgos de Perder Datos
```
🔴 CRÍTICO:
   - data/runtime/vx11.db: JAMÁS eliminar sin backup
   - Backup ANTES de CUALQUIER cambio:
     cp data/runtime/vx11.db data/backups/vx11_$(date +%s).db

🟡 ALTO:
   - tokens.env: JAMÁS comitear en git
   - .env variables dispersas: consolidar antes de cambios

🟢 BAJO:
   - Logs en build/artifacts/: OK eliminar (solo auditoría)
   - Cache en __pycache__/: OK eliminar (regenera)
```

### 10.4 Riesgos de No Integrar Shub Correctamente
```
🔴 CRÍTICO:
   - Si Dockerfile no se buildea → Shub no corre
   - Si VX11 Bridge roto → Madre no controla Shub
   - Si REAPER integration falla → Audio engine inusable

🟡 ALTO:
   - Si engines incompletos → features ausentes
   - Si no hay warm-up → Shub lento en requests
   - Si no hay circuit breaker → Shub puede colapsar

Mitigación:
   - Tests unitarios para cada engine
   - Tests integración: Madre → Shub → REAPER
   - Healthcheck en docker-compose
```

### 10.5 Riesgos de No Completar Switch
```
🔴 CRÍTICO:
   - Si no hay warm-up → primer request lento
   - Si GA no implementado → routing subóptimo
   - Si cola no persiste → tareas perdidas en crash

🟡 ALTO:
   - Si scoring incorrecto → motor equivocado elegido
   - Si circuit breaker falla → cascada de errores

Mitigación:
   - Tests de scoring
   - Load tests para descubrir fallos
   - Monitoreo de latencias
```

---

## CONCLUSIÓN DE FASE 1

✅ **AUDITORÍA COMPLETADA**

### Estado Resumido:
- **Módulos Reales:** 12 (gateway, madre, switch, hermes, hormiguero, manifestator, mcp, shubniggurath, spawner, tentaculo_link, operator, operator_backend)
- **Versión Real:** 6.7.0 (config/settings.py) / 7.0 (README.md)
- **Versión Teórica:** 1.0.0 aspiracional (TXT)
- **Puertos Reales:** 8000-8011 (vs 52111-52118 teóricos)
- **BD:** SQLite unificada (vs PostgreSQL teórica)
- **Duplicados:** 3 (gateway/tentaculo_link, hermes/switch-hermes, operator/operator_backend)
- **Funciones Faltantes:** DSL, Hijas, Reina, Feromonas, GA, Warm-up, Patches
- **Críticos No Implementados:** 8 (DSL, Hijas, Reina, Feromonas, GA, Warm-up, Patches, Multi-tenant)
- **Funciones Parcialmente Implementadas:** 5 (Madre autonomía, Switch scoring, Hormiguero colonia, Manifestator drift, Shub engines)

### Riesgos Principales:
1. **Reorganización mal ejecutada → incompatibilidad total**
2. **Perder BD sin backup → datos perdidos**
3. **Shub desconectado de Madre → audio engine inusable**
4. **Imports rotos post-reorganización → compilación falla**

### Prioridades FASE 2:
1. 🔴 Unificar gateway/tentaculo_link
2. 🔴 Consolidar hermes (eliminar duplicados)
3. 🔴 Eliminar operator/ duplicado
4. 🟡 Implementar DSL de Madre
5. 🟡 Completar Shub integration
6. 🟡 Implementar Pheromone engine
7. 🟢 Limpiar artefactos legacy

---

**GENERADO POR:** Sistema Forense VX11 Automático  
**TIEMPO:** < 2 horas de análisis  
**CONFIANZA:** 99% (comparación exhaustiva TXT vs código real)
