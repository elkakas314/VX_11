# VX11 Operator (Unificado)

## Estructura
- `backend/` FastAPI + WebSocket bridge hacia `tentaculo_link` (puerto 8000).
- `frontend/` React/Vite UI (dashboard, chat, Shub).
- `disabled/` Modo legacy conservado para compatibilidad.
- `main.py` expone `app` para uvicorn.

## Desarrollo
```bash
cd operator/frontend
npm install
npm run dev
```
Backend:
```bash
uvicorn operator.main:app --host 0.0.0.0 --port 8011 --reload
```

## Producción
- Backend: `uvicorn operator.main:app --port 8011`
- Frontend: build con Vite, servido por NGINX (ver Dockerfile).
- Token obligatorio: header `X-VX11-Token` igual a `VX11_TENTACULO_LINK_TOKEN` (fallback a `VX11_GATEWAY_TOKEN`).

## Endpoints clave
- `GET /health`
- `GET /system/status`
- `POST /intent` (proxy Tentáculo Link)
- `POST /intent/chat` (Switch)
- `POST /shub/upload`
- `GET /ws` (bridge a Tentáculo Link)
