#!/usr/bin/env python3
"""
vx11_scan_and_map.py — VX11 Agent Bootstrap: scan repo + BD + crea mapa.
Ejecutado automáticamente en cada arranque del agente vx11.
Estado: PRODUCCIÓN (aditivo, sin romper nada).
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py


import sys
import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
import subprocess

REPO_ROOT = Path(__file__).parent.parent
DB_PATHS = [
    REPO_ROOT / "data" / "runtime" / "vx11.db",
    REPO_ROOT / "data" / "vx11.db",
]

CANONICAL_PATHS = {
    "config/module_template.py": "Module template (FastAPI factory)",
    "config/db_schema.py": "BD schema unificada",
    "config/settings.py": "Settings + env vars",
    "config/tokens.py": "Token management",
    ".github/copilot-instructions.md": "Instrucciones canónicas",
    "docs/ARCHITECTURE.md": "Visión general",
    "tentaculo_link/main.py": "Gateway (8000)",
    "operator_backend/backend/main_v7.py": "Operator Backend (8011)",
    "docker-compose.yml": "Orquestación de servicios",
}

def find_db():
    """Localizar BD existente."""
    for db_path in DB_PATHS:
        if db_path.exists():
            return db_path
    return None

def init_agent_tables(conn):
    """Crear tablas copilot_* si no existen (aditivo, seguro)."""
    cursor = conn.cursor()
    
    tables = [
        """
        CREATE TABLE IF NOT EXISTS copilot_repo_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            file_hash TEXT,
            file_type TEXT,
            status TEXT DEFAULT 'tracked',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS copilot_runtime_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT UNIQUE,
            host TEXT DEFAULT 'localhost',
            port INTEGER,
            health_url TEXT,
            status TEXT DEFAULT 'unknown',
            last_check TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS copilot_actions_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            mode TEXT,
            files_touched INTEGER DEFAULT 0,
            git_commit TEXT,
            status TEXT,
            notes TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS copilot_workflows_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_file TEXT UNIQUE,
            workflow_name TEXT,
            triggers TEXT,
            jobs TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
    ]
    
    for sql in tables:
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError as e:
            print(f"⚠️ Table creation skipped: {e}")
    
    conn.commit()

def compute_file_hash(path):
    """Calcular SHA256 de un archivo."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def scan_canonical_paths(conn):
    """Escanear paths canónicos y registrar en BD."""
    cursor = conn.cursor()
    
    for path_str, description in CANONICAL_PATHS.items():
        full_path = REPO_ROOT / path_str
        
        if full_path.exists():
            file_hash = compute_file_hash(full_path) if full_path.is_file() else None
            file_type = "dir" if full_path.is_dir() else "file"
            status = "✓ found"
            
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO copilot_repo_map (path, file_hash, file_type, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (path_str, file_hash, file_type, status)
                )
            except sqlite3.Error as e:
                print(f"⚠️ Error inserting {path_str}: {e}")
        else:
            try:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO copilot_repo_map (path, file_hash, file_type, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (path_str, None, "file", "✗ MISSING")
                )
            except sqlite3.Error as e:
                print(f"⚠️ Error inserting {path_str}: {e}")
    
    conn.commit()

def scan_runtime_services():
    """Detectar servicios en puerto 8000-8020 (healthchecks)."""
    services = [
        ("tentaculo_link", "localhost", 8000, "/health"),
        ("madre", "localhost", 8001, "/madre/health"),
        ("switch", "localhost", 8002, "/switch/health"),
        ("hermes", "localhost", 8003, "/hermes/health"),
        ("hormiguero", "localhost", 8004, "/hormiguero/health"),
        ("manifestator", "localhost", 8005, "/manifestator/health"),
        ("mcp", "localhost", 8006, "/mcp/health"),
        ("shub", "localhost", 8007, "/shub/health"),
        ("spawner", "localhost", 8008, "/spawner/health"),
        ("operator_backend", "localhost", 8011, "/health"),
    ]
    
    active_services = []
    for service_name, host, port, health_url in services:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            status = "up" if result == 0 else "down"
            active_services.append((service_name, host, port, health_url, status))
        except Exception:
            active_services.append((service_name, host, port, health_url, "unknown"))
    
    return active_services

def register_services(conn, services):
    """Registrar servicios en BD."""
    cursor = conn.cursor()
    for service_name, host, port, health_url, status in services:
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO copilot_runtime_services
                (service_name, host, port, health_url, status, last_check)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (service_name, host, port, health_url, status, datetime.utcnow())
            )
        except sqlite3.Error as e:
            print(f"⚠️ Error registering service {service_name}: {e}")
    conn.commit()

def generate_bootstrap_report(conn):
    """Generar reporte de bootstrap."""
    report_path = REPO_ROOT / "docs" / "audit" / "VX11_AGENT_BOOTSTRAP_REPORT.md"
    
    # Leer estado de BD
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM copilot_repo_map WHERE status='✓ found'")
    found_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM copilot_repo_map WHERE status='✗ MISSING'")
    missing_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM copilot_runtime_services")
    services = cursor.fetchall()
    
    # Contar BD existentes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    report = f"""# VX11 Agent Bootstrap Report

**Generated:** {datetime.utcnow().isoformat()}Z  
**Repo:** {REPO_ROOT}  
**DB:** {REPO_ROOT / 'data/runtime/vx11.db'}

## Canonical Paths

- ✓ Found: {found_count} files
- ✗ Missing: {missing_count} files

"""
    
    cursor.execute("SELECT path, status FROM copilot_repo_map ORDER BY path")
    for path, status in cursor.fetchall():
        report += f"- {status}: {path}\n"
    
    report += f"\n## Runtime Services\n\n"
    report += "| Service | Host | Port | Status |\n"
    report += "|---------|------|------|--------|\n"
    
    for row in services:
        service, host, port, health_url, status, _ = row[1:7]
        status_icon = "🟢" if status == "up" else "🔴"
        report += f"| {service} | {host} | {port} | {status_icon} {status} |\n"
    
    report += f"\n## Database State\n\nTables: {len(tables)}\n"
    for table in tables:
        report += f"- {table[0]}\n"
    
    # Escribir reporte
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    
    return report_path

def main():
    print("=" * 70)
    print("VX11 Agent Bootstrap: Repo Scan + BD Map + Report")
    print("=" * 70)
    
    # Localizar BD
    db_path = find_db()
    if not db_path:
        print("\n⚠️ No database found. Creating in data/runtime/vx11.db...")
        db_path = REPO_ROOT / "data" / "runtime" / "vx11.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nDatabase: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        
        # Crear tablas
        print("\n1. Initializing copilot_* tables...")
        init_agent_tables(conn)
        print("   ✓ Tables ready")
        
        # Scan canonical paths
        print("\n2. Scanning canonical paths...")
        scan_canonical_paths(conn)
        print("   ✓ Canonical paths scanned")
        
        # Scan runtime services
        print("\n3. Checking runtime services (ports 8000-8020)...")
        services = scan_runtime_services()
        register_services(conn, services)
        active = sum(1 for s in services if s[4] == "up")
        print(f"   ✓ {active}/{len(services)} services up")
        
        # Generate report
        print("\n4. Generating bootstrap report...")
        report_path = generate_bootstrap_report(conn)
        print(f"   ✓ Report: {report_path.relative_to(REPO_ROOT)}")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ Bootstrap complete. Agent ready.")
        print("=" * 70)
        return 0
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())