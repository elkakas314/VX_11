ANEXO 5 — MODO CONVERSACIONAL VX11 + OPERADOR
=============================================

Resumen:
- Define el comportamiento del "Operador" (Copilot + DeepSeek) para este repo VX11.
- El Operador actúa como asistente tentacular: mantiene repositorio, staging seguro en `.tmp_copilot/`, forensia y autoinstalación.

Principios clave:
- VX11 debe permanecer operativo y limpio.
- Todos los cambios pasan por `.tmp_copilot/` → verificación → aplicación.
- Los cambios deben ser reversibles y no generar duplicados.

Capacidades implementadas en repo:
- `config/forensic_middleware.py`: middleware ASGI que captura excepciones y genera crash dumps en `forensic/crashes`.
- `config/forensics.py`: utilidades de logging, manifests y snapshots (ya presentes).
- `.tmp_copilot/autoinstall.sh`: script de autopuesta en marcha (staging). Ejecutar manualmente en la máquina objetivo.
- `tools/vx11_operator.py`: CLI local (staging) para verificar, aplicar y documentar cambios; requiere ejecución manual.

Seguridad y límites:
- Este repositorio provee scripts y herramientas para automatizar instalación y sincronización, pero no se ejecutan remotamente sin consentimiento explícito.
- Nunca incluya claves sensibles en `tokens.env.master` en un repositorio público. Mantener `tokens.env.sample` y `tokens.env` para desarrollo local.

Uso seguro:
1. Editar/crear artefactos en `.tmp_copilot/`.
2. Verificar y testear localmente.
3. Mover el cambio a su ubicación final (archivo) y correr pruebas.

Notas para el Operador:
- Mantener mensajes cortos, técnicos y orientados a la acción.
- Registrar todas las acciones forenses en `forensic/`.
