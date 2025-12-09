
# Panel VX11 - Control Rápido

Paso 1: Arrancar VX11

- Asegúrate de haber arrancado los procesos de VX11 (gateway y manifestator) en tu máquina según tu configuración local.

Paso 2: Atajos de teclado

- `Ctrl+Alt+1` → abre `gateway.http` (peticiones HTTP directas al gateway)
- `Ctrl+Alt+2` → abre `manifestator.http` (peticiones HTTP directas al manifestator)

Paso 3: Usar REST Client

- Abre `gateway.http` y selecciona la línea `GET {{gateway}}/vx11/status`.
- Pulsa el botón "Send Request" que aparece encima de la petición para ejecutar la solicitud.
- Abre `manifestator.http` y selecciona la petición deseada (drift, generate-patch, apply-patch), luego pulsa "Send Request".

Paso 4: Usar las tareas de VS Code

- Abrir el menú de tareas: `Terminal → Run Task…`.
- Ejecutar una de las tareas:
	- "VX11: Gateway Status"
	- "VX11: Manifestator Drift"
	- "VX11: Manifestator Generate Patch"
	- "VX11: Manifestator Apply Patch"

Notas:

- Todas las peticiones en este panel usan HTTP directo a puertos locales (`127.0.0.1`) y no usan HTTPS ni Caddy.
- No ejecutes comandos de sistema desde aquí; las tareas lanzan `curl` localmente.

