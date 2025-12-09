# Madre v6.3
- Orquestador y P&P: estados off/standby/active por módulo en `_MODULE_STATES`.
- Reglas: si `ModuleHealth.error_count` supera umbral → off; si idle prolongado → standby; peticiones activan estado.
- Endpoints: `/orchestration/module_states`, `/orchestration/set_module_state`.
- Persistencia: tablas `madre_policies` y `madre_actions` guardan políticas y acciones aplicadas.
