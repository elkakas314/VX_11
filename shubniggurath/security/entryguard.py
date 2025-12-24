"""
VX11 EntryGuard Middleware — HMAC Signature Validation + Replay Protection

Este middleware es OBLIGATORIO para todas las rutas de Shub.
Valida:
- Headers requeridos (X-VX11-Entry, X-VX11-Request-Id, etc)
- HMAC-SHA256 signature contra VX11_TENTACULO_LINK_SHARED_SECRET
- Timestamp skew (max 30 segundos)
- Nonce replay protection (tabla shub_request_nonces)

Canonical String (HMAC input):
  METHOD\nPATH\nX-VX11-Timestamp\nX-VX11-Nonce\nSHA256(body)\nX-VX11-Request-Id\nX-VX11-Correlation-Id
"""

import hashlib
import hmac
import time
import os
import logging
from typing import Optional, Dict

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from shubniggurath.database.schema_shub_security import (
    check_nonce_exists,
    insert_nonce,
)

logger = logging.getLogger("shubniggurath.security.entryguard")

# Configuration (from environment or defaults)
SHARED_SECRET = os.getenv("VX11_TENTACULO_LINK_SHARED_SECRET", "")
MAX_SKEW_SECONDS = int(os.getenv("VX11_ENTRYGUARD_MAX_SKEW", "30"))
ENTRYGUARD_ENABLED = os.getenv("VX11_ENTRYGUARD_ENABLED", "1") == "1"

# Required headers specification
REQUIRED_HEADERS = {
    "X-VX11-Entry": "tentaculo_link",
    "X-VX11-Request-Id": None,  # Must exist, value flexible (uuid)
    "X-VX11-Correlation-Id": None,
    "X-VX11-Timestamp": None,  # Unix seconds
    "X-VX11-Nonce": None,  # Unique identifier
    "X-VX11-Signature": None,  # HMAC-SHA256 hex
}

# Endpoints que NO requieren firma (health checks públicos)
BYPASS_ENDPOINTS = {
    "/health",
    "/ready",
    "/openapi.json",
    "/docs",
    "/redoc",
}


# =============================================================================
# SIGNATURE VERIFICATION
# =============================================================================


def compute_canonical_string(
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    body_hash: str,
    request_id: str,
    correlation_id: str,
) -> str:
    """
    Build canonical string for HMAC verification.

    Format (exact):
        METHOD\nPATH\nTimestamp\nNonce\nBodyHash\nRequest-Id\nCorrelation-Id
    """
    return (
        f"{method}\n"
        f"{path}\n"
        f"{timestamp}\n"
        f"{nonce}\n"
        f"{body_hash}\n"
        f"{request_id}\n"
        f"{correlation_id}"
    )


def verify_hmac_signature(
    canonical_string: str,
    provided_signature: str,
    shared_secret: str,
) -> bool:
    """
    Verify HMAC-SHA256 signature.

    Args:
        canonical_string: Pre-built canonical string
        provided_signature: Hex signature from X-VX11-Signature header
        shared_secret: Shared secret key

    Returns:
        True if signature matches, False otherwise
    """
    if not shared_secret:
        logger.warning("ENTRYGUARD: No shared secret configured (INSECURE)")
        return False

    expected_sig = hmac.new(
        shared_secret.encode(),
        canonical_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_sig, provided_signature)


async def verify_vx11_signature(request: Request) -> Dict[str, str]:
    """
    Main signature verification logic.

    Args:
        request: FastAPI Request object

    Returns:
        Dict with extracted header values if valid

    Raises:
        HTTPException with appropriate status if invalid
    """

    # 1. Check if endpoint is in bypass list
    path = request.url.path
    if path in BYPASS_ENDPOINTS:
        return {}  # Skip verification

    # 2. Extract and validate required headers
    headers = dict(request.headers)
    missing = []
    extracted = {}

    for header_name, expected_value in REQUIRED_HEADERS.items():
        if header_name not in headers:
            missing.append(header_name)
        else:
            extracted[header_name] = headers[header_name]

            # Validate fixed value (if specified)
            if expected_value and headers[header_name] != expected_value:
                logger.warning(
                    f"ENTRYGUARD: Invalid {header_name}: expected '{expected_value}', "
                    f"got '{headers[header_name]}'"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Invalid {header_name} value",
                )

    if missing:
        logger.warning(f"ENTRYGUARD: Missing headers: {missing}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing required headers: {', '.join(missing)}",
        )

    # 3. Validate entry point
    if extracted["X-VX11-Entry"] != "tentaculo_link":
        logger.warning(f"ENTRYGUARD: Invalid entry point: {extracted['X-VX11-Entry']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid entry point (must be 'tentaculo_link')",
        )

    # 4. Check timestamp skew
    try:
        ts = int(extracted["X-VX11-Timestamp"])
    except ValueError:
        logger.warning(
            f"ENTRYGUARD: Invalid timestamp format: {extracted['X-VX11-Timestamp']}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid timestamp format",
        )

    now = int(time.time())
    skew = abs(now - ts)
    if skew > MAX_SKEW_SECONDS:
        logger.warning(
            f"ENTRYGUARD: Timestamp skew too large: {skew}s (max {MAX_SKEW_SECONDS}s)"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Timestamp skew exceeded ({skew}s > {MAX_SKEW_SECONDS}s)",
        )

    # 5. Check nonce for replay attacks
    nonce = extracted["X-VX11-Nonce"]
    if check_nonce_exists(nonce):
        logger.warning(f"ENTRYGUARD: Replay detected for nonce: {nonce}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nonce replay detected",
        )

    # Store nonce for future replay detection
    if not insert_nonce(nonce, ts):
        logger.warning(f"ENTRYGUARD: Failed to store nonce: {nonce}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate nonce",
        )

    # 6. Compute body hash and verify HMAC signature
    body = await request.body()
    body_hash = hashlib.sha256(body).hexdigest()

    canonical_string = compute_canonical_string(
        method=request.method,
        path=path,
        timestamp=extracted["X-VX11-Timestamp"],
        nonce=nonce,
        body_hash=body_hash,
        request_id=extracted["X-VX11-Request-Id"],
        correlation_id=extracted["X-VX11-Correlation-Id"],
    )

    if not verify_hmac_signature(
        canonical_string,
        extracted["X-VX11-Signature"],
        SHARED_SECRET,
    ):
        logger.warning(f"ENTRYGUARD: Invalid HMAC signature from {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC signature",
        )

    logger.debug(f"ENTRYGUARD: Valid signature for {request.method} {path}")
    return extracted


# =============================================================================
# MIDDLEWARE
# =============================================================================


class ShubEntryGuardMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for VX11 EntryGuard validation.

    Apply with: app.add_middleware(ShubEntryGuardMiddleware)
    """

    async def dispatch(self, request: Request, call_next):
        if not ENTRYGUARD_ENABLED:
            logger.debug("ENTRYGUARD: Disabled (VX11_ENTRYGUARD_ENABLED=0)")
            return await call_next(request)

        try:
            # Verify signature
            await verify_vx11_signature(request)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"ENTRYGUARD: Unexpected error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error during signature verification"
                },
            )

        # Proceed to next middleware/handler
        return await call_next(request)
