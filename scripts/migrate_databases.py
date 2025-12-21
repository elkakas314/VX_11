#!/usr/bin/env python3
"""
VX11 Database Migration Script
Consolida BDs legadas presentes en data/runtime hacia vx11.db con namespaces.

Uso:
  python scripts/migrate_databases.py  [--dry-run]
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py


import sys
import os
import sqlite3
import json
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "runtime"
DB_PATH.mkdir(parents=True, exist_ok=True)
NEW_DB = DB_PATH / "vx11.db"
BACKUP_DIR = DB_PATH / "backups"


def discover_old_dbs() -> dict:
    """
    Detecta BDs legadas (excluyendo vx11.db).
    """
    legacy = {}
    for db_path in DB_PATH.glob("*.db"):
        if db_path.name == "vx11.db":
            continue
        legacy[db_path.stem] = db_path
    return legacy


def log(msg: str, level="INFO"):
    """Log with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {level}: {msg}")


def backup_old_dbs(old_dbs: dict):
    """Crear backups de BDs antiguas."""
    BACKUP_DIR.mkdir(exist_ok=True)
    for db_name, db_path in old_dbs.items():
        if db_path.exists():
            backup_path = BACKUP_DIR / f"{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db.bak"
            # Use sqlite3 to create backup
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(backup_path)
            src_conn.backup(dst_conn)
            dst_conn.close()
            src_conn.close()
            log(f"Backup de {db_name}.db → {backup_path.name}", "BACKUP")


def get_all_tables(db_path: Path) -> list:
    """Obtener todas las tablas de una BD."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_table_schema(db_path: Path, table_name: str) -> str:
    """Obtener CREATE TABLE statement de una tabla."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def migrate_table_data(src_conn, src_table: str, dst_conn, dst_table: str, namespace: str = None):
    """Copiar datos de una tabla a otra, opcionalmente con namespace."""
    src_cursor = src_conn.cursor()
    dst_cursor = dst_conn.cursor()
    
    # Get all rows from source
    src_cursor.execute(f"SELECT * FROM {src_table};")
    rows = src_cursor.fetchall()
    
    if not rows:
        log(f"  {src_table} vacía, saltando")
        return 0
    
    # Get column info
    src_cursor.execute(f"PRAGMA table_info({src_table})")
    columns = [row[1] for row in src_cursor.fetchall()]
    
    # Insert into destination
    placeholders = ", ".join(["?" for _ in columns])
    cols_str = ", ".join(columns)
    insert_sql = f"INSERT INTO {dst_table} ({cols_str}) VALUES ({placeholders})"
    
    for row in rows:
        try:
            dst_cursor.execute(insert_sql, row)
        except Exception as e:
            log(f"  Error insertando fila en {dst_table}: {e}", "WARN")
    
    dst_conn.commit()
    log(f"  Migrados {len(rows)} registros: {src_table} → {dst_table}")
    return len(rows)


def migrate_databases(dry_run=False):
    """Ejecutar migración completa."""
    old_dbs = discover_old_dbs()
    if not old_dbs:
        log("No se encontraron BDs legadas en data/runtime. Nada que migrar.", "INFO")
        return
    
    if dry_run:
        log("MODO DRY-RUN: No se escribirá nada", "INFO")
    
    log("=== INICIANDO MIGRACIÓN VX11 ===")
    
    # Paso 1: Backup
    log("\n[PASO 1/5] Creando backups de BDs antiguas...")
    if not dry_run:
        backup_old_dbs(old_dbs)
    else:
        log("  (dry-run: no se crean backups)", "INFO")
    
    # Paso 2: Verificar BDs antiguas
    log("\n[PASO 2/5] Verificando BDs antiguas...")
    for db_name, db_path in old_dbs.items():
        if db_path.exists():
            tables = get_all_tables(db_path)
            log(f"  {db_name}.db: {len(tables)} tablas ({', '.join(tables[:3])}...)")
        else:
            log(f"  {db_name}.db: NO ENCONTRADA", "WARN")
    
    # Paso 3: Preparar nueva BD
    log("\n[PASO 3/5] Creando nueva BD unificada...")
    if dry_run:
        log(f"  (dry-run: no se crea {NEW_DB})", "INFO")
        return
    
    # Si ya existe, hacer backup
    if NEW_DB.exists():
        backup_path = BACKUP_DIR / f"vx11_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db.bak"
        import shutil
        shutil.copy(NEW_DB, backup_path)
        log(f"  Backup de BD existente: {backup_path.name}")
    
    # Copiar schema de la primera BD disponible
    primary_db = next(iter(old_dbs.values()))
    src_conn = sqlite3.connect(primary_db)
    dst_conn = sqlite3.connect(NEW_DB)
    
    # Copiar schemas de todas las BDs a la nueva (solo si tabla no existe)
    for db_name, db_path in old_dbs.items():
        if not db_path.exists():
            continue
        
        temp_conn = sqlite3.connect(db_path)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        
        for table_row in temp_cursor.fetchall():
            table_name = table_row[0]
            
            # Crear tabla prefijada si no existe
            prefixed_table = f"{db_name}_{table_name}"
            
            schema = get_table_schema(db_path, table_name)
            if schema:
                # Reemplazar nombre de tabla en schema
                namespaced_schema = schema.replace(
                    f"CREATE TABLE {table_name}",
                    f"CREATE TABLE {prefixed_table}"
                )
                
                try:
                    dst_cursor = dst_conn.cursor()
                    dst_cursor.execute(namespaced_schema)
                    dst_conn.commit()
                    log(f"  Tabla creada: {prefixed_table}")
                except sqlite3.OperationalError as e:
                    if "already exists" in str(e):
                        log(f"  Tabla ya existe: {prefixed_table}")
                    else:
                        log(f"  Error creando {prefixed_table}: {e}", "ERROR")
        
        temp_conn.close()
    
    log(f"  BD unificada creada: {NEW_DB}")
    
    # Paso 4: Migrar datos
    log("\n[PASO 4/5] Migrando datos...")
    total_records = 0
    
    for db_name, db_path in old_dbs.items():
        if not db_path.exists():
            continue
        
        log(f"\n  Migrando desde {db_name}.db...")
        src_conn = sqlite3.connect(db_path)
        dst_conn = sqlite3.connect(NEW_DB)
        
        src_cursor = src_conn.cursor()
        src_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in src_cursor.fetchall()]
        
        for table in tables:
            prefixed_table = f"{db_name}_{table}"
            records = migrate_table_data(src_conn, table, dst_conn, prefixed_table, db_name)
            total_records += records
        
        src_conn.close()
        dst_conn.close()
    
    log(f"\n  Total de registros migrados: {total_records}")
    
    # Paso 5: Verificar
    log("\n[PASO 5/5] Verificando integridad...")
    verify_conn = sqlite3.connect(NEW_DB)
    verify_cursor = verify_conn.cursor()
    verify_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables_in_new = [row[0] for row in verify_cursor.fetchall()]
    verify_conn.close()
    
    log(f"  BD unificada contiene {len(tables_in_new)} tablas:")
    for table in tables_in_new:
        v_conn = sqlite3.connect(NEW_DB)
        v_cursor = v_conn.cursor()
        v_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = v_cursor.fetchone()[0]
        v_conn.close()
        log(f"    - {table}: {count} registros")
    
    log("\n=== MIGRACIÓN COMPLETADA ===")
    log("PRÓXIMOS PASOS:", "INFO")
    log("  1. Verificar integridad de vx11.db")
    log("  2. Actualizar config/db_schema.py para usar vx11.db")
    log("  3. Actualizar módulos para usar DB unificada")
    log("  4. Ejecutar tests")
    log("  5. Eliminar BDs antiguas (backup en data/backups/)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VX11 Database Migration")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulación")
    args = parser.parse_args()
    
    try:
        migrate_databases(dry_run=args.dry_run)
    except Exception as e:
        log(f"ERROR EN MIGRACIÓN: {e}", "ERROR")
        sys.exit(1)