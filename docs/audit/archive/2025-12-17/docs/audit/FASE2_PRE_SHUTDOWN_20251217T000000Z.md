# FASE 2 — Pre-cierre y plan (no destructivo)

Fecha (UTC): 2025-12-17T00:00:00Z

Acciones realizadas (no destructivas):

- Listado de contenedores (docker-compose):

```
       Name                      Command                  State                     Ports               
--------------------------------------------------------------------------------------------------------
vx11-hermes           python -m uvicorn switch.h ...   Up (healthy)   0.0.0.0:8003->8003/tcp,:::8003-   
                                                                      >8003/tcp                         
vx11-switch           python -m uvicorn switch.m ...   Up (healthy)   0.0.0.0:8002->8002/tcp,:::8002-   
                                                                      >8002/tcp                         
vx11-tentaculo-link   python -m uvicorn tentacul ...   Up (healthy)   0.0.0.0:8000->8000/tcp,:::8000-   
                                                                      >8000/tcp                         
```

- Salud de puertos (8000-8005):

```
Port 8000: ok
Port 8001: 
Port 8002: ok
Port 8003: ok
Port 8004: 
Port 8005: 
```

- `docker ps` resumen:

```
NAMES                 STATUS                  PORTS
vx11-switch           Up 12 hours (healthy)   0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
vx11-hermes           Up 12 hours (healthy)   0.0.0.0:8003->8003/tcp, [::]:8003->8003/tcp
vx11-tentaculo-link   Up 12 hours (healthy)   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
```

- Uptime y procesos top (extracto):

```
 12:19:15 up 22:28,  2 users,  load average: 5,33, 5,09, 4,37

USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
... (truncado)
```

Observaciones y plan de cierre (seguro):

- Todos los servicios principales (`tentaculo_link`, `switch`, `hermes`) están `Up (healthy)` y responden en puertos 8000, 8002, 8003.
- No se detuvieron servicios. Conforme a `AGENTS.md`, no ejecuto acciones destructivas (detenciones/`docker-compose down`) sin autorización explícita.

Pasos recomendados para cierre controlado (manual/órdenes explícitas previas):

1. Informar a operadores y detener tráfico entrante (balanceadores / proxys).
2. Marcar modo mantenimiento en `operator`/`gateway` si existe endpoint de mantenimiento.
3. Parar hijos/servicios en orden: baja carga → detener colas → detener servicios secundarios → detener servicios principales.
4. Verificar logs y persistir estado en `data/backups/` antes de cualquier migración.
5. Registrar evidencia completa en `docs/audit/`.

Evidencia guardada: este archivo.
