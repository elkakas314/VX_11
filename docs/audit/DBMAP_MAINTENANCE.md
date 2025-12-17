# DBMAP Maintenance Report

scanned_at: 2025-12-17T14:03:00Z

database_path: data/runtime/vx11.db

database_sha256: 0a8a2599e79044ec2e1cd02d25f5e546b85692d6697c998c38450cea8df4f4c8

database_size_bytes: 368566272

copilot_repo_map_rows: 11

map_file: docs/audit/DB_MAP_v7_FINAL.md

map_sha256: 2bdc3ab0bfddac22f0eb38a291667d0ac89066352e1e219803518893f690602c

schema_file: docs/audit/DB_SCHEMA_v7_FINAL.json

schema_sha256: e14a9248ed4d33dcc8c40726f04986cb69025d15c59dbef1a49094eb9a87ab6c

backups_dir: docs/audit/backups/dbmap/

Actions performed:
- Created timestamped backup copy of DB_MAP and DB_SCHEMA at docs/audit/backups/dbmap/
- Regenerated docs/audit/DB_SCHEMA_v7_FINAL.json from live sqlite schema
- Regenerated docs/audit/DB_MAP_v7_FINAL.md exported from `copilot_repo_map` table
- Validated JSON syntax for DB_SCHEMA

Commands used (examples):
- sqlite3 data/runtime/vx11.db ".tables"
- sqlite3 data/runtime/vx11.db "SELECT count(*) FROM copilot_repo_map;"
- python3 ./.tmp/gen_schema.py
- python3 ./.tmp/gen_map.py

