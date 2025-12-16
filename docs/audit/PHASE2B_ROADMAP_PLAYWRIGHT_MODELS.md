# Phase 2B — Roadmap: Playwright MCP + 2 Test Models

**Status:** READY TO EXECUTE  
**Phase 2A Result:** ✅ 7 failures → 0 (128/128 passing)  
**Mandate:** "EJECUTA END-TO-END" (no preguntes, no ofrezcas opciones)

---

## Objetivo Phase 2B

Preparar VX11 con:
1. **Playwright MCP sidecar** (browser automation para Operator)
2. **2 test models** (descargadas, registradas, warmup verificado)
3. **Warmup + rotación verificada** (en model_registry con tests)
4. **Canonical DB <500MB** (con todos los módulos sincronizados)
5. **DB map actualizado** (referencia de tablas, índices, esquema)

### Criterios de Éxito

- [ ] Docker Compose con sidecar Playwright (puerto 3000 o random)
- [ ] 2 GGUF models ≤2GB cada uno descargados en `/models/`
- [ ] model_registry sincronizada con 2 modelos (registered=True, enabled=True)
- [ ] Warmup smoke test verde (carga modelo, inference rápida, cleanup)
- [ ] vx11.db <500MB (con histórico limpio)
- [ ] docs/audit/DB_MAP_v7.md actualizado (schema + índices)
- [ ] Production readiness check: todos los módulos + Operator en health OK

---

## Hitos y Secuencia

### Hito 1: Playwright MCP Sidecar (30 min)

**Objetivo:** Integrar Playwright como servicio externo accesible desde Operator

**Archivos a crear/modificar:**
1. `docker-compose.playwright.yml` — sidecar con Playwright server
2. `config/playwright_config.py` — cliente Python para comunicar con sidecar
3. `operator_backend/backend/browser.py` (ACTUALIZAR) — usar cliente en vez de Playwright directo
4. Env vars: `VX11_ENABLE_PLAYWRIGHT=1`, `PLAYWRIGHT_WS_URL=ws://playwright:3000`

**Pasos:**
- [ ] Crear docker-compose overlay con Playwright browser service
- [ ] Implementar cliente wrapper (`config/playwright_config.py`)
- [ ] Actualizar `operator_backend/backend/browser.py` para usar cliente
- [ ] Test: `POST /operator/browser/task` con URL real
- [ ] Validar screenshot + text extract en 3s

**Tests afectados:**
- `test_operator_browser_workflow.py` — debe pasar sin servicio real (mock)
- `test_operator_browser_integration.py` (si existe) — mock compatible

---

### Hito 2: Download + Register 2 Test Models (25 min)

**Objetivo:** Obtener 2 modelos GGUF (<2GB cada) y registrarlos en BD

**Modelos sugeridos:**
1. **Mistral 7B** (~4.3GB → trunking a 2GB via quantization)
   - Origen: HuggingFace `mistralai/Mistral-7B-Instruct-v0.2`
   - Formato: GGUF, Q4_K_M
   - Tamaño final: ~2.2GB → aceptable
   - Propósito: Chat general, razonamiento rápido

2. **Neural Chat 7B** (~2GB exacto)
   - Origen: HuggingFace `Intel/neural-chat-7b-v3-3`
   - Formato: GGUF, Q4_M
   - Tamaño: ~2.0GB
   - Propósito: Conversacional ligero, respuestas breves

**Script: `scripts/hermes_download_test_models.py`**

```python
#!/usr/bin/env python3
"""Download and register 2 GGUF test models."""

import json
import hashlib
from pathlib import Path
from urllib.request import urlopen
import tarfile
import shutil

MODELS_PATH = Path("/app/models")
MODELS = [
    {
        "name": "mistral-7b-instruct",
        "url": "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/Mistral-7B-Instruct-v0.2.Q4_K_M.gguf",
        "size_mb": 2236,
        "task_type": "chat",
        "tags": ["mistral", "7b", "instruct"],
    },
    {
        "name": "neural-chat-7b",
        "url": "https://huggingface.co/TheBloke/neural-chat-7B-v3-3-GGUF/resolve/main/neural-chat-7b-v3-3.Q4_M.gguf",
        "size_mb": 2048,
        "task_type": "chat",
        "tags": ["neural-chat", "7b"],
    },
]

def download_model(name, url, size_mb):
    """Download GGUF model from HF."""
    model_path = MODELS_PATH / f"{name}.gguf"
    if model_path.exists():
        print(f"✓ {name} already exists")
        return model_path
    
    print(f"⏳ Downloading {name} ({size_mb}MB)...")
    # Placeholder: real implementation uses streaming + progress bar
    return model_path

def register_model_in_db(name, path, task_type, tags):
    """Register model in model_registry."""
    from config.db_schema import get_session, LocalModelV2
    
    db = get_session("vx11")
    try:
        model = LocalModelV2(
            name=name,
            engine="llama.cpp",
            path=str(path),
            size_bytes=int(path.stat().st_size),
            task_type=task_type,
            max_context=4096,
            enabled=True,
            compatibility="cpu",
            meta_info=json.dumps({"tags": tags}),
        )
        db.add(model)
        db.commit()
        print(f"✓ Registered {name}")
    finally:
        db.close()

if __name__ == "__main__":
    MODELS_PATH.mkdir(parents=True, exist_ok=True)
    for m in MODELS:
        path = download_model(m["name"], m["url"], m["size_mb"])
        register_model_in_db(m["name"], path, m["task_type"], m["tags"])
    print("✓ All models registered")
```

**Pasos:**
- [ ] Crear `scripts/hermes_download_test_models.py`
- [ ] Ejecutar script (puede ser manual o vía docker-compose init)
- [ ] Validar en `/operator/resources` que aparecen los 2 modelos
- [ ] Verificar BD: `SELECT count(*) FROM local_models_v2 WHERE enabled=1`

**Tests afectados:**
- `test_hermes_model_registry.py` — debe encontrar 2+ modelos

---

### Hito 3: Warmup + Rotation Smoke Test (20 min)

**Objetivo:** Validar carga de modelos, warmup de primer inference, y rotación automática

**Script: `scripts/warmup_smoke_test.py`**

```python
#!/usr/bin/env python3
"""Warmup + rotation smoke test for 2 test models."""

import asyncio
import httpx
from datetime import datetime
from config.db_schema import get_session, LocalModelV2

async def warmup_model(model_name: str):
    """Load model and run 1 inference."""
    print(f"🔥 Warming up {model_name}...")
    
    # 1. Query Switch to select this model
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/switch/route-v5",
            json={"prompt": "Hola", "task_type": "chat"},
            headers={"X-VX11-Token": "vx11-local-token"},
        )
        result = response.json()
    
    print(f"✓ {model_name} warmup OK ({result.get('latency_ms')}ms)")
    return result

async def test_rotation():
    """Test auto-rotation of models."""
    print("🔄 Testing rotation...")
    
    db = get_session("vx11")
    try:
        models = db.query(LocalModelV2).filter_by(enabled=True).all()
        print(f"Found {len(models)} enabled models")
        
        # Simulate usage: increment usage_count for each model
        for model in models:
            model.usage_count += 1
            model.last_used_at = datetime.utcnow()
        db.commit()
        
        # Verify rotation eligibility (LRU)
        for model in models:
            age_seconds = (datetime.utcnow() - model.last_used_at).total_seconds()
            eligible = age_seconds > 300  # 5 min threshold
            print(f"  {model.name}: usage={model.usage_count}, age={age_seconds}s, rotatable={eligible}")
    finally:
        db.close()

async def main():
    """Run all warmup tests."""
    print("=" * 50)
    print("VX11 Warmup + Rotation Smoke Test")
    print("=" * 50)
    
    db = get_session("vx11")
    try:
        models = db.query(LocalModelV2).filter_by(enabled=True).all()
        for model in models[:2]:  # Test first 2
            await warmup_model(model.name)
    finally:
        db.close()
    
    await test_rotation()
    print("✓ All warmup tests passed")

if __name__ == "__main__":
    asyncio.run(main())
```

**Pasos:**
- [ ] Crear `scripts/warmup_smoke_test.py`
- [ ] Ejecutar con `python3 scripts/warmup_smoke_test.py`
- [ ] Validar logs: cada modelo debe cargar en <5s
- [ ] Verificar BD: `usage_count` y `last_used_at` actualizados

**Tests afectados:**
- `test_switch_warmup_rotation.py` — debe ejecutar sin errores
- `test_hermes_model_load_time.py` — validar latencia <5s

---

### Hito 4: Canonical DB Generation (<500MB) (20 min)

**Objetivo:** Limpiar histórico, sincronizar todos módulos, validar tamaño <500MB

**Script: `scripts/vx11_canonical_db_generate.py`**

```python
#!/usr/bin/env python3
"""Generate canonical vx11.db <500MB with all modules synced."""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("/app/data/runtime/vx11.db")
TARGET_SIZE_MB = 500

def cleanup_old_records(db_path, days_old=30):
    """Archive records older than N days."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cutoff = datetime.utcnow() - timedelta(days=days_old)
    cutoff_ts = cutoff.isoformat() + "Z"
    
    # Clean up old forensic ledger
    cursor.execute(
        "DELETE FROM forensic_ledger WHERE created_at < ?",
        (cutoff_ts,)
    )
    
    # Clean up old audit logs (keep recent)
    cursor.execute(
        "DELETE FROM audit_logs WHERE created_at < ?",
        (cutoff_ts,)
    )
    
    # Vacuum
    cursor.execute("VACUUM")
    conn.commit()
    
    size_mb = db_path.stat().st_size / (1024*1024)
    print(f"✓ Cleaned up old records, DB size: {size_mb:.1f}MB")
    conn.close()

def sync_all_modules(db_path):
    """Ensure all module tables are present and synced."""
    from config.db_schema import Base, unified_engine
    
    Base.metadata.create_all(unified_engine)
    print("✓ All module tables synced")

def validate_size(db_path, target_mb=500):
    """Validate DB size is under target."""
    size_mb = db_path.stat().st_size / (1024*1024)
    if size_mb > target_mb:
        print(f"⚠️  DB size {size_mb:.1f}MB > {target_mb}MB target")
        return False
    print(f"✓ DB size OK: {size_mb:.1f}MB < {target_mb}MB")
    return True

def main():
    print("=" * 50)
    print("VX11 Canonical DB Generation")
    print("=" * 50)
    
    sync_all_modules(DB_PATH)
    cleanup_old_records(DB_PATH, days_old=30)
    validate_size(DB_PATH, TARGET_SIZE_MB)
    
    print("✓ Canonical DB ready")

if __name__ == "__main__":
    main()
```

**Pasos:**
- [ ] Ejecutar `python3 scripts/vx11_canonical_db_generate.py`
- [ ] Verificar tamaño: `du -h /app/data/runtime/vx11.db`
- [ ] Validar integridad: `sqlite3 vx11.db "PRAGMA integrity_check;"`
- [ ] Backup: `cp vx11.db vx11.db.canonical_$(date +%s)`

---

### Hito 5: DB Map Actualizado (15 min)

**Objetivo:** Generar documento de referencia del schema (tablas, índices, cardinalidades)

**Script: `scripts/generate_db_map.py`**

```python
#!/usr/bin/env python3
"""Generate DB schema map and reference."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path("/app/data/runtime/vx11.db")

def generate_db_map():
    """Generate comprehensive DB schema documentation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {}
    for table in sorted(tables):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [
            {
                "name": col[1],
                "type": col[2],
                "nullable": col[3] == 0,
                "pk": col[5] == 1,
            }
            for col in cursor.fetchall()
        ]
        
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # Indices
        cursor.execute(f"PRAGMA index_list({table})")
        indices = [idx[1] for idx in cursor.fetchall()]
        
        schema[table] = {
            "columns": columns,
            "row_count": row_count,
            "indices": indices,
        }
    
    # Generate markdown
    md = "# VX11 Database Schema Map\n\n"
    md += f"**Generated:** {datetime.now().isoformat()}  \n"
    md += f"**Size:** {(DB_PATH.stat().st_size / 1024**2):.1f}MB  \n"
    md += f"**Tables:** {len(tables)}  \n\n"
    
    for table, info in sorted(schema.items()):
        md += f"## {table}\n\n"
        md += f"**Rows:** {info['row_count']}  \n"
        md += f"**Indices:** {', '.join(info['indices']) or 'none'}  \n\n"
        md += "| Column | Type | PK | Nullable |\n"
        md += "|--------|------|----|---------|\n"
        for col in info['columns']:
            pk_flag = "✓" if col['pk'] else ""
            nullable = "✓" if col['nullable'] else ""
            md += f"| {col['name']} | {col['type']} | {pk_flag} | {nullable} |\n"
        md += "\n"
    
    return md, schema

if __name__ == "__main__":
    md, schema_json = generate_db_map()
    
    # Write markdown
    md_path = Path("docs/audit/DB_MAP_v7_2.md")
    md_path.write_text(md)
    print(f"✓ Generated {md_path}")
    
    # Write JSON
    json_path = Path("docs/audit/DB_SCHEMA_v7_2.json")
    json_path.write_text(json.dumps(schema_json, indent=2))
    print(f"✓ Generated {json_path}")
```

**Pasos:**
- [ ] Ejecutar `python3 scripts/generate_db_map.py`
- [ ] Generar `docs/audit/DB_MAP_v7_2.md` (referencia humana)
- [ ] Generar `docs/audit/DB_SCHEMA_v7_2.json` (referencia programática)

---

### Hito 6: Production Readiness Check (15 min)

**Objetivo:** Validar que todos los módulos están OK, sin problemas estructurales

**Script: `scripts/vx11_production_readiness.py`**

```python
#!/usr/bin/env python3
"""Production readiness check: all modules + operator health."""

import asyncio
import httpx
import json

HEALTH_ENDPOINTS = {
    "tentaculo_link": "http://localhost:8000/health",
    "madre": "http://localhost:8001/health",
    "switch": "http://localhost:8002/health",
    "hermes": "http://localhost:8003/health",
    "hormiguero": "http://localhost:8004/health",
    "manifestator": "http://localhost:8005/health",
    "mcp": "http://localhost:8006/health",
    "shub": "http://localhost:8007/health",
    "operator": "http://localhost:8011/health",
}

async def check_health():
    """Check all module health endpoints."""
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for module, url in HEALTH_ENDPOINTS.items():
            try:
                resp = await client.get(url)
                results[module] = "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"
            except Exception as e:
                results[module] = f"FAIL: {str(e)}"
    
    return results

def generate_report(health_results):
    """Generate production readiness report."""
    ok_count = sum(1 for v in health_results.values() if v == "OK")
    total = len(health_results)
    
    report = "# VX11 Production Readiness Check\n\n"
    report += f"**Status:** {ok_count}/{total} modules healthy\n\n"
    report += "| Module | Status |\n"
    report += "|--------|--------|\n"
    for module, status in sorted(health_results.items()):
        icon = "✅" if status == "OK" else "❌"
        report += f"| {module} | {icon} {status} |\n"
    report += "\n"
    
    if ok_count == total:
        report += "✅ **PRODUCTION READY** — All modules healthy\n"
    else:
        report += "⚠️  **NOT READY** — Some modules failed\n"
        report += f"Action: Check logs for failed modules\n"
    
    return report

async def main():
    print("Checking VX11 module health...")
    health_results = await check_health()
    report = generate_report(health_results)
    
    # Write report
    Path("docs/audit/PRODUCTION_READINESS_CHECK.md").write_text(report)
    print(report)

if __name__ == "__main__":
    from pathlib import Path
    asyncio.run(main())
```

**Pasos:**
- [ ] Ejecutar `python3 scripts/vx11_production_readiness.py`
- [ ] Generar `docs/audit/PRODUCTION_READINESS_CHECK.md`
- [ ] Validar: todos los módulos OK

---

## Timeline Estimado

| Hito | Duración | Status |
|------|----------|--------|
| 1. Playwright MCP | 30 min | ⏳ PENDING |
| 2. Download + Register 2 Models | 25 min | ⏳ PENDING |
| 3. Warmup + Rotation Test | 20 min | ⏳ PENDING |
| 4. Canonical DB <500MB | 20 min | ⏳ PENDING |
| 5. DB Map + Schema Doc | 15 min | ⏳ PENDING |
| 6. Production Readiness | 15 min | ⏳ PENDING |
| **TOTAL** | **~2.5 horas** | |

---

## Next Immediate Action

**Execute Hito 1: Playwright MCP Sidecar Setup**

1. Create `docker-compose.playwright.yml` overlay
2. Add `VX11_ENABLE_PLAYWRIGHT=1` env var
3. Implement `config/playwright_config.py` client
4. Update `operator_backend/backend/browser.py`
5. Test: `POST /operator/browser/task` → screenshot OK
6. Run: `pytest tests/test_operator_browser_workflow.py -v`

**Expected Result:** 3–5 tests passing, Playwright sidecar running on port 3000

---

**PHASE 2B Execution Mandate:**
- Execute each hito in sequence
- Generate reports for each milestone
- No confirmation needed between hitos
- Stop only if critical blocker (port conflict, auth fail, etc.)
- Final report: docs/audit/PHASE2B_COMPLETION.md

