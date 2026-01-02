import time
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any


def json_response_403_off_by_policy(
    policy: str = "solo_madre",
    reason: str = "Operation disabled by current policy",
    retry_after_ms: int = 0,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Return structured 403 OFF_BY_POLICY response.
    Used when solo_madre policy blocks an operation.
    """
    content = {
        "status": "off_by_policy",
        "policy": policy,
        "reason": reason,
        "retry_after_ms": retry_after_ms,
        "details": details or {},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    headers = {}
    if retry_after_ms > 0:
        headers["Retry-After"] = str(retry_after_ms // 1000)
    return JSONResponse(status_code=403, content=content, headers=headers)
