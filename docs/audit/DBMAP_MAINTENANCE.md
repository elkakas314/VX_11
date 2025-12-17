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


## Run 2025-12-17T14:38:43Z

- database_path: data/runtime/vx11.db
- database_sha256: 825320e78ea19b2e7b67d7027d9eeed08112eba6d46da836477da08bf2570b3a
- database_size_bytes: 374923264
- copilot_repo_map_rows: 983
- map_sha256: 2bdc3ab0bfddac22f0eb38a291667d0ac89066352e1e219803518893f690602c
- schema_sha256: e14a9248ed4d33dcc8c40726f04986cb69025d15c59dbef1a49094eb9a87ab6c


## Run 2025-12-17T14:43:34Z

- database_path: data/runtime/vx11.db
- database_sha256: aa937243a3115d28edb18ce931defa3d19b3fc3004a66636a4f2f05cb7d69a3b
- database_size_bytes: 375955456
- copilot_repo_map_rows: 983
- map_sha256: 2bdc3ab0bfddac22f0eb38a291667d0ac89066352e1e219803518893f690602c
- schema_sha256: e14a9248ed4d33dcc8c40726f04986cb69025d15c59dbef1a49094eb9a87ab6c


## Run 2025-12-17T14:47:25Z

- database_path: data/runtime/vx11.db
- database_sha256: 0aa1d4ec8addd3dfaa69b4f44dd69de32e61f9783642bc2b6175b4dd9e0c7d8d
- database_size_bytes: 376946688
- copilot_repo_map_rows: 983
- map_sha256: 1061ff266b74febac6c510d80925a2a14a6caeee7af4564549469c1e24c2b14f
- schema_sha256: 17a5136eb7460369b1d39485febfe530d08d6ce9236c0ea2416345391ed85556

---
P0: sitecustomize patch applied (sys.path reordering)
- fecha_UTC: $(date -u --rfc-3339=seconds)
- acción: sitecustomize.py actualizado para mover repo root al final de sys.path
- motivo: evitar shadowing de stdlib 'operator' por paquete local
- riesgo: P0 (bajo) — cambio reversible; backup creado: sitecustomize.py.bak.$TS
- verificación: python3 -c "import datetime, random; print('ok')" -> ok
- nota: no se eliminó ni movió contenido forense ni backups
---
P0: automated run (FASE0-4)
- fecha_UTC: $(date -u --rfc-3339=seconds)
- db_sha256: af8bf0eedb86bf0196b940cc55cd89aa1dac7213a8bea994469ac626766c45e4
- db_map_sha256: 4fb185cc4d5dc9ad1862cc3109cba9b9e249657b9c0f414e08ded8656c1b03b5
- rows: 983
---
P0: archived untracked files
- fecha_UTC: 2025-12-17 16:29:43+00:00
- archived_path: docs/audit/archived_copilot
- moved_count: 6
- list_file: docs/audit/archived_copilot/_moved_list.txt
