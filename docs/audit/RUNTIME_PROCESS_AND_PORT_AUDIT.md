# RUNTIME PROCESS & PORT AUDIT

Fecha: 2025-12-14
Ámbito: procesos, puertos, contenedores Docker, systemd — solo lectura (no se mató ni modificó nada)

Comandos ejecutados (solo lectura):
- `ps -eo pid,ppid,stat,cmd --sort=ppid`
- `ss -lptn`
- `docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"`
- `systemctl --type=service --no-pager --no-legend`

---

## C.1 Procesos activos (resumen)

Observaciones clave:
- Varios procesos `uvicorn` corriendo dentro del entorno virtual de `vx11/.venv` (puertos 52112, 52114, 52115, 52116, 52117). Estos corresponden a módulos: `madre`, `hormiguero`, `manifestator`, `mcp`, `shubniggurath`.
- Procesos `containerd` y `dockerd` están activos (docker funcionando).
- Hay instancias `uvicorn` y procesos Node/Vite en ejecución en el host (por ejemplo `node` escuchando en 127.0.0.1:5173 — Vite dev server).
- No se detectaron procesos con estado `Z` (zombies) en la muestra analizada.
- No se observaron múltiples duplicados obvios de `uvicorn` para los mismos puertos; sí hay múltiples contenedores y shim processes de containerd (normal).

Detalle relevante (extracto):
- PID 729-733: `/home/elkakas314/.venv/bin/uvicorn` para varios módulos (puertos 52112..52117)
- PID ~2014233: `node` escuchando en 127.0.0.1:5173 (vite dev server)

Riesgos detectados:
- Dev server de Vite (`5173`) activo en el host; si se planifica limpieza de artefactos o reinicio de puertos, coordinar para no interrumpir desarrolladores.
- Varios servicios `uvicorn` corriendo en puertos no estándar (5211x) — confirmar que no son procesos huérfanos antes de matar.

---

## C.2 Puertos (resumen)

Comando: `ss -lptn`

Puertos VX11 y asociados (observados):
- 5173 — `node` (Vite dev) listen on 127.0.0.1:5173
- 52112 — uvicorn (madre)
- 52114 — uvicorn (hormiguero)
- 52115 — uvicorn (manifestator)
- 52116 — uvicorn (mcp)
- 52117 — uvicorn (shubniggurath)
- 8000, 8001, 8002, 8005, 8006, 8008, 8011, 8012 — puertos abiertos en 0.0.0.0 para servicios Docker (tentaculo, madre, switch, manifestator, mcp, spawner, operator-backend, operator-frontend)
- 8012 appears mapped to operator-frontend container.

Observaciones:
- Los puertos canónicos 8000..8008 y 8011 están escuchando; esto indica que los contenedores/módulos del stack están activos.
- No se detectaron puertos duplicados que colisionen entre sí.

Riesgos:
- Puertos 8011/8012 expuestos — si se van a limpiar puertos, verificar no romper Docker maps.

---

## C.3 Docker (resumen)

Comando: `docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}"`

Estado observado (extracto):
- `vx11-operator-backend` (image `vx11-operator-backend:v7.0`) — puerto 8011 mapped, Up 36 hours (healthy)
- `vx11-operator-frontend` (image `vx11_operator-frontend`) — mapped 8012, Up 36 hours (healthy)
- Otros containers `vx11-madre`, `vx11-tentaculo-link`, `vx11-manifestator`, `vx11-mcp`, etc. — varios en estado `Up 36 hours (healthy)`.
- Algunos servicios en restarting/unhealthy state briefly (e.g., `vx11-shubniggurath` showing restarting/unhealthy). Estado varía en tiempo real.

Riesgos detectados:
- Contenedores marcados `unhealthy` o en `restarting` requieren investigación antes de matar nada; podrían indicar problemas de configuración o recursos.
- No se observan duplicados idénticos en `docker ps` (por nombre), pero hay muchos shims de containerd — normal.

Recomendación:
- Para limpieza runtime no matar contenedores Docker salvo que estén huérfanos y fuera del namespace vx11; documentar y coordinar rollback.

---

## C.4 systemd (resumen)

Comando: `systemctl --type=service`

Observaciones:
- Existen servicios `vx11-*` registrados (ej: `vx11-gateway.service`, `vx11-hormiguero.service`, `vx11-madre.service`, etc.). Están `active` o `activating`.
- No se detectaron servicios sospechosos con nombre claramente antiguo (`vx10`), pero hay muchos servicios del sistema normal.

Riesgos:
- Si se reinician servicios systemd relacionados con vx11, coordinar para evitar downtime.

---

## C.5 Conclusión y riesgos globales

- No se detectaron zombies (STAT = Z) en el volcado analizado.
- El stack Docker VX11 está activo; muchos servicios han estado `Up` durante ~36h.
- El dev server `vite` escucha en 5173 — coordinar con desarrolladores antes de cualquier acción sobre artefactos del frontend.
- `vx11-shubniggurath` y algún otro servicio muestran `unhealthy/restarting` en Docker — investigarlo antes de matar procesos.

---

## Acción siguiente (según flujo impuesto)

Se creó este documento como paso C.5. No se realizó ninguna acción destructiva.

Estado de precondiciones para Fase D (verificación):
- `docs/REPO_LAYOUT.md` existe: SÍ (creado)
- `docs/CLEANUP_RULES.md` existe: SÍ (creado)
- Inventarios en `docs/audit/` existen: SÍ (creados)
- `git status` limpio: NO — hay cambios sin commitear y archivos no trackeados. **STOP**: no ejecutar limpieza hasta que `git status` esté limpio o se cree un backup branch.

Registro de salida raw (extractos):
- `ps` y `ss` outputs han sido consultados y resumidos arriba.
- `docker ps` output fue consultado y resumido arriba.
- `systemctl` output fue consultado y resumido arriba.

---

Documentado por: Copilot (agente de análisis)

Acción: NO MATAR procesos — espera aprobación humana para Fase D.
