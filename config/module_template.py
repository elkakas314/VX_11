from fastapi import FastAPI
from pydantic import BaseModel
from config.forensics import ensure_forensic_dirs, write_log, write_hash_manifest
try:
    # middleware import is optional but preferred
    from config.forensic_middleware import ForensicMiddleware
except Exception:
    ForensicMiddleware = None

try:
    from config.state_endpoints import create_state_router
except Exception:
    create_state_router = None


class ControlRequest(BaseModel):
    action: str = "status"


def create_module_app(name: str) -> FastAPI:
    app = FastAPI(title=f"VX11 {name}")

    # Registrar middleware forense si está disponible (captura excepciones y crea crash dumps)
    try:
        if ForensicMiddleware is not None:
            app.add_middleware(ForensicMiddleware)
    except Exception:
        # No romper la creación de la app si el middleware falla
        pass

    # Initialize forensic directories and write startup log and manifest
    try:
        ensure_forensic_dirs(name)
        write_log(name, "module_initializing")
        # write a quick manifest of repo hashes (only .py files to keep size small)
        write_hash_manifest(name, filter_exts={".py"})
    except Exception:
        # be conservative: do not raise during app creation
        pass

    # Agregar endpoints de control de estado (P&P)
    try:
        if create_state_router is not None:
            state_router = create_state_router(name)
            app.include_router(state_router)
    except Exception:
        write_log(name, "state_router_error", level="WARN")

    @app.get("/health")
    def health():
        return {"module": name, "status": "ok"}

    @app.post("/control")
    def control(req: ControlRequest):
        if req.action == "status":
            return {"module": name, "status": "running"}
        elif req.action in ("start", "stop", "restart"):
            # stub: aquí iría la lógica real
            write_log(name, f"control:{req.action}")
            return {"module": name, "action": req.action, "status": "accepted"}
        else:
            write_log(name, f"control:unknown:{req.action}", level="WARN")
            return {"module": name, "status": "unknown_action", "action": req.action}

    return app
