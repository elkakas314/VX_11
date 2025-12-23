import logging
import httpx
import os
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from config.settings import VX11Settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("operator-backend")

# Load settings
settings = VX11Settings()

app = FastAPI(
    title="VX11 Operator Backend",
    version=settings.version,
    description="Canonical Operator Backend for VX11. Provides local control and proxy to Madre."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for local authentication
async def verify_token(x_vx11_token: str = Header(None, alias=settings.token_header)):
    """
    Simple token-based authentication for local operator.
    In production, this should be more robust.
    """
    if settings.enable_auth:
        if not x_vx11_token or x_vx11_token != settings.api_token:
            logger.warning(f"Unauthorized access attempt. Header: {settings.token_header}")
            raise HTTPException(status_code=401, detail="Unauthorized")
    return x_vx11_token

@app.get("/health")
async def health():
    """
    Canonical health endpoint.
    """
    return {
        "status": "healthy",
        "module": "operator-backend",
        "version": settings.version,
        "madre_url": settings.madre_url,
        "timestamp": os.popen("date -u +'%Y-%m-%dT%H:%M:%SZ'").read().strip()
    }

@app.get("/status")
async def get_system_status(token: str = Depends(verify_token)):
    """
    Aggregated system status.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Query Madre's health
            response = await client.get(
                f"{settings.madre_url}/health",
                headers={settings.token_header: settings.api_token},
                timeout=5.0
            )
            madre_status = response.json() if response.status_code == 200 else {"status": "error", "code": response.status_code}
        except Exception as exc:
            logger.error(f"Madre health check failed: {exc}")
            madre_status = {"status": "unreachable", "error": str(exc)}

    return {
        "operator": "online",
        "madre": madre_status,
        "environment": settings.environment,
        "version": settings.version
    }

@app.api_route("/madre/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_madre(path: str, request: Request, token: str = Depends(verify_token)):
    """
    Proxy requests to Madre core orchestrator.
    This allows the operator UI to communicate with Madre through the backend.
    """
    target_url = f"{settings.madre_url}/{path}"
    logger.info(f"Proxying {request.method} request to: {target_url}")
    
    # Prepare request components
    params = dict(request.query_params)
    body = await request.body()
    
    # Forward headers, but override auth with internal token
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    headers[settings.token_header] = settings.api_token

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=params,
                content=body,
                headers=headers,
                timeout=60.0
            )
            
            # Return response from Madre
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    return JSONResponse(content=response.json(), status_code=response.status_code)
                except Exception:
                    return JSONResponse(content={"detail": response.text}, status_code=response.status_code)
            else:
                return JSONResponse(content={"detail": response.text}, status_code=response.status_code)
                
        except httpx.RequestError as exc:
            logger.error(f"Error proxying to Madre at {target_url}: {exc}")
            raise HTTPException(status_code=502, detail=f"Madre unreachable: {exc}")
        except Exception as exc:
            logger.error(f"Unexpected error during proxy: {exc}")
            raise HTTPException(status_code=500, detail=str(exc))

def get_http_client():
    \"\"\"Compatibility shim for tests.\"\"\"
    return httpx.AsyncClient()

if __name__ == "__main__":
    import uvicorn
    # Use settings for port if available, else default to 8011
    port = getattr(settings, "operator_port", 8011)
    uvicorn.run(app, host="0.0.0.0", port=port)
