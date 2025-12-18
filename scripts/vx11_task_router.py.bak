#!/usr/bin/env python3
"""


























































































































































































































































Versión: 2.0Generated: 2025-12-15T15:45:00Z  **Próxima sesión:** Copiar este prompt y pegarlo en un chat nuevo con agente genérico GPT-5-mini.---- [ ] ✅ Estar listo para recibir comandos operativos- [ ] ✅ Reconocer estructura VX11 completa- [ ] ✅ Tener configurado VS Code para auto-aprobación- [ ] ✅ Presentar estado del sistema en español coloquial- [ ] ✅ Ejecutar diagnóstico inicial silenciosoTras activar este prompt, el agente debe:## ✅ CHECKLIST FINAL---4. 📋 **Reportar** en `docs/audit/EMERGENCIA_$(date).md`3. 💾 **Usar backups** en `data/backups/`2. 📊 **Consultar BD** para último estado conocido1. ❌ **No entrar en bucle** de diagnósticosSi algo falla:## 🚨 PROTOCOLO DE EMERGENCIA---```└── tokens.env (read-only)├── operador_ui/ (8011/8020)├── switch/ (8002)├── madre/ (8001)├── tentaculo_link/ (puerto 8000)│   └── vx11_runtime_truth.py ← Diagnóstico│   ├── vx11_task_router.py ← Router de tareas│   ├── vx11_agent_bootstrap.py ← Auto-ejecutar├── scripts/│   └── vx11.db (85 tablas)├── data/runtime/│   └── tokens.py│   ├── db_schema.py│   ├── settings.py├── config/│   └── settings.json (auto-aprobación configurada)├── .vscode/│   └── copilot-instructions.md│   ├── workflows/│   ├── agents/vx11.agent.md├── .github//home/elkakas314/vx11/```El agente debe reconocer y usar:## 📁 ESTRUCTURA ESPERADA---```  -d '{"action": "diagnóstico", "system": "vx11"}'  -H "Content-Type: application/json" \curl -s -X POST http://localhost:8000/vx11/context7/enrich \```bashPara cada operación importante, consulta Context7 automáticamente:## 🧠 CONTEXT7 INTEGRADO---✅ **SÍ:** "Diagnosticando..."❌ **NO:** "Procederé a ejecutar un diagnóstico del sistema"  ✅ **SÍ:** "Módulos activos: Tentáculo Link (8000), Madre (8001), Switch (8002)"❌ **NO:** "A continuación se presenta una tabla con los módulos activos"  ✅ **SÍ:** "Tentáculo Link funcionando en puerto 8000"❌ **NO:** "El módulo Tentáculo Link está en estado operativo en el puerto 8000"  ### Ejemplos:- ✅ **Sin explicaciones largas** a menos que sean necesarias- ✅ **Respuestas directas y operativas**- ✅ **Evitar tablas automáticas** (solo si se piden)- ✅ **Español coloquial siempre**### Reglas:## 💬 ESTILO DE COMUNICACIÓN---```  -d '{"instruction":"optimizar rutas"}'  -H "X-VX11-Token: vx11-local-token" \curl -X POST http://localhost:8002/prompt \# Ejemplo: @vx11 inyecta "optimizar rutas" en switch```bashInyecta instrucción en módulo activo:### 5. `@vx11 inyecta [prompt] en [módulo]````PYEOF        print(f"Removido: {log.name}")        log.unlink()    if datetime.fromtimestamp(log.stat().st_mtime) < datetime.now() - timedelta(days=7):for log in logs_dir.glob("*.log"):logs_dir = Path("/home/elkakas314/vx11/logs")# Limpiar logs >7 díasfrom datetime import datetime, timedeltafrom pathlib import Pathimport ospython3 << 'PYEOF'```bashMantenimiento inteligente:### 4. `@vx11 limpia````# Si falla → reiniciar container o diagnosticarcurl -s http://localhost:8002/health | jq .# Ejemplo: @vx11 repara switch```bashDiagnóstico y reparación automática:### 3. `@vx11 repara [servicio]`**Detecta automáticamente:** chat, audio, code, system, task, scan, audit```python3 scripts/vx11_task_router.py "descripción de la tarea"```bashEjecuta tarea automáticamente en el módulo adecuado:### 2. `@vx11 ejecuta [descripción]`- Recursos (CPU/RAM)- Workflows configurados- Estado de BD- Módulos activos (puertos 8000-8020)**Retorna:**```curl -s http://localhost:8000/health | jq .python3 scripts/vx11_runtime_truth.py 2>&1```bashDiagnóstico completo del sistema:### 1. `@vx11 status`## 📊 COMANDOS OPERATIVOS---- Exposición de tokens/secrets- `git reset --hard`- `docker compose down`- `rm -rf` sin backup claro- `sudo` cualquier comando**Requiere confirmación:**- Git status/diff/log- Scripts de VX11- Consultas HTTP locales- Lectura de archivos- Comandos de diagnóstico**Auto-aprobado:**- ✅ **Python formatter** (black) listo- ✅ **REST Client** configurado con URLs de todos los módulos- ✅ **Denylist** de comandos destructivos (sudo, rm -rf, git reset --hard)- ✅ **Auto-aprobación** de comandos seguros (lectura, git status, python, curl)La configuración está en `.vscode/settings.json` con:## ⚙️ CONFIGURACIÓN VS CODE---```¿Qué necesitas operar hoy?• @vx11 inyecta ... → Inyectar instrucción en módulo• @vx11 limpia      → Mantenimiento automático• @vx11 repara ...  → Diagnóstico y reparación• @vx11 ejecuta ... → Ejecutar tarea automáticamente• @vx11 status      → Estado completo del sistemaComandos disponibles:Rama git: copilot-vx11-agent-hardeningBD: 85 tablas presentesMódulos: 9/10 compiladosEstado: OPERATIVO ✅Sistema detectado en: /home/elkakas314/vx11🔧 AGENTE VX11 ACTIVADO```Genera un mensaje como este:### Paso 2: Presentar Estado```PYEOFdb.close()print(f"Tablas en BD: {len(inspector.get_table_names())}")inspector = inspect(db.get_bind())db = get_session()from sqlalchemy import inspectfrom config.db_schema import get_sessionpython3 << 'PYEOF'# 4. Consultar BDgit log --oneline -1# 3. Git statuspython3 scripts/vx11_agent_bootstrap.py 2>&1 | tail -15# 2. Verificar estructura claveecho "__VX11_AGENTE_ACTIVO__"pwd && whoamicd /home/elkakas314/vx11# 1. Estado básico del sistema```bashEjecuta estos comandos SILENCIOSAMENTE:### Paso 1: Diagnóstico Inmediato## 🎯 PROTOCOLO DE AUTO-CONFIGURACIÓN---4. ✅ Espera comandos operativos3. ✅ Presenta estado del sistema en **español coloquial**2. ✅ Configura el entorno para operatividad máxima1. ✅ Lee el estado actual del sistema VX11Cuando actives este prompt en un **chat nuevo con agente genérico y modelo GPT-5-mini**, **automáticamente**:## 📋 INSTRUCCIONES DE INICIO---**Status:** ✅ LISTO PARA DEPLOY**Versión:** 2.0 (15 Diciembre 2025)  vx11_task_router.py - Auto-router de tareas para agente VX11
Detecta tipo de tarea y enruta al módulo más apropiado.
Soporta fallback y registro en BD.
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

import sys
import json
import httpx
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data/runtime/vx11.db"
API_TOKEN = "vx11-local-token"

# Keywords para detectar tipo de tarea
KEYWORDS = {
    "chat": ["chat", "pregunta", "explica", "qué es", "cómo", "ayuda"],
    "audio": ["audio", "música", "sonido", "wav", "mp3", "track", "mixing"],
    "code": ["código", "python", "js", "ts", "bug", "función"],
    "system": ["sistema", "vx11", "estado", "health", "status"],
    "task": ["tarea", "ejecuta", "corre", "run", "spawn", "hija"],
    "scan": ["escanea", "detecta", "encuentra", "identifica"],
    "audit": ["audita", "revisa", "valida", "drift", "patch"],
}

ROUTER = [
    ("TentaculoLink", "http://localhost:8000", "/vx11/intent"),
    ("Madre", "http://localhost:8001", "/madre/daughter/spawn"),
    ("Spawner", "http://localhost:8008", "/spawner/spawn"),
    ("MCP", "http://localhost:8006", "/mcp/sandbox/exec_cmd"),
]


def get_db():
    """Obtener conexión a BD."""
    conn = sqlite3.connect(str(DB_PATH))
    return conn


def ensure_copilot_tables():
    """Crear tabla copilot_actions_log si no existe."""
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS copilot_actions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                status TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        conn.commit()
    finally:
        conn.close()


def log_action(
    source: str,
    action: str,
    target: Optional[str] = None,
    status: str = "pending",
    details: str = "",
):
    """Registrar acción en BD."""
    ensure_copilot_tables()
    conn = get_db()
    try:
        conn.execute(
            """
            INSERT INTO copilot_actions_log (timestamp, source, action, target, status, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                datetime.utcnow().isoformat() + "Z",
                source,
                action,
                target,
                status,
                details,
            ),
        )
        conn.commit()
        cursor = conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]
    finally:
        conn.close()


async def try_http_post(
    base_url: str, endpoint: str, payload: dict
) -> tuple[int, dict]:
    """Intentar POST HTTP a endpoint."""
    url = f"{base_url}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"X-VX11-Token": API_TOKEN, "Content-Type": "application/json"},
            )
            try:
                return resp.status_code, resp.json()
            except:
                return resp.status_code, {"text": resp.text}
    except httpx.TimeoutException:
        return 408, {"error": "timeout"}
    except Exception as e:
        return 500, {"error": str(e)}


async def enqueue_task(text: str):
    """Encolar tarea con router."""
    print(f"[ENQUEUE] Task: {text[:50]}...")

    ensure_copilot_tables()

    # Construir payload
    payload = {
        "source": "copilot-agent",
        "intent_type": "task",
        "description": text,
        "priority": 5,
    }

    # Intentar router secuencialmente
    for target, base_url, endpoint in ROUTER:
        print(f"  → Intentando {target} {base_url}{endpoint}...", end=" ", flush=True)

        status_code, result = await try_http_post(base_url, endpoint, payload)

        if 200 <= status_code < 300:
            task_id = result.get("task_id") or result.get("id") or str(status_code)
            print(f"✅ {status_code}")
            log_action("agent", "enqueue", target, "accepted", json.dumps(result))
            print(f"✅ Task {task_id} enqueued at {target}")
            return 0

        print(f"❌ {status_code}")

    # Fallback a terminal (último recurso)
    print(f"  → Fallback: Terminal")
    log_action("agent", "enqueue", "Terminal", "fallback", text)
    print(f"⚠️ No endpoint disponible. Task registrada para ejecución manual.")
    return 1


async def watch_task(task_id: str):
    """Monitorear task en BD."""
    print(f"[WATCH] Task {task_id}")

    conn = get_db()
    try:
        cursor = conn.execute(
            "SELECT * FROM copilot_actions_log WHERE id = ? ORDER BY timestamp DESC LIMIT 1",
            (int(task_id),),
        )
        row = cursor.fetchone()
        if row:
            print(f"  Timestamp: {row[1]}")
            print(f"  Source: {row[2]}")
            print(f"  Action: {row[3]}")
            print(f"  Target: {row[4]}")
            print(f"  Status: {row[5]}")
            print(f"  Details: {row[6]}")
        else:
            print(f"❌ Task no encontrada")
    finally:
        conn.close()


def main():
    if len(sys.argv) < 2:
        print("Uso: vx11_task_router.py <enqueue|watch> [args]")
        return 1

    cmd = sys.argv[1]

    if cmd == "enqueue":
        if len(sys.argv) < 3:
            print("Uso: vx11_task_router.py enqueue '<texto>'")
            return 1
        text = sys.argv[2]

        # Usar asyncio
        import asyncio

        return asyncio.run(enqueue_task(text))

    elif cmd == "watch":
        if len(sys.argv) < 3:
            print("Uso: vx11_task_router.py watch <task_id>")
            return 1
        task_id = sys.argv[2]

        import asyncio

        asyncio.run(watch_task(task_id))
        return 0

    else:
        print(f"❌ Comando desconocido: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())