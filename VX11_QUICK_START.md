# 🚀 VX11 Quick Start — Referencia Minimalista

**Status:** ✅ OPERATIONAL  
**Actualizado:** 2025-12-24T23:55:00Z  
**Archivo Principal:** `.github/agents/vx11.agent.md` (v2.2, 1133 líneas)

---

## 🔄 PERSISTENCIA: ¿Copilot Recuerda el Comportamiento Cada Chat?

**Respuesta:** ✅ **SÍ, GARANTIZADO**

El protocolo quirúrgico está en `.github/agents/vx11.agent.md`:
- **YAML Frontmatter** → Copilot lo lee CADA VEZ
- **Instructions Field** → 5 pasos auto-ejecutables
- **On-Invocation Injection** → Dispara con `@vx11 <comando>`

Referencia completa: [docs/audit/RESPUESTA_PERSISTENCIA.md](docs/audit/RESPUESTA_PERSISTENCIA.md)

---

## 🔬 CAMBIOS QUIRURGICOS (NEW)

### Cuando Pidas Editar Código: SIEMPRE

1. **Auditoría Primero** — Leer contexto (-3/+3 líneas mínimo)
2. **Cambio Mínimo** — Una cosa = un cambio (NO refactor "mientras estamos")
3. **Validación Post** — Syntax + tests + health checks
4. **Evidencia** — Guardar en docs/audit/<TS>/
5. **Nunca Destructivo** — Pre-backup antes de rm/DELETE

### Reglas de Oro

- ✂️ Si se pide arreglar typo → SOLO typo (no limpies imports)
- 🔍 Si se pide refactor → ASK primero (no lo hagas en paralelo)
- 🗑️ Si se pide borrar → Pre-backup + DRY-RUN + ask confirmación
- 🛡️ Si toca BD → PRAGMA checks pre+post
- 🚀 Si toca servicios → Health check pre+post

### Atajos Quirúrgicos

**Validación Post-Cambio:**
```bash
# Copia esto después de editar:
TS=$(date -u +%Y%m%dT%H%M%SZ); mkdir -p docs/audit/$TS
python -m py_compile archivo.py > docs/audit/$TS/validation.log 2>&1
echo "✅ Validado: docs/audit/$TS/validation.log"
```

**Pre-Backup Antes de Borrar:**
```bash
cp archivo_importante.ext archivo_importante.backup
echo "Pre-backup: archivo_importante.backup"
```

---

## 1️⃣ Status en 1 Línea

```bash
echo "Health: $(for p in 8000 8001 8003 8004; do curl -s http://localhost:$p/health 2>/dev/null | jq -r '.status' | head -c1; done), DB: $(du -h data/runtime/vx11.db | cut -f1), Spawns: $(sqlite3 data/runtime/vx11.db 'SELECT COUNT(*) FROM spawns')"
```

---

## 2️⃣ Auditoría Completa

```bash
TS=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p docs/audit/$TS
for port in 8000 8001 8002 8003 8004 8006 8007 8008 8011; do
  curl -s http://localhost:$port/health > docs/audit/$TS/h$port.json 2>/dev/null
done
sqlite3 data/runtime/vx11.db "PRAGMA quick_check;" > docs/audit/$TS/db_quick.txt
curl -X POST http://localhost:8001/madre/power/maintenance/post_task -d '{}' > docs/audit/$TS/madre_post.json 2>&1
echo "✓ Evidencia: docs/audit/$TS/"
```

---

## 3️⃣ Ejecutar Tarea (Spawn)

```bash
curl -X POST http://localhost:8008/spawn \
  -H "Content-Type: application/json" \
  -d '{
    "action": "scan_incidents",
    "ttl_seconds": 300,
    "max_retries": 3,
    "target_module": "hormiguero",
    "payload": {}
  }' | jq '.'
```

---

## 4️⃣ Monitoreo Real-Time

```bash
watch -n 2 "sqlite3 data/runtime/vx11.db 'SELECT COUNT(*) as pending FROM spawns WHERE status=\"pending\", COUNT(*) as running FROM spawns WHERE status=\"running\", COUNT(*) as daughters FROM daughters WHERE status IN (\"spawned\",\"running\");'"
```

---

## 5️⃣ Limpieza SAFE (Sin Confirmar)

```bash
# Logs > 7 días
find logs -type f -name "*.log" -mtime +7 -delete -print | wc -l

# Archivar crashes
mkdir -p docs/audit/archived_forensic && mv forensic/crashes/* docs/audit/archived_forensic/ 2>/dev/null || true

# Backups: conserva 2
ls -t data/backups/vx11*.db | tail -n +3 | xargs -I {} mv {} data/backups/archived/ && echo "✓ Rotados"
```

---

## 6️⃣ Limpieza AGGRESSIVE (Pedir Confirmación)

```bash
read -p "¿Limpiar audits > 30 días? (s/n): " -n 1 -r
if [[ $REPLY =~ ^[Ss]$ ]]; then
  find docs/audit -maxdepth 1 -type d -mtime +30 ! -name "archived*" ! -name "archive" -exec rm -rfv {} \;
  echo "✓ Limpieza completada"
fi
```

---

## 7️⃣ Limpieza SURGICAL (Pedir Palabra Clave)

```bash
# NUNCA vaciar: spawns, daughters, incidents, module_status
# SAFE: routing_events, cli_usage_stats, pheromone_log

TABLE="routing_events"
read -p "⚠️  ¿REALMENTE VACIAR $TABLE? (escribir 'sí'): " CONFIRM
if [ "$CONFIRM" = "sí" ]; then
  cp data/runtime/vx11.db data/backups/vx11_backup_pre_delete_$TABLE.db
  sqlite3 data/runtime/vx11.db "DELETE FROM $TABLE;"
  sqlite3 data/runtime/vx11.db "PRAGMA integrity_check;" | head -1
fi
```

---

## 📊 Herramientas (Por Necesidad)

| Necesito | Comando | Archivo |
|----------|---------|---------|
| Ver status | Status en 1 Línea (👆 #1) | vx11.agent.md |
| Auditar sistema | Auditoría Completa (👆 #2) | vx11.agent.md |
| Correr tarea | Spawn Task (👆 #3) | vx11.agent.md |
| Monitorear | Monitor Loop (👆 #4) | vx11.agent.md |
| Limpiar safe | Limpieza SAFE (👆 #5) | vx11.agent.md |
| Limpiar aggressive | Limpieza AGGRESSIVE (👆 #6) | vx11.agent.md |
| Limpiar surgical | Limpieza SURGICAL (👆 #7) | vx11.agent.md |
| Más herramientas | HERRAMIENTAS AVANZADAS | vx11.agent.md (línea 35-180) |
| Índice completo | VX11_AGENT_TOOLS_INDEX.md | docs/audit/ |
| Pre/post checks | Pre-Action/Post-Action | vx11.agent.md (línea 350-500) |
| E2E flows | Flow A/B/C validation | vx11.agent.md (línea 600-680) |
| Diagnóstico fallos | Failure Diagnosis | vx11.agent.md (línea 750-850) |

---

## 🔐 NUNCA Hagas Esto

- ❌ `rm -rf data/runtime/vx11.db` (usar backup + restore)
- ❌ `docker compose down` (escalate a operador)
- ❌ Editar `madre/main.py` (requiere code review)
- ❌ `DELETE FROM spawns` (escalate)
- ❌ Tocar `tokens.env` (READ-ONLY)

---

## 📁 Archivos Clave

- `.github/agents/vx11.agent.md` → Tu bootstrap completo
- `docs/audit/VX11_AGENT_TOOLS_INDEX.md` → Índice rápido
- `docs/audit/DB_MAP_v7_FINAL.md` → Schema BD (70 tablas)
- `docs/audit/CLEANUP_EXCLUDES_CORE.txt` → Paths protegidos
- `data/runtime/vx11.db` → BD principal

---

## ⚡ Después de Cualquier Acción

```bash
# Siempre ejecutar post-action:
curl -X POST http://localhost:8001/madre/power/maintenance/post_task \
  -H "Content-Type: application/json" \
  -d '{}' | jq '.'
```

---

**¿Más detalle?** Abre `.github/agents/vx11.agent.md`  
**¿Referencia índice?** Abre `docs/audit/VX11_AGENT_TOOLS_INDEX.md`  
**¿Historia cambios?** Abre `docs/audit/20251224T214931Z/VX11_AGENT_IMPROVEMENTS_SUMMARY.md`
