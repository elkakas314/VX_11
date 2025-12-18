#!/usr/bin/env python3
"""
Generate distilled canonical DB and JSON from runtime vx11.db (read-only).
Produces:
 - data/backups/vx11_CANONICAL_DISTILLED.db
 - data/backups/vx11_CANONICAL_STATE.json

Safe: only reads runtime DB. No schema changes.
"""
from scripts.cleanup_guard import safe_move_py, safe_rm_py

import sqlite3
import json
import os
from collections import defaultdict, Counter
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
RUNTIME_DB = os.path.join(ROOT, 'data', 'runtime', 'vx11.db')
BACKUP_DIR = os.path.join(ROOT, 'data', 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)
DISTILLED_DB = os.path.join(BACKUP_DIR, 'vx11_CANONICAL_DISTILLED.db')
STATE_JSON = os.path.join(BACKUP_DIR, 'vx11_CANONICAL_STATE.json')

conn = sqlite3.connect(RUNTIME_DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. List all tables
tables = []
for row in cur.execute("""SELECT name, type, sql FROM sqlite_master
                        WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name"""):
    tables.append({'name': row['name'], 'sql': row['sql']})

# 2. Gather stats per table
table_stats = {}
samples = {}
for t in tables:
    name = t['name']
    try:
        c = cur.execute(f"SELECT COUNT(*) as cnt FROM '{name}'").fetchone()
        cnt = c['cnt'] if c else 0
    except Exception:
        cnt = None
    table_stats[name] = {'count': cnt, 'sql': t['sql']}
    # sample up to 5 rows
    try:
        rows = cur.execute(f"SELECT * FROM '{name}' LIMIT 5").fetchall()
        samples[name] = [dict(r) for r in rows]
    except Exception:
        samples[name] = []

# 3. Heuristic classification
core_keywords = {'operator_session','operator_message','tasks','engines','module_health','model_registry','cli_registry'}
operational_keywords = {'task_queue','tasks','spawns','operator_jobs','hijas_runtime','daughters','daughter_tasks'}
autonomy_keywords = {'ia_decisions','pheromone_log','feromona_events','madre_actions','madre_policies'}
historical_keywords = {'reports','audit_logs','forensic_ledger','drift_reports','scheduler_history','events','system_events'}
legacy_keywords = {'models_local','models_remote_cli','tokens_usage'}

classification = defaultdict(list)
for name in table_stats.keys():
    lname = name.lower()
    if lname in core_keywords or any(k in lname for k in ['session','operator','engine','module_health','model_registry']):
        classification['CORE'].append(name)
    elif any(k in lname for k in ['task','queue','spawn','job','hija','daughter']):
        classification['OPERATIVA'].append(name)
    elif any(k in lname for k in ['ia_decision','pheromone','feromona','madre','operator_switch_adjustment']):
        classification['AUTONOMIA'].append(name)
    elif any(k in lname for k in ['report','audit','forensic','drift','history','events','usage_stats']):
        classification['HISTORICA'].append(name)
    else:
        classification['LEGACY / RUÍDO'].append(name)

# 4. Detect empty / rarely used tables
empty_tables = [n for n,s in table_stats.items() if s['count'] == 0]
small_tables = [n for n,s in table_stats.items() if isinstance(s['count'], int) and s['count']>0 and s['count']<10]

# 5. Identify implied relations via column names
relations = defaultdict(list)
for name in table_stats.keys():
    cols = []
    try:
        colinfo = cur.execute(f"PRAGMA table_info('{name}')").fetchall()
        cols = [r['name'] for r in colinfo]
    except Exception:
        pass
    for col in cols:
        if col.endswith('_id') or col.endswith('id'):
            relations[col].append(name)
        if col in ('session_id','task_id','message_id','parent_task_id'):
            relations[col].append(name)

# 6. Extract operational flows: counts and recent timestamps
flows = {}
# tasks/daughter_tasks/operator_jobs
for key in ('tasks','daughter_tasks','operator_jobs','task_queue'):
    if key in table_stats:
        try:
            r = cur.execute(f"SELECT COUNT(*) as cnt, MAX(created_at) as last FROM '{key}'").fetchone()
            flows[key] = {'count': r['cnt'], 'last': r['last']}
        except Exception:
            flows[key] = {'count': table_stats[key]['count']}

# 7. IA decisions summary
ia_summary = {}
if 'ia_decisions' in table_stats:
    try:
        total = cur.execute("SELECT COUNT(*) as c FROM ia_decisions").fetchone()['c']
        per_provider = {r['provider']: r['cnt'] for r in cur.execute("SELECT provider, COUNT(*) as cnt FROM ia_decisions GROUP BY provider").fetchall()}
        avg_latency = cur.execute("SELECT AVG(latency_ms) as a FROM ia_decisions").fetchone()['a']
        ia_summary = {'total': total, 'per_provider': per_provider, 'avg_latency_ms': avg_latency}
    except Exception:
        ia_summary = {}

# 8. Model usage and tokens
model_usage = {}
if 'model_usage_stats' in table_stats:
    try:
        mu = cur.execute("SELECT model_or_cli_name, SUM(tokens_used) as tokens, COUNT(*) as calls FROM model_usage_stats GROUP BY model_or_cli_name ORDER BY tokens DESC LIMIT 20").fetchall()
        model_usage = [{ 'name': r['model_or_cli_name'], 'tokens': r['tokens'], 'calls': r['calls']} for r in mu]
    except Exception:
        model_usage = []

# 9. Events and incidents top errors
top_errors = []
if 'incidents' in table_stats:
    try:
        errs = cur.execute("SELECT incident_type, COUNT(*) as c FROM incidents GROUP BY incident_type ORDER BY c DESC LIMIT 10").fetchall()
        top_errors = [{ 'type': r['incident_type'], 'count': r['c']} for r in errs]
    except Exception:
        top_errors = []

# 10. Build distilled DB
if os.path.exists(DISTILLED_DB):
    safe_rm_py(DISTILLED_DB)
db_out = sqlite3.connect(DISTILLED_DB)
oc = db_out.cursor()
# Create summary tables
oc.execute('CREATE TABLE summary(key TEXT PRIMARY KEY, value TEXT)')
oc.execute('CREATE TABLE table_stats(name TEXT PRIMARY KEY, count INTEGER, sample_json TEXT)')
oc.execute('CREATE TABLE classifications(category TEXT, table_name TEXT)')

# Insert high level info
oc.execute('INSERT INTO summary(key,value) VALUES(?,?)', ('generated_at', datetime.utcnow().isoformat()+'Z'))
oc.execute('INSERT INTO summary(key,value) VALUES(?,?)', ('source_runtime_db', RUNTIME_DB))
oc.execute('INSERT INTO summary(key,value) VALUES(?,?)', ('tables_extracted', str(len(table_stats))))

for name, s in table_stats.items():
    samp = json.dumps(samples.get(name, []), default=str)
    cnt = s['count'] if s['count'] is not None else -1
    oc.execute('INSERT INTO table_stats(name,count,sample_json) VALUES(?,?,?)', (name, cnt, samp))

for cat, tbls in classification.items():
    for tname in tbls:
        oc.execute('INSERT INTO classifications(category,table_name) VALUES(?,?)', (cat, tname))

# store flows, ia_summary, model_usage, top_errors as JSON in summary
oc.execute('INSERT INTO summary(key,value) VALUES(?,?)', ('flows', json.dumps(flows)))
oc.execute('INSERT INTO summary(key,value) VALUES(?,?)', ('ia_summary', json.dumps(ia_summary)))
oc.execute('INSERT INTO summary(key,value) VALUES(?,?)', ('model_usage_top', json.dumps(model_usage)))
oc.execute('INSERT INTO summary(key,value) VALUES(?,?)', ('top_errors', json.dumps(top_errors)))

db_out.commit()
db_out.close()

# 11. Build large JSON state doc
state = {}
state['generated_at'] = datetime.utcnow().isoformat()+'Z'
state['tables'] = {}
for name,s in table_stats.items():
    state['tables'][name] = {
        'count': s['count'],
        'sample': samples.get(name, []),
        'sql': s['sql']
    }
state['classification'] = {k: v for k,v in classification.items()}
state['empty_tables'] = empty_tables
state['small_tables'] = small_tables
state['relations'] = {k:v for k,v in relations.items()}
state['flows'] = flows
state['ia_summary'] = ia_summary
state['model_usage_top'] = model_usage
state['top_errors'] = top_errors

# Add high-level system map heuristics
modules = set()
for t in table_stats.keys():
    if '_' in t:
        modules.add(t.split('_')[0])
state['modules_detected'] = sorted(list(modules))

# autonomy level heuristic
autonomy_level = 'medium'
if ia_summary.get('total',0) > 100:
    autonomy_level = 'high'
elif ia_summary.get('total',0) == 0:
    autonomy_level = 'low'
state['autonomy_level'] = autonomy_level

with open(STATE_JSON, 'w', encoding='utf-8') as f:
    json.dump(state, f, indent=2, ensure_ascii=False, default=str)

# 12. Close runtime connection
conn.close()

# 13. Output summary
print('DISTILLED_DB=', DISTILLED_DB)
print('STATE_JSON=', STATE_JSON)
print('TABLES_COUNT=', len(table_stats))
print('EMPTY_TABLES=', len(empty_tables))
print('AUTONOMY_LEVEL=', autonomy_level)