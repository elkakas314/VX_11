#!/usr/bin/env python3
"""
copilot_repo_scan.py — Scan repo y crea tablas BD con prefijo copilot_ (aditivo, seguro).
Estado: AUTO-GENERATED (safe).
"""

import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "runtime" / "vx11.db"

def init_copilot_tables(conn, dry_run=False):
    """Crea tablas copilot_* si no existen."""
    errors = []
    cursor = conn.cursor()
    
    tables = [
        """
        CREATE TABLE IF NOT EXISTS copilot_repo_scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            git_hash TEXT,
            repo_files_count INTEGER,
            notes TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS copilot_repo_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id INTEGER,
            file_path TEXT,
            file_size INTEGER,
            file_hash TEXT,
            FOREIGN KEY (scan_id) REFERENCES copilot_repo_scans(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS copilot_agent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            agent_name TEXT,
            session_id TEXT,
            action TEXT,
            status TEXT,
            result TEXT
        );
        """
    ]
    
    for sql in tables:
        try:
            if not dry_run:
                cursor.execute(sql)
        except Exception as e:
            errors.append(f"Error creating table: {e}")
    
    if not dry_run:
        conn.commit()
    
    return errors

def scan_repo_files():
    """Obtiene lista de archivos del repo."""
    files = []
    exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "build", "dist", ".pytest_cache"}
    
    for p in REPO_ROOT.rglob("*"):
        if p.is_file():
            # Skip excluded
            if any(ex in p.parts for ex in exclude_dirs):
                continue
            files.append({
                "path": str(p.relative_to(REPO_ROOT)),
                "size": p.stat().st_size
            })
    
    return files

def insert_scan_data(conn, scan_id, files, dry_run=False):
    """Inserta archivos del scan."""
    errors = []
    cursor = conn.cursor()
    
    for file_info in files:
        try:
            if not dry_run:
                cursor.execute(
                    "INSERT INTO copilot_repo_files (scan_id, file_path, file_size) VALUES (?, ?, ?)",
                    (scan_id, file_info["path"], file_info["size"])
                )
        except Exception as e:
            errors.append(f"Error inserting file {file_info['path']}: {e}")
    
    if not dry_run:
        conn.commit()
    
    return errors

def get_git_hash():
    """Obtiene hash actual de git."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"

def main():
    print("=" * 70)
    print("Copilot Repo Scan (BD)")
    print("=" * 70)
    
    dry_run = "--dry-run" in sys.argv
    mode = "DRY-RUN" if dry_run else "REAL"
    
    print(f"\nModo: {mode}")
    print(f"Repo: {REPO_ROOT}")
    print(f"BD: {DB_PATH}")
    
    # Check BD
    if not DB_PATH.exists():
        print(f"\n✗ BD no encontrada en {DB_PATH}")
        print("  (Continuando sin BD)")
        return 0
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        
        # Crear tablas copilot_*
        print("\n1. Creando tablas copilot_*...")
        errors = init_copilot_tables(conn, dry_run=dry_run)
        if errors:
            for err in errors:
                print(f"  ⚠ {err}")
        else:
            print("  ✓ Tablas OK")
        
        # Scan repo
        print("\n2. Escaneando archivos repo...")
        files = scan_repo_files()
        print(f"  ✓ {len(files)} archivos encontrados")
        
        # Insertar scan
        if not dry_run:
            print("\n3. Insertando datos de scan...")
            cursor = conn.cursor()
            git_hash = get_git_hash()
            cursor.execute(
                "INSERT INTO copilot_repo_scans (git_hash, repo_files_count, notes) VALUES (?, ?, ?)",
                (git_hash, len(files), "Auto-scan by copilot_repo_scan.py")
            )
            conn.commit()
            
            # Obtener scan_id
            scan_id = cursor.lastrowid
            print(f"  Scan ID: {scan_id}")
            
            # Insertar archivos
            insert_errors = insert_scan_data(conn, scan_id, files, dry_run=dry_run)
            if insert_errors:
                for err in insert_errors:
                    print(f"  ⚠ {err}")
            else:
                print(f"  ✓ {len(files)} archivos insertados")
        else:
            print("\n3. [DRY-RUN] No insertando datos")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✓ Scan completado")
        return 0
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
