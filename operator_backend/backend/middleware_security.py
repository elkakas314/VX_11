"""
operator_backend/backend/middleware_security.py

Middleware de seguridad para FASE E:
- Rate limiting (100 req/min per token)
- CSRF token validation
- Structured JSON logs
"""

import time
import uuid
import json
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger("security_middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting: 100 requests/minute per auth token."""

    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Get auth token from header
        auth_header = request.headers.get("authorization", "anonymous")
        auth_token = auth_header.replace("Bearer ", "")

        # Get current time
        now = time.time()
        cutoff_time = now - 60  # Last 60 seconds

        # Clean old requests
        if auth_token in self.request_history:
            self.request_history[auth_token] = [
                ts for ts in self.request_history[auth_token] if ts > cutoff_time
            ]

        # Check rate limit
        request_count = len(self.request_history[auth_token])
        if request_count >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for token: {auth_token[:10]}...")
            return Response(
                json.dumps(
                    {
                        "ok": False,
                        "errors": ["Rate limit exceeded (100 req/min)"],
                        "data": {},
                    }
                ),
                status_code=429,
                media_type="application/json",
            )

        # Record this request
        self.request_history[auth_token].append(now)

        # Add rate limit info to request state
        request.state.rate_limit_remaining = (
            self.requests_per_minute - request_count - 1
        )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(
            request.state.rate_limit_remaining
        )
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF token validation for POST/PUT/DELETE requests."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.csrf_tokens: Dict[str, float] = {}

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # For POST/PUT/DELETE, require CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            logger.warning(
                f"CSRF token missing for {request.method} {request.url.path}"
            )
            return Response(
                json.dumps(
                    {
                        "ok": False,
                        "errors": ["CSRF token required"],
                        "data": {},
                    }
                ),
                status_code=403,
                media_type="application/json",
            )

        # Validate token (in production: check against session store)
        if (
            csrf_token not in self.csrf_tokens
            or (time.time() - self.csrf_tokens[csrf_token]) > 3600
        ):
            logger.warning(f"Invalid or expired CSRF token")
            return Response(
                json.dumps(
                    {
                        "ok": False,
                        "errors": ["Invalid or expired CSRF token"],
                        "data": {},
                    }
                ),
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)

    def generate_csrf_token(self) -> str:
        """Generate a new CSRF token."""
        token = str(uuid.uuid4())
        self.csrf_tokens[token] = time.time()
        # Cleanup old tokens
        self.csrf_tokens = {
            k: v for k, v in self.csrf_tokens.items() if time.time() - v < 3600
        }
        return token


class StructuredLogsMiddleware(BaseHTTPMiddleware):
    """Structured JSON logging with request_id, route_taken, elapsed_ms, status."""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Get route_taken
        route_taken = f"{request.method} {request.url.path}"

        # Call next middleware
        try:
            response = await call_next(request)
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "route_taken": route_taken,
                "status": 500,
                "elapsed_ms": elapsed_ms,
                "error": str(e),
            }
            logger.error(json.dumps(log_entry))
            raise

        # Calculate elapsed time
        elapsed_ms = (time.time() - start_time) * 1000

        # Build structured log
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "route_taken": route_taken,
            "status": response.status_code,
            "elapsed_ms": round(elapsed_ms, 2),
            "auth_token": request.headers.get("authorization", "none")[:20],
            "user_agent": request.headers.get("user-agent", "unknown")[:50],
        }

        # Log based on status
        if response.status_code >= 500:
            logger.error(json.dumps(log_entry))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_entry))
        else:
            logger.info(json.dumps(log_entry))

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Elapsed-Ms"] = str(round(elapsed_ms, 2))

        return response
