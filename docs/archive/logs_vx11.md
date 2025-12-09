# Logs VX11 - Guía

Para ver logs del gateway y servicios relacionados en tu máquina (requiere permisos y uso local):

- Comando sugerido para revisar el servicio del sistema (no ejecutar desde aquí):

```
# Ver estado del servicio del gateway
systemctl status vx11-gateway.service

# Ver logs en tiempo real
journalctl -u vx11-gateway.service -f
```

- Si usas containers o uvicorn en foreground, revisa la salida del proceso correspondiente.

(Estos comandos son referencias; no se ejecutan desde VS Code desde este archivo.)
