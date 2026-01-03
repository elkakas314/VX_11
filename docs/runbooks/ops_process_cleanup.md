# VX11 Operations: Process Cleanup & Troubleshooting

**Date**: 2026-01-03  
**Purpose**: Runbook reproducible para detectar y limpiar procesos "zombies", huérfanos, duplicados, y bucles.  
**Scope**: Docker, systemd (si aplica), VS Code remote, watchers, reconexiones.

---

## 1. Detección de Procesos Zombies

### ¿Qué es un zombie?

Proceso que ha terminado pero su padre no ha "recolectado" su estado de salida (`wait()`).  
No se puede matar directamente; solo el padre puede resolverlo.

### Comandos de Detección

```bash
# Listar TODOS los zombies
ps -eo pid,ppid,stat,etime,cmd | awk '$3 ~ /Z/ {print}'

# Contar zombies
ps -eo stat | grep -c Z || echo "0"

# Zombies con detalles + PPIDs
ps -o pid,ppid,stat,cmd -p $(pgrep -f Z || true)

# Ver el PADRE del zombie (y si está en estado "S" de sleep/esperanza)
ps -o pid,ppid,stat,cmd -p <PID_PADRE_DEL_ZOMBIE>
```

### Solución de Zombies

**Caso 1: Padre es un proceso vivo**
```bash
# Enviar SIGCHLD al padre (le obliga a recolectar)
kill -SIGCHLD <PID_PADRE>

# Si eso no funciona, reiniciar el padre
# (ej: docker restart vx11-madre, systemctl restart vx11-madre, etc.)
```

**Caso 2: Padre es `init` (PID 1) o `systemd`**
```bash
# Zombie huérfano: solo se limpian al reiniciar
# Esto es raro en Docker pero puede ocurrir en systemd mal configurado
# SOLUCIÓN: revisar que el servicio tenga:
#   KillMode=control-group
#   TimeoutStopSec=10  # ajustar si es necesario
```

**Caso 3: En Docker Compose**
```bash
# Reiniciar servicio específico
docker compose restart <service_name>

# O down + up
docker compose down && docker compose up -d
```

---

## 2. Detección de Procesos Huérfanos & Duplicados

### Comandos de Mapeo de Árboles

```bash
# Árbol completo de procesos (todas las relaciones padre-hijo)
pstree -ap | less

# Buscar procesos VX11 (docker, compose, python servers, node)
pgrep -fa "docker|compose|uvicorn|gunicorn|python.*madre|python.*tentaculo|python.*operator|node|code"

# Contar instancias de un proceso
pgrep -c "uvicorn"  # ej: debería ser ~5 (madre, operator, switch, tentaculo_link)

# Ver todos los puertos en escucha (y qué proceso los usa)
ss -tlnp 2>/dev/null | grep LISTEN
# O: lsof -i -P -n | grep LISTEN
```

### Indicadores de Problemas

| Síntoma | Causa Probable | Acción |
|---------|---|---|
| `pgrep -c "docker compose"` > 1 | Dos `docker compose` corriendo | `docker compose ps -a`, luego `kill` o `docker compose down` el duplicado |
| `pgrep -c "uvicorn"` > 6 | Múltiples instancias del mismo servicio | Revisar `docker compose.yml`, eliminar réplicas no deseadas |
| Puerto 8000 escuchando pero no responde | Proceso zombie en ese puerto | `fuser 8000/tcp`, luego kill PID si es zombie |
| VS Code server colgado (lag, no reconoce cambios) | Sesión remota duplicada o watcher loop | Ver sección **3. VS Code Remote** |

---

## 3. VS Code Remote: Killer & Debugging

### Problema: VS Code Server Colgado

**Síntomas**:
- VS Code lento o no reconoce cambios de archivos
- Watchers infinitos ("watching...")
- Extensiones duplicadas o conflictivas

### Solución 1: Kill VS Code Server (Recomendada)

**Opción A: Desde VS Code UI**
1. Abre Command Palette (`Ctrl+Shift+P`)
2. Escribe: `Remote-SSH: Kill VS Code Server on Host…`
3. Selecciona el host → Confirma

**Opción B: Manual (Terminal)**
```bash
# Si VS Code está conectado por SSH
ssh -i ~/.ssh/id_rsa user@host "pkill -9 -f 'code.*server' || true"

# O locally (si es Docker/WSL)
docker exec vx11-madre pkill -9 -f "code" || true
```

### Solución 2: Aislar Extensiones (Diagnóstico)

```bash
# Lanzar VS Code SIN extensiones
code --disable-extensions

# Luego:
# - Verifica si lag/problema desaparece
# - Si sí → una extensión lo causaba
# - Si no → problema es del workspace o servidor
```

### Solución 3: Revisar Output del Remote-SSH

1. Command Palette → `Remote-SSH: Open Configuration File...`
2. Verifica que `HostName`, `User`, `IdentityFile` sean correctos
3. Output tab → busca errores de handshake o auth

### Solución 4: Limpiar Sesiones Duplicadas

```bash
# Si hay dos conexiones al mismo host
code --remote ssh-remote://<host>/path/to/project

# VS Code debería detectar duplicadas; si no:
# Cierra todas las ventanas de VS Code
# Abre DE NUEVO (fuerza nueva conexión limpia)
```

---

## 4. Docker Compose: Huérfanos & Limpieza Segura

### Problema: Contenedores Huérfanos Tras Crash

```bash
# Ver estado de containers (incluyendo stopped)
docker compose ps -a

# Ver contenedores no listados en compose.yml
docker ps -a | grep -v "$(docker compose config -q | xargs -I {} docker images --format '{{.Repository}}' {})"
```

### Limpieza Segura (Sin Romper Nada)

```bash
# Opción 1: Stop + Remove (tú controlas qué se elimina)
docker compose stop
docker compose rm -f

# Opción 2: Down + Remove Orphans (recomendado para limpieza periódica)
docker compose down --remove-orphans

# Opción 3: System Prune (SOLO si estás SEGURO; borra imágenes, volúmenes sin usar)
# ⚠️ PELIGRO: borra TODO lo que no esté en uso; revisa primero
docker system df  # Ver qué se eliminará
# Luego:
docker system prune --volumes --all -f
```

### Verificación Post-Limpieza

```bash
# Confirmar que servicios críticos están arriba
docker compose up -d

# Smoke test
curl -s http://localhost:8000/health | jq .
```

---

## 5. Systemd Services: KillMode y Timeout

### Problema: Procesos Colgados Tras `systemctl stop`

Si tienes units `vx11-*.service`, revisa que maten TODO el árbol (no solo PID principal):

```bash
# Ver configuración actual
systemctl cat vx11-madre.service | grep -A5 "^\[Service\]"
```

### Configuración Recomendada (si aplica)

```ini
[Service]
# ...
Type=notify
KillMode=control-group  # ← Mata TODO el grupo de procesos (hijas, workers)
TimeoutStopSec=10       # ← Espera máx 10s antes de SIGKILL
Restart=always
RestartSec=5
# ...
```

### Aplicar Cambios

```bash
sudo systemctl daemon-reload
sudo systemctl restart vx11-madre.service

# Verificar
systemctl status vx11-madre.service
```

---

## 6. Watchers & Bucles de Reconexión

### Problema: SSE/EventsClient Infinito Retry

**Síntomas**:
- Console spam: `[EventsClient] Connecting...`
- Red tab en browser: muchas peticiones 401 o 403

**Solución**:
- Token guard en EventsClient debe prevenir esto (ver `operator/frontend/src/lib/events-client.ts`)
- Si aún ocurre:
  ```bash
  # Revisar logs
  docker logs vx11-operator-backend | tail -50 | grep -i "event\|401\|403"
  
  # Verificar token en localStorage (browser DevTools → Storage → Local Storage)
  # Debe mostrar: vx11_token = <tu_token>
  
  # Si vacío, usuario debe usar "Set Token" en UI
  ```

### Problema: Node Watchers Infinitos (Nodemon, Vite, etc.)

```bash
# Identificar watcher colgado
pgrep -fa "nodemon|vite|webpack" | head -10

# Si es watcher en REPL/desarrollo (no en prod):
kill -9 <PID>  # Matar el watcher

# Luego reiniciar aplicación
npm run dev  # o docker compose restart
```

---

## 7. Runbook: Limpieza Completa (Paso a Paso)

**Objetivo**: Dejar VX11 limpio tras sesión caótica.

### PASO 1: Detectar Problemas (2 min)

```bash
#!/bin/bash
set -e

echo "=== DETECCIÓN DE PROBLEMAS ==="

# Zombies
ZOMBIES=$(ps -eo stat | grep -c Z || echo 0)
echo "Zombies encontrados: $ZOMBIES"
[ "$ZOMBIES" -gt 0 ] && echo "  ⚠️  Hay zombies; ver FASE 1 arriba"

# Procesos duplicados
DOCKER_COUNT=$(pgrep -c "docker compose" || echo 0)
UVICORN_COUNT=$(pgrep -c "uvicorn" || echo 0)
echo "docker compose instancias: $DOCKER_COUNT"
echo "uvicorn instancias: $UVICORN_COUNT"

# Puertos
echo ""
echo "=== PUERTOS EN ESCUCHA ==="
ss -tlnp 2>/dev/null | grep -E ":8000|:8001|:8002"

echo ""
echo "=== DOCKER COMPOSE STATUS ==="
docker compose ps --all
```

### PASO 2: Limpiar Docker (3 min)

```bash
#!/bin/bash
set -e

echo "Bajando servicios..."
docker compose down --remove-orphans

echo "Limpiando volúmenes no usados (opcional)..."
docker volume prune -f

echo "Rearmando..."
docker compose -f docker-compose.full-test.yml up -d

echo "Esperando inicialización..."
sleep 5

echo "=== SMOKE TEST ==="
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/vx11/status | jq .
```

### PASO 3: Verificar VS Code (2 min, solo si aplicable)

```bash
# Si VS Code está lento o colgado:
# 1. Abre Command Palette (Ctrl+Shift+P)
# 2. "Remote-SSH: Kill VS Code Server on Host…"
# 3. Reconecta
```

### PASO 4: Confirmar Estado Final

```bash
echo "=== ESTADO FINAL ==="
echo "Zombies: $(ps -eo stat | grep -c Z || echo 0)"
echo "Procesos docker: $(pgrep -c docker || echo 0)"
echo "Servicios up: $(docker compose ps --format '{{.State}}' | grep -c running || echo 0)"
echo ""
echo "✅ LIMPIEZA COMPLETADA"
```

---

## 8. Alertas & Prevención

### Alertas Automáticas (Cron/Systemd)

```bash
# Crear script de check (ej: /usr/local/bin/vx11_health_check.sh)

#!/bin/bash
ZOMBIES=$(ps -eo stat 2>/dev/null | grep -c Z || echo 0)
if [ "$ZOMBIES" -gt 0 ]; then
  echo "ALERTA: $ZOMBIES zombies detectados en $(date)" | \
    mail -s "VX11: Zombies" admin@example.com
fi
```

```bash
# Añadir cron (cada hora)
0 * * * * /usr/local/bin/vx11_health_check.sh >> /var/log/vx11_check.log 2>&1
```

### Prevención en Producción

1. **Logs Centralizados**: enviar `docker logs` a ELK/Splunk (detectar bucles antes de que causen zombies)
2. **Alertas de Puerto**: si `:8000` deja de responder, reboot automático (systemd OnFailure=)
3. **Rotación de Audit**: cron que rote `docs/audit/` diariamente (ver FASE 2 en prompt principal)

---

## 9. Checklist: Antes de Desplegar

- [ ] `ps -eo stat | grep Z` → 0 zombies
- [ ] `pgrep -c docker compose` → 1
- [ ] `docker compose ps` → todos "healthy" o "running"
- [ ] `curl http://localhost:8000/health` → 200 OK
- [ ] VS Code: sin lag (responde inmediatamente)
- [ ] Token configurado en browser localStorage (si aplica UI)
- [ ] Logs sin errores (docker logs) en últimos 5 min

---

## Referencias

- [ps man page](https://man7.org/linux/man-pages/man1/ps.1.html) - Estados de procesos
- [Systemd KillMode](https://www.freedesktop.org/software/systemd/man/systemd.kill.html) - Matar árboles de procesos
- [Docker Compose down](https://docs.docker.com/engine/reference/commandline/compose_down/) - Limpieza segura
- [VS Code Remote SSH](https://code.visualstudio.com/docs/remote/ssh) - Troubleshooting

---

**Última actualización**: 2026-01-03  
**Status**: ✅ Reproducible, sin breaking changes
