#!/usr/bin/env python3
"""
vx11_agent_bootstrap.py - Auto-configuración del agente VX11
Ejecutado automáticamente al inicio del agente
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_LOG = REPO_ROOT / "logs" / "agent_bootstrap.log"


def log_message(msg: str, level: str = "INFO"):
    """Registra mensaje de bootstrap."""
    BOOTSTRAP_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat() + "Z"
    with open(BOOTSTRAP_LOG, "a") as f:
        f.write(f"{timestamp} [{level}] {msg}\n")
    if level == "ERROR":
        print(f"❌ {msg}")
    else:
        print(f"✅ {msg}")


def bootstrap_agent():
    """Ejecuta bootstrap del agente."""
    print("🔧 AGENTE VX11 - AUTO-BOOTSTRAP")
    print("=" * 50)

    # 1. Validar estructura
    print("\n1️⃣  Validando estructura...")
    required_dirs = [
        ".github",
        "config",
        "data/runtime",
        "scripts",
        "tentaculo_link",
        "madre",
        "switch",
    ]
    for d in required_dirs:
        path = REPO_ROOT / d
        if path.exists():
            log_message(f"✓ {d} presente")
        else:
            log_message(f"✗ {d} FALTANTE", level="ERROR")

    # 2. Validar Python
    print("\n2️⃣  Validando Python...")
    try:
        result = subprocess.run(
            ["python3", "--version"], capture_output=True, text=True
        )
        log_message(f"Python: {result.stdout.strip()}")
    except Exception as e:
        log_message(f"Python error: {str(e)}", level="ERROR")

    # 3. Validar módulos principales
    print("\n3️⃣  Compilando módulos...")
    modules = ["tentaculo_link", "madre", "switch", "hormiguero", "manifestator"]
    for mod in modules:
        try:
            subprocess.run(
                ["python3", "-m", "py_compile", f"{mod}/main.py"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=True,
                timeout=5,
            )
            log_message(f"✓ {mod} compila correctamente")
        except Exception as e:
            log_message(f"✗ {mod} error: {str(e)[:50]}", level="ERROR")

    # 4. Validar BD
    print("\n4️⃣  Verificando BD SQLite...")
    db_path = REPO_ROOT / "data" / "runtime" / "vx11.db"
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        log_message(f"✓ BD encontrada ({size_mb:.1f}MB)")
    else:
        log_message(f"✗ BD no encontrada", level="ERROR")

    # 5. Validar tokens
    print("\n5️⃣  Verificando tokens...")
    tokens_path = REPO_ROOT / "tokens.env"
    if tokens_path.exists():
        with open(tokens_path) as f:
            lines = len(f.readlines())
        log_message(f"✓ Tokens: {lines} credenciales cargadas")
    else:
        log_message(f"✗ tokens.env no encontrado", level="ERROR")

    # 6. Estado de git
    print("\n6️⃣  Git status...")
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        commit = result.stdout.strip()
        log_message(f"✓ Git: commit {commit}")
    except Exception as e:
        log_message(f"✗ Git error: {str(e)[:50]}", level="ERROR")

    print("\n" + "=" * 50)
    print("✅ AGENTE VX11 LISTO PARA OPERAR")
    print(f"\n📋 Log: {BOOTSTRAP_LOG}")

    return True


if __name__ == "__main__":
    bootstrap_agent()
