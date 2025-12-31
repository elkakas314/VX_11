# VX11 Operator

Operador VX11 contiene:

- `backend/`: API FastAPI para UI y orquestación segura (vía tentaculo_link).
- `frontend/`: UI React (Vite) consumiendo rutas públicas (`/operator/*`).

**Notas**
- En `solo_madre`, módulos full-profile permanecen OFF y deben responder `OFF_BY_POLICY`.
- El acceso externo siempre pasa por `tentaculo_link` (single entrypoint).
