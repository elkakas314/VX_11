# 🎮 VX11 AGENTE - QUICK REFERENCE

**Use en cualquier sesión. Copiar/pegar rápidamente.**

---

## ⚡ BOOTSTRAP INMEDIATO

```bash
cd /home/elkakas314/vx11 && \
echo "🔧 Inicializando agente VX11..." && \
python3 scripts/vx11_agent_bootstrap.py
```

---

## 📊 COMANDOS RÁPIDOS

| Comando | Qué hace | Ejemplo |
|---------|----------|---------|
| `@vx11 status` | Diagnóstico completo | `@vx11 status` |
| `@vx11 ejecuta` | Ejecutar tarea | `@vx11 ejecuta optimizar switch` |
| `@vx11 repara` | Reparar servicio | `@vx11 repara madre` |
| `@vx11 limpia` | Mantenimiento | `@vx11 limpia` |
| `@vx11 inyecta` | Inyectar prompt | `@vx11 inyecta "test" en switch` |

---

## 🔍 DIAGNÓSTICO RÁPIDO

```bash
# Health de todos los módulos
for p in 8000 8001 8002 8004 8005 8006 8007 8008; do
  echo -n "Puerto $p: "
  curl -s http://localhost:$p/health | jq -r '.status' || echo "DOWN"
done

# Última línea de cada log
for mod in tentaculo_link madre switch hormiguero manifestator mcp shubniggurath; do
  echo "$mod: $(tail -1 logs/*$mod* 2>/dev/null | tail -1)"
done

# Git status
git log --oneline -5
git status --short
```

---

## 📋 ESTRUCTURA VX11

```
🟢 Tentáculo Link (8000)    — Gateway
🟢 Madre (8001)             — Orquestación
🟢 Switch (8002)            — Router IA
🟡 Hormiguero (8004)        — Scanning
🟡 Manifestator (8005)      — Auditoría
🟢 MCP (8006)               — Conversacional
🟡 Shubniggurath (8007)     — Audio/Video
🟢 Spawner (8008)           — Hijas efímeras
🟢 Operator (8011/8020)     — Chat UI
```

---

## 🛠️ REPARACIONES COMUNES

### Si un módulo falla:
```bash
# 1. Revisar log
tail -50 logs/[modulo].log

# 2. Diagnosticar puerto
netstat -tlnp | grep 800[0-9]

# 3. Compilar Python
python3 -m py_compile [modulo]/main.py

# 4. Resetear BD (CUIDADO)
sqlite3 data/runtime/vx11.db "VACUUM;"
```

### Si hay conflictos de import:
```bash
python3 << 'EOF'
import sys
# Remover cached imports
for key in list(sys.modules.keys()):
    if 'vx11' in key or 'tentaculo' in key:
        del sys.modules[key]
print("Cache limpiado")
EOF
```

---

## 🔒 OPERACIONES SEGURAS (Auto-aprobadas)

✅ `git status`  
✅ `git log`  
✅ `git diff`  
✅ `curl http://127.0.0.1:800X`  
✅ `python3 scripts/vx11_*.py`  
✅ `ls`, `cat`, `grep`, `find`  
✅ `docker compose ps`  
✅ `docker compose logs`  

---

## ❌ OPERACIONES DESTRUCTIVAS (Requieren confirmar)

❌ `sudo` (cualquier comando)  
❌ `rm -rf`  
❌ `git reset --hard`  
❌ `git clean -fd`  
❌ `docker compose down`  
❌ `git push`  
❌ Exponer `tokens.env`  

---

## 💾 BD QUERIES ÚTILES

```sql
-- Contar módulos activos
SELECT COUNT(*) FROM module_health WHERE status='ok';

-- Últimas tareas
SELECT name, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 5;

-- Errores recientes
SELECT * FROM audit_logs WHERE level='ERROR' ORDER BY created_at DESC LIMIT 10;

-- Estado del sistema
SELECT * FROM system_state LIMIT 1;
```

---

## 🚀 PARA LA PRÓXIMA SESIÓN

1. **Copiar prompt** desde `.github/agents/VX11_AGENT_CONFIG_v2.md`
2. **Abrir chat nuevo** con agente genérico
3. **Pegar prompt** completo
4. **Escribir:** `@vx11 status`
5. **Agente se auto-configura automáticamente**

---

**Creado:** 2025-12-15  
**Status:** ✅ OPERATIVO
