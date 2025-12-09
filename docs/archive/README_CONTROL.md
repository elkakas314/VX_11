Cómo usar `gateway.http`

- Abre el archivo `gateway.http` en el workspace.
- Selecciona la petición `GET {{gateway}}/vx11/status`.
- Usa la acción "Send Request" del REST Client (icono "Send Request" que aparece arriba de la petición) para ejecutarla.

Cómo usar `manifestator.http`

- Abre el archivo `manifestator.http` en el workspace.
- Selecciona la petición `GET {{gateway}}/manifestator/drift`.
- Pulsa "Send Request" para enviarla.

Indicaciones para "Send Request"

- El REST Client mostrará la respuesta en una pestaña lateral o en el panel de respuesta.
- Si la petición usa `https://localhost`, acepta certificados locales si VS Code lo solicita.
- Verifica el header y el entorno `{{gateway}}` en `.vscode/settings.json` antes de enviar.

Indicaciones de uso del REST Client

- Asegúrate de tener la extensión "REST Client" instalada.
- Los endpoints usan la variable `{{gateway}}` definida en el workspace.
- Para cambiar target, edita la variable `gateway` en `.vscode/settings.json`.
