"""
VX11 WindowGuard — Bearer Token Validation Against Madre

Este decorator es OBLIGATORIO para endpoints mutadores (POST, PUT, DELETE que modifiquen estado).

Validación:
- Extrae Bearer token de Authorization header
- Introspección a Madre POST /auth/window/verify
- Cache local en shub_window_cache para reducir latencia
- Scopes validation (por endpoint)

Uso:
  @app.post("/jobs")
  async def submit_job(window: dict = Depends(require_window_token)):
      # window contiene: {valid, scopes, claims, ...}
      pass
"""

import hashlib
import logging
import os
from typing import Optional, List

import requests
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthCredentialBase

from shubniggurath.database.schema_shub_security import (
    get_cached_token_scopes,
    cache_window_token,
)

logger = logging.getLogger("shubniggurath.security.windowguard")

# Configuration
MADRE_URL = os.getenv("MADRE_URL", "http://madre:8001")
MADRE_VERIFY_ENDPOINT = f"{MADRE_URL}/auth/window/verify"
MADRE_VERIFY_TIMEOUT = int(os.getenv("VX11_MADRE_VERIFY_TIMEOUT", "5"))
WINDOWGUARD_ENABLED = os.getenv("VX11_WINDOWGUARD_ENABLED", "1") == "1"


# Custom credential class for more explicit Bearer token handling
class BearerCredentials(HTTPAuthCredentialBase):
    """Custom Bearer credentials extractor"""

    scheme = "Bearer"

    def __init__(self, token: str):
        self.token = token


def extract_bearer_token(authorization: str = Header(None)) -> str:
    """
    Extract Bearer token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer token123")

    Returns:
        Token string

    Raises:
        HTTPException if invalid format or missing
    """
    if not authorization:
        logger.warning("WINDOWGUARD: Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(
            f"WINDOWGUARD: Invalid Authorization format: {parts[0] if parts else 'empty'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization format (expected 'Bearer <token>')",
        )

    return parts[1]


def hash_token(token: str) -> str:
    """SHA256 hash of token (for caching without storing plaintext)"""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_with_madre(
    token: str,
    audience: str = "shubniggurath",
    scopes: Optional[List[str]] = None,
) -> dict:
    """
    Call Madre window/verify endpoint to validate token.

    Args:
        token: Bearer token
        audience: Expected audience (default: "shubniggurath")
        scopes: Required scopes (optional)

    Returns:
        Response dict: {valid, scopes, claims, ...}

    Raises:
        HTTPException on error
    """
    try:
        payload = {
            "token": token,
            "audience": audience,
        }
        if scopes:
            payload["scopes"] = scopes

        resp = requests.post(
            MADRE_VERIFY_ENDPOINT,
            json=payload,
            timeout=MADRE_VERIFY_TIMEOUT,
        )

        if resp.status_code != 200:
            logger.warning(
                f"WINDOWGUARD: Madre returned {resp.status_code}: {resp.text[:200]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid window token (Madre validation failed)",
            )

        data = resp.json()
        if not data.get("valid"):
            logger.warning(f"WINDOWGUARD: Madre marked token as invalid")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Window token invalid or expired",
            )

        return data

    except requests.RequestException as e:
        logger.error(f"WINDOWGUARD: Madre connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Madre window verification unavailable",
        )


async def require_window_token(
    authorization: str = Header(None),
    required_scopes: Optional[List[str]] = None,
) -> dict:
    """
    Dependency for FastAPI endpoint protection.

    Usage:
        @app.post("/jobs")
        async def submit_job(window: dict = Depends(require_window_token)):
            pass

    Args:
        authorization: Authorization header
        required_scopes: List of required scopes (optional)

    Returns:
        dict with token claims/scopes

    Raises:
        HTTPException on invalid token
    """
    if not WINDOWGUARD_ENABLED:
        logger.debug("WINDOWGUARD: Disabled")
        return {"valid": True, "scopes": ["shub:mutate"]}

    # Extract token
    token = extract_bearer_token(authorization)
    token_hash = hash_token(token)

    # Try cache first
    cached_scopes = get_cached_token_scopes(token_hash)
    if cached_scopes:
        logger.debug(f"WINDOWGUARD: Cache hit for token {token_hash[:8]}...")
        result = {
            "valid": True,
            "scopes": cached_scopes.split(","),
            "cached": True,
        }
    else:
        # Verify with Madre
        result = verify_with_madre(token, scopes=required_scopes)

        # Cache result if token has expiry
        if "exp" in result.get("claims", {}):
            exp_ts = result["claims"]["exp"]
            iat_ts = result["claims"].get("iat", 0)
            scopes_str = ",".join(result.get("scopes", []))

            if cache_window_token(token_hash, iat_ts, exp_ts, scopes_str):
                logger.debug(
                    f"WINDOWGUARD: Cached token {token_hash[:8]}... until {exp_ts}"
                )

        result["cached"] = False

    # Validate required scopes
    if required_scopes:
        token_scopes = set(result.get("scopes", []))
        missing = set(required_scopes) - token_scopes

        if missing:
            logger.warning(
                f"WINDOWGUARD: Token missing scopes: {missing} "
                f"(has: {token_scopes})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token missing required scopes: {', '.join(missing)}",
            )

    return result


# =============================================================================
# DECORATORS & HELPERS
# =============================================================================


def require_scopes(*scopes: str):
    """
    Decorator to specify required scopes for an endpoint.

    Usage:
        @app.post("/jobs")
        @require_scopes("shub:jobs:submit", "shub:mutate")
        async def submit_job(window: dict = Depends(require_window_token)):
            pass
    """

    def decorator(func):
        func._required_scopes = list(scopes)
        return func

    return decorator


async def get_window_with_scopes(
    required_scopes: Optional[List[str]] = None,
) -> dict:
    """
    Helper to manually invoke window guard with specific scopes.

    Args:
        required_scopes: List of required scopes

    Returns:
        Window token claims dict
    """
    # This would be called inside an endpoint as:
    # window = await get_window_with_scopes(["shub:mutate"])
    pass  # Placeholder (use require_window_token dependency instead)
