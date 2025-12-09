from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import traceback
import json
from typing import Callable


class ForensicMiddleware(BaseHTTPMiddleware):
    """Middleware ASGI que captura excepciones no manejadas y las registra
    usando el sistema forense (`config.forensics.record_crash`).

    Es segura: en caso de fallo interno, no suprime la excepción original.
    """

    def __init__(self, app, dispatch: Callable = None):
        super().__init__(app, dispatch)

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Intentar registrar el crash forensemente; no detener la excepción original
            try:
                # Import tardío para evitar ciclos de import
                from config.forensics import record_crash, write_log

                # Construir un resumen seguro del request
                try:
                    body = await request.body()
                    body_text = body.decode(errors="replace")
                except Exception:
                    body_text = "<unreadable>"

                extra = {
                    "path": str(request.url.path),
                    "method": request.method,
                    "headers": {k: v for k, v in request.headers.items()},
                    "body": body_text,
                }

                # Registrar un log previo
                try:
                    app_name = getattr(request.scope.get("app"), "title", "vx11")
                except Exception:
                    app_name = "vx11"

                write_log(app_name, f"exception_captured: {type(exc).__name__}")
                # record_crash acepta el objeto de excepción
                record_crash(app_name, exc)
            except Exception:
                # fallar silenciosamente en el registro forense
                pass
            # Re-emitir la excepción para que el manejador de FastAPI/uvicorn la procese
            raise
